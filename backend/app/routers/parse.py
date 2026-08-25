from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.dto import ParseQueryIn
from app.security import MAX_QUERY_LEN
from db.models import QueryHistory
from db.session import get_db
from nlp.pipeline import parse_query

router = APIRouter(prefix="/api", tags=["nlp"])


@router.post("/parse-query")
def parse(body: ParseQueryIn, db: Session = Depends(get_db)):
    text = body.query.strip()[:MAX_QUERY_LEN]
    result = parse_query(text)
    db.add(QueryHistory(raw_query=text, parse_result=result))
    db.commit()
    return result
