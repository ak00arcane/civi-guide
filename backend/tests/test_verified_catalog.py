import unittest
from data_quality.validators import validate_collection
from services.import_schemes import load_verified_catalog


class TestVerifiedCatalog(unittest.TestCase):
    def test_verified_catalog_completeness(self):
        records = load_verified_catalog()
        self.assertGreaterEqual(len(records), 12, "Verified catalog must contain at least 12 real schemes")

        hand_verified = [r for r in records if r.get("verification_status") == "VERIFIED"]
        pipeline_sourced = [r for r in records if r.get("verification_status") == "needs_review"]
        self.assertGreaterEqual(len(hand_verified), 12, "Must keep at least the original 12 hand-verified schemes")

        for r in records:
            self.assertTrue(r.get("scheme_id"), f"Scheme missing scheme_id: {r}")
            self.assertTrue(r.get("scheme_name"), f"Scheme missing scheme_name: {r['scheme_id']}")
            self.assertTrue(r.get("category"), f"Scheme missing category: {r['scheme_id']}")
            self.assertIn(r.get("government_level"), {"central", "state"}, f"Invalid gov level in {r['scheme_id']}")
            self.assertTrue(r.get("description"), f"Scheme missing description: {r['scheme_id']}")
            self.assertTrue(r.get("sources"), f"Scheme missing sources: {r['scheme_id']}")
            self.assertFalse(r.get("is_demo"), f"Verified-catalog scheme {r['scheme_id']} must have is_demo=False")
            self.assertIn(
                r.get("verification_status"),
                {"VERIFIED", "needs_review"},
                f"Scheme {r['scheme_id']} has an unexpected verification_status",
            )

            for s in r["sources"]:
                self.assertTrue(s.get("official_source"), f"Scheme {r['scheme_id']} missing official_source")
                self.assertTrue(
                    s["official_source"].startswith("http"), f"Invalid official_source URL in {r['scheme_id']}"
                )
                if s.get("official_application_url"):
                    self.assertTrue(
                        s["official_application_url"].startswith("http"),
                        f"Invalid application URL in {r['scheme_id']}",
                    )

        # Hand-verified schemes were fully curated by a human and must already
        # have real rules/benefits filled in.
        for r in hand_verified:
            self.assertTrue(r.get("rules"), f"Hand-verified scheme missing rules: {r['scheme_id']}")
            self.assertTrue(r.get("benefits"), f"Hand-verified scheme missing benefits: {r['scheme_id']}")

        # Pipeline-sourced schemes (see docs/TRUST_PIPELINE.md) start with no
        # rules on purpose - the extractor fills them in from the live official
        # page, never from anyone's memory. eligibility/engine.py's
        # combine_status treats an empty rule list as NEEDS_INFO, never a false
        # ELIGIBLE, so shipping these before extraction has run is safe.
        for r in pipeline_sourced:
            self.assertEqual(
                r.get("rules"), [], f"Pipeline-sourced scheme {r['scheme_id']} should start with no hand-written rules"
            )

    def test_verified_catalog_passes_data_quality_validators(self):
        records = load_verified_catalog()
        issues = validate_collection(records)
        # missing_eligibility is expected for pipeline-sourced schemes (no rules
        # yet, by design - see above); anything else is a real data problem.
        unexpected = {sid: flags for sid, flags in issues.items() if flags != ["missing_eligibility"]}
        self.assertEqual(unexpected, {}, f"Unexpected data quality issues in verified catalog: {unexpected}")


if __name__ == "__main__":
    unittest.main()
