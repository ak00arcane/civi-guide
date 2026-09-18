import json
import unittest

from app.config import settings
from extraction.extractor import (
    AnthropicSchemeExtractor,
    ExtractorUnavailable,
    GeminiSchemeExtractor,
    get_configured_extractor,
    parse_extraction,
)
from extraction.golden_set import load_golden_set, score_rules
from extraction.schema import html_to_text


class TestExtractAcceptsBytesOrStr(unittest.TestCase):
    def test_extract_decodes_bytes_before_extraction(self):
        # Regression test: services.snapshots.read_snapshot_content() returns bytes
        # (raw_snapshot_path.read_bytes()), and extract() is always called with that
        # in real usage (watcher.py, scripts/score_from_snapshots.py) - a live run
        # against real snapshots caught "cannot use a string pattern on a bytes-like
        # object" because html_to_text()'s regexes require str, and this used to only
        # ever be tested with a str fixture.
        extractor = AnthropicSchemeExtractor(api_key="sk-test-not-real")
        captured = {}

        class FakeClient:
            class messages:
                @staticmethod
                def create(**kwargs):
                    captured["content"] = kwargs["messages"][0]["content"]

                    class Block:
                        type = "tool_use"
                        input = {"rules": []}

                    class Response:
                        content = [Block()]

                    return Response()

        extractor._client = lambda: FakeClient()
        extractor.extract(b"<html><body><p>Eligible if age &gt;= 18.</p></body></html>", "https://example.gov.in/")
        self.assertIn("Eligible if age", captured["content"])
        self.assertNotIn("<p>", captured["content"])


class TestHtmlToText(unittest.TestCase):
    def test_strips_tags_scripts_and_collapses_whitespace(self):
        html = """
        <html><head><script>track();</script><style>.a{color:red}</style></head>
        <body>  <h1>Scheme  Name</h1>\n\n<p>Eligible if age &gt;= 18.</p>  </body></html>
        """
        text = html_to_text(html)
        self.assertNotIn("<", text)
        self.assertNotIn("track()", text)
        self.assertNotIn("color:red", text)
        self.assertIn("Scheme Name", text)
        self.assertIn("Eligible if age", text)


class TestParseExtraction(unittest.TestCase):
    def test_parses_valid_rules_and_drops_malformed_ones(self):
        data = {
            "scheme_name": "Test Scheme",
            "description": "desc",
            "benefits_summary": "benefits",
            "deadline": "2027-01-01",
            "rules": [
                {"rule_type": "min_age", "op": "gte", "value": 18, "required": True},
                {"rule_type": "not_a_real_type", "op": "gte", "value": 1},
                {"rule_type": "gender", "op": "not_a_real_op", "value": ["female"]},
            ],
        }
        result = parse_extraction(data)
        self.assertEqual(result.scheme_name, "Test Scheme")
        self.assertEqual(len(result.rules), 1)
        self.assertEqual(result.rules[0].rule_type, "min_age")

    def test_missing_optional_fields_default_to_none_or_empty(self):
        result = parse_extraction({"rules": []})
        self.assertIsNone(result.scheme_name)
        self.assertEqual(result.rules, [])


class TestAnthropicSchemeExtractor(unittest.TestCase):
    def test_raises_when_no_api_key_configured(self):
        # Must not depend on the ambient environment having no key configured -
        # a real ANTHROPIC_API_KEY in backend/.env (as this repo now has) would
        # otherwise make this test silently fire a real API call instead of
        # testing the "no key" path.
        original = settings.anthropic_api_key
        try:
            settings.anthropic_api_key = None
            extractor = AnthropicSchemeExtractor(api_key=None)
            with self.assertRaises(ExtractorUnavailable):
                extractor.extract("<html></html>", "https://example.gov.in/")
        finally:
            settings.anthropic_api_key = original

    def test_falls_back_to_settings_anthropic_api_key_when_not_passed_explicitly(self):
        original = settings.anthropic_api_key
        try:
            settings.anthropic_api_key = "sk-test-from-settings"
            extractor = AnthropicSchemeExtractor()
            self.assertEqual(extractor.api_key, "sk-test-from-settings")
        finally:
            settings.anthropic_api_key = original

    def test_explicit_api_key_overrides_settings(self):
        original = settings.anthropic_api_key
        try:
            settings.anthropic_api_key = "sk-from-settings"
            extractor = AnthropicSchemeExtractor(api_key="sk-explicit")
            self.assertEqual(extractor.api_key, "sk-explicit")
        finally:
            settings.anthropic_api_key = original


