from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.dto import RecommendIn
from app.security import require_admin
from db.session import get_db
from nlp.pipeline import parse_query
from services.recommend import recommend as run_recommend

router = APIRouter(prefix="/api/research", tags=["research"], dependencies=[Depends(require_admin)])


@router.get("/trace")
def trace(query: str, db: Session = Depends(get_db)):
    parsed = parse_query(query)
    fields = {k: v for k, v in parsed["fields"].items() if v is not None}
    rec = run_recommend(db, parsed["fields"], parsed["needs"])
    return {
        "input_query": query,
        "extracted_attributes": parsed["fields"],
        "detected_needs": parsed["needs"],
        "detected_life_events": parsed["life_events"],
        "eligible_schemes": [x["scheme_id"] for x in rec["recommendations"] if x["eligibility_status"] in {"eligible", "likely_eligible"}],
        "needs_info_schemes": [x["scheme_id"] for x in rec["recommendations"] if x["eligibility_status"] == "needs_more_information"],
        "rejected_schemes": [x["scheme_id"] for x in rec["research"]["rejected"]],
        "recommendation_scores": [{"scheme_id": x["scheme_id"], "score": x["score"], "status": x["eligibility_status"]} for x in rec["recommendations"]],
        "ranking": [x["scheme_id"] for x in rec["recommendations"]],
        "full": rec,
        "parse": parsed,
    }
