from __future__ import annotations

from datetime import date

from app.constants import NEED_TO_CATEGORY
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
from trust.language_gate import gate_scheme_language

NEAR_MISS_MIN_PASS = 2


def _scheme_view(s: Scheme) -> dict:
    return {
        "id": s.id,
        "scheme_id": s.scheme_id,
        "scheme_name": s.scheme_name,
        "category": s.category,
        "government_level": s.government_level,
        "state": s.state,
        "district": s.district,
        "description": s.description,
        "benefits_summary": s.benefits_summary,
        "application_status": s.application_status,
        "verification_status": s.verification_status,
        "is_demo": s.is_demo,
        "demo_banner": s.demo_banner,
        "deadline": s.deadline.isoformat() if s.deadline else None,
        "trust_mode": s.trust_mode,
        "confidence": s.confidence,
        "last_verified_date": s.last_verified_date.isoformat() if s.last_verified_date else None,
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
            "trust": gate_scheme_language(
                trust_mode=s.trust_mode,
                is_demo=s.is_demo,
                verification_status=s.verification_status,
                official_source=(s.sources[0].official_source if s.sources else None),
                last_verified_date=view["last_verified_date"],
                confidence=s.confidence,
            ),
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
        "no_match_explanation": _no_match_explanation(profile, need_codes, schemes, primary, near, rejected),
    }


def _citizen_reasons(elig: dict, category: str) -> list[str]:
    out = []
    for t in elig["traces"]:
        if t["result"] == "pass":
            out.append(t["message"].split(" — ")[-1] if " — " in t["message"] else t["message"])
    out.append(f"Matches your need area: {category}.")
    return out


_PROFILE_SIGNAL_FIELDS = (
    "age",
    "gender",
    "state",
    "district",
    "education",
    "occupation",
    "employment_status",
    "annual_family_income",
    "disability_status",
    "farmer_status",
    "business_status",
    "student_status",
)


def _no_match_explanation(
    profile: dict,
    need_codes: list[str],
    all_schemes: list[Scheme],
    primary: list[dict],
    near: list[dict],
    rejected: list[dict],
) -> dict | None:
    """When there's nothing to show in primary/near-misses, tell the citizen
    *why* rather than leaving a bare empty state - and be honest about which
    of three different situations this is, since they call for different next
    steps: (1) we didn't understand the request, (2) we have no verified
    scheme for this at all (a data-coverage gap, not a fact about the
    citizen), or (3) real schemes exist here and the citizen doesn't meet
    their criteria. Returns None when there's something to show already."""
    if primary or near:
        return None

    has_profile_signal = any(profile.get(f) not in (None, "") for f in _PROFILE_SIGNAL_FIELDS)
    if not need_codes and not has_profile_signal:
        return {
            "reason": "unclear_concern",
            "message": (
                "We couldn't tell what kind of help you're looking for from what you've shared. "
                "Try describing your situation in more detail, or fill in your profile."
            ),
        }

    relevant_categories = {NEED_TO_CATEGORY[c] for c in need_codes if c in NEED_TO_CATEGORY}
    has_matching_category_scheme = any(s.category in relevant_categories for s in all_schemes)
    if relevant_categories and not has_matching_category_scheme:
        return {
            "reason": "no_data_for_need",
            "message": (
                "We don't have any verified schemes for this in our database yet. "
                "This isn't the same as being ineligible — we simply don't have data here."
            ),
        }

    return {
        "reason": "not_eligible",
        "message": (
            f"We checked {len(rejected)} scheme(s) related to your need, but based on what you've told us, "
            "you don't currently meet their eligibility criteria."
            if rejected
            else "We couldn't find a matching scheme based on what you've told us."
        ),
    }


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
