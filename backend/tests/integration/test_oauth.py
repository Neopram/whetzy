"""Integration tests for OAuth 2.0 social login endpoints.

Uses the `test` provider (only available outside production) to verify the
complete OAuth flow without real GitHub/Google credentials.
"""
from __future__ import annotations

import itertools
import urllib.parse

from app.core.cookies import ACCESS_COOKIE, OAUTH_STATE_COOKIE, REFRESH_COOKIE
from app.core.security import verify_token

OAUTH = "/api/v1/auth/oauth"

_ip_counter = itertools.count(200)


def _h() -> dict:
    n = next(_ip_counter)
    return {"X-Forwarded-For": f"192.0.3.{n % 255 or 255}"}


def _state_cookie_header(start_response) -> dict:
    """41.14: la cookie del `state` va `Secure`, y el cliente de test habla
    por `http://test` -- httpx (bien) nunca manda una cookie `Secure` por una
    conexión sin TLS, igual que no lo haría un navegador real. Sin esto el
    callback vería la cookie ausente en cualquier test, incluido uno con un
    `state` legítimo. La extrae a mano del `Set-Cookie`, igual que ya hace
    este fichero con el `state` de la query."""
    for c in start_response.headers.get_list("set-cookie"):
        if c.startswith(f"{OAUTH_STATE_COOKIE}="):
            return {"Cookie": c.split(";", 1)[0]}
    raise AssertionError("no oauth state cookie in /start response")


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


async def test_start_github_unconfigured_returns_404(client):
    # In the test environment GITHUB_CLIENT_ID is "". A provider this server has
    # no credentials for doesn't exist here: 404, like an unknown provider. It was
    # 503, which Sentry reports as an error: an old link or a bot hitting
    # /github/start paged the team (2026-10-17).
    r = await client.get(f"{OAUTH}/github/start", headers=_h(), follow_redirects=False)
    assert r.status_code == 404
    assert "not configured" in r.json()["detail"]


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
        headers={**_h(), **_state_cookie_header(start)},
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
        headers={**_h(), **_state_cookie_header(start)},
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
        headers={**h, **_state_cookie_header(s1)},
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
        headers={**h, **_state_cookie_header(s2)},
        follow_redirects=False,
    )
    assert r2.status_code == 302
    assert "oauth_token" not in r2.headers["location"]
    # Same email → same account: both sessions belong to one user id.
    assert _session_user(r1) == _session_user(r2)


async def test_callback_refuses_to_link_an_unverified_existing_email(client):
    """El email del proveedor está verificado (GitHub filtra `verified`,
    Google `email_verified`); el de una cuenta de Whetzy registrada por
    contraseña, no -- quien se registra nunca tiene por qué haber
    confirmado que es el dueño real de ese email. Sin este chequeo, quien
    se registrara antes con el email de otra persona recibía el inicio de
    sesión real de esa persona en cuanto usara OAuth con el mismo email."""
    code = "squatted"
    email = f"oauth-{code}@example.com"
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": "squatter1",
            "password": "Str0ng!Pass",
            "display_name": "Squatter",
            "language": "es",
            "age_confirmed": True,
        },
        headers=_h(),
    )
    assert register.status_code == 201, register.text

    start = await client.get(f"{OAUTH}/test/start", headers=_h(), follow_redirects=False)
    qs = dict(p.split("=", 1) for p in start.headers["location"].split("?")[1].split("&"))
    cb = await client.get(
        f"{OAUTH}/test/callback",
        params={"code": code, "state": qs["state"]},
        headers={**_h(), **_state_cookie_header(start)},
        follow_redirects=False,
    )
    assert cb.status_code == 302
    assert "oauth_error=email_unverified" in cb.headers["location"]
    assert not any(
        c.startswith(f"{ACCESS_COOKIE}=") for c in cb.headers.get_list("set-cookie")
    )


# ── 41.14: state atado a cookie + PKCE ─────────────────────────────────────────


async def test_callback_with_a_valid_state_but_no_cookie_returns_400(client):
    """El `state` existe en la base y no ha expirado -- pero sin la cookie
    que puso /start, no es el mismo navegador que lo pidió. Antes de esto,
    cualquier navegador con un `state` válido y sin consumir entraba."""
    start = await client.get(f"{OAUTH}/test/start", headers=_h(), follow_redirects=False)
    qs = dict(p.split("=", 1) for p in start.headers["location"].split("?")[1].split("&"))

    r = await client.get(
        f"{OAUTH}/test/callback",
        params={"code": qs["code"], "state": qs["state"]},
        headers=_h(),  # sin la cookie de _state_cookie_header
        follow_redirects=False,
    )
    assert r.status_code == 400


