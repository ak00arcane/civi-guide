from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from app.constants import CATEGORIES, DISCLAIMER
from db.models import Scheme
from db.session import get_db
from services.import_schemes import scheme_to_dict

router = APIRouter(prefix="/api/schemes", tags=["schemes"])


@router.get("")
def list_schemes(
    category: str | None = None,
    state: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Scheme).options(
        selectinload(Scheme.rules),
        selectinload(Scheme.benefits),
        selectinload(Scheme.documents),
        selectinload(Scheme.sources),
    )
    if category:
        q = q.filter(Scheme.category == category)
    if state:
        q = q.filter((Scheme.state == state) | (Scheme.state.is_(None)))
    rows = q.order_by(Scheme.category, Scheme.scheme_id).all()
    return {"categories": CATEGORIES, "disclaimer": DISCLAIMER, "items": [scheme_to_dict(s) for s in rows]}


@router.get("/{scheme_id}")
def get_scheme(scheme_id: str, db: Session = Depends(get_db)):
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
    return scheme_to_dict(s)
