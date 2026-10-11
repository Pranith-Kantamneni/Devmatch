"""Lightweight in-memory rate limiter (fixed window per client IP).

Suitable for a single replica. When scaling past one API replica, replace
the store with Redis (see README "Scaling") — the middleware interface stays
the same.
"""

import time
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings


class InMemoryRateLimiter(BaseHTTPMiddleware):
    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
        # (bucket_key, window_start) -> count
        self._hits: dict[tuple[str, int], int] = defaultdict(int)
        self._last_sweep = time.monotonic()

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if not self.enabled or not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        path = request.url.path
        if path in ("/health", "/readyz", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        if path.startswith("/api/v1/auth"):
            limit = settings.RATE_LIMIT_AUTH_PER_MINUTE
            bucket = "auth"
        else:
            limit = settings.RATE_LIMIT_DEFAULT_PER_MINUTE
            bucket = "api"

        client_ip = self._client_ip(request)
        window = int(time.time() // 60)
        key = (f"{bucket}:{client_ip}", window)
        self._hits[key] += 1
        self._sweep()

        if self._hits[key] > limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={"Retry-After": "60"},
            )
        return await call_next(request)

    @staticmethod
    def _client_ip(request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client is not None:
            return request.client.host
        return "unknown"

    def _sweep(self) -> None:
        now = time.monotonic()
        if now - self._last_sweep < 120:
            return
        self._last_sweep = now
        current_window = int(time.time() // 60)
        stale = [k for k in self._hits if k[1] < current_window - 1]
        for k in stale:
            del self._hits[k]
