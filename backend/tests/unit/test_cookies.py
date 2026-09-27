"""Cookie SameSite/Secure policy (30.9).

`whetzy.com` (Cloudflare Pages) and `api-production-9751.up.railway.app`
(Railway) are different registrable domains in production, so `SameSite=Lax`
cookies never reached the cross-site `fetch()` calls in `services/api.ts`:
a real login worked (the `POST /auth/login` returned 200) but the browser
dropped the cookies on the next request, and the frontend's own auth check
(a JS-readable cookie that is host-only to the API domain and therefore
never visible on `whetzy.com` regardless of SameSite) sent the user back to
the landing page. `SameSite=None` only applies in production, where the
domains actually differ and `Secure` is guaranteed; local dev (same site,
often plain HTTP) keeps `SameSite=Lax`.
"""
from __future__ import annotations

import pytest

from app.core.config import settings


@pytest.fixture(autouse=True)
def _reset_environment(monkeypatch):
    # Cada test fija su propio ENVIRONMENT; nada debe quedar en production.
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")


def test_cookies_are_lax_outside_production():
    from app.core.cookies import _cookie_policy

    _secure, samesite = _cookie_policy()
    assert samesite == "lax"


def test_cookies_are_samesite_none_in_production(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    from app.core.cookies import _cookie_policy

    secure, samesite = _cookie_policy()
    assert samesite == "none"
    # SameSite=None que el navegador acepte exige Secure; sin esto, Chrome y
    # Firefox descartan la cookie entera en vez de degradarla a Lax.
    assert secure is True


def test_logged_in_cookie_matches_the_auth_cookies_policy(monkeypatch):
    """El companion cookie (LOGGED_IN_COOKIE) llevaba `samesite='lax'` fijo a
    mano: en producción quedaba desalineado del resto si alguna vez alguien
    tocaba solo `_cookie_kwargs()`. Ahora los tres cookies del login
    comparten SameSite/Secure — se comprueba en la respuesta real."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    from fastapi import Response

    from app.core.cookies import LOGGED_IN_COOKIE, set_auth_cookies

    response = Response()
    set_auth_cookies(response, "access-token", "refresh-token")
    cookies = [v.decode() for k, v in response.raw_headers if k == b"set-cookie"]
    logged_in = next(c for c in cookies if c.startswith(f"{LOGGED_IN_COOKIE}="))
    assert "SameSite=none" in logged_in
    assert "Secure" in logged_in


def test_cookie_domain_still_applied_when_set(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "COOKIE_DOMAIN", ".whetzy.com")
    from app.core.cookies import _cookie_kwargs, _cookie_policy

    secure, samesite = _cookie_policy()
    assert _cookie_kwargs(secure, samesite)["domain"] == ".whetzy.com"
