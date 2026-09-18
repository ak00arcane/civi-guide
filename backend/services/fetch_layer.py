"""Polite fetch layer for the trust pipeline (see docs/TRUST_PIPELINE.md, Phase 2).

Respects robots.txt per-domain, rate-limits to one request per domain per
`min_interval_seconds`, retries transient failures with backoff, and writes
every successful fetch into the raw snapshot store. Not wired to a cron yet
(that's Phase 6) — invoke via `backend/scripts/fetch_sources.py`.
"""

import ssl
import time
from urllib import robotparser
from urllib.parse import urlparse

import httpx
import truststore
from db.models import RawSnapshot
from services.snapshots import save_snapshot
from sqlalchemy.orm import Session

USER_AGENT = "CivicGuideBot/0.1 (+https://github.com/civicguide/civicguide; research/non-commercial polite crawler)"
DEFAULT_MIN_INTERVAL_SECONDS = 1.0
DEFAULT_TIMEOUT_SECONDS = 15.0
MAX_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 2.0


class FetchSkipped(Exception):
    """Raised when a URL is not fetched — currently only for robots.txt disallow."""


def _default_client() -> httpx.Client:
    """Uses the OS-native certificate store (via truststore) instead of a static
    CA bundle. Several .gov.in sites (mudra.org.in, scd.tn.gov.in — found on a
    live run) serve an incomplete certificate chain that a static bundle can't
    validate but the OS's own chain-building can, since it fetches missing
    intermediates the same way a browser does. Verification stays fully on -
    this is not verify=False."""
    ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    return httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=DEFAULT_TIMEOUT_SECONDS, follow_redirects=True, verify=ctx)


class PoliteFetcher:
    def __init__(
        self,
        client: httpx.Client | None = None,
        min_interval_seconds: float = DEFAULT_MIN_INTERVAL_SECONDS,
    ):
        self.client = client or _default_client()
        self.min_interval_seconds = min_interval_seconds
        self._robots_cache: dict[str, robotparser.RobotFileParser] = {}
        self._last_request_at: dict[str, float] = {}

    def _robots_for(self, url: str) -> robotparser.RobotFileParser:
        netloc = urlparse(url).netloc
        if netloc in self._robots_cache:
            return self._robots_cache[netloc]
        rp = robotparser.RobotFileParser()
        robots_url = f"{urlparse(url).scheme}://{netloc}/robots.txt"
        try:
            resp = self.client.get(robots_url)
            rp.parse(resp.text.splitlines() if resp.status_code == 200 else [])
        except httpx.HTTPError:
            rp.parse([])  # unreachable robots.txt -> treat as permissive, still rate-limited
        self._robots_cache[netloc] = rp
        return rp

    def _wait_for_slot(self, url: str) -> None:
        netloc = urlparse(url).netloc
        last = self._last_request_at.get(netloc)
        if last is not None:
            remaining = self.min_interval_seconds - (time.monotonic() - last)
            if remaining > 0:
                time.sleep(remaining)
        self._last_request_at[netloc] = time.monotonic()

    def fetch(self, url: str) -> httpx.Response:
        robots = self._robots_for(url)
        if not robots.can_fetch(USER_AGENT, url):
            raise FetchSkipped(f"{url} disallowed by robots.txt")

        last_exc: Exception | None = None
        for attempt in range(MAX_ATTEMPTS):
            self._wait_for_slot(url)
            try:
                resp = self.client.get(url)
                if resp.status_code >= 500:
                    resp.raise_for_status()
                return resp
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt < MAX_ATTEMPTS - 1:
                    time.sleep(BACKOFF_BASE_SECONDS * (2**attempt))
        raise last_exc

    def fetch_and_store(
        self,
        db: Session,
        url: str,
        *,
        source_type: str | None = None,
        scheme_pk: str | None = None,
    ) -> RawSnapshot:
        resp = self.fetch(url)
        return save_snapshot(
            db,
            source_url=url,
            content=resp.content,
            source_type=source_type,
            http_status=resp.status_code,
            scheme_pk=scheme_pk,
        )

    def close(self) -> None:
        self.client.close()
