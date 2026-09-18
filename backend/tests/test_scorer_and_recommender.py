import unittest
from eligibility.engine import ELIGIBLE, NOT_ELIGIBLE
from recommendation.scorer import (
    edu_occ_component,
    eligibility_component,
    location_component,
    need_component,
    profile_income_component,
    weighted_score,
)


class TestScorerAndRecommender(unittest.TestCase):
    def test_hard_eligibility_invariant_not_eligible(self):
        """
        CRITICAL RULE: Semantic similarity must NEVER override factual eligibility.
        If a candidate is not_eligible, eligibility component score is strictly 0.0.
        """
        score = eligibility_component(NOT_ELIGIBLE, passed=0, total=3)
        self.assertEqual(score, 0.0)

    def test_eligible_candidate_scoring(self):
        score_el = eligibility_component(ELIGIBLE, passed=3, total=3)
        self.assertEqual(score_el, 1.0)

        loc_score = location_component({"state": "Tamil Nadu", "district": "Chennai"}, {"state": "Tamil Nadu", "district": "Chennai"})
        self.assertEqual(loc_score, 1.0)

        need_score = need_component(["education"], "Education", 0.9)
        self.assertGreater(need_score, 0.9)

        weights = {
            "eligibility": 0.45,
            "need": 0.25,
            "location": 0.10,
            "income": 0.10,
            "edu_occ": 0.05,
            "usefulness": 0.05,
        }
        parts = {
            "eligibility": score_el,
            "need": need_score,
            "location": loc_score,
            "income": 1.0,
            "edu_occ": 1.0,
            "usefulness": 1.0,
        }
        total = weighted_score(parts, weights)
        self.assertGreater(total, 0.85)


if __name__ == "__main__":
    unittest.main()
