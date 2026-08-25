from eligibility.engine import ELIGIBLE, LIKELY, NEEDS_INFO, NOT_ELIGIBLE

STATUS_SCORE = {
    ELIGIBLE: 1.0,
    LIKELY: 0.75,
    NEEDS_INFO: 0.45,
    NOT_ELIGIBLE: 0.0,
}


def eligibility_component(status: str, passed: int, total: int) -> float:
    if status == NOT_ELIGIBLE:
        return 0.0
    base = STATUS_SCORE.get(status, 0.0)
    ratio = (passed / total) if total else 1.0
    return min(1.0, 0.6 * base + 0.4 * ratio)


def location_component(profile: dict, scheme: dict) -> float:
    pst = (profile.get("state") or "").lower()
    sst = (scheme.get("state") or "").lower()
    if not sst or sst in {"all", "india", "all india"}:
        return 0.7
    if pst and pst == sst:
        pd = (profile.get("district") or "").lower()
        sd = (scheme.get("district") or "").lower()
        if sd and pd == sd:
            return 1.0
        return 0.9
    return 0.15


def profile_income_component(profile: dict, traces: list[dict]) -> float:
    income_traces = [t for t in traces if t.get("rule_type") == "income_max"]
    if not income_traces:
        return 0.6
    t = income_traces[0]
    if t["result"] == "pass":
        return 1.0
    if t["result"] == "unknown":
        return 0.4
    return 0.0


def edu_occ_component(traces: list[dict]) -> float:
    relevant = [t for t in traces if t.get("rule_type") in {"education", "occupation", "employment"}]
    if not relevant:
        return 0.55
    score = 0.0
    for t in relevant:
        score += {"pass": 1.0, "unknown": 0.4, "fail": 0.0}[t["result"]]
    return score / len(relevant)


def usefulness_component(scheme: dict) -> float:
    score = 0.4
    if scheme.get("application_status") in {"open", "active"}:
        score += 0.3
    sources = scheme.get("sources") or []
    if any(s.get("official_application_url") for s in sources):
        score += 0.3
    return min(1.0, score)


def need_component(need_codes: list[str], scheme_category: str, semantic: float) -> float:
    from app.constants import CATEGORY_TO_NEED, NEED_TO_CATEGORY

    cat_need = CATEGORY_TO_NEED.get(scheme_category, "")
    if cat_need in need_codes or scheme_category.lower() in {c.replace("_", " ") for c in need_codes}:
        match = 1.0
    elif any(NEED_TO_CATEGORY.get(c) == scheme_category for c in need_codes):
        match = 1.0
    elif "skill_development" in need_codes and scheme_category == "Employment":
        match = 0.85
    else:
        match = 0.2
    # semantic only blends into need relevance
    return min(1.0, 0.7 * match + 0.3 * max(0.0, semantic))


def weighted_score(parts: dict[str, float], w: dict[str, float]) -> float:
    return round(sum(parts[k] * w[k] for k in w), 4)
