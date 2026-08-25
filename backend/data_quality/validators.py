from __future__ import annotations

from datetime import date
from typing import Any
from urllib.parse import urlparse


DEMO_BANNER = "DEMO DATA – Replace with verified official scheme information."


def validate_scheme(record: dict[str, Any], all_ids: list[str] | None = None) -> list[str]:
    flags: list[str] = []
    rules = record.get("rules") or []
    if not rules:
        flags.append("missing_eligibility")
    sources = record.get("sources") or []
    if not sources or not any(s.get("official_source") for s in sources):
        flags.append("missing_official_source")
    deadline = record.get("deadline")
    if deadline:
        try:
            d = date.fromisoformat(str(deadline)[:10])
            if d < date.today():
                flags.append("expired_deadline")
        except ValueError:
            flags.append("invalid_deadline")
    for src in sources:
        url = src.get("official_application_url") or ""
        if url:
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                flags.append("invalid_url")
    sid = record.get("scheme_id")
    if all_ids and sid and all_ids.count(sid) > 1:
        flags.append("duplicate_scheme")
    names = record.get("_all_names")
    if names and names.count(record.get("scheme_name")) > 1:
        flags.append("duplicate_scheme")
    return flags


def validate_collection(records: list[dict[str, Any]]) -> dict[str, list[str]]:
    ids = [r.get("scheme_id") for r in records]
    names = [r.get("scheme_name") for r in records]
    out: dict[str, list[str]] = {}
    for rec in records:
        rec = {**rec, "_all_names": names}
        flags = validate_scheme(rec, ids)
        if flags:
            out[rec["scheme_id"]] = flags
    return out
