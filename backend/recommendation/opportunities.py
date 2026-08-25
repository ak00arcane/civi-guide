from nlp.needs import inferred_categories
from app.constants import NEED_TO_CATEGORY

GAP_LABELS = {
    "education": "Education support",
    "employment": "Employment support",
    "skill_development": "Skill development",
    "entrepreneurship": "Entrepreneurship support",
    "financial_assistance": "Financial assistance",
    "healthcare": "Healthcare",
    "housing": "Housing",
    "women_child": "Women & Child benefits",
    "agriculture": "Agriculture support",
    "disability": "Disability support",
    "senior_citizens": "Senior citizen benefits",
}


def explore_other(fields: dict, needs: list[dict]) -> list[dict]:
    explicit = {n["need_code"] for n in needs if n.get("explicit")}
    extras = inferred_categories(fields, explicit)
    return [{"need_code": c, "label": GAP_LABELS.get(c, c), "category": NEED_TO_CATEGORY.get(c)} for c in extras]


def opportunity_map(items: list[dict]) -> list[dict]:
    counts: dict[str, int] = {}
    for it in items:
        cat = it.get("need_group") or it.get("category") or "Other"
        counts[cat] = counts.get(cat, 0) + 1
    max_c = max(counts.values()) if counts else 1
    return [{"category": k, "count": v, "bar": round(v / max_c, 2)} for k, v in sorted(counts.items(), key=lambda x: -x[1])]
