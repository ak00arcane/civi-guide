import unittest
from fastapi.testclient import TestClient
from app.main import app


class TestAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])

    def test_schemes_list_endpoint(self):
        response = self.client.get("/api/schemes")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertGreater(len(data["items"]), 0)

    def test_parse_query_endpoint(self):
        response = self.client.post(
            "/api/parse-query",
            json={"query": "I am a 20-year-old female student from Tamil Nadu looking for education financial help"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["locale"], "en")
        self.assertEqual(data["fields"]["age"], 20)
        self.assertEqual(data["fields"]["gender"], "female")
        self.assertEqual(data["fields"]["state"], "Tamil Nadu")

    def test_recommend_endpoint_tamil_nadu_student(self):
        response = self.client.post(
            "/api/recommend",
            json={
                "profile": {
                    "age": 20,
                    "gender": "female",
                    "state": "Tamil Nadu",
                    "education": "Student",
                    "annual_family_income": 120000,
                },
                "needs": [{"need_code": "education", "confidence": 0.9, "explicit": True}],
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("recommendations", data)
        rec_ids = [r["scheme_id"] for r in data["recommendations"]]
        # Real verified scheme Pudhumai Penn should be present
        self.assertIn("TN-EDU-PUDHUMAI-PENN", rec_ids)
        pudhumai_penn = next(r for r in data["recommendations"] if r["scheme_id"] == "TN-EDU-PUDHUMAI-PENN")
        self.assertEqual(pudhumai_penn["government_level"], "state")
        self.assertEqual(
            next(r for r in data["recommendations"] if r["scheme_id"] == "IN-AGR-PM-KISAN")["government_level"],
            "central",
        )


if __name__ == "__main__":
    unittest.main()
