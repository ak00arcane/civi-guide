"""Multilingual-ready stub: English only in MVP. Do not fake Tamil/Hindi."""

from __future__ import annotations

import re

TAMIL_RANGE = re.compile(r"[\u0B80-\u0BFF]")
DEVANAGARI = re.compile(r"[\u0900-\u097F]")


def detect_locale(text: str) -> str:
    if TAMIL_RANGE.search(text or ""):
        return "ta"
    if DEVANAGARI.search(text or ""):
        return "hi"
    return "en"


def assert_english_or_message(text: str) -> str | None:
    loc = detect_locale(text)
    if loc != "en":
        return "English only for now. Tamil and Hindi support is planned and not enabled."
    return None
