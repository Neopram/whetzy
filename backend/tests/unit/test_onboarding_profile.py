"""PATCH /auth/me guarda idioma y respuestas del onboarding (34.11).

Antes el onboarding preguntaba experiencia/objetivo/horas y no guardaba nada,
y el idioma elegido solo cambiaba la UI local: al recargar volvía el del
registro.
"""
import uuid

import pytest
from httpx import AsyncClient


async def _registrar(client: AsyncClient) -> dict[str, str]:
    # Usuario propio con un dominio válido: la fixture `user` usa
    # @whetzy.test, que EmailStr rechaza al serializar la respuesta de /me.
    u = f"ob{uuid.uuid4().hex[:10]}"
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": f"{u}@example.com", "username": u, "display_name": "Ob", "password": "pass-onboarding-1", "language": "es", "age_confirmed": True},
    )
    assert r.status_code in (200, 201), r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.mark.asyncio
async def test_patch_me_guarda_idioma_y_segmento(client: AsyncClient) -> None:
    auth_headers = await _registrar(client)
    r = await client.patch(
        "/api/v1/auth/me",
        json={"language": "en", "onboarding_experience": 2, "onboarding_goal": 1, "onboarding_weekly_time": 0},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert (body["language"], body["onboarding_experience"], body["onboarding_goal"], body["onboarding_weekly_time"]) == ("en", 2, 1, 0)
    me = (await client.get("/api/v1/auth/me", headers=auth_headers)).json()
    assert me["language"] == "en" and me["onboarding_experience"] == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("field,value", [("onboarding_experience", 3), ("onboarding_goal", -1), ("language", "fr")])
async def test_patch_me_rechaza_valores_fuera_de_rango(client: AsyncClient, field: str, value: object) -> None:
    auth_headers = await _registrar(client)
    r = await client.patch("/api/v1/auth/me", json={field: value}, headers=auth_headers)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_patch_me_rechaza_nombre_con_palabra_bloqueada(client: AsyncClient) -> None:
    """19.11: el filtro de palabras también se aplica al editar la cuenta, no solo al crearla."""
    auth_headers = await _registrar(client)
    r = await client.patch("/api/v1/auth/me", json={"display_name": "Soy un cabron"}, headers=auth_headers)
    assert r.status_code == 422


# ── D-20 y D-23 (dueño, 2026-10-12) ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_la_ruta_elegida_se_guarda_en_el_servidor(client: AsyncClient, content_seed) -> None:
    """D-20: antes solo vivía en el localStorage del dispositivo."""
    auth_headers = await _registrar(client)
    r = await client.patch(
        "/api/v1/auth/me", json={"target_track_id": content_seed["track_id"]}, headers=auth_headers
    )
    assert r.status_code == 200, r.text
    me = (await client.get("/api/v1/auth/me", headers=auth_headers)).json()
    assert me["target_track_id"] == content_seed["track_id"]


@pytest.mark.asyncio
async def test_una_ruta_que_no_existe_se_rechaza(client: AsyncClient) -> None:
    auth_headers = await _registrar(client)
    r = await client.patch("/api/v1/auth/me", json={"target_track_id": "track999"}, headers=auth_headers)
    assert r.status_code == 422


async def _origen(client: AsyncClient, db_session, headers, attribution: dict) -> tuple:
    from sqlalchemy import select

    from app.models.user import User

    r = await client.patch("/api/v1/auth/me", json={"signup_attribution": attribution}, headers=headers)
    assert r.status_code == 200, r.text
    me = (await client.get("/api/v1/auth/me", headers=headers)).json()
    db_session.expire_all()
    row = (
        await db_session.execute(
            select(User.signup_source, User.signup_campaign).where(User.id == uuid.UUID(me["id"]))
        )
    ).one()
    return tuple(row)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "attribution,expected",
    [
        ({}, ("direct", None)),
        ({"utm_source": "reddit", "utm_campaign": "aif-beta"}, ("utm", "aif-beta")),
        ({"utm_source": "google", "utm_medium": "cpc", "utm_campaign": "aif"}, ("paid", "aif")),
        ({"utm_source": "reddit", "referred": True}, ("referral", None)),
    ],
)
async def test_el_origen_del_alta_se_clasifica_en_el_servidor(
    client: AsyncClient, db_session, attribution: dict, expected: tuple
) -> None:
    """D-23: utm / pago / referido / directo, mínimo y sin terceros."""
    headers = await _registrar(client)
    assert await _origen(client, db_session, headers, attribution) == expected


@pytest.mark.asyncio
async def test_el_origen_es_el_primer_contacto_y_no_se_reescribe(client: AsyncClient, db_session) -> None:
    headers = await _registrar(client)
    assert await _origen(client, db_session, headers, {"utm_campaign": "primera"}) == ("utm", "primera")
    assert await _origen(client, db_session, headers, {"utm_campaign": "segunda"}) == ("utm", "primera")
