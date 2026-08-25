from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.dto import RecommendIn
from app.security import optional_profile_id
from db.models import CitizenProfile, Need, Recommendation, Scheme
from db.session import get_db
from nlp.needs import detect_needs
from nlp.pipeline import parse_query
from services.profile import profile_to_dict
from services.recommend import recommend as run_recommend
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/api", tags=["recommend"])


@router.post("/recommend")
def recommend(body: RecommendIn, db: Session = Depends(get_db), pid: UUID | None = Depends(optional_profile_id)):
    profile = body.profile
    needs = body.needs
    if not profile and pid:
        p = db.get(CitizenProfile, str(pid))
        if p and not p.deleted_at:
            profile = profile_to_dict(p)
            needs = needs or [
                {"need_code": n.need_code, "confidence": n.confidence, "explicit": n.explicit}
                for n in db.query(Need).filter(Need.profile_id == p.id).all()
            ]
    if body.query:
        parsed = parse_query(body.query)
        profile = {**(profile or {}), **{k: v for k, v in parsed["fields"].items() if v is not None}}
        needs = parsed["needs"]
    profile = profile or {}
    needs = needs or detect_needs("", profile)
    return run_recommend(db, profile, needs, profile_id=str(pid) if pid else None)


@router.post("/opportunities")
def opportunities(body: RecommendIn, db: Session = Depends(get_db), pid: UUID | None = Depends(optional_profile_id)):
    data = recommend(body, db, pid)
    return {
        "opportunity_map": data["opportunity_map"],
        "explore_other": data["explore_other"],
        "grouped": data["grouped"],
    }


@router.get("/user/recommendations")
def last_recs(db: Session = Depends(get_db), pid: UUID | None = Depends(optional_profile_id)):
    if not pid:
        return {"items": []}
    rows = (
        db.query(Recommendation)
        .filter(Recommendation.profile_id == str(pid))
        .order_by(Recommendation.rank)
        .all()
    )
    return {
        "items": [
            {
                "scheme_id": r.scheme_id,
                "score": r.score,
                "rank": r.rank,
                "eligibility_status": r.eligibility_status,
                "need_group": r.need_group,
            }
            for r in rows
        ]
    }
