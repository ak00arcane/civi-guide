from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.schemas.dto import EligibilityIn
from db.models import Scheme
from db.session import get_db
from eligibility.engine import evaluate_scheme
from datetime import date

router = APIRouter(prefix="/api", tags=["eligibility"])


def _eval(s: Scheme, profile: dict) -> dict:
    expired = s.verification_status == "expired" or (s.deadline and s.deadline < date.today())
    rules = [{"rule_type": r.rule_type, "op": r.op, "value": r.value, "required": r.required} for r in s.rules]
    result = evaluate_scheme(rules, profile, expired=expired)
    return {
        "scheme_id": s.scheme_id,
        "scheme_name": s.scheme_name,
        "is_demo": s.is_demo,
        "expired": expired,
        **result,
    }


@router.post("/check-eligibility")
def check_eligibility(body: EligibilityIn, db: Session = Depends(get_db)):
    q = db.query(Scheme).options(selectinload(Scheme.rules))
    if body.scheme_id:
        s = q.filter(Scheme.scheme_id == body.scheme_id).one_or_none()
        if not s:
            raise HTTPException(404, "Scheme not found.")
        return {"results": [_eval(s, body.profile)]}
    return {"results": [_eval(s, body.profile) for s in q.all()]}
