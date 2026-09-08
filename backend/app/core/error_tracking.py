"""Sentry-compatible error tracking integration.

Initialises the Sentry SDK when a DSN is provided; degrades gracefully when
the SDK is not installed or the DSN is empty so development stays friction-free.

Usage (called once at startup in main.py):
    from app.core.error_tracking import configure_sentry
    configure_sentry(dsn=settings.SENTRY_DSN,
                     environment=settings.ENVIRONMENT,
                     release="1.0.0")

Per-request user context (called from RequestIDMiddleware after auth):
    from app.core.error_tracking import set_user_context
    set_user_context(user_id="uuid-here", email="user@example.com")
"""

from __future__ import annotations

import logging

logger = logging.getLogger("whetzy.sentry")


def configure_sentry(
    dsn: str,
    environment: str = "development",
    release: str | None = None,
    traces_sample_rate: float | None = None,
) -> None:
    """Initialise Sentry SDK.

    If *dsn* is empty or falsy, or the SDK is not installed, this is a no-op.
    The *traces_sample_rate* defaults to 0.0 in dev/test and 0.1 otherwise.
    """
    if not dsn:
        logger.debug("Sentry DSN not set; error tracking disabled")
        return

    try:
        import sentry_sdk  # noqa: PLC0415

        if traces_sample_rate is None:
            traces_sample_rate = 0.0 if environment in ("development", "test") else 0.1

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release,
            traces_sample_rate=traces_sample_rate,
            send_default_pii=False,
        )
        logger.info(
            "Sentry initialised (env=%s, traces_sample_rate=%s)",
            environment,
            traces_sample_rate,
        )
    except Exception:  # noqa: BLE001
        logger.warning("Sentry initialisation failed; error tracking disabled", exc_info=True)


def set_user_context(user_id: str, email: str | None = None) -> None:
    """Attach user information to the current Sentry scope.

    Safe to call even when Sentry is not configured — all failures are silently
    swallowed so this never affects request handling.
    """
    if not user_id or user_id == "-":
        return

    try:
        import sentry_sdk  # noqa: PLC0415

        sentry_sdk.set_user({"id": user_id, **({"email": email} if email else {})})
    except Exception:  # noqa: BLE001
        pass
