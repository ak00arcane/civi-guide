from __future__ import annotations

EXPLICIT_NEED_PATTERNS: list[tuple[str, list[str]]] = [
    ("education", ["college", "scholarship", "higher education", "tuition", "student", "school", "education"]),
    ("employment", ["job", "unemployed", "employment", "work", "hiring", "lost my job"]),
    ("entrepreneurship", ["business", "startup", "entrepreneur", "self-employed", "shop"]),
    ("financial_assistance", ["money", "financial", "loan", "income support", "financial support", "financial assistance"]),
    ("skill_development", ["skill", "training", "upskill", "vocational"]),
    ("healthcare", ["health", "hospital", "medical", "insurance", "treatment"]),
    ("housing", ["house", "housing", "rent", "home loan", "shelter"]),
    ("women_child", ["pregnant", "maternity", "child", "widow", "woman", "women"]),
    ("agriculture", ["farm", "farmer", "crop", "agriculture"]),
    ("disability", ["disability", "disabled", "pwd", "divyang"]),
    ("senior_citizens", ["senior", "retired", "pension", "old age"]),
]

INFERRED_RULES: list[tuple[callable, list[str]]] = []


def detect_needs(text: str, fields: dict | None = None) -> list[dict]:
    text_l = (text or "").lower()
    fields = fields or {}
    found: dict[str, dict] = {}
    for code, kws in EXPLICIT_NEED_PATTERNS:
        if any(k in text_l for k in kws):
            found[code] = {"need_code": code, "confidence": 0.9, "explicit": True}
    emp = (fields.get("employment_status") or "").lower()
    edu = (fields.get("education") or "").lower()
    if emp in {"unemployed", "job_seeker"} and "employment" not in found:
        found["employment"] = {"need_code": "employment", "confidence": 0.75, "explicit": False}
    if "start" in text_l and "business" in text_l:
        found["entrepreneurship"] = {"need_code": "entrepreneurship", "confidence": 0.9, "explicit": True}
    if fields.get("age") and int(fields["age"]) >= 60:
        found.setdefault("senior_citizens", {"need_code": "senior_citizens", "confidence": 0.7, "explicit": False})
    if (fields.get("disability_status") or "").lower() in {"yes", "true", "disabled"}:
        found.setdefault("disability", {"need_code": "disability", "confidence": 0.85, "explicit": False})
    if (fields.get("farmer_status") or "").lower() in {"yes", "farmer"}:
        found.setdefault("agriculture", {"need_code": "agriculture", "confidence": 0.8, "explicit": False})
    if edu in {"graduate", "engineering"} and emp in {"unemployed", "job_seeker"}:
        found.setdefault("skill_development", {"need_code": "skill_development", "confidence": 0.7, "explicit": False})
        found.setdefault("financial_assistance", {"need_code": "financial_assistance", "confidence": 0.65, "explicit": False})
    return list(found.values())


def inferred_categories(fields: dict, explicit_codes: set[str]) -> list[str]:
    """Structured opportunity-gap categories the user did not name."""
    extra: list[str] = []
    emp = (fields.get("employment_status") or "").lower()
    edu = (fields.get("education") or "").lower()
    age = fields.get("age")
    if emp in {"unemployed", "job_seeker"}:
        for c in ("skill_development", "entrepreneurship", "financial_assistance"):
            if c not in explicit_codes:
                extra.append(c)
    if edu in {"student", "engineering"} and "education" not in explicit_codes:
        extra.append("education")
    if age and int(age) >= 60 and "senior_citizens" not in explicit_codes:
        extra.append("senior_citizens")
    # unique preserve order
    seen = set()
    out = []
    for c in extra:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out
