from __future__ import annotations

from datetime import date

from db.models import Recommendation, RecommendationReason, Scheme
from eligibility.engine import NOT_ELIGIBLE, evaluate_scheme
from nlp.embeddings import cosine, embed_text
from recommendation.grouping import group_key, group_results
from recommendation.opportunities import explore_other, opportunity_map
from recommendation.scorer import (
    edu_occ_component,
    eligibility_component,
    location_component,
    need_component,
    profile_income_component,
    usefulness_component,
    weighted_score,
)
from recommendation.weights import weights
from sqlalchemy.orm import Session, selectinload

NEAR_MISS_MIN_PASS = 2


def _scheme_view(s: Scheme) -> dict:
    return {
        "id": s.id,
        "scheme_id": s.scheme_id,
        "scheme_name": s.scheme_name,
        "category": s.category,
        "state": s.state,
        "district": s.district,
        "description": s.description,
        "benefits_summary": s.benefits_summary,
        "application_status": s.application_status,
        "verification_status": s.verification_status,
        "is_demo": s.is_demo,
        "demo_banner": s.demo_banner,
        "deadline": s.deadline.isoformat() if s.deadline else None,
        "sources": [
            {
                "official_source": x.official_source,
                "official_application_url": x.official_application_url,
            }
            for x in s.sources
        ],
        "rules": [{"rule_type": r.rule_type, "op": r.op, "value": r.value, "required": r.required} for r in s.rules],
    }


def recommend(db: Session, profile: dict, needs: list[dict], situation_id: str | None = None, profile_id: str | None = None) -> dict:
    w = weights()
    need_codes = [n["need_code"] for n in needs]
    user_text = " ".join(
        [
            profile.get("education") or "",
            profile.get("employment_status") or "",
            " ".join(need_codes),
            profile.get("occupation") or "",
            "government benefits",
        ]
    )
    user_vec = embed_text(user_text)
    schemes = (
        db.query(Scheme)
        .options(
            selectinload(Scheme.rules),
            selectinload(Scheme.sources),
            selectinload(Scheme.embedding),
            selectinload(Scheme.benefits),
            selectinload(Scheme.documents),
        )
        .filter(Scheme.verification_status != "archived")
        .all()
    )
    primary = []
    near = []
    rejected = []
    today = date.today()
    for s in schemes:
        expired = bool(
            s.verification_status == "expired" or (s.deadline and s.deadline < today)
        )
        rules = [{"rule_type": r.rule_type, "op": r.op, "value": r.value, "required": r.required} for r in s.rules]
        elig = evaluate_scheme(rules, profile, expired=expired)
        sem = cosine(user_vec, (s.embedding.vector if s.embedding else None))
        view = _scheme_view(s)
        parts = {
            "eligibility": eligibility_component(elig["status"], elig["passed"], max(1, len(rules))),
            "need": need_component(need_codes, s.category, sem),
            "location": location_component(profile, view),
            "profile": profile_income_component(profile, elig["traces"]),
            "education_occupation": edu_occ_component(elig["traces"]),
            "usefulness": usefulness_component(view),
        }
        score = weighted_score(parts, w)
        # hard rule: not eligible cannot enter primary
        item = {
            **view,
            "eligibility_status": elig["status"],
            "score": score,
            "components": parts,
            "semantic": round(sem, 4),
            "traces": elig["traces"],
            "need_group": group_key(need_codes, s.category),
            "reasons": _citizen_reasons(elig, s.category),
            "why_not": _why_not(elig) if elig["status"] == NOT_ELIGIBLE else None,
            "expired": expired,
        }
        if expired:
            rejected.append(item)
            continue
        if elig["status"] == NOT_ELIGIBLE:
            rejected.append(item)
            if elig["passed"] >= NEAR_MISS_MIN_PASS:
                near.append(item)
            continue
        primary.append(item)

    primary.sort(key=lambda x: x["score"], reverse=True)
    for i, it in enumerate(primary, start=1):
        it["rank"] = i
    if profile_id:
        db.query(Recommendation).filter(Recommendation.profile_id == profile_id).delete()
        for it in primary[:20]:
            rec = Recommendation(
                situation_id=situation_id,
                profile_id=profile_id,
                scheme_pk=it["id"],
                scheme_id=it["scheme_id"],
                score=it["score"],
                rank=it["rank"],
                eligibility_status=it["eligibility_status"],
                need_group=it["need_group"],
            )
            db.add(rec)
            db.flush()
            for r in it["traces"]:
                db.add(
                    RecommendationReason(
                        recommendation_id=rec.id,
                        kind=r["rule_type"],
                        result=r["result"],
                        message=r["message"],
                        extra=r,
                    )
                )
        db.commit()

    grouped = group_results(primary)
    return {
        "recommendations": primary,
        "grouped": grouped,
        "near_misses": sorted(near, key=lambda x: -x["score"])[:8],
        "opportunity_map": opportunity_map(primary),
        "explore_other": explore_other(profile, needs),
        "weights": w,
        "rejected_count": len(rejected),
        "research": {"rejected": rejected[:30]},
    }


def _citizen_reasons(elig: dict, category: str) -> list[str]:
    out = []
    for t in elig["traces"]:
        if t["result"] == "pass":
            out.append(t["message"].split(" — ")[-1] if " — " in t["message"] else t["message"])
    out.append(f"Matches your need area: {category}.")
    return out


def _why_not(elig: dict) -> list[dict]:
    fails = [t for t in elig["traces"] if t["result"] == "fail"]
    return [
        {
            "rule_type": t["rule_type"],
            "requirement": t["requirement"],
            "your_value": t["your_value"],
            "message": t["message"],
        }
        for t in fails
    ]
