"""CSRF: con cookie de sesión, solo un origen de la lista cambia estado (S.13).

En producción las cookies van con `SameSite=None`, así que el navegador las
manda en una petición que dispara otra web, y un `POST` sin cuerpo no pasa por
preflight de CORS. `POST /billing/paddle/cancel` desde una página ajena
cancelaba la suscripción de quien tuviera la sesión abierta.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.cookies import ACCESS_COOKIE, REFRESH_COOKIE
from app.core.security import create_access_token
from app.models.user import User

CANCEL = "/api/v1/billing/paddle/cancel"
EVIL = "https://evil.example"


def _allowed() -> str:
    return settings.active_cors_origins[0]


def _cookie(user: User) -> dict[str, str]:
    return {"cookie": f"{ACCESS_COOKIE}={create_access_token(user.id)}"}


@pytest.mark.asyncio
async def test_post_con_cookie_desde_origen_ajeno_da_403(client: AsyncClient, user: User) -> None:
    res = await client.post(CANCEL, headers={**_cookie(user), "origin": EVIL})
    assert res.status_code == 403, res.text
    assert "CSRF" in res.json()["detail"]


@pytest.mark.asyncio
async def test_post_con_cookie_desde_origen_de_la_lista_llega_al_endpoint(
    client: AsyncClient, user: User
) -> None:
    res = await client.post(CANCEL, headers={**_cookie(user), "origin": _allowed()})
    assert res.status_code != 403, res.text


@pytest.mark.asyncio
async def test_sin_origin_cuenta_el_origen_del_referer(client: AsyncClient, user: User) -> None:
    ok = await client.post(CANCEL, headers={**_cookie(user), "referer": f"{_allowed()}/app/ajustes"})
    assert ok.status_code != 403, ok.text
    bad = await client.post(CANCEL, headers={**_cookie(user), "referer": f"{EVIL}/trampa"})
    assert bad.status_code == 403, bad.text


@pytest.mark.parametrize(
    "headers",
    [{}, {"origin": "null"}, {"referer": "no-es-una-url"}],
    ids=["sin-origen", "origin-null", "referer-roto"],
)
@pytest.mark.asyncio
async def test_con_cookie_y_sin_origen_valido_da_403(
    client: AsyncClient, user: User, headers: dict[str, str]
) -> None:
    res = await client.post(CANCEL, headers={**_cookie(user), **headers})
    assert res.status_code == 403, res.text


@pytest.mark.asyncio
async def test_la_cookie_de_refresh_tambien_cuenta(client: AsyncClient, user: User) -> None:
    res = await client.post(
        "/api/v1/auth/refresh",
        headers={"cookie": f"{REFRESH_COOKIE}=x", "origin": EVIL},
    )
    assert res.status_code == 403, res.text


@pytest.mark.asyncio
async def test_get_con_cookie_desde_origen_ajeno_no_se_bloquea(client: AsyncClient, user: User) -> None:
    res = await client.get("/api/v1/content/tracks", headers={**_cookie(user), "origin": EVIL})
    assert res.status_code == 200, res.text


@pytest.mark.asyncio
async def test_sin_cookie_no_hay_csrf_que_parar(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    """Un cliente con `Authorization: Bearer` o un webhook no lleva credencial ambiental."""
    res = await client.post(CANCEL, headers={**auth_headers, "origin": EVIL})
    assert res.status_code != 403, res.text
