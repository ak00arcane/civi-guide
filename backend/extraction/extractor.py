"""Scheme extractor (see docs/TRUST_PIPELINE.md, Phase 3): turns a raw HTML
snapshot into an ExtractedScheme. The `anthropic` and `google-genai` packages
are optional dependencies (`pip install -e .[extraction]`) and are only
imported when an extraction actually runs, so the rest of the backend works
without either installed.
"""

import json
from abc import ABC, abstractmethod

from app.config import settings
from eligibility.rules import OPS, RULE_TYPES
from extraction.schema import ExtractedRule, ExtractedScheme, html_to_text

MAX_INPUT_CHARS = 15000

EXTRACTION_SYSTEM_PROMPT = f"""You extract Indian government welfare scheme eligibility information from a
scraped web page into strict structured data. Only report what the page text actually states — never infer,
estimate, or fill in a value the page does not contain. If a field is not present on the page, omit it (for
scheme-level fields) or omit that rule (for eligibility rules) rather than guessing.

Each rule must use one of these rule_type values: {", ".join(RULE_TYPES)}.
Each rule must use one of these op values: {", ".join(OPS)}.
- min_age / max_age / income_max use op "gte" / "lte" / "lte" respectively with a numeric value.
- gender / education / occupation / employment / residency_state / residency_district / disability / business /
  student / farmer use op "in" with a list of string values as stated on the page.
Use "other" only for a clearly-stated eligibility condition that does not fit any other rule_type.
"""

EXTRACTION_TOOL = {
    "name": "record_scheme",
    "description": "Record the scheme details and eligibility rules found on the page.",
    "input_schema": {
        "type": "object",
        "properties": {
            "scheme_name": {"type": "string"},
            "description": {"type": "string"},
            "benefits_summary": {"type": "string"},
            "deadline": {"type": ["string", "null"], "description": "ISO date (YYYY-MM-DD) if the page states one, else null."},
            "rules": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "rule_type": {"type": "string", "enum": RULE_TYPES},
                        "op": {"type": "string", "enum": OPS},
                        "value": {},
                        "required": {"type": "boolean"},
                    },
                    "required": ["rule_type", "op", "value"],
                },
            },
        },
        "required": ["rules"],
    },
}


class ExtractorUnavailable(RuntimeError):
    """Raised when extraction cannot run right now (e.g. no API key configured)."""


class SchemeExtractor(ABC):
    @abstractmethod
    def extract(self, html: str | bytes, source_url: str) -> ExtractedScheme: ...


class AnthropicSchemeExtractor(SchemeExtractor):
    """Calls the Claude API with a constrained tool schema so rule_type/op values
    can never drift from what eligibility/rules.py understands. Deterministic
    (temperature=0) so Phase 4's stability check (run twice, compare) is meaningful.
    """

    MODEL = "claude-sonnet-5"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.anthropic_api_key

    def _client(self):
        if not self.api_key:
            raise ExtractorUnavailable(
                "ANTHROPIC_API_KEY is not set. Set it in the environment (or backend/.env) to run extraction."
            )
        try:
            import anthropic
        except ImportError as exc:
            raise ExtractorUnavailable(
                "the 'anthropic' package is not installed. Install it with `pip install anthropic`."
            ) from exc
        return anthropic.Anthropic(api_key=self.api_key)

    def extract(self, html: str | bytes, source_url: str) -> ExtractedScheme:
        client = self._client()
        if isinstance(html, bytes):
            html = html.decode("utf-8", errors="replace")
        text = html_to_text(html)[:MAX_INPUT_CHARS]
        response = client.messages.create(
            model=self.MODEL,
            max_tokens=2000,
            temperature=0,
            system=EXTRACTION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Source URL: {source_url}\n\nPage text:\n{text}"}],
            tools=[EXTRACTION_TOOL],
            tool_choice={"type": "tool", "name": "record_scheme"},
        )
        tool_use = next(block for block in response.content if block.type == "tool_use")
        return parse_extraction(tool_use.input)


GEMINI_TIMEOUT_MS = 30_000  # per HTTP request
GEMINI_RETRY_ATTEMPTS = 3  # including the original request; google-genai retries 429/5xx internally with backoff
GEMINI_RETRY_INITIAL_DELAY = 2.0
GEMINI_RETRY_MAX_DELAY = 30.0

