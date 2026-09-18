import unittest
from eligibility.engine import RuleTrace, combine_status, evaluate_rule, evaluate_scheme, ELIGIBLE, LIKELY, NEEDS_INFO, NOT_ELIGIBLE


class TestEligibilityEngine(unittest.TestCase):
    def test_evaluate_rule_age(self):
        rule_min = {"rule_type": "min_age", "op": "gte", "value": 18, "required": True}
        rule_max = {"rule_type": "max_age", "op": "lte", "value": 35, "required": True}

        # Within bounds
        self.assertEqual(evaluate_rule(rule_min, {"age": 20}).result, "pass")
        self.assertEqual(evaluate_rule(rule_max, {"age": 20}).result, "pass")

        # Too young
        self.assertEqual(evaluate_rule(rule_min, {"age": 16}).result, "fail")

        # Too old
        self.assertEqual(evaluate_rule(rule_max, {"age": 40}).result, "fail")

        # Unknown
        self.assertEqual(evaluate_rule(rule_min, {}).result, "unknown")

    def test_evaluate_rule_gender(self):
        rule = {"rule_type": "gender", "op": "in", "value": ["female"], "required": True}
        self.assertEqual(evaluate_rule(rule, {"gender": "female"}).result, "pass")
        self.assertEqual(evaluate_rule(rule, {"gender": "male"}).result, "fail")
        self.assertEqual(evaluate_rule(rule, {}).result, "unknown")

    def test_evaluate_rule_income(self):
        rule = {"rule_type": "income_max", "op": "lte", "value": 200000, "required": True}
        self.assertEqual(evaluate_rule(rule, {"annual_family_income": 100000}).result, "pass")
        self.assertEqual(evaluate_rule(rule, {"annual_family_income": 250000}).result, "fail")
        self.assertEqual(evaluate_rule(rule, {}).result, "unknown")

    def test_evaluate_rule_residency(self):
        rule = {"rule_type": "residency_state", "op": "in", "value": ["Tamil Nadu"], "required": True}
        self.assertEqual(evaluate_rule(rule, {"state": "Tamil Nadu"}).result, "pass")
        self.assertEqual(evaluate_rule(rule, {"state": "Kerala"}).result, "fail")
        self.assertEqual(evaluate_rule(rule, {}).result, "unknown")

    def test_combine_status(self):
        trace_pass = RuleTrace("min_age", 18, 20, "pass", True, "pass")
        trace_fail = RuleTrace("max_age", 35, 40, "fail", True, "fail")
        trace_unknown = RuleTrace("income_max", 200000, None, "unknown", True, "unknown")
        trace_opt_unknown = RuleTrace("other", "flag", None, "unknown", False, "unknown")

        self.assertEqual(combine_status([trace_pass]), ELIGIBLE)
        self.assertEqual(combine_status([trace_pass, trace_unknown]), NEEDS_INFO)
        self.assertEqual(combine_status([trace_pass, trace_fail]), NOT_ELIGIBLE)
        self.assertEqual(combine_status([trace_pass, trace_opt_unknown]), LIKELY)

    def test_combine_status_with_no_rules_never_claims_confident_eligibility(self):
        # Regression: a scheme with zero extracted rules (e.g. pipeline-sourced,
        # not yet extracted) used to fall through to ELIGIBLE - the exact
        # "claiming something we don't know" failure this app must avoid.
        self.assertEqual(combine_status([]), NEEDS_INFO)
        self.assertEqual(evaluate_scheme([], {"age": 20})["status"], NEEDS_INFO)


if __name__ == "__main__":
    unittest.main()
