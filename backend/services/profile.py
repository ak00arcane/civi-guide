from __future__ import annotations

from datetime import datetime

from db.models import CitizenProfile, CitizenSituation, LifeEvent, Need, ProfileChange, QueryHistory
from nlp.life_events import detect_life_events
from nlp.needs import detect_needs
from sqlalchemy.orm import Session

PROFILE_FIELDS = [
    "age",
    "gender",
    "education",
    "occupation",
    "employment_status",
    "student_status",
    "family_status",
    "disability_status",
    "farmer_status",
    "business_status",
    "annual_family_income",
    "state",
    "district",
    "locale",
]


def profile_to_dict(p: CitizenProfile) -> dict:
    return {f: getattr(p, f) for f in PROFILE_FIELDS} | {"id": p.id, "is_temporary": p.is_temporary}


def apply_fields(p: CitizenProfile, fields: dict) -> list[ProfileChange]:
    changes = []
    old = profile_to_dict(p)
    for k, v in fields.items():
        if k not in PROFILE_FIELDS or v is None:
            continue
        prev = getattr(p, k)
        if prev != v:
            changes.append(ProfileChange(profile_id=p.id, field_name=k, old_value=None if prev is None else str(prev), new_value=str(v)))
            setattr(p, k, v)
    p.updated_at = datetime.utcnow()
    return changes


def create_or_update_profile(db: Session, payload: dict, profile_id: str | None) -> CitizenProfile:
    fields = payload.get("fields") or payload
    if profile_id:
        p = db.get(CitizenProfile, profile_id)
        if p and not p.deleted_at:
            ch = apply_fields(p, fields)
            for c in ch:
                db.add(c)
            events = detect_life_events(payload.get("source_query") or "", old={c.field_name: c.old_value for c in ch}, new=profile_to_dict(p))
            # also field-based
            old_map = {c.field_name: c.old_value for c in ch}
            events = detect_life_events(payload.get("source_query") or "", old=old_map, new=profile_to_dict(p))
            for e in events:
                db.add(LifeEvent(profile_id=p.id, event_code=e["event_code"], from_value=e.get("from_value"), to_value=e.get("to_value")))
            return p
    p = CitizenProfile(is_temporary=True, locale=fields.get("locale") or "en")
    db.add(p)
    db.flush()
    apply_fields(p, fields)
    return p


def save_situation(db: Session, profile: CitizenProfile, query: str | None, fields: dict, needs: list[dict]) -> CitizenSituation:
    sit = CitizenSituation(profile_id=profile.id, source_query=query, situation_text=query, structured=fields)
    db.add(sit)
    db.flush()
    db.query(Need).filter(Need.profile_id == profile.id).delete()
    for n in needs or detect_needs(query or "", fields):
        db.add(Need(profile_id=profile.id, situation_id=sit.id, need_code=n["need_code"], confidence=n.get("confidence", 1.0), explicit=n.get("explicit", True)))
    if query:
        db.add(QueryHistory(profile_id=profile.id, raw_query=query, parse_result={"fields": fields, "needs": needs}))
    return sit
