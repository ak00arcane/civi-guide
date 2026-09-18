"""Polite HTTP fetching shared by the harvester and the classifier.

Rules this module enforces, in order:
  1. robots.txt is consulted per host and cached for the process lifetime.
     A disallowed URL is never fetched.
  2. One request per second per host, minimum.
  3. Every response body is cached on disk by URL hash, so re-running a stage
     costs nothing and never re-hammers a government site.
  4. TLS chains are validated against the OS trust store when `truststore` is
     available, which is what makes the .gov.in sites with incomplete chains
     work. Verification is never disabled.
"""

from __future__ import annotations

import hashlib
import json
import ssl
import time
import urllib.robotparser
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx

USER_AGENT = (
    "CivicGuideBot/0.1 (+student research project; contact: you@example.com)"
)

DEFAULT_CACHE = Path(".cache/discovery")


def _ssl_context() -> ssl.SSLContext:
    try:
        import truststore

        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except ImportError:
        return ssl.create_default_context()


def url_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


@dataclass
class FetchResult:
    url: str
    status: int
    body: bytes
    from_cache: bool
    final_url: str

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300


class PoliteFetcher:
    def __init__(
        self,
        cache_dir: Path = DEFAULT_CACHE,
        delay: float = 1.0,
        timeout: float = 30.0,
        respect_robots: bool = True,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.delay = delay
        self.respect_robots = respect_robots
        self._last_hit: dict[str, float] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            follow_redirects=True,
            verify=_ssl_context(),
        )

    # -- cache ---------------------------------------------------------

    def _cache_paths(self, url: str) -> tuple[Path, Path]:
        key = url_key(url)
        return self.cache_dir / f"{key}.body", self.cache_dir / f"{key}.meta.json"

    def _read_cache(self, url: str) -> FetchResult | None:
        body_path, meta_path = self._cache_paths(url)
        if not (body_path.exists() and meta_path.exists()):
            return None
        meta = json.loads(meta_path.read_text())
        return FetchResult(
            url=url,
            status=meta["status"],
            body=body_path.read_bytes(),
            from_cache=True,
            final_url=meta.get("final_url", url),
        )

    def _write_cache(self, result: FetchResult) -> None:
        body_path, meta_path = self._cache_paths(result.url)
        body_path.write_bytes(result.body)
        meta_path.write_text(
            json.dumps(
                {
                    "status": result.status,
                    "final_url": result.final_url,
                    "fetched_at": time.time(),
                }
            )
        )

    # -- robots --------------------------------------------------------

    def _robots_for(self, url: str) -> urllib.robotparser.RobotFileParser | None:
        host = urlparse(url).netloc
        if host in self._robots:
            return self._robots[host]
        scheme = urlparse(url).scheme or "https"
        robots_url = f"{scheme}://{host}/robots.txt"
        parser = urllib.robotparser.RobotFileParser()
        try:
            resp = self._client.get(robots_url)
            if 200 <= resp.status_code < 300:
                parser.parse(resp.text.splitlines())
            else:
                parser.parse([])  # no robots.txt means everything is allowed
        except Exception:
            parser = None  # unreachable robots.txt: treat host as off limits
        self._robots[host] = parser
        return parser

    def allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        parser = self._robots_for(url)
        if parser is None:
            return False
        return parser.can_fetch(USER_AGENT, url)

    def sitemaps_from_robots(self, url: str) -> list[str]:
        parser = self._robots_for(url)
        if parser is None:
            return []
        return list(getattr(parser, "sitemaps", None) or [])

    # -- fetch ---------------------------------------------------------

    def _throttle(self, host: str) -> None:
        last = self._last_hit.get(host)
        if last is not None:
            wait = self.delay - (time.time() - last)
            if wait > 0:
                time.sleep(wait)
        self._last_hit[host] = time.time()

    def get(self, url: str, use_cache: bool = True) -> FetchResult | None:
        if use_cache:
            cached = self._read_cache(url)
            if cached is not None:
                return cached
        if not self.allowed(url):
            return None
        self._throttle(urlparse(url).netloc)
        try:
            resp = self._client.get(url)
        except Exception:
            return None
        result = FetchResult(
            url=url,
            status=resp.status_code,
            body=resp.content,
            from_cache=False,
            final_url=str(resp.url),
        )
        if result.ok:
            self._write_cache(result)
        return result

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "PoliteFetcher":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
