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
