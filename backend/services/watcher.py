"""Watcher (Phase 6, see docs/TRUST_PIPELINE.md): refetch -> hash-diff -> (if
changed) re-extract -> re-score -> apply. Manual-trigger only right now via
backend/scripts/watch_sources.py — no cron is scheduled from this repo.

Re-scoring requires a configured extractor. When none is available (e.g. no
ANTHROPIC_API_KEY), the watcher still refetches and reports the hash-diff,
but leaves Scheme.confidence/trust_mode untouched rather than fabricating a
score from fetch signals alone — a scheme's rules have to actually be
re-extracted from the fetched page before we can say anything about whether
they're still correct.
"""

from dataclasses import dataclass
from datetime import datetime

from db.models import Scheme, SchemeSource
from extraction.extractor import ExtractorUnavailable, SchemeExtractor
from services.fetch_layer import FetchSkipped, PoliteFetcher
from services.snapshots import latest_snapshot, read_snapshot_content
from sqlalchemy.orm import Session
from trust.engine import SignalInputs, apply_trust_score, score_scheme
from trust.sanity import check_rule_sanity


@dataclass
class WatchResult:
    scheme_id: str
    source_url: str
    outcome: str  # "first_fetch" | "unchanged" | "changed" | "skipped" | "failed"
    detail: str = ""
    rescored: bool = False


def _rules_equal(a: list[dict], b: list[dict]) -> bool:
    key = lambda r: (r["rule_type"], r["op"])  # noqa: E731
    return sorted(a, key=key) == sorted(b, key=key)


def watch_scheme_source(
    db: Session,
    scheme: Scheme,
    source: SchemeSource,
    fetcher: PoliteFetcher,
    extractor: SchemeExtractor | None,
) -> WatchResult:
    url = source.official_source
    if not url:
        return WatchResult(scheme.scheme_id, "", "skipped", "no official_source on record")

    previous = latest_snapshot(db, url)

    try:
        snap = fetcher.fetch_and_store(db, url, source_type=source.source_type, scheme_pk=scheme.id)
    except FetchSkipped as exc:
        return WatchResult(scheme.scheme_id, url, "skipped", str(exc))
    except Exception as exc:  # noqa: BLE001 - report and let the caller move to the next source
        return WatchResult(scheme.scheme_id, url, "failed", str(exc))

    changed = previous is None or previous.normalized_hash != snap.normalized_hash
    outcome = "first_fetch" if previous is None else ("changed" if changed else "unchanged")
    if not changed:
        return WatchResult(scheme.scheme_id, url, outcome)

    if extractor is None:
        return WatchResult(
            scheme.scheme_id, url, outcome, detail="content changed but no extractor configured - re-score skipped"
        )

    html = read_snapshot_content(snap)
    try:
        first = extractor.extract(html, url)
        second = extractor.extract(html, url)  # run twice at temperature 0 to check stability
    except ExtractorUnavailable as exc:
        return WatchResult(scheme.scheme_id, url, outcome, detail=f"extractor unavailable: {exc} - re-score skipped")

    first_rules = first.as_dict()["rules"]
    second_rules = second.as_dict()["rules"]
    stable = _rules_equal(first_rules, second_rules)
    sanity_flags = check_rule_sanity(first_rules)

    signals = SignalInputs(
        source_types=[source.source_type or "unknown"],  # we did fetch a source, just don't know its authority tier
        field_agreement=None,  # single source per scheme today - nothing to cross-check yet
        extraction_stable=stable,
        sanity_flags=sanity_flags,
        last_fetched_at=snap.fetched_at,
        now=datetime.utcnow(),
    )
    score = score_scheme(signals)
    apply_trust_score(scheme, score)

    return WatchResult(
        scheme.scheme_id,
        url,
        outcome,
        detail=f"confidence={score.confidence} mode={score.mode}",
        rescored=True,
    )
