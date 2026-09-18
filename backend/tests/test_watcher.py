import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from app.config import settings
from db.models import Scheme, SchemeSource
from db.session import Base
from extraction.extractor import ExtractorUnavailable
from extraction.schema import ExtractedRule, ExtractedScheme
from services.fetch_layer import FetchSkipped
from services.watcher import watch_scheme_source
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class TestWatchSchemeSource(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self._orig_snapshot_dir = settings.raw_snapshot_dir
        settings.raw_snapshot_dir = str(self.tmp_dir)

        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db = SessionLocal()

        self.scheme = Scheme(scheme_id="TEST-001", scheme_name="Test Scheme", category="Education", description="d")
        self.db.add(self.scheme)
        self.db.flush()
        self.source = SchemeSource(
            scheme_pk=self.scheme.id, official_source="https://ministry.gov.in/scheme", source_type="gov_ministry"
        )
        self.db.add(self.source)
        self.db.flush()

    def tearDown(self):
        self.db.close()
        settings.raw_snapshot_dir = self._orig_snapshot_dir
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _fetcher(self, content: bytes):
        fetcher = MagicMock()
        resp = MagicMock(status_code=200, content=content)
        fetcher.fetch_and_store.side_effect = None
        from services.snapshots import save_snapshot

        fetcher.fetch_and_store.side_effect = lambda db, url, **kw: save_snapshot(
            db, source_url=url, content=content, http_status=200, **kw
        )
        return fetcher

    def test_first_fetch_with_no_extractor_reports_first_fetch_and_does_not_rescore(self):
        fetcher = self._fetcher(b"<html>v1</html>")
        result = watch_scheme_source(self.db, self.scheme, self.source, fetcher, extractor=None)
        self.assertEqual(result.outcome, "first_fetch")
        self.assertFalse(result.rescored)
        self.assertIsNone(self.scheme.confidence)

    def test_unchanged_content_skips_extractor_entirely(self):
        fetcher = self._fetcher(b"<html>same</html>")
        watch_scheme_source(self.db, self.scheme, self.source, fetcher, extractor=None)

        extractor = MagicMock()
        result = watch_scheme_source(self.db, self.scheme, self.source, fetcher, extractor=extractor)
        self.assertEqual(result.outcome, "unchanged")
        self.assertFalse(result.rescored)
        extractor.extract.assert_not_called()

    def test_markup_only_diff_between_fetches_reports_unchanged(self):
        fetcher = self._fetcher(b'<html><body><p>Eligible if age >= 18.</p><input value="csrf-aaa"></body></html>')
        watch_scheme_source(self.db, self.scheme, self.source, fetcher, extractor=None)

        fetcher2 = self._fetcher(b'<html><body><p>Eligible if age >= 18.</p><input value="csrf-zzz"></body></html>')
        result = watch_scheme_source(self.db, self.scheme, self.source, fetcher2, extractor=None)
        self.assertEqual(result.outcome, "unchanged")

    def test_changed_content_with_stable_extraction_rescoring_applies_confidence(self):
        fetcher = self._fetcher(b"<html>v1</html>")
        watch_scheme_source(self.db, self.scheme, self.source, fetcher, extractor=None)

        fetcher2 = self._fetcher(b"<html>v2 changed</html>")
        rule = ExtractedRule("min_age", "gte", 18, True)
        extracted = ExtractedScheme("Test Scheme", "desc", "benefits", None, rules=[rule])
        extractor = MagicMock()
        extractor.extract.side_effect = [extracted, extracted]  # identical both runs -> stable

        result = watch_scheme_source(self.db, self.scheme, self.source, fetcher2, extractor=extractor)
        self.assertEqual(result.outcome, "changed")
        self.assertTrue(result.rescored)
        self.assertIsNotNone(self.scheme.confidence)
        self.assertEqual(extractor.extract.call_count, 2)

    def test_zero_rules_extracted_stably_still_caps_confidence_low(self):
        # Regression: a live run against a homepage with no stated eligibility
        # criteria extracted zero rules on both stability-check runs and, because
        # "stable + no sanity flags" used to look clean, scored confidence=0.70
        # mode=hedged - misleadingly implying some confirmed information exists.
        fetcher = self._fetcher(b"<html>v1</html>")
        watch_scheme_source(self.db, self.scheme, self.source, fetcher, extractor=None)

        fetcher2 = self._fetcher(b"<html>v2 changed</html>")
        empty = ExtractedScheme("Test Scheme", "d", "b", None, rules=[])
        extractor = MagicMock()
        extractor.extract.side_effect = [empty, empty]  # stable, but empty both times

        result = watch_scheme_source(self.db, self.scheme, self.source, fetcher2, extractor=extractor)
        self.assertTrue(result.rescored)
        self.assertLessEqual(self.scheme.confidence, 0.3)
        self.assertEqual(self.scheme.trust_mode, "discovery_only")

    def test_unstable_extraction_caps_confidence_low(self):
        fetcher = self._fetcher(b"<html>v1</html>")
        watch_scheme_source(self.db, self.scheme, self.source, fetcher, extractor=None)

        fetcher2 = self._fetcher(b"<html>v2 changed</html>")
        run1 = ExtractedScheme("Test Scheme", "d", "b", None, rules=[ExtractedRule("min_age", "gte", 18, True)])
        run2 = ExtractedScheme("Test Scheme", "d", "b", None, rules=[ExtractedRule("min_age", "gte", 21, True)])
        extractor = MagicMock()
        extractor.extract.side_effect = [run1, run2]  # disagree -> unstable

        result = watch_scheme_source(self.db, self.scheme, self.source, fetcher2, extractor=extractor)
        self.assertTrue(result.rescored)
        self.assertLessEqual(self.scheme.confidence, 0.4)

    def test_extractor_unavailable_at_call_time_skips_rescore_gracefully(self):
        fetcher = self._fetcher(b"<html>v1</html>")
        watch_scheme_source(self.db, self.scheme, self.source, fetcher, extractor=None)

        fetcher2 = self._fetcher(b"<html>v2 changed</html>")
        extractor = MagicMock()
        extractor.extract.side_effect = ExtractorUnavailable("no key")

        result = watch_scheme_source(self.db, self.scheme, self.source, fetcher2, extractor=extractor)
        self.assertEqual(result.outcome, "changed")
        self.assertFalse(result.rescored)
        self.assertIn("unavailable", result.detail)

    def test_robots_disallow_reports_skipped(self):
        fetcher = MagicMock()
        fetcher.fetch_and_store.side_effect = FetchSkipped("disallowed by robots.txt")
        result = watch_scheme_source(self.db, self.scheme, self.source, fetcher, extractor=None)
        self.assertEqual(result.outcome, "skipped")

    def test_missing_official_source_is_skipped_without_fetching(self):
        source = SchemeSource(scheme_pk=self.scheme.id, official_source=None)
        fetcher = MagicMock()
        result = watch_scheme_source(self.db, self.scheme, source, fetcher, extractor=None)
        self.assertEqual(result.outcome, "skipped")
        fetcher.fetch_and_store.assert_not_called()


if __name__ == "__main__":
    unittest.main()
