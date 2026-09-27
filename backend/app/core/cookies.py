"""HttpOnly cookie helpers for JWT auth tokens (22.15).

Tokens are set as HttpOnly + Secure + SameSite cookies, invisible to
JavaScript.  A companion `whetzy_logged_in=1` cookie (NOT HttpOnly) lets the
frontend detect auth state without a server call *when frontend and backend
share a site* — they don't in production (`whetzy.com` on Cloudflare Pages,
`api-production-9751.up.railway.app` on Railway are different registrable
domains), so `SameSite=Lax` there silently dropped every cookie from the
cross-site `fetch()` calls in `services/api.ts`, and the `whetzy_logged_in`
cookie is host-only to the API domain, never visible to `document.cookie` on
`whetzy.com` regardless of SameSite. That is why a real login redirected
back to the landing page (30.9): `isAuthenticated()` read a cookie that
could never be there. `SameSite=None` (30.9) fixes the cookies actually
reaching `/auth/me`; the frontend fix (App.tsx) stops trusting the
`whetzy_logged_in` cookie for the initial decision and asks the server
instead.

During migration, `get_current_user` reads cookies OR the Authorization
header — whichever is present — so old clients keep working.
"""

from __future__ import annotations

from typing import Literal

from fastapi import Response

from app.core.config import settings

ACCESS_COOKIE = "whetzy_access"
REFRESH_COOKIE = "whetzy_refresh"
LOGGED_IN_COOKIE = "whetzy_logged_in"

SameSite = Literal["lax", "none"]


def _cross_site() -> bool:
    """Frontend and backend are on different registrable domains only in
    production today (ADR-45 previews aside, which don't set auth cookies).
    `SameSite=None` requires `Secure`; browsers reject it otherwise, so it is
    never applied over plain HTTP local dev."""
    return settings.ENVIRONMENT == "production"


def _cookie_policy() -> tuple[bool, SameSite]:
    cross_site = _cross_site()
    secure: bool = settings.COOKIE_SECURE or cross_site
    samesite: SameSite = "none" if cross_site else "lax"
    return secure, samesite


def _cookie_kwargs(secure: bool, samesite: SameSite) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "httponly": True,
        "secure": secure,
        "samesite": samesite,
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
    secure, samesite = _cookie_policy()
    base = _cookie_kwargs(secure, samesite)

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
        secure=secure,
        samesite=samesite,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    opts: dict[str, object] = {"path": "/"}
    if settings.COOKIE_DOMAIN:
        opts["domain"] = settings.COOKIE_DOMAIN
    response.delete_cookie(key=ACCESS_COOKIE, **opts)  # type: ignore[arg-type]
    response.delete_cookie(key=REFRESH_COOKIE, **opts)  # type: ignore[arg-type]
    response.delete_cookie(key=LOGGED_IN_COOKIE, **opts)  # type: ignore[arg-type]
