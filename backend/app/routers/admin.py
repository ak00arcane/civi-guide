from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.schemas.dto import AdminSchemeIn
from app.security import require_admin
from db.models import Scheme
from db.session import get_db
from services.import_schemes import scheme_to_dict, upsert_record

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    total = db.query(Scheme).count()
    by_status = dict(db.query(Scheme.verification_status, func.count()).group_by(Scheme.verification_status).all())
    by_cat = dict(db.query(Scheme.category, func.count()).group_by(Scheme.category).all())
    by_state = dict(db.query(Scheme.state, func.count()).group_by(Scheme.state).all())
    return {
        "total_schemes": total,
        "verified_schemes": by_status.get("verified", 0),
        "needs_review": by_status.get("needs_review", 0),
        "expired_schemes": by_status.get("expired", 0),
        "by_status": by_status,
        "categories": by_cat,
        "states": {str(k): v for k, v in by_state.items()},
    }


@router.get("/schemes")
def list_admin(db: Session = Depends(get_db)):
    rows = (
        db.query(Scheme)
        .options(
            selectinload(Scheme.rules),
            selectinload(Scheme.benefits),
            selectinload(Scheme.documents),
            selectinload(Scheme.sources),
        )
        .all()
    )
    return {"items": [scheme_to_dict(s) for s in rows]}


@router.post("/schemes")
def create_scheme(body: AdminSchemeIn, db: Session = Depends(get_db)):
    s = upsert_record(db, body.model_dump())
    db.commit()
    return scheme_to_dict(s)


@router.patch("/schemes/{scheme_id}")
def patch_scheme(scheme_id: str, body: dict, db: Session = Depends(get_db)):
    s = (
        db.query(Scheme)
        .options(
            selectinload(Scheme.rules),
            selectinload(Scheme.benefits),
            selectinload(Scheme.documents),
            selectinload(Scheme.sources),
        )
        .filter(Scheme.scheme_id == scheme_id)
        .one_or_none()
    )
    if not s:
        raise HTTPException(404, "Scheme not found.")
    current = scheme_to_dict(s)
    current.update({k: v for k, v in body.items() if v is not None})
    current["scheme_id"] = scheme_id
    s2 = upsert_record(db, current)
    db.commit()
    return scheme_to_dict(s2)
