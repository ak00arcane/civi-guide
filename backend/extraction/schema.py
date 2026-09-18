"""Canonical shape the extractor (Phase 3) produces from a raw HTML snapshot.
Rule fields deliberately reuse the enums the eligibility engine already
understands (see eligibility/rules.py) so extracted rules plug straight into
SchemeRule without translation.
"""

import re
from dataclasses import dataclass, field

from eligibility.rules import OPS, RULE_TYPES


@dataclass
class ExtractedRule:
    rule_type: str
    op: str
    value: object
    required: bool = True

    def __post_init__(self):
        if self.rule_type not in RULE_TYPES:
            raise ValueError(f"unknown rule_type: {self.rule_type!r}")
        if self.op not in OPS:
            raise ValueError(f"unknown op: {self.op!r}")

    def as_dict(self) -> dict:
        return {"rule_type": self.rule_type, "op": self.op, "value": self.value, "required": self.required}


@dataclass
class ExtractedScheme:
    scheme_name: str | None
    description: str | None
    benefits_summary: str | None
    deadline: str | None
    rules: list[ExtractedRule] = field(default_factory=list)
    raw_model_json: dict | None = None

    def as_dict(self) -> dict:
        return {
            "scheme_name": self.scheme_name,
            "description": self.description,
            "benefits_summary": self.benefits_summary,
            "deadline": self.deadline,
            "rules": [r.as_dict() for r in self.rules],
        }


_TAG_STRIP_RE = re.compile(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>")
_ANY_TAG_RE = re.compile(r"(?s)<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def html_to_text(html: str) -> str:
    """Dependency-free best-effort HTML -> plain text: drop script/style blocks,
    strip remaining tags, collapse whitespace. Good enough for LLM extraction
    input; not a rendering-accurate parser."""
    text = _TAG_STRIP_RE.sub(" ", html)
    text = _ANY_TAG_RE.sub(" ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return _WHITESPACE_RE.sub(" ", text).strip()