class TestGeminiSchemeExtractor(unittest.TestCase):
    def test_raises_when_no_api_key_configured(self):
        original = settings.gemini_api_key
        try:
            settings.gemini_api_key = None
            extractor = GeminiSchemeExtractor(api_key=None)
            with self.assertRaises(ExtractorUnavailable):
                extractor.extract("<html></html>", "https://example.gov.in/")
        finally:
            settings.gemini_api_key = original

    def test_falls_back_to_settings_gemini_api_key_when_not_passed_explicitly(self):
        original = settings.gemini_api_key
        try:
            settings.gemini_api_key = "gm-test-from-settings"
            extractor = GeminiSchemeExtractor()
            self.assertEqual(extractor.api_key, "gm-test-from-settings")
        finally:
            settings.gemini_api_key = original

    def test_client_configures_bounded_timeout_and_retry_via_sdk_not_manual_loop(self):
        # Regression: an earlier version wrapped generate_content() in its own
        # manual retry-on-429 loop on top of google-genai's built-in retries
        # (default up to 5 attempts, backoff up to 60s each). The two stacked
        # and, across several schemes in a batch, looked indistinguishable from
        # a hang on a real run. Retry/timeout must come from the SDK's own
        # HttpRetryOptions/HttpOptions.timeout, not be reimplemented here.
        from extraction.extractor import (
            GEMINI_RETRY_ATTEMPTS,
            GEMINI_RETRY_INITIAL_DELAY,
            GEMINI_RETRY_MAX_DELAY,
            GEMINI_TIMEOUT_MS,
        )

        extractor = GeminiSchemeExtractor(api_key="gm-test-not-real")
        client = extractor._client()
        http_options = client._api_client._http_options
        self.assertEqual(http_options.timeout, GEMINI_TIMEOUT_MS)
        self.assertEqual(http_options.retry_options.attempts, GEMINI_RETRY_ATTEMPTS)
        self.assertEqual(http_options.retry_options.initial_delay, GEMINI_RETRY_INITIAL_DELAY)
        self.assertEqual(http_options.retry_options.max_delay, GEMINI_RETRY_MAX_DELAY)

    def test_extract_parses_json_response_and_decodes_bytes(self):
        extractor = GeminiSchemeExtractor(api_key="gm-test-not-real")

        class FakeResponse:
            text = json.dumps(
                {
                    "scheme_name": "Test Scheme",
                    "rules": [{"rule_type": "min_age", "op": "gte", "value": 18, "required": True}],
                }
            )

        class FakeModels:
            @staticmethod
            def generate_content(**kwargs):
                return FakeResponse()

        class FakeClient:
            models = FakeModels()

        extractor._client = lambda: FakeClient()
        result = extractor.extract(b"<html><body>Eligible if age &gt;= 18.</body></html>", "https://example.gov.in/")
        self.assertEqual(result.scheme_name, "Test Scheme")
        self.assertEqual(len(result.rules), 1)
        self.assertEqual(result.rules[0].rule_type, "min_age")


class TestGetConfiguredExtractor(unittest.TestCase):
    def setUp(self):
        self._orig_gemini = settings.gemini_api_key
        self._orig_anthropic = settings.anthropic_api_key

    def tearDown(self):
        settings.gemini_api_key = self._orig_gemini
        settings.anthropic_api_key = self._orig_anthropic

    def test_prefers_gemini_when_both_configured(self):
        settings.gemini_api_key = "gm-key"
        settings.anthropic_api_key = "an-key"
        self.assertIsInstance(get_configured_extractor(), GeminiSchemeExtractor)

    def test_falls_back_to_anthropic_when_only_that_is_set(self):
        settings.gemini_api_key = None
        settings.anthropic_api_key = "an-key"
        self.assertIsInstance(get_configured_extractor(), AnthropicSchemeExtractor)

    def test_returns_none_when_neither_configured(self):
        settings.gemini_api_key = None
        settings.anthropic_api_key = None
        self.assertIsNone(get_configured_extractor())


class TestGoldenSet(unittest.TestCase):
    def test_golden_set_loads_the_verified_catalog(self):
        records = load_golden_set()
        self.assertEqual(len(records), 12)
        self.assertTrue(all(r.get("rules") for r in records))

    def test_score_rules_perfect_match(self):
        rules = [{"rule_type": "min_age", "op": "gte", "value": 18, "required": True}]
        result = score_rules(rules, rules)
        self.assertEqual(result["precision"], 1.0)
        self.assertEqual(result["recall"], 1.0)
        self.assertEqual(result["value_accuracy"], 1.0)

    def test_score_rules_missing_rule_lowers_recall(self):
        golden = [
            {"rule_type": "min_age", "op": "gte", "value": 18, "required": True},
            {"rule_type": "gender", "op": "in", "value": ["female"], "required": True},
        ]
        extracted = [{"rule_type": "min_age", "op": "gte", "value": 18, "required": True}]
        result = score_rules(golden, extracted)
        self.assertEqual(result["recall"], 0.5)
        self.assertEqual(result["precision"], 1.0)

    def test_score_rules_value_mismatch_lowers_value_accuracy_not_recall(self):
        golden = [{"rule_type": "income_max", "op": "lte", "value": 200000, "required": True}]
        extracted = [{"rule_type": "income_max", "op": "lte", "value": 250000, "required": True}]
        result = score_rules(golden, extracted)
        self.assertEqual(result["recall"], 1.0)
        self.assertEqual(result["value_accuracy"], 0.0)

    def test_score_rules_normalizes_list_value_order(self):
        golden = [{"rule_type": "gender", "op": "in", "value": ["female", "other"], "required": True}]
        extracted = [{"rule_type": "gender", "op": "in", "value": ["Other", "Female"], "required": True}]
        result = score_rules(golden, extracted)
        self.assertEqual(result["value_accuracy"], 1.0)


if __name__ == "__main__":
    unittest.main()
