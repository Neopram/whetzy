"""Structured JSON logging for the Whetzy backend.

Every log line includes at minimum:
  timestamp, level, logger, message

When a request is in scope the `RequestIDMiddleware` (below) injects:
  request_id, user_id (when auth'd), path, method, status_code, latency_ms

Usage:
    from app.core.logging import configure_logging, RequestIDMiddleware
    configure_logging()  # call once at startup
    app.add_middleware(RequestIDMiddleware)
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# ── Context var shared across the current async task tree ─────────────────────

_request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
_user_id_var: ContextVar[str] = ContextVar("user_id", default="-")


def get_request_id() -> str:
    return _request_id_var.get()


def set_user_id(uid: str) -> None:
    _user_id_var.set(uid)


# ── JSON log formatter ────────────────────────────────────────────────────────


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": _request_id_var.get(),
            "user_id": _user_id_var.get(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: int = logging.INFO) -> None:
    """Replace root handler with a structured JSON handler.

    Call once at application startup (before any log records are emitted).
    """
    handler = logging.StreamHandler()
    handler.setFormatter(_JSONFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


# ── Request-ID middleware ─────────────────────────────────────────────────────


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assigns a unique request_id to every request and logs it on completion.

    The id is taken from `X-Request-ID` if provided by a proxy, otherwise
    generated. It is set in the response header so callers can correlate logs.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        req_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        token_rid = _request_id_var.set(req_id)
        token_uid = _user_id_var.set("-")

        start = time.monotonic()
        response = await call_next(request)
        latency_ms = round((time.monotonic() - start) * 1000)

        # Propagate authenticated user to Sentry (no-op when Sentry is absent).
        uid = _user_id_var.get()
        if uid and uid != "-":
            try:
                from app.core.error_tracking import set_user_context  # noqa: PLC0415
                set_user_context(uid)
            except Exception:  # noqa: BLE001
                pass

        response.headers["X-Request-ID"] = req_id
        logging.getLogger("whetzy.access").info(
            "%s %s %s",
            request.method,
            request.url.path,
            response.status_code,
            extra={},
        )

        _request_id_var.reset(token_rid)
        _user_id_var.reset(token_uid)

        return response
