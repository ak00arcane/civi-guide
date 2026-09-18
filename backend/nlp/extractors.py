from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOC_PATH = ROOT / "data" / "gazetteers" / "locations.json"

_LOC = None


def locations() -> dict:
    global _LOC
    if _LOC is None:
        _LOC = json.loads(LOC_PATH.read_text(encoding="utf-8"))
    return _LOC


INCOME_RE = re.compile(
    r"(?:₹|rs\.?\s*)?\s*(\d+(?:\.\d+)?)\s*(lakh|lakhs|lacs|lac|crore)?",
    re.I,
)
def rupees_from_match(num: str, unit: str | None) -> int:
    n = float(num)
    u = (unit or "").lower()
    if u.startswith("l"):
        return int(n * 100000)
    if u.startswith("c"):
        return int(n * 10000000)
    if n < 1000:
        # bare "2.5" near lakh is handled by unit; otherwise treat as lakh if < 100
        return int(n * 100000) if n <= 99 else int(n)
    return int(n)


def extract_income(text: str) -> int | None:
    # Prefer patterns with lakh
    for m in re.finditer(r"(?:(?:income|salary|earning|earnings)(?:\s+of)?\s*)?(?:₹|rs\.?\s*)?\s*(\d+(?:\.\d+)?)\s*(lakh|lakhs|lacs|lac)\b", text, re.I):
        return rupees_from_match(m.group(1), m.group(2))
    m = re.search(r"(?:(?:income|salary|earning|earnings)(?:\s+of)?\s*)?(?:₹|rs\.?\s*)\s*(\d[\d,]*)", text, re.I)
    if m:
        return int(m.group(1).replace(",", ""))
    m = re.search(r"\b(?:income|salary|earning|earnings)(?:\s+of)?\s*[:=-]?\s*(\d[\d,]*)\b", text, re.I)
    if m:
        val = int(m.group(1).replace(",", ""))
        if val > 1000:
            return val
    return None


AGE_PATTERNS = [
    re.compile(r"\b(\d{1,2})\s*[-]?\s*(?:years?[- ]old|yrs?[- ]old|year[- ]old)\b", re.I),
    re.compile(r"\b(?:aged?|age)\s*[-:]?\s*(\d{1,2})\b", re.I),
    re.compile(r"\bi(?:['’]?m| am)\s+(\d{1,2})\b", re.I),
    re.compile(r"\b(\d{1,2})\s*(?:years?|yrs?)\s+old\b", re.I),
    re.compile(r"\b(\d{1,2})\s*(?:years?|yrs?)\b", re.I),
]


def extract_age(text: str) -> int | None:
    for pat in AGE_PATTERNS:
        m = pat.search(text)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 120:
                return n
    return None


def extract_location(text: str) -> tuple[str | None, str | None]:
    loc = locations()
    low = text.lower()
    district = None
    state = None
    for dist, st in loc["district_to_state"].items():
        if re.search(rf"\b{re.escape(dist)}\b", low):
            district = dist.title() if dist != "new delhi" else "New Delhi"
            if dist == "chennai":
                district = "Chennai"
            state = st
            break
    for st in loc["states"]:
        if st.lower() in low:
            state = st
            break
    return state, district


def extract_education(text: str) -> str | None:
    low = text.lower()
    if "engineering" in low:
        return "Engineering"
    if "graduate" in low or "graduated" in low:
        return "Graduate"
    if "student" in low or "college" in low:
        return "Student"
    if "12th" in low or "class 12" in low:
        return "Class 12"
    return None


def extract_employment(text: str) -> str | None:
    low = text.lower()
    if "lost my job" in low or "unemployed" in low or "looking for a job" in low or "looking for a job" in low:
        return "unemployed"
    if "job seeker" in low or "need a job" in low or "looking for a job" in low:
        return "job_seeker"
    if "student" in low and "graduat" not in low:
        return "student"
    if "farmer" in low:
        return "farmer"
    if "entrepreneur" in low or "own a business" in low:
        return "self_employed"
    return None


def extract_occupation(text: str) -> str | None:
    low = text.lower()
    if "engineering student" in low or ("engineering" in low and "student" in low):
        return "Student"
    if "student" in low:
        return "Student"
    if "farmer" in low:
        return "Farmer"
    if "teacher" in low:
        return "Teacher"
    return None


def extract_gender(text: str) -> str | None:
    low = text.lower()
    if re.search(r"\b(woman|female|girl|lady)\b", low):
        return "female"
    if re.search(r"\b(man|male|boy)\b", low):
        return "male"
    return None


def extract_business(text: str) -> str | None:
    low = text.lower()
    if "registered business" in low and "don't" not in low and "do not" not in low:
        return "registered"
    if "start a small business" in low or "start a business" in low or "want to start" in low:
        return "planning"
    return None


def extract_student_status(text: str, education: str | None) -> str | None:
    low = text.lower()
    if "final-year" in low or "final year" in low:
        return "final_year"
    if education == "Student" or "student" in low:
        return "student"
    if education in {"Graduate"} or "graduat" in low:
        return "not_student"
    return None
