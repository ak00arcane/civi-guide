import unittest
from types import SimpleNamespace

from services.recommend import _no_match_explanation


class TestNoMatchExplanation(unittest.TestCase):
    def test_returns_none_when_there_are_primary_recommendations(self):
        result = _no_match_explanation({}, [], [], primary=[{"x": 1}], near=[], rejected=[])
        self.assertIsNone(result)

    def test_returns_none_when_there_are_near_misses(self):
        result = _no_match_explanation({}, [], [], primary=[], near=[{"x": 1}], rejected=[])
        self.assertIsNone(result)

    def test_empty_profile_and_no_needs_is_unclear_concern(self):
        result = _no_match_explanation({}, [], [], primary=[], near=[], rejected=[])
        self.assertEqual(result["reason"], "unclear_concern")

    def test_profile_signal_present_is_not_unclear_even_without_needs(self):
        # Some real info was given (age) - the request wasn't unclear, we just
        # have nothing to say about it yet.
        result = _no_match_explanation({"age": 25}, [], [], primary=[], near=[], rejected=[])
        self.assertNotEqual(result["reason"], "unclear_concern")

    def test_detected_need_with_no_matching_catalog_category_is_no_data_for_need(self):
        schemes = [SimpleNamespace(category="Healthcare"), SimpleNamespace(category="Housing")]
        result = _no_match_explanation({"age": 25}, ["education"], schemes, primary=[], near=[], rejected=[])
        self.assertEqual(result["reason"], "no_data_for_need")

    def test_detected_need_with_matching_catalog_category_but_rejected_is_not_eligible(self):
        schemes = [SimpleNamespace(category="Education")]
        rejected = [{"scheme_id": "X"}]
        result = _no_match_explanation({"age": 25}, ["education"], schemes, primary=[], near=[], rejected=rejected)
        self.assertEqual(result["reason"], "not_eligible")
        self.assertIn("1", result["message"])


if __name__ == "__main__":
    unittest.main()
