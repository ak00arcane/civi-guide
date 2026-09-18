import unittest

from app.config import settings
from app.main import app
from fastapi.testclient import TestClient


class TestSchemeReports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_report_valid_scheme_succeeds(self):
        response = self.client.post(
            "/api/scheme-reports", json={"scheme_id": "TN-EDU-PUDHUMAI-PENN", "reason": "The income limit looks outdated."}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])

    def test_report_unknown_scheme_returns_404(self):
        response = self.client.post("/api/scheme-reports", json={"scheme_id": "NOT-A-REAL-SCHEME", "reason": "test"})
        self.assertEqual(response.status_code, 404)

    def test_report_without_reason_is_rejected(self):
        response = self.client.post("/api/scheme-reports", json={"scheme_id": "TN-EDU-PUDHUMAI-PENN", "reason": ""})
        self.assertEqual(response.status_code, 422)

    def test_admin_listing_requires_admin_token(self):
        response = self.client.get("/api/admin/scheme-reports")
        self.assertEqual(response.status_code, 401)

    def test_admin_listing_returns_submitted_reports_with_valid_token(self):
        self.client.post("/api/scheme-reports", json={"scheme_id": "TN-EDU-PUDHUMAI-PENN", "reason": "Duplicate check."})
        response = self.client.get("/api/admin/scheme-reports", headers={"X-Admin-Token": settings.admin_token})
        self.assertEqual(response.status_code, 200)
        items = response.json()["items"]
        self.assertTrue(any(i["scheme_id"] == "TN-EDU-PUDHUMAI-PENN" for i in items))


if __name__ == "__main__":
    unittest.main()
