from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.schemas.dto import DetectNeedsIn, LifeEventIn, ProfileIn, ProfileUpdateIn
from app.security import optional_profile_id, set_session_cookie
from db.models import CitizenProfile, LifeEvent, ProfileChange
from db.session import get_db
from nlp.needs import detect_needs
from nlp.life_events import detect_life_events
from services.profile import create_or_update_profile, profile_to_dict, save_situation

router = APIRouter(prefix="/api", tags=["profile"])


def _load(db: Session, pid: UUID | None) -> CitizenProfile | None:
    if not pid:
        return None
    p = db.get(CitizenProfile, str(pid))
    if p and not p.deleted_at:
        return p
    return None


@router.post("/profile")
def upsert_profile(body: ProfileIn, response: Response, db: Session = Depends(get_db), pid: UUID | None = Depends(optional_profile_id)):
    p = create_or_update_profile(db, {"fields": body.fields, "source_query": body.source_query}, str(pid) if pid else None)
    sit = save_situation(db, p, body.source_query, profile_to_dict(p), body.needs or detect_needs(body.source_query or "", body.fields))
    db.commit()
    set_session_cookie(response, UUID(p.id))
    return {"profile": profile_to_dict(p), "situation_id": sit.id}


@router.post("/profile/update")
def update_profile(body: ProfileUpdateIn, response: Response, db: Session = Depends(get_db), pid: UUID | None = Depends(optional_profile_id)):
    p = _load(db, pid)
    if not p:
        p = create_or_update_profile(db, {"fields": body.fields}, None)
    else:
        create_or_update_profile(db, {"fields": body.fields, "source_query": body.source_query}, p.id)
        p = db.get(CitizenProfile, p.id)
    db.commit()
    set_session_cookie(response, UUID(p.id))
    return {"profile": profile_to_dict(p), "message": "Your recommendations may have changed."}


@router.post("/detect-needs")
def detect(body: DetectNeedsIn):
    return {"needs": detect_needs(body.text or "", body.fields)}


@router.post("/life-event")
def life_event(body: LifeEventIn, db: Session = Depends(get_db), pid: UUID | None = Depends(optional_profile_id)):
    p = _load(db, pid)
    if not p:
        raise HTTPException(400, "Create a profile first.")
    events = detect_life_events(body.text or "", new=profile_to_dict(p))
    if body.event_code:
        events.append({"event_code": body.event_code, "from_value": body.from_value, "to_value": body.to_value})
    for e in events:
        db.add(LifeEvent(profile_id=p.id, event_code=e["event_code"], from_value=e.get("from_value"), to_value=e.get("to_value")))
    db.commit()
    return {"events": events, "message": "Your recommendations may have changed."}


@router.get("/profile/changes")
def changes(db: Session = Depends(get_db), pid: UUID | None = Depends(optional_profile_id)):
    p = _load(db, pid)
    if not p:
        return {"changes": [], "events": []}
    ch = db.query(ProfileChange).filter(ProfileChange.profile_id == p.id).order_by(ProfileChange.changed_at.desc()).all()
    ev = db.query(LifeEvent).filter(LifeEvent.profile_id == p.id).order_by(LifeEvent.detected_at.desc()).all()
    return {
        "changes": [{"field": c.field_name, "old": c.old_value, "new": c.new_value, "at": c.changed_at.isoformat()} for c in ch],
        "events": [{"event_code": e.event_code, "from": e.from_value, "to": e.to_value, "at": e.detected_at.isoformat()} for e in ev],
        "profile": profile_to_dict(p),
    }


@router.post("/profile/delete")
def delete_profile(response: Response, db: Session = Depends(get_db), pid: UUID | None = Depends(optional_profile_id)):
    p = _load(db, pid)
    if p:
        from datetime import datetime

        p.deleted_at = datetime.utcnow()
        db.commit()
    response.delete_cookie("civicguide_session")
    return {"ok": True}


@router.post("/profile/reset")
def reset_profile(response: Response, db: Session = Depends(get_db), pid: UUID | None = Depends(optional_profile_id)):
    delete_profile(response, db, pid)
    return {"ok": True, "message": "Profile reset."}
