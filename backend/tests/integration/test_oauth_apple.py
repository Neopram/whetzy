"""Sign in with Apple (19.2): preparado, NO verificado contra Apple (H.2).

Sin el Apple Developer Program no hay Services ID ni clave, así que aquí todo
se firma con claves de prueba generadas en el test: una EC P-256 para el
`client_secret` (lo que haría la .p8) y una RSA para el `id_token` (lo que
haría Apple), publicada como JWKS en un `/auth/keys` simulado con
`httpx.MockTransport`. Prueba el contrato de la documentación de Apple
(`app/services/apple_signin.py`), no que Apple lo acepte.
"""
from __future__ import annotations

import itertools
import time
import urllib.parse

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from app.core.cookies import ACCESS_COOKIE, OAUTH_STATE_COOKIE
from app.services import apple_signin

OAUTH = "/api/v1/auth/oauth"
CLIENT_ID = "app.whetzy.signin"
_ip = itertools.count(10)


def _h() -> dict[str, str]:
    return {"X-Forwarded-For": f"192.0.9.{next(_ip) % 250 + 1}"}


def _pem(key: ec.EllipticCurvePrivateKey | rsa.RSAPrivateKey) -> str:
    return key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    ).decode()


_EC = ec.generate_private_key(ec.SECP256R1())
_APPLE = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_OTRA = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _jwks(key: rsa.RSAPrivateKey, kid: str = "AK1") -> dict:
    k = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
    k.update(kid=kid, use="sig", alg="RS256")
    return {"keys": [k]}


def _id_token(key: rsa.RSAPrivateKey = _APPLE, **claims: object) -> str:
    base: dict[str, object] = {
        "iss": apple_signin.ISSUER,
        "aud": CLIENT_ID,
        "sub": "000123.apple-user",
        "email": "ana@privaterelay.appleid.com",
        "email_verified": "true",
        "is_private_email": "true",
        "exp": int(time.time()) + 600,
        "iat": int(time.time()),
    }
    base.update(claims)
    return jwt.encode({k: v for k, v in base.items() if v is not None}, _pem(key), algorithm="RS256", headers={"kid": "AK1"})


@pytest.fixture
def apple(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "APPLE_CLIENT_ID", CLIENT_ID)
    monkeypatch.setattr(settings, "APPLE_TEAM_ID", "TEAM123456")
    monkeypatch.setattr(settings, "APPLE_KEY_ID", "KEY1234567")
    # Como la guarda Railway: en una línea, con «\n» escritos.
    monkeypatch.setattr(settings, "APPLE_PRIVATE_KEY", _pem(_EC).replace("\n", "\\n"))
    return settings


# ── configuración y client_secret ────────────────────────────────────────────


async def test_sin_las_cuatro_variables_no_hay_boton(client, monkeypatch, apple):
    r = await client.get(f"{OAUTH}/providers", headers=_h())
    assert "apple" in r.json()["providers"]
    monkeypatch.setattr(apple, "APPLE_KEY_ID", "")
    r = await client.get(f"{OAUTH}/providers", headers=_h())
    assert "apple" not in r.json()["providers"]
    r = await client.get(f"{OAUTH}/apple/start", headers=_h(), follow_redirects=False)
    assert r.status_code == 404


def test_client_secret_es_el_jwt_que_pide_apple(apple):
    now = int(time.time())
    token = apple_signin.client_secret(now)
    assert jwt.get_unverified_header(token)["alg"] == "ES256"
    assert jwt.get_unverified_header(token)["kid"] == "KEY1234567"
    pub = _EC.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    claims = jwt.decode(token, pub, algorithms=["ES256"], audience=apple_signin.ISSUER)
    assert claims["iss"] == "TEAM123456"
    assert claims["sub"] == CLIENT_ID
    assert claims["iat"] == now
    assert 0 < claims["exp"] - now <= 15_777_000


# ── /start ───────────────────────────────────────────────────────────────────


