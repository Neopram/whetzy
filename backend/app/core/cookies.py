"""HttpOnly cookie helpers for JWT auth tokens (22.15).

Tokens are set as HttpOnly + Secure + SameSite=Lax cookies, invisible
to JavaScript.  A companion `whetzy_logged_in=1` cookie (NOT HttpOnly)
lets the frontend detect auth state without a server call.

During migration, `get_current_user` reads cookies OR the Authorization
header — whichever is present — so old clients keep working.
"""

from __future__ import annotations

from fastapi import Response

from app.core.config import settings

ACCESS_COOKIE = "whetzy_access"
REFRESH_COOKIE = "whetzy_refresh"
LOGGED_IN_COOKIE = "whetzy_logged_in"


def _cookie_kwargs() -> dict[str, object]:
    kwargs: dict[str, object] = {
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": "lax",
        "path": "/",
    }
    if settings.COOKIE_DOMAIN:
        kwargs["domain"] = settings.COOKIE_DOMAIN
    return kwargs


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
) -> None:
    base = _cookie_kwargs()

    response.set_cookie(
        key=ACCESS_COOKIE,
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        **base,  # type: ignore[arg-type]
    )
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        **base,  # type: ignore[arg-type]
    )
    response.set_cookie(
        key=LOGGED_IN_COOKIE,
        value="1",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        httponly=False,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    opts: dict[str, object] = {"path": "/"}
    if settings.COOKIE_DOMAIN:
        opts["domain"] = settings.COOKIE_DOMAIN
    response.delete_cookie(key=ACCESS_COOKIE, **opts)  # type: ignore[arg-type]
    response.delete_cookie(key=REFRESH_COOKIE, **opts)  # type: ignore[arg-type]
    response.delete_cookie(key=LOGGED_IN_COOKIE, **opts)  # type: ignore[arg-type]
