"""HMAC-SHA256 admin authentication (22.15 phase 3).

Replaces the plaintext ``X-Admin-Key`` comparison with HMAC-signed requests.
The caller sends three headers:

    X-Admin-Timestamp: <unix-epoch-seconds>
    X-Admin-Nonce: <random-hex-16+>
    X-Admin-Signature: <hex(HMAC-SHA256(key, timestamp.nonce.method.path))>

The server validates:
  1. Timestamp is within ±5 min of server time (replay window).
  2. Nonce has not been seen in the last 10 min (replay prevention).
  3. HMAC matches.

In non-production environments the old ``X-Admin-Key: <plaintext>`` header
is still accepted for local development and CI, but production requires
HMAC.  Both paths share the same ``CONTENT_ADMIN_KEY`` secret.
"""
from __future__ import annotations

import hashlib
import hmac
import time

from fastapi import Header, HTTPException, Request, status

from app.core.config import settings

_CLOCK_SKEW_SECONDS = 300
_NONCE_WINDOW_SECONDS = 600
_seen_nonces: dict[str, float] = {}


def _prune_nonces() -> None:
    cutoff = time.monotonic() - _NONCE_WINDOW_SECONDS
    expired = [k for k, t in _seen_nonces.items() if t < cutoff]
    for k in expired:
        del _seen_nonces[k]


def _verify_hmac(
    request: Request,
    timestamp_str: str,
    nonce: str,
    signature: str,
) -> None:
    key = settings.CONTENT_ADMIN_KEY
    if not key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    try:
        ts = int(timestamp_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid timestamp",
        )

    now = int(time.time())
    if abs(now - ts) > _CLOCK_SKEW_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Timestamp out of range",
        )

    if len(nonce) < 16:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nonce too short",
        )

    _prune_nonces()
    if nonce in _seen_nonces:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nonce already used",
        )
    _seen_nonces[nonce] = time.monotonic()

    message = f"{timestamp_str}.{nonce}.{request.method}.{request.url.path}"
    expected = hmac.new(
        key.encode(), message.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )


async def require_admin(
    request: Request,
    x_admin_key: str = Header(default=""),
    x_admin_timestamp: str = Header(default=""),
    x_admin_nonce: str = Header(default=""),
    x_admin_signature: str = Header(default=""),
) -> None:
    """FastAPI dependency: validates admin authentication.

    Accepts HMAC-signed requests (preferred) or plain key (dev/CI only).
    """
    key = settings.CONTENT_ADMIN_KEY
    if not key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    if x_admin_signature:
        _verify_hmac(request, x_admin_timestamp, x_admin_nonce, x_admin_signature)
        return

    if x_admin_key:
        if settings.ENVIRONMENT == "production":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="HMAC signature required in production",
            )
        if hmac.compare_digest(x_admin_key, key):
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
