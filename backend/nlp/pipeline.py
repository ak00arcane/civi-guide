from __future__ import annotations

from nlp.extractors import (
    extract_age,
    extract_business,
    extract_education,
    extract_employment,
    extract_gender,
    extract_income,
    extract_location,
    extract_occupation,
    extract_student_status,
)
from nlp.life_events import detect_life_events
from nlp.multilingual import assert_english_or_message, detect_locale
from nlp.needs import detect_needs


BLOCKING_FIELDS = ["state", "annual_family_income"]


def parse_query(text: str) -> dict:
    original = (text or "").strip()
    locale_msg = assert_english_or_message(original)
    locale = detect_locale(original)
    state, district = extract_location(original)
    education = extract_education(original)
    fields = {
        "age": extract_age(original),
        "gender": extract_gender(original),
        "state": state,
        "district": district,
        "annual_family_income": extract_income(original),
        "education": education,
        "occupation": extract_occupation(original),
        "employment_status": extract_employment(original),
        "student_status": extract_student_status(original, education),
        "family_status": None,
        "disability_status": "yes" if "disab" in original.lower() else None,
        "farmer_status": "farmer" if "farmer" in original.lower() else None,
        "business_status": extract_business(original),
    }
    needs = detect_needs(original, fields)
    life_events = detect_life_events(original)
    intent = "find_benefits"
    low = original.lower()
    if "browse" in low:
        intent = "browse"
    if "update" in low and "status" in low:
        intent = "update_situation"

    missing_blocking = [f for f in BLOCKING_FIELDS if not fields.get(f)]
    questions = []
    if "annual_family_income" in missing_blocking:
        questions.append(
            {
                "field": "annual_family_income",
                "prompt": "What is your approximate annual family income?",
                "options": [
                    {"label": "Below ₹1 lakh", "value": 80000},
                    {"label": "₹1–2.5 lakh", "value": 200000},
                    {"label": "₹2.5–5 lakh", "value": 350000},
                    {"label": "Above ₹5 lakh", "value": 600000},
                    {"label": "Prefer not to say", "value": None},
                ],
            }
        )
    if "state" in missing_blocking:
        questions.append(
            {
                "field": "state",
                "prompt": "Which state do you live in?",
                "options": None,
            }
        )
    if fields.get("business_status") is None and any(n["need_code"] == "entrepreneurship" for n in needs):
        questions.append(
            {
                "field": "business_status",
                "prompt": "Do you already have a registered business?",
                "options": [
                    {"label": "Yes", "value": "registered"},
                    {"label": "No", "value": "planning"},
                    {"label": "Not sure", "value": "unknown"},
                ],
            }
        )
    questions = questions[:3]
    display = {k: v for k, v in fields.items() if v is not None}
    return {
        "locale": locale,
        "locale_message": locale_msg,
        "intent": intent,
        "fields": fields,
        "display": display,
        "needs": needs,
        "life_events": life_events,
        "missing_blocking": missing_blocking,
        "clarifying_questions": questions,
        "original_query": original,
        "names_schemes": False,
    }
