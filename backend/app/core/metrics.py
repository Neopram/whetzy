"""Prometheus metrics middleware and /metrics endpoint.

RED metrics (Rate / Errors / Duration) are exposed per endpoint so a
Prometheus scraper or Grafana Cloud agent can consume them.

Skipped paths:  /metrics itself and anything under /health* to avoid
cardinality explosion from liveness / readiness probes.
"""

from __future__ import annotations

import time

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ── Metric definitions ────────────────────────────────────────────────────────

_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "path"],
)

# ── Paths excluded from instrumentation ───────────────────────────────────────

_SKIP_PREFIXES = ("/metrics", "/health")


def _should_skip(path: str) -> bool:
    return any(path == p or path.startswith(p + "/") or path.startswith(p + "?")
               for p in _SKIP_PREFIXES)


# ── Middleware ────────────────────────────────────────────────────────────────


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record RED metrics for every instrumented HTTP request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        method = request.method

        if _should_skip(path):
            return await call_next(request)

        _REQUESTS_IN_PROGRESS.labels(method=method, path=path).inc()
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.perf_counter() - start
            status_str = str(status_code)
            _REQUESTS_IN_PROGRESS.labels(method=method, path=path).dec()
            _REQUESTS_TOTAL.labels(method=method, path=path, status=status_str).inc()
            _REQUEST_DURATION.labels(method=method, path=path, status=status_str).observe(duration)


# ── /metrics route handler ────────────────────────────────────────────────────


async def metrics_endpoint(request: Request) -> Response:
    """Return Prometheus text format metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