GEMINI_JSON_INSTRUCTIONS = (
    EXTRACTION_SYSTEM_PROMPT
    + "\n\nRespond with ONLY a single JSON object (no markdown code fences, no commentary before or after) "
    "shaped exactly like this, with no extra fields:\n"
    '{"scheme_name": string or null, "description": string or null, "benefits_summary": string or null, '
    '"deadline": string in YYYY-MM-DD format or null, '
    '"rules": [{"rule_type": string, "op": string, "value": <string, number, or list of strings>, "required": boolean}]}'
)


class GeminiSchemeExtractor(SchemeExtractor):
    """Same contract as AnthropicSchemeExtractor, calling Google's Gemini API
    instead (has a free tier, unlike Anthropic's API - see
    docs/TRUST_PIPELINE.md Phase 3 for why this exists alongside it). Uses
    plain JSON mode with an explicit shape in the prompt rather than Gemini's
    stricter response_schema structured-output feature, since that requires a
    fixed type per field and our "value" field is deliberately polymorphic
    (string, number, or list) depending on rule_type - JSON mode plus the
    already-lenient parse_extraction() is more robust to that than fighting
    the schema validator.

    Retry/backoff on 429s is handled by google-genai's own HttpRetryOptions,
    not reimplemented here - a first version wrapped generate_content() in its
    own manual retry loop on top of the SDK's built-in one, and the two
    stacked (SDK retries up to 5 times internally before raising, then the
    manual loop retried again on top), which on a real run looked
    indistinguishable from a hang. Configuring the SDK's own retry/timeout
    instead keeps this bounded.
    """

    MODEL = "gemini-3.6-flash"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.gemini_api_key

    def _client(self):
        if not self.api_key:
            raise ExtractorUnavailable(
                "GEMINI_API_KEY is not set. Set it in the environment (or backend/.env) to run extraction."
            )
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise ExtractorUnavailable(
                "the 'google-genai' package is not installed. Install it with `pip install google-genai`."
            ) from exc
        return genai.Client(
            api_key=self.api_key,
            http_options=types.HttpOptions(
                timeout=GEMINI_TIMEOUT_MS,
                retry_options=types.HttpRetryOptions(
                    attempts=GEMINI_RETRY_ATTEMPTS,
                    initial_delay=GEMINI_RETRY_INITIAL_DELAY,
                    max_delay=GEMINI_RETRY_MAX_DELAY,
                ),
            ),
        )

    def extract(self, html: str | bytes, source_url: str) -> ExtractedScheme:
        client = self._client()
        if isinstance(html, bytes):
            html = html.decode("utf-8", errors="replace")
        text = html_to_text(html)[:MAX_INPUT_CHARS]

        from google.genai import types

        response = client.models.generate_content(
            model=self.MODEL,
            contents=f"Source URL: {source_url}\n\nPage text:\n{text}",
            config=types.GenerateContentConfig(
                system_instruction=GEMINI_JSON_INSTRUCTIONS,
                temperature=0,
                response_mime_type="application/json",
            ),
        )
        return parse_extraction(json.loads(response.text))


def get_configured_extractor() -> SchemeExtractor | None:
    """Whichever extractor has a configured key, preferring Gemini (the free
    tier) when both are set. Returns None if neither is configured."""
    if settings.gemini_api_key:
        return GeminiSchemeExtractor()
    if settings.anthropic_api_key:
        return AnthropicSchemeExtractor()
    return None


def parse_extraction(data: dict) -> ExtractedScheme:
    rules = []
    for r in data.get("rules") or []:
        try:
            rules.append(ExtractedRule(r["rule_type"], r["op"], r.get("value"), r.get("required", True)))
        except (KeyError, ValueError):
            continue  # drop malformed rules rather than fail the whole extraction
    return ExtractedScheme(
        scheme_name=data.get("scheme_name"),
        description=data.get("description"),
        benefits_summary=data.get("benefits_summary"),
        deadline=data.get("deadline"),
        rules=rules,
        raw_model_json=data,
    )