async def test_start_pide_form_post_con_nonce_y_cookie_samesite_none(client, db_session, apple):
    from sqlalchemy import select

    from app.models.oauth import OAuthState

    r = await client.get(f"{OAUTH}/apple/start?lang=en", headers=_h(), follow_redirects=False)
    assert r.status_code == 302
    url = urllib.parse.urlsplit(r.headers["location"])
    assert f"{url.scheme}://{url.netloc}{url.path}" == apple_signin.AUTH_URL
    assert "scope=name%20email" in url.query
    qs = dict(urllib.parse.parse_qsl(url.query))
    assert qs["response_mode"] == "form_post"
    assert qs["response_type"] == "code"
    assert qs["client_id"] == CLIENT_ID
    assert "code_challenge" not in qs

    fila = (await db_session.execute(select(OAuthState).where(OAuthState.state == qs["state"]))).scalar_one()
    assert qs["nonce"] == apple_signin.nonce_for(fila.code_verifier)

    cookie = next(c for c in r.headers.get_list("set-cookie") if c.startswith(f"{OAUTH_STATE_COOKIE}="))
    assert "samesite=none" in cookie.lower() and "secure" in cookie.lower()


# ── id_token ─────────────────────────────────────────────────────────────────


def test_id_token_valido(apple):
    claims = apple_signin.verify_id_token(_id_token(nonce="n1"), _jwks(_APPLE), "n1")
    assert apple_signin.verified_email(claims) == "ana@privaterelay.appleid.com"


@pytest.mark.parametrize(
    "token",
    [
        pytest.param(lambda: _id_token(key=_OTRA, nonce="n1"), id="firmado-por-otra-clave"),
        pytest.param(lambda: _id_token(aud="otra.app", nonce="n1"), id="otra-audiencia"),
        pytest.param(lambda: _id_token(iss="https://evil.example", nonce="n1"), id="otro-emisor"),
        pytest.param(lambda: _id_token(exp=int(time.time()) - 60, nonce="n1"), id="caducado"),
        pytest.param(lambda: _id_token(nonce="otro"), id="otro-nonce"),
        pytest.param(lambda: _id_token(nonce=None), id="sin-nonce"),
    ],
)
def test_id_token_invalido(apple, token):
    with pytest.raises(apple_signin.InvalidAppleToken):
        apple_signin.verify_id_token(token(), _jwks(_APPLE), "n1")


def test_email_sin_verificar_no_vale(apple):
    claims = apple_signin.verify_id_token(_id_token(email_verified="false", nonce="n1"), _jwks(_APPLE), "n1")
    assert apple_signin.verified_email(claims) is None


# ── callback (form_post) ─────────────────────────────────────────────────────


def _apple_falso(monkeypatch, token_de: callable) -> dict:  # type: ignore[valid-type]
    """/auth/token y /auth/keys de Apple, sin red. `token_de(nonce)` da el id_token."""
    from app.api.v1.endpoints import oauth

    visto: dict = {}

    def handler(req: httpx.Request) -> httpx.Response:
        if str(req.url) == apple_signin.TOKEN_URL:
            visto["form"] = dict(urllib.parse.parse_qsl(req.content.decode()))
            return httpx.Response(200, json={"access_token": "a", "id_token": token_de(visto["nonce"])})
        if str(req.url) == apple_signin.KEYS_URL:
            return httpx.Response(200, json=_jwks(_APPLE))
        return httpx.Response(404)

    monkeypatch.setattr(oauth, "_http_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    return visto


async def _start(client, db_session, visto: dict) -> tuple[str, dict[str, str]]:
    from sqlalchemy import select

    from app.models.oauth import OAuthState

    r = await client.get(f"{OAUTH}/apple/start", headers=_h(), follow_redirects=False)
    state = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(r.headers["location"]).query))["state"]
    fila = (await db_session.execute(select(OAuthState).where(OAuthState.state == state))).scalar_one()
    visto["nonce"] = apple_signin.nonce_for(fila.code_verifier)
    cookie = next(c for c in r.headers.get_list("set-cookie") if c.startswith(f"{OAUTH_STATE_COOKIE}="))
    return state, {"Cookie": cookie.split(";", 1)[0]}


