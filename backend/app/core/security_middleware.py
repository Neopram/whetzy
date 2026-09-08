"""Security middleware aligned with OWASP ASVS 5.0 (targeting L2).

- Security response headers (ASVS V14.4 / V13): HSTS, CSP, X-Content-Type-Options,
  X-Frame-Options, Referrer-Policy, Permissions-Policy, COOP/CORP.
- A lightweight fixed-window per-IP rate limiter (ASVS V11.2 anti-automation).
  In-memory (single instance) — swap the store for Redis for horizontal scale.
"""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings

# ASVS V14.4: security headers. CSP is API-appropriate (no inline content served).
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
    "X-Permitted-Cross-Domain-Policies": "none",
    "Cache-Control": "no-store",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, enable_hsts: bool = False) -> None:
        super().__init__(app)
        self._enable_hsts = enable_hsts

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        for key, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
        # HSTS only over HTTPS / in production behind TLS.
        if self._enable_hsts:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload"
            )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window per-client rate limit. Auth endpoints get a stricter budget
    to blunt credential-stuffing (ASVS V11.2 / V2.2.1)."""

    def __init__(
        self,
        app: Any,
        default_limit: int = 120,
        auth_limit: int = 12,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self._default_limit = default_limit
        self._auth_limit = auth_limit
        self._window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def _client_key(self, request: Request) -> str:
        # Only trust X-Forwarded-For when TRUST_PROXY_HEADERS=true (ASVS V11.2).
        # Default: use socket peer to prevent IP spoofing via forged headers.
        if settings.TRUST_PROXY_HEADERS:
            fwd = request.headers.get("x-forwarded-for")
            if fwd:
                return fwd.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        path = request.url.path
        # Health/docs are exempt.
        if path in ("/health", "/") or path.startswith(("/docs", "/redoc")):
            return await call_next(request)

        is_auth = path.startswith("/api/v1/auth")
        is_tutor = path.startswith("/api/v1/tutor")
        limit = self._auth_limit if (is_auth or is_tutor) else self._default_limit
        key_suffix = "auth" if is_auth else "tutor" if is_tutor else "api"
        key = f"{self._client_key(request)}:{key_suffix}"

        now = time.monotonic()
        window_start = now - self._window
        bucket = self._hits[key]
        # Drop timestamps outside the window.
        bucket[:] = [t for t in bucket if t >= window_start]

        if len(bucket) >= limit:
            retry_after = int(self._window - (now - bucket[0])) + 1
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": str(max(1, retry_after))},
            )

        bucket.append(now)
        return await call_next(request)
