"""Trust engine (Phase 4, see docs/TRUST_PIPELINE.md).

Turns fetch/extraction signals into a confidence score and a trust_mode for a
scheme. Pure Python, no network, no LLM — fully deterministic and unit-tested.

Design rule this encodes: disagreement never silently picks a winner, it
demotes. Source disagreement, unstable extraction, and failed sanity checks
are hard caps on the score, not just averaged in — a scheme cannot buy its
way to "assertive" by being fresh and well-sourced if its sources contradict
each other or its numbers don't make sense.
"""

from dataclasses import dataclass, field
from datetime import datetime

SOURCE_AUTHORITY = {
    "gov_ministry": 1.0,
    "state_portal": 0.9,
    "myscheme": 0.8,
}
DEFAULT_SOURCE_AUTHORITY = 0.5

FRESHNESS_HALF_LIFE_DAYS = 90.0

MODE_ASSERTIVE = "assertive"
MODE_HEDGED = "hedged"
MODE_DISCOVERY_ONLY = "discovery_only"

ASSERTIVE_THRESHOLD = 0.75
HEDGED_THRESHOLD = 0.45

DISAGREEMENT_CAP = 0.4
INSTABILITY_CAP = 0.4
SANITY_FAILURE_CAP = 0.3

WEIGHTS = {
    "source_authority": 0.30,
    "field_agreement": 0.30,
    "extraction_stability": 0.15,
    "sanity": 0.15,
    "freshness": 0.10,
}


@dataclass
class SignalInputs:
    source_types: list[str]
    """source_type ("gov_ministry"/"state_portal"/"myscheme") of each independent source reporting this scheme."""
    field_agreement: dict[str, bool] | None = None
    """Per extracted field: True if >=2 independent sources agree on it, False if they disagree.
    Fields not cross-checked (only one source available) should be omitted, not set to True."""
    extraction_stable: bool = True
    """False if two temperature=0 extractor runs on the same HTML disagreed."""
    sanity_flags: list[str] = field(default_factory=list)
    """Non-empty if e.g. income_max is implausible, or min_age >= max_age."""
    last_fetched_at: datetime | None = None
    now: datetime | None = None


@dataclass
class TrustScore:
    confidence: float
    mode: str
    components: dict[str, float]
    reasons: list[str]


def _source_authority_score(source_types: list[str]) -> float:
    if not source_types:
        return 0.0
    return max(SOURCE_AUTHORITY.get(t, DEFAULT_SOURCE_AUTHORITY) for t in source_types)


def _freshness_score(last_fetched_at: datetime | None, now: datetime | None) -> float:
    if last_fetched_at is None:
        return 0.0
    now = now or datetime.utcnow()
    days_stale = max((now - last_fetched_at).total_seconds() / 86400.0, 0.0)
    return 0.5 ** (days_stale / FRESHNESS_HALF_LIFE_DAYS)


def score_scheme(signals: SignalInputs) -> TrustScore:
    reasons: list[str] = []
    authority = _source_authority_score(signals.source_types)
    freshness = _freshness_score(signals.last_fetched_at, signals.now)

    agreement = signals.field_agreement or {}
    disagreements = sorted(f for f, ok in agreement.items() if not ok)
    agreements = [f for f, ok in agreement.items() if ok]
    if disagreements:
        agreement_score = 0.0
    elif agreements:
        agreement_score = 1.0
    else:
        agreement_score = 0.5  # nothing cross-checked yet (e.g. single source) - neutral, not a boost

    stability_score = 1.0 if signals.extraction_stable else 0.0
    sanity_score = 1.0 if not signals.sanity_flags else 0.0

    components = {
        "source_authority": authority,
        "field_agreement": agreement_score,
        "extraction_stability": stability_score,
        "sanity": sanity_score,
        "freshness": freshness,
    }

    weighted = sum(WEIGHTS[name] * value for name, value in components.items())

    hard_cap = 1.0
    if not signals.source_types:
        hard_cap = 0.0
        reasons.append("no sources fetched")
    if disagreements:
        hard_cap = min(hard_cap, DISAGREEMENT_CAP)
        reasons.append(f"source disagreement on: {', '.join(disagreements)}")
    if not signals.extraction_stable:
        hard_cap = min(hard_cap, INSTABILITY_CAP)
        reasons.append("extraction unstable across repeated runs")
    if signals.sanity_flags:
        hard_cap = min(hard_cap, SANITY_FAILURE_CAP)
        reasons.append(f"sanity check failed: {', '.join(signals.sanity_flags)}")

    confidence = round(min(weighted, hard_cap), 4)

    if confidence >= ASSERTIVE_THRESHOLD:
        mode = MODE_ASSERTIVE
    elif confidence >= HEDGED_THRESHOLD:
        mode = MODE_HEDGED
    else:
        mode = MODE_DISCOVERY_ONLY

    return TrustScore(confidence=confidence, mode=mode, components=components, reasons=reasons)


def apply_trust_score(scheme, score: TrustScore, now: datetime | None = None) -> None:
    """Write a computed TrustScore onto a Scheme ORM instance. Caller commits."""
    scheme.confidence = score.confidence
    scheme.trust_mode = score.mode
    scheme.last_scored_at = now or datetime.utcnow()
