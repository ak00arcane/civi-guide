from app.constants import NEED_TO_CATEGORY


def group_key(need_codes: list[str], category: str) -> str:
    for code in need_codes:
        if NEED_TO_CATEGORY.get(code) == category:
            return _label(code)
    if category == "Employment" and "skill_development" in need_codes:
        return "Skill development"
    return category


def _label(code: str) -> str:
    return {
        "education": "Education",
        "employment": "Employment",
        "healthcare": "Healthcare",
        "housing": "Housing",
        "women_child": "Women & Child",
        "agriculture": "Agriculture",
        "financial_assistance": "Financial support",
        "disability": "Disability",
        "senior_citizens": "Senior Citizens",
        "entrepreneurship": "Entrepreneurship",
        "skill_development": "Skill development",
    }.get(code, code.replace("_", " ").title())


def group_results(items: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for item in items:
        key = item.get("need_group") or item.get("category") or "Other"
        grouped.setdefault(key, []).append(item)
    return grouped
