from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.dto import SavedIn
from app.security import optional_profile_id
from db.models import CitizenProfile, SavedScheme, Scheme
from db.session import get_db

router = APIRouter(prefix="/api", tags=["saved"])

ALLOWED = {"saved", "need_to_apply", "applied_reminder", "expired"}


@router.post("/saved-schemes")
def save(body: SavedIn, db: Session = Depends(get_db), pid: UUID | None = Depends(optional_profile_id)):
    if not pid:
        raise HTTPException(400, "Start with a temporary profile first.")
    if body.personal_status not in ALLOWED:
        raise HTTPException(400, "Invalid personal reminder status.")
    if not db.query(Scheme).filter(Scheme.scheme_id == body.scheme_id).one_or_none():
        raise HTTPException(404, "Scheme not found.")
    row = (
        db.query(SavedScheme)
        .filter(SavedScheme.profile_id == str(pid), SavedScheme.scheme_id == body.scheme_id)
        .one_or_none()
    )
    if row:
        row.personal_status = body.personal_status
    else:
        row = SavedScheme(profile_id=str(pid), scheme_id=body.scheme_id, personal_status=body.personal_status)
        db.add(row)
    db.commit()
    return {"ok": True, "label": "Personal reminder", "item": {"scheme_id": row.scheme_id, "personal_status": row.personal_status}}


@router.get("/saved-schemes")
def list_saved(db: Session = Depends(get_db), pid: UUID | None = Depends(optional_profile_id)):
    if not pid:
        return {"items": [], "note": "Personal reminder — not official application tracking."}
    rows = db.query(SavedScheme).filter(SavedScheme.profile_id == str(pid)).all()
    return {
        "note": "Personal reminder — not official application tracking.",
        "items": [{"scheme_id": r.scheme_id, "personal_status": r.personal_status} for r in rows],
    }
