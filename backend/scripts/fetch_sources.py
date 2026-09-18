"""CLI: polite fetch of each verified scheme's official source URL into the raw
snapshot store. Manual-trigger only for now (Phase 2) — the weekly cron comes
in Phase 6. See docs/TRUST_PIPELINE.md.

Usage (from backend/):
    python scripts/fetch_sources.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.models import Scheme
from db.session import SessionLocal
from services.fetch_layer import FetchSkipped, PoliteFetcher


def _source_type_for(url: str) -> str:
    if "myscheme.gov.in" in url:
        return "myscheme"
    if ".gov.in" in url:
        return "gov_ministry"
    return "state_portal"


def main() -> None:
    db = SessionLocal()
    fetcher = PoliteFetcher()
    seen: set[str] = set()
    try:
        for scheme in db.query(Scheme).filter(Scheme.is_demo == False).all():  # noqa: E712 - SQLAlchemy needs `== False`, not `is False`
            for source in scheme.sources:
                url = source.official_source
                if not url or url in seen:
                    continue
                seen.add(url)
                try:
                    snap = fetcher.fetch_and_store(
                        db, url, source_type=_source_type_for(url), scheme_pk=scheme.id
                    )
                    db.commit()  # commit per URL - an interrupted run keeps whatever it finished
                    print(f"OK   {url} -> {snap.content_hash[:12]} ({snap.http_status})", flush=True)
                except FetchSkipped as exc:
                    print(f"SKIP {url}: {exc}", flush=True)
                except Exception as exc:  # noqa: BLE001 - CLI: report and continue to next URL
                    print(f"FAIL {url}: {exc}", flush=True)
    finally:
        fetcher.close()
        db.close()


if __name__ == "__main__":
    main()