async def test_callback_crea_la_cuenta_con_el_email_verificado(client, db_session, monkeypatch, apple):
    from sqlalchemy import select

    from app.models.oauth import OAuthAccount
    from app.models.user import User

    visto = _apple_falso(monkeypatch, lambda nonce: _id_token(nonce=nonce))
    state, cookie = await _start(client, db_session, visto)
    r = await client.post(
        f"{OAUTH}/apple/callback",
        data={"code": "c-1", "state": state},
        headers={**_h(), **cookie, "Origin": "https://appleid.apple.com"},
        follow_redirects=False,
    )
    assert r.status_code == 302, r.text
    assert "oauth_error" not in r.headers["location"]
    assert any(c.startswith(f"{ACCESS_COOKIE}=") for c in r.headers.get_list("set-cookie"))

    # El canje lleva el client_secret ES256 y no lleva PKCE.
    assert visto["form"]["grant_type"] == "authorization_code"
    assert jwt.get_unverified_header(visto["form"]["client_secret"])["alg"] == "ES256"
    assert "code_verifier" not in visto["form"]

    user = (await db_session.execute(select(User).where(User.email == "ana@privaterelay.appleid.com"))).scalar_one()
    assert user.email_verified
    link = (await db_session.execute(select(OAuthAccount).where(OAuthAccount.user_id == user.id))).scalar_one()
    assert (link.provider, link.provider_user_id) == ("apple", "000123.apple-user")


async def test_callback_con_id_token_de_otro_intento_no_abre_sesion(client, db_session, monkeypatch, apple):
    visto = _apple_falso(monkeypatch, lambda nonce: _id_token(nonce="de-otro-intento"))
    state, cookie = await _start(client, db_session, visto)
    r = await client.post(
        f"{OAUTH}/apple/callback", data={"code": "c-2", "state": state},
        headers={**_h(), **cookie}, follow_redirects=False,
    )
    assert r.status_code == 302
    assert "oauth_error=provider_error" in r.headers["location"]
    assert not any(c.startswith(f"{ACCESS_COOKIE}=") for c in r.headers.get_list("set-cookie"))


async def test_callback_sin_la_cookie_del_state_da_400(client, db_session, monkeypatch, apple):
    visto = _apple_falso(monkeypatch, lambda nonce: _id_token(nonce=nonce))
    state, _cookie = await _start(client, db_session, visto)
    r = await client.post(f"{OAUTH}/apple/callback", data={"code": "c-3", "state": state}, headers=_h())
    assert r.status_code == 400


async def test_callback_por_get_no_vale(client, apple):
    r = await client.get(f"{OAUTH}/apple/callback?code=x&state=y", headers=_h())
    assert r.status_code == 405


async def test_cancelar_en_apple_vuelve_a_la_app(client, apple):
    r = await client.post(
        f"{OAUTH}/apple/callback", data={"state": "s", "error": "user_cancelled_authorize"},
        headers=_h(), follow_redirects=False,
    )
    assert r.status_code == 302 and "oauth_error=cancelled" in r.headers["location"]


# ── control de Origin (csrf.py) ──────────────────────────────────────────────


async def test_la_excepcion_de_origin_es_solo_esa_ruta(client, apple):
    sesion = {"Cookie": f"{ACCESS_COOKIE}=cualquiera", "Origin": "https://appleid.apple.com"}
    # El callback de Apple pasa el control de Origin (y cae en el del state: 400).
    r = await client.post(f"{OAUTH}/apple/callback", data={"code": "c", "state": "s"}, headers={**_h(), **sesion})
    assert r.status_code == 400
    # Cualquier otro POST con sesión y ese Origin sigue en 403.
    r = await client.post("/api/v1/auth/logout", headers={**_h(), **sesion})
    assert r.status_code == 403
