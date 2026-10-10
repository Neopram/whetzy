"""CSRF: una petición que cambia estado con cookie de sesión tiene que venir de
un origen de la lista (S.13).

En producción las cookies de sesión van con `SameSite=None` (`cookies.py`,
frontend y API en dominios distintos), así que el navegador las manda también
en una petición que dispara otra web. CORS no lo para: impide *leer* la
respuesta, no que la petición llegue. Un `POST` sin cuerpo, como
`/billing/paddle/cancel`, es una «simple request» sin preflight: una página
cualquiera podía cancelar la suscripción de quien la visitara con la sesión
abierta.

La regla: `POST`, `PUT`, `PATCH` o `DELETE` con cookie de sesión exige que
`Origin` (o, si falta, el origen de `Referer`) esté en
`settings.active_cors_origins`, la misma lista que CORS. Sin cookie no hay
credencial ambiental que robar: los webhooks y los clientes con
`Authorization: Bearer` pasan sin mirar.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from urllib.parse import urlsplit

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.core.cookies import ACCESS_COOKIE, REFRESH_COOKIE

UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
SESSION_COOKIES = (ACCESS_COOKIE, REFRESH_COOKIE)


def request_origin(request: Request) -> str | None:
    """`Origin`, o el origen (`esquema://host[:puerto]`) de `Referer` si falta."""
    origin = request.headers.get("origin")
    if origin:
        return origin
    referer = request.headers.get("referer")
    if not referer:
        return None
    parts = urlsplit(referer)
    if not parts.scheme or not parts.netloc:
        return None
    return f"{parts.scheme}://{parts.netloc}"


class CSRFOriginMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, allowed_origins: Iterable[str]) -> None:
        super().__init__(app)
        self.allowed_origins = frozenset(o.rstrip("/") for o in allowed_origins)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.method in UNSAFE_METHODS and any(c in request.cookies for c in SESSION_COOKIES):
            origin = request_origin(request)
            # `Origin: null` (iframe con sandbox, redirecciones) tampoco vale.
            if origin is None or origin.rstrip("/") not in self.allowed_origins:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Origen no permitido para esta petición (CSRF)"},
                )
        return await call_next(request)
