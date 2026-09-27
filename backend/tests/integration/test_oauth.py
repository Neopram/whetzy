"""Integration tests for OAuth 2.0 social login endpoints.

Uses the `test` provider (only available outside production) to verify the
complete OAuth flow without real GitHub/Google credentials.
"""
from __future__ import annotations

import itertools

from app.core.cookies import ACCESS_COOKIE, REFRESH_COOKIE
from app.core.security import verify_token

OAUTH = "/api/v1/auth/oauth"

_ip_counter = itertools.count(200)


def _h() -> dict:
    n = next(_ip_counter)
    return {"X-Forwarded-For": f"192.0.3.{n % 255 or 255}"}


# ── providers ──────────────────────────────────────────────────────────────────


async def test_providers_lists_only_the_configured_ones(client, monkeypatch):
    from app.core.config import settings

    # Entorno de test: ningún client_id → lista vacía, no 503 ni botones.
    r = await client.get(f"{OAUTH}/providers", headers=_h())
    assert r.status_code == 200
    assert r.json() == {"providers": []}

    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "google-client-id")
    r = await client.get(f"{OAUTH}/providers", headers=_h())
    assert r.json() == {"providers": ["google"]}


# ── start ──────────────────────────────────────────────────────────────────────


async def test_start_unknown_provider_returns_404(client):
    r = await client.get(f"{OAUTH}/notareal/start", headers=_h(), follow_redirects=False)
    assert r.status_code == 404


async def test_start_github_unconfigured_returns_503(client):
    # In the test environment GITHUB_CLIENT_ID is "" → 503
    r = await client.get(f"{OAUTH}/github/start", headers=_h(), follow_redirects=False)
    assert r.status_code == 503


async def test_start_test_provider_redirects_to_callback(client):
    r = await client.get(f"{OAUTH}/test/start", headers=_h(), follow_redirects=False)
    # Should redirect to /test/callback?code=test-code&state=...
    assert r.status_code == 302
    location = r.headers["location"]
    assert "/test/callback" in location
    assert "code=test-code" in location
    assert "state=" in location


# ── callback ───────────────────────────────────────────────────────────────────


async def test_callback_invalid_state_returns_400(client):
    r = await client.get(
        f"{OAUTH}/test/callback",
        params={"code": "test-code", "state": "invalid-state-xyz"},
        headers=_h(),
        follow_redirects=False,
    )
    assert r.status_code == 400


async def test_callback_wrong_provider_returns_400(client):
    # Store a state for 'test', then try to use it for 'github'
    start = await client.get(f"{OAUTH}/test/start", headers=_h(), follow_redirects=False)
    assert start.status_code == 302
    location = start.headers["location"]
    state = dict(p.split("=") for p in location.split("?")[1].split("&"))["state"]

    r = await client.get(
        f"{OAUTH}/github/callback",
        params={"code": "test-code", "state": state},
        headers=_h(),
        follow_redirects=False,
    )
    assert r.status_code in (400, 404)


def _session_user(response) -> str:
    """User id (`sub`) of the access cookie a callback response sets."""
    for c in response.headers.get_list("set-cookie"):
        if c.startswith(f"{ACCESS_COOKIE}="):
            return verify_token(c.split(";", 1)[0].split("=", 1)[1], expected_type="access").sub
    raise AssertionError("no access cookie")


async def test_callback_test_provider_creates_new_user(client):
    # Start → get state from redirect
    start = await client.get(f"{OAUTH}/test/start", headers=_h(), follow_redirects=False)
    assert start.status_code == 302
    location = start.headers["location"]
    qs = dict(p.split("=", 1) for p in location.split("?")[1].split("&"))

    # Callback → redirects to FRONTEND_BASE_URL with the session in HttpOnly cookies.
    # The JWT pair used to travel as ?oauth_token=&oauth_refresh= (browser history,
    # Referer, proxy logs); since the cookie migration it must not appear in the URL.
    r = await client.get(
        f"{OAUTH}/test/callback",
        params={"code": qs["code"], "state": qs["state"]},
        headers=_h(),
        follow_redirects=False,
    )
    assert r.status_code == 302
    final = r.headers["location"]
    assert "oauth_token" not in final and "oauth_refresh" not in final
    cookies = r.headers.get_list("set-cookie")
    assert any(c.startswith(f"{ACCESS_COOKIE}=") and "HttpOnly" in c for c in cookies)
    assert any(c.startswith(f"{REFRESH_COOKIE}=") and "HttpOnly" in c for c in cookies)


async def test_callback_test_provider_idempotent(client):
    # Two separate start+callback flows with the same effective email → same user
    def _do_flow(code: str):
        return code  # We'll run sequentially below

    h = _h()

    # Flow 1
    s1 = await client.get(f"{OAUTH}/test/start", headers=h, follow_redirects=False)
    l1 = s1.headers["location"]
    q1 = dict(p.split("=", 1) for p in l1.split("?")[1].split("&"))
    r1 = await client.get(
        f"{OAUTH}/test/callback",
        params={"code": "same-code", "state": q1["state"]},
        headers=h,
        follow_redirects=False,
    )
    assert r1.status_code == 302

    # Flow 2 (new state, same code → same email → existing user linked)
    s2 = await client.get(f"{OAUTH}/test/start", headers=h, follow_redirects=False)
    l2 = s2.headers["location"]
    q2 = dict(p.split("=", 1) for p in l2.split("?")[1].split("&"))
    r2 = await client.get(
        f"{OAUTH}/test/callback",
        params={"code": "same-code", "state": q2["state"]},
        headers=h,
        follow_redirects=False,
    )
    assert r2.status_code == 302
    assert "oauth_token" not in r2.headers["location"]
    # Same email → same account: both sessions belong to one user id.
    assert _session_user(r1) == _session_user(r2)


async def test_oauth_user_cannot_login_with_password(client):
    # Complete OAuth flow to create user
    h = _h()
    start = await client.get(f"{OAUTH}/test/start", headers=h, follow_redirects=False)
    location = start.headers["location"]
    qs = dict(p.split("=", 1) for p in location.split("?")[1].split("&"))
    cb = await client.get(
        f"{OAUTH}/test/callback",
        params={"code": "pw-test", "state": qs["state"]},
        headers=h,
        follow_redirects=False,
    )
    assert cb.status_code == 302

    # Attempt password login — should fail (no password set)
    r = await client.post(
        "/api/v1/auth/login",
        data={"username": "oauth-pw-test@example.com", "password": "anything"},
        headers=_h(),
    )
    assert r.status_code == 401
