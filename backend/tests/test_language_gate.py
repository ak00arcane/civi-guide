import unittest

from trust.language_gate import ASSERTIVE, DISCOVERY_ONLY, HEDGED, effective_claim_level, gate_scheme_language


class TestEffectiveClaimLevel(unittest.TestCase):
    def test_scored_mode_wins_regardless_of_other_flags(self):
        self.assertEqual(effective_claim_level(HEDGED, is_demo=False, verification_status="VERIFIED"), HEDGED)
        self.assertEqual(effective_claim_level(DISCOVERY_ONLY, is_demo=False, verification_status="VERIFIED"), DISCOVERY_ONLY)

    def test_unscored_verified_scheme_defaults_to_assertive(self):
        self.assertEqual(effective_claim_level("unscored", is_demo=False, verification_status="VERIFIED"), ASSERTIVE)

    def test_unscored_demo_scheme_defaults_to_discovery_only(self):
        self.assertEqual(effective_claim_level("unscored", is_demo=True, verification_status="demo"), DISCOVERY_ONLY)

    def test_unscored_needs_review_scheme_defaults_to_hedged(self):
        self.assertEqual(effective_claim_level("unscored", is_demo=False, verification_status="needs_review"), HEDGED)

    def test_missing_mode_behaves_like_unscored(self):
        self.assertEqual(effective_claim_level(None, is_demo=False, verification_status="VERIFIED"), ASSERTIVE)


class TestGateSchemeLanguage(unittest.TestCase):
    def test_assertive_has_no_qualifier(self):
        result = gate_scheme_language(
            trust_mode=ASSERTIVE,
            is_demo=False,
            verification_status="VERIFIED",
            official_source="https://pmkisan.gov.in/",
            last_verified_date="2026-08-31",
            confidence=0.92,
        )
        self.assertIsNone(result["qualifier"])
        self.assertIn("pmkisan.gov.in", result["source_line"])
        self.assertIn("2026-08-31", result["source_line"])

    def test_hedged_and_discovery_only_carry_a_qualifier(self):
        for mode in (HEDGED, DISCOVERY_ONLY):
            result = gate_scheme_language(
                trust_mode=mode,
                is_demo=False,
                verification_status="VERIFIED",
                official_source="https://example.gov.in/",
                last_verified_date=None,
                confidence=0.3,
            )
            self.assertIsNotNone(result["qualifier"])
            self.assertEqual(result["claim_level"], mode)

    def test_confidence_and_as_of_pass_through_unchanged(self):
        result = gate_scheme_language(
            trust_mode=HEDGED,
            is_demo=False,
            verification_status="VERIFIED",
            official_source=None,
            last_verified_date="2026-01-01",
            confidence=0.5,
        )
        self.assertEqual(result["confidence"], 0.5)
        self.assertEqual(result["as_of"], "2026-01-01")


if __name__ == "__main__":
    unittest.main()
