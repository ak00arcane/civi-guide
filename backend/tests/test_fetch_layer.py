import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
from app.config import settings
from db.session import Base
from services.fetch_layer import FetchSkipped, PoliteFetcher, _default_client
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _fake_response(url: str, status_code: int = 200, text: str = "", content: bytes | None = None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.content = content if content is not None else text.encode("utf-8")
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"status {status_code}", request=MagicMock(), response=resp
        )
    else:
        resp.raise_for_status.side_effect = None
    return resp


class TestPoliteFetcher(unittest.TestCase):
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

    def test_default_client_constructs_with_truststore_ssl_context(self):
        # Regression: mudra.org.in and scd.tn.gov.in serve an incomplete cert chain
        # that a static CA bundle can't validate; truststore's OS-native chain
        # building (AIA-fetching, like a browser) fixes it without verify=False.
        # This only checks construction succeeds - the actual chain-building
        # behavior needs a real network call to verify, done manually against
        # those two sites when this was diagnosed.
        client = _default_client()
        try:
            self.assertIsInstance(client, httpx.Client)
        finally:
            client.close()

    def test_disallowed_by_robots_txt_raises_and_does_not_fetch_page(self):
        client = MagicMock()
        client.get.return_value = _fake_response("robots", text="User-agent: *\nDisallow: /private/\n")
        fetcher = PoliteFetcher(client=client, min_interval_seconds=0)

        with self.assertRaises(FetchSkipped):
            fetcher.fetch("https://example.gov.in/private/page")

        # Only the robots.txt request should have happened, never the page itself.
        self.assertEqual(client.get.call_count, 1)

    def test_allowed_url_is_fetched_and_stored_as_snapshot(self):
        client = MagicMock()

        def get(url, *args, **kwargs):
            if url.endswith("/robots.txt"):
                return _fake_response(url, text="User-agent: *\nAllow: /\n")
            return _fake_response(url, text="<html>scheme details</html>")

        client.get.side_effect = get
        fetcher = PoliteFetcher(client=client, min_interval_seconds=0)

        snap = fetcher.fetch_and_store(
            self.db, "https://pmkisan.gov.in/", source_type="gov_ministry", scheme_pk=None
        )
        self.assertEqual(snap.http_status, 200)
        self.assertEqual(snap.source_type, "gov_ministry")
        self.assertTrue(Path(snap.raw_snapshot_path).exists())

    def test_missing_robots_txt_is_treated_as_permissive(self):
        client = MagicMock()

        def get(url, *args, **kwargs):
            if url.endswith("/robots.txt"):
                return _fake_response(url, status_code=404, text="")
            return _fake_response(url, text="<html>ok</html>")

        client.get.side_effect = get
        fetcher = PoliteFetcher(client=client, min_interval_seconds=0)

        resp = fetcher.fetch("https://ministry.gov.in/scheme")
        self.assertEqual(resp.status_code, 200)

    @patch("services.fetch_layer.time.sleep", return_value=None)
    def test_server_error_retries_then_succeeds(self, mock_sleep):
        client = MagicMock()
        call_log = []

        def get(url, *args, **kwargs):
            if url.endswith("/robots.txt"):
                return _fake_response(url, text="User-agent: *\nAllow: /\n")
            call_log.append(url)
            if len(call_log) < 3:
                return _fake_response(url, status_code=500, text="error")
            return _fake_response(url, status_code=200, text="ok")

        client.get.side_effect = get
        fetcher = PoliteFetcher(client=client, min_interval_seconds=0)

        resp = fetcher.fetch("https://ministry.gov.in/scheme")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(call_log), 3)
        self.assertTrue(mock_sleep.called)


if __name__ == "__main__":
    unittest.main()
