"""Language gate (Phase 5, see docs/TRUST_PIPELINE.md).

Turns a scheme's trust_mode into how confidently the app is allowed to talk
about it — the underlying deterministic eligibility status (eligible / not
eligible / needs info) never changes here, only the wording and the
explainability source line. Schemes the pipeline hasn't scored yet
("unscored", i.e. every scheme today — see docs/TRUST_PIPELINE.md "What's
real vs stubbed") fall back to the existing hand-verification flags
(is_demo / verification_status) instead of being silently hedged; hedging
only kicks in once the pipeline has actually scored a scheme.
"""

ASSERTIVE = "assertive"
HEDGED = "hedged"
DISCOVERY_ONLY = "discovery_only"
UNSCORED = "unscored"

_KNOWN_MODES = {ASSERTIVE, HEDGED, DISCOVERY_ONLY}


def effective_claim_level(trust_mode: str | None, is_demo: bool, verification_status: str | None) -> str:
    if trust_mode in _KNOWN_MODES:
        return trust_mode
    if is_demo:
        return DISCOVERY_ONLY
    if verification_status == "VERIFIED":
        return ASSERTIVE
    return HEDGED


def gate_scheme_language(
    *,
    trust_mode: str | None,
    is_demo: bool,
    verification_status: str | None,
    official_source: str | None,
    last_verified_date: str | None,
    confidence: float | None,
) -> dict:
    level = effective_claim_level(trust_mode, is_demo, verification_status)
    as_of = last_verified_date or "an unknown date"
    source = official_source or "the official source"

    if level == ASSERTIVE:
        qualifier = None
        source_line = f"Verified against {source} as of {as_of}."
    elif level == HEDGED:
        qualifier = "This hasn't been independently reconfirmed recently — please check the official source before applying."
        source_line = f"Last checked against {source} as of {as_of}."
    else:
        qualifier = "CivicGuide could not confirm this scheme's current eligibility rules. Treat this as a lead, not a confirmed match — verify on the official source."
        source_line = f"Source: {source}. Current rules could not be independently confirmed."

    return {
        "claim_level": level,
        "qualifier": qualifier,
        "source_line": source_line,
        "confidence": confidence,
        "as_of": last_verified_date,
    }
