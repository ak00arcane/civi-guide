"""CLI: one-shot watcher run (Phase 6, see docs/TRUST_PIPELINE.md). Refetches
each verified scheme's official source, diffs against the last snapshot, and
re-extracts + re-scores changed ones if an extractor is configured. Manual
trigger only — no cron is wired up from this repo; run this by hand (or from
your own scheduler) when you want a fresh pass.

Usage (from backend/):
    python scripts/watch_sources.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.models import Scheme
from db.session import SessionLocal
from extraction.extractor import get_configured_extractor
from services.fetch_layer import PoliteFetcher
from services.watcher import watch_scheme_source


def main() -> None:
    db = SessionLocal()
    fetcher = PoliteFetcher()
    extractor = get_configured_extractor()
    if extractor is None:
        print(
            "No GEMINI_API_KEY or ANTHROPIC_API_KEY set - refetching and hash-diffing only; "
            "re-extraction/re-scoring will be skipped.\n",
            flush=True,
        )

    try:
        for scheme in db.query(Scheme).filter(Scheme.is_demo == False).all():  # noqa: E712
            for source in scheme.sources:
                result = watch_scheme_source(db, scheme, source, fetcher, extractor)
                db.commit()  # commit per source - an interrupted run keeps whatever it finished
                print(
                    f"{result.outcome.upper():12} {scheme.scheme_id:28} {result.source_url}  {result.detail}",
                    flush=True,
                )
    finally:
        fetcher.close()
        db.close()


if __name__ == "__main__":
    main()
