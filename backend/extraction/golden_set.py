"""Golden-set regression harness for the extractor (Phase 3, see docs/TRUST_PIPELINE.md).

Uses the hand-verified schemes in data/verified/schemes.json (verification_status
== "VERIFIED") as golden fixtures — they were already checked against live
official sources by a human when authored, so they serve as ground truth
without a separate research pass. data/verified/schemes.json also holds
pipeline-sourced schemes (verification_status == "needs_review") added later
without hand-written rules — those are excluded here since there's no human-
confirmed ground truth to compare an extraction against. Growing the golden
set needs a dedicated verification pass per scheme (fetch the live page, a
human confirms the rules) — not something to fabricate from a model's own
output.
"""

import json
from pathlib import Path

from extraction.schema import ExtractedScheme

ROOT = Path(__file__).resolve().parents[2]
GOLDEN_PATH = ROOT / "data" / "verified" / "schemes.json"


def load_golden_set() -> list[dict]:
    records = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    return [r for r in records if r.get("verification_status") == "VERIFIED"]


def _normalize_value(value):
    if isinstance(value, list):
        return frozenset(str(v).strip().lower() for v in value)
    if isinstance(value, (int, float)):
        return value
    return str(value).strip().lower()


def _rule_key(rule: dict) -> tuple:
    return (rule["rule_type"], rule["op"])


def score_rules(golden_rules: list[dict], extracted_rules: list[dict]) -> dict:
    """Field-level precision/recall between a golden rule set and an extracted one,
    keyed on (rule_type, op) with normalized value comparison."""
    golden_by_key = {_rule_key(r): r for r in golden_rules}
    extracted_by_key = {_rule_key(r): r for r in extracted_rules}

    matched = 0
    value_matches = 0
    for key, golden_rule in golden_by_key.items():
        extracted_rule = extracted_by_key.get(key)
        if extracted_rule is None:
            continue
        matched += 1
        if _normalize_value(golden_rule["value"]) == _normalize_value(extracted_rule["value"]):
            value_matches += 1

    precision = matched / len(extracted_by_key) if extracted_by_key else 0.0
    recall = matched / len(golden_by_key) if golden_by_key else 1.0
    value_accuracy = value_matches / matched if matched else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "value_accuracy": value_accuracy,
        "golden_rule_count": len(golden_by_key),
        "extracted_rule_count": len(extracted_by_key),
        "matched_rule_count": matched,
    }


def score_extraction(golden_record: dict, extracted: ExtractedScheme) -> dict:
    return score_rules(golden_record.get("rules") or [], extracted.as_dict()["rules"])
