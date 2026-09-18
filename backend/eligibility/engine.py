from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ELIGIBLE = "eligible"
LIKELY = "likely_eligible"
NEEDS_INFO = "needs_more_information"
NOT_ELIGIBLE = "not_eligible"

PROFILE_KEYS = {
    "min_age": "age",
    "max_age": "age",
    "income_max": "annual_family_income",
    "education": "education",
    "occupation": "occupation",
    "employment": "employment_status",
    "gender": "gender",
    "residency_state": "state",
    "residency_district": "district",
    "disability": "disability_status",
    "business": "business_status",
    "student": "student_status",
    "farmer": "farmer_status",
}


@dataclass
class RuleTrace:
    rule_type: str
    requirement: Any
    your_value: Any
    result: str  # pass | fail | unknown
    required: bool
    message: str


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _norm(v: Any) -> str:
    return str(v).strip().lower() if v is not None else ""


def evaluate_rule(rule: dict[str, Any], profile: dict[str, Any]) -> RuleTrace:
    rtype = rule["rule_type"]
    op = rule.get("op") or "eq"
    required = bool(rule.get("required", True))
    requirement = rule.get("value")
    key = PROFILE_KEYS.get(rtype, rtype if rtype == "other" else None)
    your = profile.get(key) if key else profile.get("other")

    if rtype == "other":
        # Optional extra constraints; unknown unless profile has matching flag.
        extra = profile.get("other_flags") or {}
        name = requirement if isinstance(requirement, str) else (requirement or {}).get("name")
        your = extra.get(name) if name else None
        if your is None:
            return RuleTrace(rtype, requirement, None, "unknown", required, "This extra condition is not filled in yet.")
        ok = _norm(your) in {_norm(x) for x in _as_list(requirement if not isinstance(requirement, dict) else requirement.get("allowed", [your]))}
        return RuleTrace(rtype, requirement, your, "pass" if ok else "fail", required, "Extra condition satisfied." if ok else "Extra condition not satisfied.")

    if your is None or your == "":
        return RuleTrace(
            rtype,
            requirement,
            None,
            "unknown",
            required,
            "You're missing one piece of information." if required else "Optional detail not provided.",
        )

    result = "fail"
    if rtype == "min_age":
        result = "pass" if int(your) >= int(requirement) else "fail"
        msg = f"Age {your} vs minimum {requirement}"
    elif rtype == "max_age":
        result = "pass" if int(your) <= int(requirement) else "fail"
        msg = f"Age {your} vs maximum {requirement}"
    elif rtype == "income_max":
        result = "pass" if int(your) <= int(requirement) else "fail"
        msg = f"Income ₹{int(your):,} vs limit ₹{int(requirement):,}"
    elif op in {"in", "eq"}:
        allowed = {_norm(x) for x in _as_list(requirement)}
        # national / all-india schemes: empty or "all"
        if not allowed or allowed <= {"all", "any", "india", "all india"}:
            result = "pass"
        else:
            result = "pass" if _norm(your) in allowed else "fail"
        msg = f"{your} vs {requirement}"
    elif op == "gte":
        result = "pass" if float(your) >= float(requirement) else "fail"
        msg = f"{your} vs ≥ {requirement}"
    elif op == "lte":
        result = "pass" if float(your) <= float(requirement) else "fail"
        msg = f"{your} vs ≤ {requirement}"
    elif op == "exists":
        result = "pass" if your not in (None, "", False, "no") else "fail"
        msg = f"Required status present: {your}"
    else:
        result = "unknown"
        msg = "Could not evaluate this rule."

    citizen = {
        "pass": "This requirement is satisfied.",
        "fail": "This requirement is not satisfied.",
        "unknown": "You're missing one piece of information.",
    }[result]
    return RuleTrace(rtype, requirement, your, result, required, f"{msg} — {citizen}")


def combine_status(traces: list[RuleTrace], *, expired: bool = False) -> str:
    if expired:
        return NOT_ELIGIBLE
    if not traces:
        # No rules to evaluate against must never fall through to a confident
        # ELIGIBLE - that's exactly the "app claims something it doesn't know"
        # failure mode. Most common cause: a pipeline-sourced scheme whose
        # eligibility rules haven't been extracted/confirmed yet (see
        # trust/sanity.py's "no eligibility rules extracted" check).
        return NEEDS_INFO
    required = [t for t in traces if t.required]
    if any(t.result == "fail" and t.required for t in traces):
        return NOT_ELIGIBLE
    if any(t.result == "unknown" and t.required for t in required):
        return NEEDS_INFO
    optional_unknown = [t for t in traces if (not t.required) and t.result == "unknown"]
    optional_fail = [t for t in traces if (not t.required) and t.result == "fail"]
    if optional_unknown or optional_fail:
        return LIKELY
    return ELIGIBLE


def evaluate_scheme(rules: list[dict[str, Any]], profile: dict[str, Any], *, expired: bool = False) -> dict[str, Any]:
    traces = [evaluate_rule(r, profile) for r in rules]
    status = combine_status(traces, expired=expired)
    return {
        "status": status,
        "traces": [
            {
                "rule_type": t.rule_type,
                "requirement": t.requirement,
                "your_value": t.your_value,
                "result": t.result,
                "required": t.required,
                "message": t.message,
            }
            for t in traces
        ],
        "passed": sum(1 for t in traces if t.result == "pass"),
        "failed": sum(1 for t in traces if t.result == "fail"),
        "unknown": sum(1 for t in traces if t.result == "unknown"),
    }
