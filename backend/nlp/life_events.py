from __future__ import annotations

LIFE_EVENT_PATTERNS = [
    ("graduation", ["graduated", "just graduated", "graduation"]),
    ("job_loss", ["lost my job", "laid off", "unemployed", "lost job"]),
    ("starting_college", ["starting college", "joined college", "first year"]),
    ("marriage", ["got married", "just married"]),
    ("childbirth", ["had a baby", "newborn", "having a child"]),
    ("starting_business", ["start a business", "starting a business", "new business"]),
    ("becoming_farmer", ["became a farmer", "started farming"]),
    ("disability_change", ["recent disability", "became disabled"]),
    ("retirement", ["retired", "retirement"]),
    ("moved_state", ["moved to", "relocated"]),
    ("income_change", ["lost income", "income dropped", "pay cut"]),
]


def detect_life_events(text: str, old: dict | None = None, new: dict | None = None) -> list[dict]:
    events: list[dict] = []
    low = (text or "").lower()
    for code, kws in LIFE_EVENT_PATTERNS:
        if any(k in low for k in kws):
            events.append({"event_code": code, "from_value": None, "to_value": None})
    old = old or {}
    new = new or {}
    if old.get("education") in {"student", "engineering"} and new.get("education") in {"graduate"}:
        events.append({"event_code": "graduation", "from_value": old.get("education"), "to_value": new.get("education")})
    if old.get("employment_status") not in {"unemployed", "job_seeker"} and new.get("employment_status") in {
        "unemployed",
        "job_seeker",
    }:
        events.append(
            {
                "event_code": "job_loss",
                "from_value": old.get("employment_status"),
                "to_value": new.get("employment_status"),
            }
        )
    if old.get("state") and new.get("state") and old.get("state") != new.get("state"):
        events.append({"event_code": "moved_state", "from_value": old.get("state"), "to_value": new.get("state")})
    # unique by code
    seen = set()
    uniq = []
    for e in events:
        if e["event_code"] not in seen:
            seen.add(e["event_code"])
            uniq.append(e)
    return uniq
