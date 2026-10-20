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
    """Frontend and backend are on different registrable domains in
    production *as long as the API answers at a Railway/`*.pages.dev` host*.
    `SameSite=None` requires `Secure`; browsers reject it otherwise, so it is
    never applied over plain HTTP local dev.

    Safari login (17.6/orden S1 punto 5): Safari's ITP blocks third-party
    cookies more aggressively than Chrome/Firefox even with `SameSite=None` —
    that is the real fix the owner needs, not this function. Once the API is
    reachable under the frontend's own registrable domain (an `api.<domain>`
    DNS record pointed at Railway — the owner's part) *and* `COOKIE_DOMAIN`
    is set to the shared parent (e.g. `.whetzy.com`), the two origins are
    first-party to each other again: the cookie can go back to `SameSite=Lax`
    and Safari stops treating it as third-party. `COOKIE_DOMAIN` already
    existed for `_cookie_kwargs`; this only teaches `_cross_site` to notice it
    was set. Nothing changes in production until that env var is set, which
    is the owner's half of this fix.
    """
    return settings.ENVIRONMENT == "production" and not settings.COOKIE_DOMAIN


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


MFA_COOKIE = "whetzy_mfa"


def set_mfa_cookie(response: Response, mfa_token: str) -> None:
    """Segundo paso del login con 2FA cuando se llega por OAuth: el token va en
    una cookie HttpOnly de 5 minutos y no en la URL de la redirección."""
    secure, samesite = _cookie_policy()
    response.set_cookie(
        key=MFA_COOKIE, value=mfa_token, max_age=5 * 60, **_cookie_kwargs(secure, samesite),  # type: ignore[arg-type]
    )


def clear_mfa_cookie(response: Response) -> None:
    opts: dict[str, object] = {"path": "/"}
    if settings.COOKIE_DOMAIN:
        opts["domain"] = settings.COOKIE_DOMAIN
    response.delete_cookie(key=MFA_COOKIE, **opts)  # type: ignore[arg-type]


OAUTH_STATE_COOKIE = "whetzy_oauth_state"


def _oauth_policy(cross_site_post: bool) -> tuple[bool, SameSite]:
    """Apple vuelve con un `POST` desde appleid.apple.com (`form_post`): con
    `SameSite=Lax` el navegador no manda la cookie en esa petición y el
    callback no podría comparar el `state`. Para ese proveedor va `None` (que
    exige `Secure`)."""
    if cross_site_post:
        return True, "none"
    return _cookie_policy()


def set_oauth_state_cookie(
    response: Response, state: str, max_age_seconds: int, *, cross_site_post: bool = False
) -> None:
    """41.14: el `state` de OAuth solo vivía en la base de datos — un `state`
    válido y sin consumir se aceptaba desde cualquier navegador, no solo el
    que lo pidió. Esta cookie HttpOnly lleva el mismo valor; `/callback` la
    compara contra el `state` de la query antes de aceptarlo."""
    secure, samesite = _oauth_policy(cross_site_post)
    response.set_cookie(
        key=OAUTH_STATE_COOKIE,
        value=state,
        max_age=max_age_seconds,
        **_cookie_kwargs(secure, samesite),  # type: ignore[arg-type]
    )


OAUTH_LANG_COOKIE = "whetzy_oauth_lang"


def set_oauth_lang_cookie(
    response: Response, lang: str, max_age_seconds: int, *, cross_site_post: bool = False
) -> None:
    """45.1 (ADR-66 E1): el idioma de la pantalla desde la que se pulsó «Continuar
    con…». Viaja junto al `state` y solo se usa si el callback crea la cuenta."""
    secure, samesite = _oauth_policy(cross_site_post)
    response.set_cookie(
        key=OAUTH_LANG_COOKIE,
        value=lang,
        max_age=max_age_seconds,
        **_cookie_kwargs(secure, samesite),  # type: ignore[arg-type]
    )


def clear_oauth_state_cookie(response: Response) -> None:
    """Borra la cookie del `state` y la del idioma (45.1): las dos son del mismo flujo."""
    opts: dict[str, object] = {"path": "/"}
    if settings.COOKIE_DOMAIN:
        opts["domain"] = settings.COOKIE_DOMAIN
    response.delete_cookie(key=OAUTH_STATE_COOKIE, **opts)  # type: ignore[arg-type]
    response.delete_cookie(key=OAUTH_LANG_COOKIE, **opts)  # type: ignore[arg-type]
