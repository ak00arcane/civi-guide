"""Lightweight in-memory rate limiter (Phase 7, see docs/TRUST_PIPELINE.md).

Per-process, per-client-IP sliding window over /api/* routes. Fine for a
single-instance deployment; a multi-instance deployment needs a shared store
(e.g. Redis) instead, since this does not coordinate across processes. Also
doesn't evict idle IPs, so memory grows slowly with distinct clients — an
acceptable MVP tradeoff, revisit if this ever runs long enough for that to
matter.
"""

import time
from collections import defaultdict, deque

from app.config import settings
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

WINDOW_SECONDS = 60.0


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int | None = None):
        super().__init__(app)
        self.limit = requests_per_minute if requests_per_minute is not None else settings.rate_limit_per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        hits = self._hits[client_ip]
        while hits and now - hits[0] > WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= self.limit:
            return JSONResponse(status_code=429, content={"detail": "Too many requests. Please slow down."})
        hits.append(now)
        return await call_next(request)
