"""OpenTelemetry distributed tracing configuration.

Wires up:
  - TracerProvider with BatchSpanProcessor
  - OTLPSpanExporter when OTEL_EXPORTER_OTLP_ENDPOINT is set; ConsoleSpanExporter otherwise
  - FastAPIInstrumentor  (HTTP spans)
  - SQLAlchemyInstrumentor (DB spans)

All OTel imports are guarded so the app starts cleanly even if the packages
are not installed (e.g. slim Docker layer without extras).

Usage (call once at startup, before the FastAPI app is constructed):
    configure_telemetry(service_name, otlp_endpoint)
"""

from __future__ import annotations

import logging

logger = logging.getLogger("whetzy.telemetry")


def configure_telemetry(service_name: str, otlp_endpoint: str) -> None:
    """Configure OTel tracing.  Never raises — failures are logged as warnings."""
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.warning(
            "opentelemetry-sdk not installed — tracing disabled. "
            "Install opentelemetry-api / opentelemetry-sdk to enable."
        )
        return

    resource = Resource(attributes={SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)

    # Choose exporter: OTLP for staging/prod, console for local dev.
    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            logger.info("OTel: OTLP exporter → %s", otlp_endpoint)
        except ImportError:
            logger.warning(
                "opentelemetry-exporter-otlp-proto-grpc not installed — "
                "falling back to ConsoleSpanExporter."
            )
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            exporter = ConsoleSpanExporter()  # type: ignore[assignment]
    else:
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter
        exporter = ConsoleSpanExporter()  # type: ignore[assignment]
        logger.info("OTel: ConsoleSpanExporter (dev mode — set OTEL_EXPORTER_OTLP_ENDPOINT to export)")

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # Instrument FastAPI HTTP layer.
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor().instrument()
        logger.info("OTel: FastAPIInstrumentor registered")
    except ImportError:
        logger.warning("opentelemetry-instrumentation-fastapi not installed — HTTP spans disabled.")

    # Instrument SQLAlchemy for DB spans.
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        SQLAlchemyInstrumentor().instrument()
        logger.info("OTel: SQLAlchemyInstrumentor registered")
    except ImportError:
        logger.warning("opentelemetry-instrumentation-sqlalchemy not installed — DB spans disabled.")

    logger.info("OTel: tracing configured (service=%s)", service_name)
