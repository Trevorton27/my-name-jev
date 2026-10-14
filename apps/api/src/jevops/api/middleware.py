"""Security middleware: rate limiting, request size limits, secure headers."""

from __future__ import annotations

import time
from collections.abc import Callable

import structlog
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.stdlib.get_logger()


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, max_size: int = 1_048_576) -> None:
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            return Response(
                content='{"error": {"message": "Request too large", "status": 413}}',
                status_code=413,
                media_type="application/json",
            )
        return await call_next(request)


class SecureHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory sliding window rate limiter. Use Redis in production."""

    def __init__(self, app: FastAPI, requests_per_minute: int = 60) -> None:
        super().__init__(app)
        self.rpm = requests_per_minute
        self._windows: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/v1/health"):
            return await call_next(request)

        key = self._get_key(request)
        now = time.monotonic()
        window = self._windows.setdefault(key, [])

        # Remove expired entries
        cutoff = now - 60.0
        self._windows[key] = [t for t in window if t > cutoff]
        window = self._windows[key]

        if len(window) >= self.rpm:
            logger.warning("rate_limit.exceeded", key=key)
            return Response(
                content='{"error": {"message": "Rate limit exceeded", "status": 429}}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": "60"},
            )

        window.append(now)
        return await call_next(request)

    def _get_key(self, request: Request) -> str:
        # Use API key prefix if present, otherwise client IP
        api_key = request.headers.get("X-API-Key", "")
        if api_key and "_" in api_key:
            parts = api_key.split("_", 3)
            if len(parts) >= 3:
                return f"key:{parts[0]}_{parts[1]}_{parts[2]}"
        client = request.client
        return f"ip:{client.host if client else 'unknown'}"