async def test_callback_with_a_mismatched_state_cookie_returns_400(client):
    """La cookie existe, pero no coincide con el `state` de la query -- el
    escenario del CSRF de login: el atacante completa su propio flujo OAuth
    (su cookie, su `state`) y engaña a la víctima para que visite ese
    callback; la víctima no tiene esa cookie, o tiene la suya propia, que
    tampoco coincide con el `state` del atacante."""
    start = await client.get(f"{OAUTH}/test/start", headers=_h(), follow_redirects=False)
    qs = dict(p.split("=", 1) for p in start.headers["location"].split("?")[1].split("&"))
    cookie = _state_cookie_header(start)["Cookie"]
    mismatched_cookie = cookie.rsplit("=", 1)[0] + "=not-the-right-state"

    r = await client.get(
        f"{OAUTH}/test/callback",
        params={"code": qs["code"], "state": qs["state"]},
        headers={**_h(), "Cookie": mismatched_cookie},
        follow_redirects=False,
    )
    assert r.status_code == 400


async def test_start_stores_a_code_verifier_and_sends_its_s256_challenge(
    client, db_session, monkeypatch
):
    """PKCE (RFC 7636): /start genera un `code_verifier`, lo guarda en
    `oauth_states` (lo necesita /callback para el intercambio del código) y
    manda `code_challenge`/`code_challenge_method=S256` -- su derivado -- en
    la URL de autorización, nunca el propio verifier."""
    import base64
    import hashlib

    from app.core.config import settings
    from app.models.oauth import OAuthState

    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "google-client-id")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "google-client-secret")

    start = await client.get(f"{OAUTH}/google/start", headers=_h(), follow_redirects=False)
    assert start.status_code == 302
    location = start.headers["location"]
    qs = dict(p.split("=") for p in location.split("?", 1)[1].split("&"))

    assert qs["code_challenge_method"] == "S256"
    assert "code_verifier" not in location

    from sqlalchemy import select

    oauth_state = (
        await db_session.execute(select(OAuthState).where(OAuthState.state == qs["state"]))
    ).scalar_one()
    assert oauth_state.code_verifier is not None

    expected_challenge = (
        base64.urlsafe_b64encode(
            hashlib.sha256(oauth_state.code_verifier.encode("ascii")).digest()
        )
        .decode("ascii")
        .rstrip("=")
    )
    assert urllib.parse.unquote(qs["code_challenge"]) == expected_challenge


async def test_exchange_code_sends_the_stored_code_verifier(monkeypatch):
    """El `code_verifier` guardado en /start viaja en el POST del intercambio
    del código por el token -- sin esto, PKCE se generaba pero nunca se
    usaba."""
    from app.api.v1.endpoints.oauth import _exchange_code

    captured: dict = {}

    class _CapturingResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"access_token": "tok"}

    class _CapturingClient:
        async def post(self, url: str, data: dict, headers: dict) -> _CapturingResponse:
            captured["data"] = data
            return _CapturingResponse()

    await _exchange_code(_CapturingClient(), "github", "a-code", "a-verifier")
    assert captured["data"]["code_verifier"] == "a-verifier"


async def test_exchange_code_omits_code_verifier_when_none(monkeypatch):
    """Una fila de `oauth_states` sin `code_verifier` (anterior a esta
    migración, o un intento que no llevaba PKCE) no manda el campo -- el
    proveedor no lo exige si /start no mandó `code_challenge`."""
    from app.api.v1.endpoints.oauth import _exchange_code

    captured: dict = {}

    class _CapturingResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"access_token": "tok"}

    class _CapturingClient:
        async def post(self, url: str, data: dict, headers: dict) -> _CapturingResponse:
            captured["data"] = data
            return _CapturingResponse()

    await _exchange_code(_CapturingClient(), "github", "a-code", None)
    assert "code_verifier" not in captured["data"]


async def test_oauth_user_cannot_login_with_password(client):
    # Complete OAuth flow to create user
    h = _h()
    start = await client.get(f"{OAUTH}/test/start", headers=h, follow_redirects=False)
    location = start.headers["location"]
    qs = dict(p.split("=", 1) for p in location.split("?")[1].split("&"))
    cb = await client.get(
        f"{OAUTH}/test/callback",
        params={"code": "pw-test", "state": qs["state"]},
        headers={**h, **_state_cookie_header(start)},
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
