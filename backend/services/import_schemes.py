from pathlib import Path
import importlib.util
import json
from datetime import date

from data_quality.validators import validate_scheme
from db.models import Scheme, SchemeBenefit, SchemeDocument, SchemeEmbedding, SchemeRule, SchemeSource
from nlp.embeddings import embed_with_optional_model
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[2]


def load_catalog() -> list[dict]:
    json_path = ROOT / "data" / "demo" / "schemes.json"
    if json_path.exists():
        return json.loads(json_path.read_text(encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("demo_catalog", ROOT / "data" / "demo" / "catalog.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    records = mod.catalog()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return records


def load_verified_catalog() -> list[dict]:
    json_path = ROOT / "data" / "verified" / "schemes.json"
    if json_path.exists():
        return json.loads(json_path.read_text(encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("verified_catalog", ROOT / "data" / "verified" / "catalog.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    records = mod.verified_catalog()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return records


def _date(val) -> date | None:
    if not val:
        return None
    if isinstance(val, date):
        return val
    return date.fromisoformat(str(val)[:10])


def scheme_to_dict(s: Scheme) -> dict:
    sources = [
        {
            "official_source": x.official_source,
            "official_application_url": x.official_application_url,
            "last_verified_date": x.last_verified_date.isoformat() if x.last_verified_date else None,
        }
        for x in s.sources
    ]
    unverified = (not sources) or not any(x.get("official_source") for x in sources)
    return {
        "scheme_id": s.scheme_id,
        "scheme_name": s.scheme_name,
        "category": s.category,
        "sub_category": s.sub_category,
        "government_level": s.government_level,
        "department": s.department,
        "state": s.state,
        "district": s.district,
        "description": s.description,
        "benefits_summary": s.benefits_summary,
        "application_status": s.application_status,
        "application_steps": s.application_steps,
        "deadline": s.deadline.isoformat() if s.deadline else None,
        "last_verified_date": s.last_verified_date.isoformat() if s.last_verified_date else None,
        "verification_status": s.verification_status,
        "confidence": s.confidence,
        "trust_mode": s.trust_mode,
        "last_scored_at": s.last_scored_at.isoformat() if s.last_scored_at else None,
        "is_demo": s.is_demo,
        "demo_banner": s.demo_banner if s.is_demo else "",
        "quality_flags": s.quality_flags or [],
        "disclaimer": (
            "CivicGuide is an independent information and recommendation tool. "
            "Applications are completed on the official government portal."
        ),
        "unverified_message": "Official information could not be verified." if unverified else None,
        "rules": [{"rule_type": r.rule_type, "op": r.op, "value": r.value, "required": r.required} for r in s.rules],
        "benefits": [{"text": b.text} for b in s.benefits],
        "documents": [{"name": d.name, "notes": d.notes} for d in s.documents],
        "sources": sources,
    }


def upsert_record(db: Session, rec: dict) -> Scheme:
    flags = validate_scheme(rec)
    is_demo = bool(rec.get("is_demo", True))
    status = rec.get("verification_status", "demo" if is_demo else "VERIFIED")
    if "expired_deadline" in flags:
        status = "expired"
    elif flags and status == "demo" and ("missing_official_source" in flags or "missing_eligibility" in flags):
        status = "needs_review"

    demo_banner = rec.get("demo_banner")
    if is_demo and not demo_banner:
        demo_banner = "DEMO DATA – Replace with verified official scheme information."
    elif not is_demo:
        demo_banner = ""

    existing = db.query(Scheme).filter(Scheme.scheme_id == rec["scheme_id"]).one_or_none()
    fields = dict(
        scheme_name=rec["scheme_name"],
        category=rec["category"],
        sub_category=rec.get("sub_category"),
        government_level=rec.get("government_level"),
        department=rec.get("department"),
        state=rec.get("state"),
        district=rec.get("district"),
        description=rec["description"],
        benefits_summary=rec.get("benefits_summary"),
        application_status=rec.get("application_status", "open"),
        application_steps=rec.get("application_steps"),
        deadline=_date(rec.get("deadline")),
        last_verified_date=_date(rec.get("last_verified_date")),
        verification_status=status,
        is_demo=is_demo,
        demo_banner=demo_banner,
        quality_flags=flags,
    )
    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
        db.query(SchemeRule).filter(SchemeRule.scheme_pk == existing.id).delete()
        db.query(SchemeBenefit).filter(SchemeBenefit.scheme_pk == existing.id).delete()
        db.query(SchemeDocument).filter(SchemeDocument.scheme_pk == existing.id).delete()
        db.query(SchemeSource).filter(SchemeSource.scheme_pk == existing.id).delete()
        scheme = existing
    else:
        scheme = Scheme(scheme_id=rec["scheme_id"], **fields)
        db.add(scheme)
        db.flush()
    for r in rec.get("rules") or []:
        db.add(
            SchemeRule(
                scheme_pk=scheme.id,
                rule_type=r["rule_type"],
                op=r.get("op", "eq"),
                value=r.get("value"),
                required=r.get("required", True),
            )
        )
    for b in rec.get("benefits") or []:
        db.add(SchemeBenefit(scheme_pk=scheme.id, text=b["text"] if isinstance(b, dict) else str(b)))
    for d in rec.get("documents") or []:
        db.add(SchemeDocument(scheme_pk=scheme.id, name=d.get("name", "Document"), notes=d.get("notes")))
    for s in rec.get("sources") or []:
        db.add(
            SchemeSource(
                scheme_pk=scheme.id,
                official_source=s.get("official_source"),
                official_application_url=s.get("official_application_url"),
                last_verified_date=_date(s.get("last_verified_date")),
            )
        )
    text = f"{scheme.scheme_name} {scheme.description} {scheme.benefits_summary or ''} {scheme.category}"
    vec, model = embed_with_optional_model(text)
    emb = db.query(SchemeEmbedding).filter(SchemeEmbedding.scheme_pk == scheme.id).one_or_none()
    if emb:
        emb.vector = vec
        emb.model_name = model
    else:
        db.add(SchemeEmbedding(scheme_pk=scheme.id, vector=vec, model_name=model))
    return scheme


def import_verified(db: Session) -> int:
    records = load_verified_catalog()
    for rec in records:
        upsert_record(db, rec)
    db.commit()
    return len(records)


def import_demo(db: Session) -> int:
    records = load_catalog()
    for rec in records:
        upsert_record(db, rec)
    db.commit()
    return len(records)


def import_all(db: Session) -> tuple[int, int]:
    n_ver = import_verified(db)
    n_demo = import_demo(db)
    return n_ver, n_demo
