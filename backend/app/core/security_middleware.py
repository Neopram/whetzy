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
        # HSTS only over HTTPS / in production behind TLS.
        if self._enable_hsts:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload"
            )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Ventana fija por cliente. Las rutas donde se adivinan credenciales
    tienen su propio presupuesto (ASVS V11.2 / V2.2.1).

    Tres cosas que no hacia y costaban caro:

    - **Metia `/auth/me` y `/auth/refresh` en el cubo estricto.** La app llama a
      `/auth/me` en cada arranque y `/auth/refresh` cada vez que caduca el token,
      asi que el uso normal se comia el presupuesto pensado para frenar ataques.
      Ahora solo cuentan ahi las rutas de `_SENSIBLES`.
    - **El cubo era global.** Con `TRUST_PROXY_HEADERS` en false y un proxy
      delante, `request.client.host` es la IP del proxy para todos.
    - **`_hits` no se vaciaba nunca.** Se limpiaban las marcas de tiempo dentro
      de cada lista pero la clave se quedaba, asi que el diccionario crecia con
      cada IP vista y no bajaba jamas.

    Sigue siendo **por proceso**: con varias replicas el limite efectivo se
    multiplica y a un mismo cliente le puede tocar un proceso u otro. Medido en
    produccion el 2026-09-20 (429 intermitentes en peticiones consecutivas). Para
    un limite real y compartido hace falta el `RedisRateLimiter` de
    `core/rate_limiter.py`, que existe y no esta conectado.
    """

    #: Rutas de `/api/v1/auth` donde un atacante prueba credenciales o quema
    #: correos. El resto (`/me`, `/refresh`, `/logout`) es trafico de sesion.
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
    ) -> None:
        super().__init__(app)
        self._default_limit = default_limit
        self._auth_limit = auth_limit
        self._window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def _client_key(self, request: Request) -> str:
        """IP del cliente, sin dejar que el cliente la elija.

        `X-Forwarded-For` se lee **por la derecha**, saltando tantas entradas
        como proxies de confianza haya. La primera entrada por la izquierda la
        escribe quien llama, asi que tomarla —como se hacia— deja que cualquiera
        se invente una IP por peticion y esquive el limite entero mandando una
        cabecera distinta cada vez.
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
        # Sondas de salud y documentacion, exentas. `/health` era coincidencia
        # exacta, asi que `/health/ready` y `/health/live` —las que consulta el
        # monitor cada pocos segundos— si contaban.
        if path == "/" or path.startswith(("/health", "/docs", "/redoc")):
            return await call_next(request)

        is_sensible = path.startswith(self._SENSIBLES)
        is_tutor = path.startswith("/api/v1/tutor")
        limit = self._auth_limit if (is_sensible or is_tutor) else self._default_limit
        key_suffix = "auth" if is_sensible else "tutor" if is_tutor else "api"
        key = f"{self._client_key(request)}:{key_suffix}"

        now = time.monotonic()
        window_start = now - self._window
        bucket = self._hits[key]
        # Drop timestamps outside the window.
        bucket[:] = [t for t in bucket if t >= window_start]
        if not bucket:
            # Sin esto la clave sobrevive a su ultima peticion y `_hits` solo
            # crece: un diccionario con una entrada por IP vista desde que
            # arranco el proceso.
            del self._hits[key]
            bucket = self._hits[key]

        if len(bucket) >= limit:
            retry_after = int(self._window - (now - bucket[0])) + 1
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": str(max(1, retry_after))},
            )

        bucket.append(now)
        return await call_next(request)
