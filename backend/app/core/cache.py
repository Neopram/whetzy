"""Cache control headers for response optimization.

Series 22.6: Cache static content (glossary, tracks) for 5 minutes.
Private data (user progress, auth) has no-cache headers.
"""

from __future__ import annotations

from fastapi.responses import JSONResponse


def public_cache_response(
    data: dict,
    max_age: int = 300,  # 5 minutes default
    status_code: int = 200,
) -> JSONResponse:
    """Return a JSON response with public cache headers."""
    response = JSONResponse(data, status_code=status_code)
    response.headers["Cache-Control"] = f"public, max-age={max_age}"
    return response


def private_cache_response(
    data: dict,
    max_age: int = 60,  # 1 minute default
    status_code: int = 200,
) -> JSONResponse:
    """Return a JSON response with private cache headers (browser-only, user-specific)."""
    response = JSONResponse(data, status_code=status_code)
    response.headers["Cache-Control"] = f"private, max-age={max_age}"
    return response


def no_cache_response(
    data: dict,
    status_code: int = 200,
) -> JSONResponse:
    """Return a JSON response with no-cache headers (for auth, sensitive data)."""
    response = JSONResponse(data, status_code=status_code)
    response.headers["Cache-Control"] = "no-store"
    return response


def set_cache_header(response: JSONResponse, max_age: int, is_private: bool = False) -> None:
    """Set Cache-Control header on an existing response."""
    if max_age <= 0:
        response.headers["Cache-Control"] = "no-store"
    else:
        visibility = "private" if is_private else "public"
        response.headers["Cache-Control"] = f"{visibility}, max-age={max_age}"
