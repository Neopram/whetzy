"""43.3 (ADR-65 D2): el onboarding terminado vive en el servidor.

Antes era `whetzy_onboarded_<id>` en el localStorage: otro navegador u otro
móvil lo repetían enteros. Ahora `/auth/me` devuelve `onboarding_completed_at`
y `PATCH /auth/me {"onboarding_completed": true}` lo fija una sola vez.
"""

from __future__ import annotations

import itertools

import pytest

ME = "/api/v1/auth/me"
_n = itertools.count(1)


@pytest.fixture
async def auth_headers(client) -> dict[str, str]:
    # El `user` común lleva un email `@whetzy.test`, que `UserRead` (EmailStr)
    # no acepta al responder `/auth/me`; aquí se registra uno de verdad.
    i = next(_n)
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"onb{i}@example.com", "username": f"onb_{i}", "password": "Str0ng!Pass",
            "display_name": "Onb", "language": "es", "age_confirmed": True,
        },
        headers={"X-Forwarded-For": f"203.0.113.{i}"},
    )
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def test_me_dice_si_el_onboarding_esta_hecho_y_se_fija_una_vez(client, auth_headers):
    before = await client.get(ME, headers=auth_headers)
    assert before.status_code == 200, before.text
    assert before.json()["onboarding_completed_at"] is None

    done = await client.patch(ME, json={"onboarding_completed": True}, headers=auth_headers)
    assert done.status_code == 200, done.text
    first = done.json()["onboarding_completed_at"]
    assert first is not None

    # «Otro navegador»: una petición nueva lo ve hecho, y repetirlo no lo mueve.
    again = await client.patch(ME, json={"onboarding_completed": True}, headers=auth_headers)
    assert again.json()["onboarding_completed_at"] == first
    assert (await client.get(ME, headers=auth_headers)).json()["onboarding_completed_at"] == first


async def test_otros_cambios_de_perfil_no_lo_marcan(client, auth_headers):
    r = await client.patch(ME, json={"language": "en"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["onboarding_completed_at"] is None


async def test_la_certificacion_relacionada_tiene_que_ser_de_certificacion(
    client, auth_headers, db_session
):
    from app.models.content import Track

    db_session.add_all(
        [
            Track(id="t_aprende", name_es="A", name_en="A", order=90, icon="x", color="#000",
                  total_questions=0),
            Track(id="t_cert", name_es="C", name_en="C", order=91, icon="x", color="#000",
                  total_questions=0, is_certification=True),
        ]
    )
    await db_session.commit()

    ok = await client.patch(
        ME,
        json={"target_track_id": "t_aprende", "target_certification_id": "t_cert",
              "onboarding_goal": 4},
        headers=auth_headers,
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["target_certification_id"] == "t_cert"
    assert ok.json()["onboarding_goal"] == 4

    bad = await client.patch(ME, json={"target_certification_id": "t_aprende"}, headers=auth_headers)
    assert bad.status_code == 422
