"""Stage 1 of discovery: find candidate scheme URLs. No LLM, no cost.

Two mechanisms:
  sitemap - read robots.txt Sitemap: entries plus the conventional paths,
            follow <sitemapindex> children, collect every <loc>.
  index   - fetch the configured index pages and take every same-host link.

Every URL is then filtered by keyword and blocklist. Output is JSONL, one
candidate per line, which stage 2 (classify.py) consumes.

    python harvest.py --config sources.yaml --out candidates.jsonl
    python harvest.py --only tn_gov --out tn.jsonl
"""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import yaml
from bs4 import BeautifulSoup

from fetcher import PoliteFetcher

SITEMAP_PATHS = ("/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml")
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


@dataclass
class Candidate:
    url: str
    domain: str
    source_id: str
    level: str
    state: str | None
    method: str
    matched_keyword: str
    discovered_at: str


# -- pure helpers ------------------------------------------------------


def matches_keyword(url: str, keywords: list[str]) -> str | None:
    """Return the first keyword found in the URL, or None."""
    lowered = url.lower()
    for kw in keywords:
        if kw.lower() in lowered:
            return kw
    return None


def is_blocked(url: str, blocklist: list[str]) -> bool:
    lowered = url.lower()
    return any(bad.lower() in lowered for bad in blocklist)


def parse_sitemap(xml_text: str) -> tuple[list[str], list[str]]:
    """Return (page_urls, child_sitemap_urls) from one sitemap document.

    Handles both <urlset> and <sitemapindex>, with or without the namespace.
    """
    try:
        root = ET.fromstring(xml_text.strip())
    except ET.ParseError:
        return [], []

    def locs(tag: str) -> list[str]:
        found = root.findall(f"{SITEMAP_NS}{tag}") or root.findall(tag)
        out = []
        for node in found:
            loc = node.find(f"{SITEMAP_NS}loc")
            if loc is None:
                loc = node.find("loc")
            if loc is not None and loc.text:
                out.append(loc.text.strip())
        return out

    tag = root.tag.split("}")[-1]
    if tag == "sitemapindex":
        return [], locs("sitemap")
    return locs("url"), []


def links_from_html(html: str, base_url: str) -> list[str]:
    """Absolute, same-host links from an index page, de-duplicated."""
    soup = BeautifulSoup(html, "lxml")
    host = urlparse(base_url).netloc
    seen: dict[str, None] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
            continue
        absolute = urljoin(base_url, href).split("#")[0]
        if urlparse(absolute).netloc != host:
            continue
        seen.setdefault(absolute, None)
    return list(seen)


# -- harvest -----------------------------------------------------------


def sitemap_urls(fetcher: PoliteFetcher, base_url: str, max_docs: int = 40) -> list[str]:
    """Walk a site's sitemaps and return every page URL found."""
    queue = list(fetcher.sitemaps_from_robots(base_url))
    queue += [urljoin(base_url, path) for path in SITEMAP_PATHS]
    seen_docs: set[str] = set()
    pages: list[str] = []

    while queue and len(seen_docs) < max_docs:
        doc_url = queue.pop(0)
        if doc_url in seen_docs:
            continue
        seen_docs.add(doc_url)
        result = fetcher.get(doc_url)
        if result is None or not result.ok:
            continue
        page_urls, child_sitemaps = parse_sitemap(result.text)
        pages.extend(page_urls)
        queue.extend(child_sitemaps)

    return pages


def index_urls(fetcher: PoliteFetcher, index_pages: list[str]) -> list[str]:
    out: list[str] = []
    for page in index_pages:
        result = fetcher.get(page)
        if result is None or not result.ok:
            continue
        out.extend(links_from_html(result.text, page))
    return out


def harvest_source(
    fetcher: PoliteFetcher, source: dict, keywords: list[str], blocklist: list[str], cap: int
) -> list[Candidate]:
    raw: list[tuple[str, str]] = []
    method = source.get("method", "sitemap")

    if method in ("sitemap", "both"):
        raw += [(u, "sitemap") for u in sitemap_urls(fetcher, source["base_url"])]
    if method in ("index", "both"):
        raw += [(u, "index") for u in index_urls(fetcher, source.get("index_pages") or [])]

    now = datetime.now(timezone.utc).isoformat()
    seen: set[str] = set()
    candidates: list[Candidate] = []

    for url, how in raw:
        if url in seen or is_blocked(url, blocklist):
            continue
        kw = matches_keyword(url, keywords)
        if kw is None:
            continue
        seen.add(url)
        candidates.append(
            Candidate(
                url=url,
                domain=urlparse(url).netloc,
                source_id=source["id"],
                level=source.get("level", "unknown"),
                state=source.get("state"),
                method=how,
                matched_keyword=kw,
                discovered_at=now,
            )
        )
        if len(candidates) >= cap:
            break

    return candidates


def main() -> None:
    ap = argparse.ArgumentParser(description="Harvest candidate scheme URLs.")
    ap.add_argument("--config", default="sources.yaml")
    ap.add_argument("--out", default="candidates.jsonl")
    ap.add_argument("--only", help="run a single source id")
    ap.add_argument("--cache", default=".cache/discovery")
    args = ap.parse_args()

    config = yaml.safe_load(Path(args.config).read_text())
    keywords = config["keywords"]
    blocklist = config.get("url_blocklist", [])
    defaults = config.get("defaults", {})
    cap = int(defaults.get("max_urls_per_source", 4000))

    sources = [s for s in config["sources"] if s.get("enabled", False)]
    if args.only:
        sources = [s for s in config["sources"] if s["id"] == args.only]
        if not sources:
            raise SystemExit(f"no source with id {args.only!r}")

    out_path = Path(args.out)
    written = 0

    # Append per source, so an interrupted run keeps what it already found.
    with PoliteFetcher(cache_dir=Path(args.cache), delay=float(defaults.get("delay", 1.0))) as f:
        with out_path.open("w", encoding="utf-8") as fh:
            for source in sources:
                print(f"[harvest] {source['id']} ...", flush=True)
                try:
                    found = harvest_source(f, source, keywords, blocklist, cap)
                except Exception as exc:  # one bad site must not kill the run
                    print(f"[harvest] {source['id']} failed: {exc}", flush=True)
                    continue
                for c in found:
                    fh.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
                fh.flush()
                written += len(found)
                print(f"[harvest] {source['id']}: {len(found)} candidates", flush=True)

    print(f"[harvest] {written} candidates -> {out_path}")


if __name__ == "__main__":
    main()
