import unittest
from datetime import datetime, timedelta

from trust.engine import MODE_ASSERTIVE, MODE_DISCOVERY_ONLY, MODE_HEDGED, SignalInputs, apply_trust_score, score_scheme
from trust.sanity import check_rule_sanity


class FakeScheme:
    confidence = None
    trust_mode = "unscored"
    last_scored_at = None


class TestTrustEngine(unittest.TestCase):
    def test_strong_signals_yield_assertive_mode(self):
        now = datetime.utcnow()
        signals = SignalInputs(
            source_types=["gov_ministry", "state_portal"],
            field_agreement={"income_max": True, "min_age": True},
            extraction_stable=True,
            sanity_flags=[],
            last_fetched_at=now,
            now=now,
        )
        score = score_scheme(signals)
        self.assertEqual(score.mode, MODE_ASSERTIVE)
        self.assertGreaterEqual(score.confidence, 0.75)

    def test_source_disagreement_demotes_regardless_of_other_signals(self):
        now = datetime.utcnow()
        signals = SignalInputs(
            source_types=["gov_ministry", "state_portal"],
            field_agreement={"income_max": False},
            extraction_stable=True,
            sanity_flags=[],
            last_fetched_at=now,
            now=now,
        )
        score = score_scheme(signals)
        self.assertLessEqual(score.confidence, 0.4)
        self.assertIn(score.mode, (MODE_HEDGED, MODE_DISCOVERY_ONLY))
        self.assertTrue(any("disagreement" in r for r in score.reasons))

    def test_unstable_extraction_caps_confidence(self):
        now = datetime.utcnow()
        signals = SignalInputs(
            source_types=["gov_ministry"],
            field_agreement=None,
            extraction_stable=False,
            sanity_flags=[],
            last_fetched_at=now,
            now=now,
        )
        score = score_scheme(signals)
        self.assertLessEqual(score.confidence, 0.4)

    def test_failed_sanity_check_forces_discovery_only(self):
        now = datetime.utcnow()
        signals = SignalInputs(
            source_types=["gov_ministry", "state_portal"],
            field_agreement={"income_max": True},
            extraction_stable=True,
            sanity_flags=["min_age >= max_age"],
            last_fetched_at=now,
            now=now,
        )
        score = score_scheme(signals)
        self.assertLessEqual(score.confidence, 0.3)
        self.assertEqual(score.mode, MODE_DISCOVERY_ONLY)

    def test_stale_fetch_lowers_confidence_via_freshness_decay(self):
        base_signals = dict(
            source_types=["gov_ministry"],
            field_agreement={"income_max": True},
            extraction_stable=True,
            sanity_flags=[],
        )
        now = datetime.utcnow()
        fresh = score_scheme(SignalInputs(**base_signals, last_fetched_at=now, now=now))
        stale = score_scheme(SignalInputs(**base_signals, last_fetched_at=now - timedelta(days=365), now=now))
        self.assertGreater(fresh.confidence, stale.confidence)

    def test_no_sources_yields_zero_confidence(self):
        score = score_scheme(SignalInputs(source_types=[]))
        self.assertEqual(score.confidence, 0.0)
        self.assertEqual(score.mode, MODE_DISCOVERY_ONLY)

    def test_apply_trust_score_writes_onto_scheme(self):
        scheme = FakeScheme()
        now = datetime.utcnow()
        score = score_scheme(SignalInputs(source_types=["gov_ministry"], last_fetched_at=now, now=now))
        apply_trust_score(scheme, score, now=now)
        self.assertEqual(scheme.confidence, score.confidence)
        self.assertEqual(scheme.trust_mode, score.mode)
        self.assertEqual(scheme.last_scored_at, now)


class TestSanityChecks(unittest.TestCase):
    def test_plausible_rules_pass(self):
        rules = [
            {"rule_type": "min_age", "value": 18},
            {"rule_type": "max_age", "value": 35},
            {"rule_type": "income_max", "value": 200000},
        ]
        self.assertEqual(check_rule_sanity(rules), [])

    def test_min_age_gte_max_age_flagged(self):
        rules = [{"rule_type": "min_age", "value": 40}, {"rule_type": "max_age", "value": 30}]
        flags = check_rule_sanity(rules)
        self.assertIn("min_age >= max_age", flags)

    def test_implausible_income_flagged(self):
        rules = [{"rule_type": "income_max", "value": 5}]
        flags = check_rule_sanity(rules)
        self.assertIn("income_max out of plausible range", flags)

    def test_no_rules_extracted_is_flagged_not_treated_as_clean(self):
        # Regression: a live run found CMCHIS and UYEGP extracted zero rules but
        # still scored "hedged" because the engine only checked the rules it had.
        flags = check_rule_sanity([])
        self.assertIn("no eligibility rules extracted", flags)

    def test_implausible_age_flagged(self):
        rules = [{"rule_type": "min_age", "value": 200}]
        flags = check_rule_sanity(rules)
        self.assertIn("min_age out of plausible range", flags)


if __name__ == "__main__":
    unittest.main()
