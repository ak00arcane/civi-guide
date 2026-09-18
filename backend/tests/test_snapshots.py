import shutil
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from db.session import Base
from db.models import RawSnapshot


class TestSnapshotStore(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self._orig_snapshot_dir = settings.raw_snapshot_dir
        settings.raw_snapshot_dir = str(self.tmp_dir)

        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()
        settings.raw_snapshot_dir = self._orig_snapshot_dir
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_save_and_read_snapshot(self):
        from services.snapshots import save_snapshot, read_snapshot_content

        snap = save_snapshot(
            self.db,
            source_url="https://pmkisan.gov.in/",
            content=b"<html>hello</html>",
            source_type="gov_ministry",
            http_status=200,
        )
        self.assertEqual(read_snapshot_content(snap), b"<html>hello</html>")
        self.assertTrue(Path(snap.raw_snapshot_path).suffix == ".html")

    def test_identical_content_dedupes_on_disk_but_records_each_fetch(self):
        from services.snapshots import save_snapshot

        s1 = save_snapshot(self.db, source_url="https://pmkisan.gov.in/", content=b"same")
        s2 = save_snapshot(self.db, source_url="https://pmkisan.gov.in/", content=b"same")

        self.assertEqual(s1.content_hash, s2.content_hash)
        self.assertEqual(s1.raw_snapshot_path, s2.raw_snapshot_path)
        self.assertNotEqual(s1.id, s2.id)
        self.assertEqual(self.db.query(RawSnapshot).count(), 2)

    def test_normalized_hash_ignores_markup_only_changes(self):
        from services.snapshots import save_snapshot

        v1 = b'<html><body><p>Eligible if age >= 18.</p><input type="hidden" value="csrf-aaa111"></body></html>'
        v2 = b'<html><body><p>Eligible if age >= 18.</p><input type="hidden" value="csrf-zzz999"></body></html>'

        s1 = save_snapshot(self.db, source_url="https://example.gov.in/", content=v1)
        s2 = save_snapshot(self.db, source_url="https://example.gov.in/", content=v2)

        self.assertNotEqual(s1.content_hash, s2.content_hash)  # raw bytes genuinely differ
        self.assertEqual(s1.normalized_hash, s2.normalized_hash)  # but visible text is identical

    def test_normalized_hash_detects_real_text_changes(self):
        from services.snapshots import save_snapshot

        s1 = save_snapshot(self.db, source_url="https://example.gov.in/", content=b"<p>Income limit: 200000</p>")
        s2 = save_snapshot(self.db, source_url="https://example.gov.in/", content=b"<p>Income limit: 250000</p>")

        self.assertNotEqual(s1.normalized_hash, s2.normalized_hash)

    def test_latest_snapshot_returns_most_recent_fetch(self):
        from datetime import datetime, timedelta

        from services.snapshots import save_snapshot, latest_snapshot

        save_snapshot(
            self.db,
            source_url="https://pmkisan.gov.in/",
            content=b"old",
            fetched_at=datetime.utcnow() - timedelta(days=1),
        )
        latest = save_snapshot(self.db, source_url="https://pmkisan.gov.in/", content=b"new")

        found = latest_snapshot(self.db, "https://pmkisan.gov.in/")
        self.assertEqual(found.id, latest.id)
        self.assertEqual(found.content_hash, latest.content_hash)


if __name__ == "__main__":
    unittest.main()
