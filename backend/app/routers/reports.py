from uuid import UUID

from app.schemas.dto import SchemeReportIn
from app.security import optional_profile_id, require_admin
from db.models import Scheme, SchemeReport
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api", tags=["reports"])


@router.post("/scheme-reports")
def report_scheme(
    body: SchemeReportIn, db: Session = Depends(get_db), pid: UUID | None = Depends(optional_profile_id)
):
    scheme = db.query(Scheme).filter(Scheme.scheme_id == body.scheme_id).one_or_none()
    if not scheme:
        raise HTTPException(404, "Scheme not found.")
    report = SchemeReport(
        scheme_pk=scheme.id, scheme_id=scheme.scheme_id, profile_id=str(pid) if pid else None, reason=body.reason
    )
    db.add(report)
    db.commit()
    return {"ok": True, "message": "Thanks — we'll take a look at this."}


admin_router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@admin_router.get("/scheme-reports")
def list_reports(status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(SchemeReport)
    if status:
        q = q.filter(SchemeReport.status == status)
    rows = q.order_by(SchemeReport.created_at.desc()).all()
    return {
        "items": [
            {
                "id": r.id,
                "scheme_id": r.scheme_id,
                "reason": r.reason,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
    }


@admin_router.patch("/scheme-reports/{report_id}")
def update_report_status(report_id: str, status: str, db: Session = Depends(get_db)):
    if status not in {"open", "reviewed", "dismissed"}:
        raise HTTPException(400, "Invalid status.")
    report = db.query(SchemeReport).filter(SchemeReport.id == report_id).one_or_none()
    if not report:
        raise HTTPException(404, "Report not found.")
    report.status = status
    db.commit()
    return {"ok": True, "id": report.id, "status": report.status}
