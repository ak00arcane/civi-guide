"""CLI: extract + re-score every verified scheme from its latest stored
snapshot, without doing a new fetch (see docs/TRUST_PIPELINE.md, Phases 3-4).
Useful for iterating on the extractor/trust engine without re-hitting
external sites. Requires GEMINI_API_KEY or ANTHROPIC_API_KEY (see .env.example).

Usage (from backend/):
    python scripts/score_from_snapshots.py
"""

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.models import Scheme
from db.session import SessionLocal
from extraction.extractor import ExtractorUnavailable, get_configured_extractor
from extraction.golden_set import score_rules
from services.snapshots import latest_snapshot, read_snapshot_content
from trust.engine import SignalInputs, apply_trust_score, score_scheme
from trust.sanity import check_rule_sanity


def _rules_equal(a: list[dict], b: list[dict]) -> bool:
    key = lambda r: (r["rule_type"], r["op"])  # noqa: E731
    return sorted(a, key=key) == sorted(b, key=key)


def main() -> None:
    extractor = get_configured_extractor()
    if extractor is None:
        print("No GEMINI_API_KEY or ANTHROPIC_API_KEY configured (see backend/.env) - nothing to do.", flush=True)
        return

    db = SessionLocal()
    try:
        for scheme in db.query(Scheme).filter(Scheme.is_demo == False).all():  # noqa: E712
            for source in scheme.sources:
                url = source.official_source
                if not url:
                    continue
                snap = latest_snapshot(db, url)
                if not snap:
                    print(f"NO SNAPSHOT  {scheme.scheme_id:28} {url}", flush=True)
                    continue

                html = read_snapshot_content(snap)
                try:
                    first = extractor.extract(html, url)
                    second = extractor.extract(html, url)  # temperature=0 twice - stability check
                except ExtractorUnavailable as exc:
                    print(f"UNAVAILABLE  {scheme.scheme_id:28} {exc}", flush=True)
                    continue
                except Exception as exc:  # noqa: BLE001 - report and move to the next scheme
                    print(f"FAILED       {scheme.scheme_id:28} {exc}", flush=True)
                    continue

                first_rules = first.as_dict()["rules"]
                second_rules = second.as_dict()["rules"]
                stable = _rules_equal(first_rules, second_rules)
                sanity_flags = check_rule_sanity(first_rules)

                golden_rules = [
                    {"rule_type": r.rule_type, "op": r.op, "value": r.value, "required": r.required}
                    for r in scheme.rules
                ]
                accuracy = score_rules(golden_rules, first_rules)

                signals = SignalInputs(
                    source_types=[source.source_type or "unknown"],
                    field_agreement=None,
                    extraction_stable=stable,
                    sanity_flags=sanity_flags,
                    last_fetched_at=snap.fetched_at,
                    now=datetime.utcnow(),
                )
                score = score_scheme(signals)
                apply_trust_score(scheme, score)
                db.commit()  # commit per scheme, not once at the end - an interrupted run keeps whatever it finished

                print(
                    f"{scheme.scheme_id:28} confidence={score.confidence:<6} mode={score.mode:<15} "
                    f"stable={stable!s:<5} sanity_flags={sanity_flags or 'none'} "
                    f"extracted={len(first_rules)} golden={len(golden_rules)} "
                    f"recall={accuracy['recall']:.2f} precision={accuracy['precision']:.2f} "
                    f"value_acc={accuracy['value_accuracy']:.2f}",
                    flush=True,
                )
    finally:
        db.close()


if __name__ == "__main__":
    main()
