import unittest

from app.rate_limit import RateLimitMiddleware
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _make_app(limit: int) -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, requests_per_minute=limit)

    @app.get("/api/ping")
    def ping():
        return {"ok": True}

    @app.get("/health")
    def health():
        return {"ok": True}

    return app


class TestRateLimitMiddleware(unittest.TestCase):
    def test_requests_under_limit_pass_through(self):
        client = TestClient(_make_app(limit=3))
        for _ in range(3):
            resp = client.get("/api/ping")
            self.assertEqual(resp.status_code, 200)

    def test_requests_over_limit_are_rejected_with_429(self):
        client = TestClient(_make_app(limit=2))
        client.get("/api/ping")
        client.get("/api/ping")
        resp = client.get("/api/ping")
        self.assertEqual(resp.status_code, 429)

    def test_non_api_paths_are_not_rate_limited(self):
        client = TestClient(_make_app(limit=1))
        client.get("/health")
        resp = client.get("/health")
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
