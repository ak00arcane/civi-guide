"""Sanity checks on extracted rules for the trust engine (Phase 4). Distinct
from data_quality/validators.py, which checks a catalog record's overall
shape (has sources, non-expired deadline); this checks whether the extracted
*rule values themselves* make sense before they're allowed to count as
verified.
"""

PLAUSIBLE_INCOME_MAX = (1_000, 100_000_000)  # INR/year; catches unit errors (e.g. paise instead of rupees)
PLAUSIBLE_AGE = (0, 120)


def check_rule_sanity(rules: list[dict]) -> list[str]:
    flags: list[str] = []
    if not rules:
        # Zero rules extracted must never read as "clean" - there's nothing here to
        # verify, so it can't earn a "hedged" (some confirmed info) confidence, only
        # "discovery_only". Otherwise a page with no stated eligibility criteria at
        # all (e.g. a homepage instead of an eligibility page) looks indistinguishable
        # from a page whose (zero) rules were stably and sanely extracted.
        return ["no eligibility rules extracted"]
    by_type = {r["rule_type"]: r for r in rules}

    min_age = by_type.get("min_age")
    max_age = by_type.get("max_age")
    if min_age is not None and not (PLAUSIBLE_AGE[0] <= min_age["value"] <= PLAUSIBLE_AGE[1]):
        flags.append("min_age out of plausible range")
    if max_age is not None and not (PLAUSIBLE_AGE[0] <= max_age["value"] <= PLAUSIBLE_AGE[1]):
        flags.append("max_age out of plausible range")
    if min_age is not None and max_age is not None and min_age["value"] >= max_age["value"]:
        flags.append("min_age >= max_age")

    income_max = by_type.get("income_max")
    if income_max is not None and not (PLAUSIBLE_INCOME_MAX[0] <= income_max["value"] <= PLAUSIBLE_INCOME_MAX[1]):
        flags.append("income_max out of plausible range")

    return flags
