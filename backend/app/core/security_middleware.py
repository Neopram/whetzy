"""Security middleware aligned with OWASP ASVS 5.0 (targeting L2).

- Security response headers (ASVS V14.4 / V13): HSTS, CSP, X-Content-Type-Options,
  X-Frame-Options, Referrer-Policy, Permissions-Policy, COOP/CORP.
- A lightweight fixed-window per-IP rate limiter (ASVS V11.2 anti-automation).
  Uses the shared ``RateLimiter`` interface from ``core/rate_limiter.py`` —
  in-memory by default, Redis when ``REDIS_URL`` is set (22.6).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.core.rate_limiter import RateLimiter, get_rate_limit_stats, get_rate_limiter

# ASVS V14.4: security headers. CSP is API-appropriate (no inline content served).
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
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
        if self._enable_hsts:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload"
            )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window per-client rate limiter delegating to the shared
    ``RateLimiter`` interface (22.6).  When ``REDIS_URL`` is set the
    limit is enforced across replicas; otherwise it falls back to an
    in-memory store per process.

    Sensitive auth routes and the tutor endpoint get a stricter budget
    than the rest of the API (ASVS V11.2 / V2.2.1).
    """

    _SENSIBLES = (
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
        "/api/v1/auth/resend-verification",
        "/api/v1/auth/verify-email",
        "/api/v1/auth/oauth",
    )

    def __init__(
        self,
        app: Any,
        default_limit: int = 120,
        auth_limit: int = 12,
        window_seconds: int = 60,
        limiter: RateLimiter | None = None,
    ) -> None:
        super().__init__(app)
        self._default_limit = default_limit
        self._auth_limit = auth_limit
        self._window = window_seconds
        self._limiter = limiter or get_rate_limiter(
            getattr(settings, "REDIS_URL", None)
        )

    def _client_key(self, request: Request) -> str:
        """IP del cliente, sin dejar que el cliente la elija.

        ``X-Forwarded-For`` se lee **por la derecha**, saltando tantas
        entradas como proxies de confianza haya.
        """
        if settings.TRUST_PROXY_HEADERS:
            fwd = request.headers.get("x-forwarded-for")
            if fwd:
                partes = [p.strip() for p in fwd.split(",") if p.strip()]
                saltos = max(1, settings.TRUSTED_PROXY_HOPS)
                if len(partes) >= saltos:
                    return partes[-saltos]
                return partes[0]
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        path = request.url.path
        if path == "/" or path.startswith(("/health", "/docs", "/redoc")):
            return await call_next(request)

        is_sensible = path.startswith(self._SENSIBLES)
        is_tutor = path.startswith("/api/v1/tutor")
        limit = self._auth_limit if (is_sensible or is_tutor) else self._default_limit
        key_suffix = "auth" if is_sensible else "tutor" if is_tutor else "api"
        key = f"{self._client_key(request)}:{key_suffix}"

        if not await self._limiter.is_allowed(key, limit, self._window):
            get_rate_limit_stats().record_hit(self._client_key(request), key_suffix)
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": str(self._window)},
            )

        return await call_next(request)
