"""43.4 (ADR-65 D5/D6): ruta activa en el servidor y Hoy filtrado por ella.

- `GET /progress/decaying?track_id=` devuelve solo las skills de esa ruta:
  antes «a punto de olvidarse» mezclaba todas, así que Hoy enseñaba skills de
  otro track.
- Cambiar de ruta (`PATCH /auth/me {target_track_id}`) no toca el progreso
  del track anterior: todo vive por skill.
"""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta

from app.models.content import Module, Skill, Track
from app.models.user import User, UserSkillState

BASE = "/api/v1"
_n = itertools.count(1)


async def _two_tracks(db, user_id) -> None:
    for t in ("ra_a", "ra_b"):
        db.add_all([
            Track(id=t, name_es=t, name_en=t, order=95, icon="x", color="#000", total_questions=0),
            Module(id=f"m_{t}", track_id=t, name_es="M", name_en="M", order=1,
                   description_es="", description_en=""),
            Skill(id=f"sk_{t}", module_id=f"m_{t}", name_es=f"ES {t}", name_en=f"EN {t}", order=1),
            UserSkillState(
                user_id=user_id, skill_id=f"sk_{t}", p_known=0.7, attempts=4, correct_count=3,
                fsrs_due=datetime.now(UTC) + timedelta(days=1),
            ),
        ])
    await db.commit()


async def _register(client) -> dict[str, str]:
    i = next(_n)
    r = await client.post(
        f"{BASE}/auth/register",
        json={"email": f"ra{i}@example.com", "username": f"ra_{i}", "password": "Str0ng!Pass",
              "display_name": "RA", "language": "es", "age_confirmed": True},
        headers={"X-Forwarded-For": f"198.18.0.{i}"},
    )
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def test_decaying_se_filtra_por_ruta(client, user, auth_headers, db_session):
    await _two_tracks(db_session, user.id)

    todas = await client.get(f"{BASE}/progress/decaying", headers=auth_headers)
    assert {r["skill_id"] for r in todas.json()} == {"sk_ra_a", "sk_ra_b"}

    solo_a = await client.get(f"{BASE}/progress/decaying?track_id=ra_a", headers=auth_headers)
    assert solo_a.status_code == 200
    assert [r["skill_id"] for r in solo_a.json()] == ["sk_ra_a"]


async def test_cambiar_de_ruta_no_toca_el_progreso_anterior(client, db_session):
    headers = await _register(client)
    me = await client.get(f"{BASE}/auth/me", headers=headers)
    user_id = me.json()["id"]
    import uuid

    await _two_tracks(db_session, uuid.UUID(user_id))

    assert (await client.patch(f"{BASE}/auth/me", json={"target_track_id": "ra_a"}, headers=headers)).status_code == 200
    antes = (await client.get(f"{BASE}/progress/skills?track_id=ra_a", headers=headers)).json()

    cambio = await client.patch(f"{BASE}/auth/me", json={"target_track_id": "ra_b"}, headers=headers)
    assert cambio.status_code == 200
    assert cambio.json()["target_track_id"] == "ra_b"
    # «Otro navegador»: la ruta activa la da el servidor.
    assert (await client.get(f"{BASE}/auth/me", headers=headers)).json()["target_track_id"] == "ra_b"

    despues = (await client.get(f"{BASE}/progress/skills?track_id=ra_a", headers=headers)).json()
    assert despues == antes
    assert despues[0]["attempts"] == 4
    assert await db_session.get(User, uuid.UUID(user_id)) is not None


async def _due_in_both(db, user_id) -> None:
    """Un repaso vencido en cada una de las dos rutas."""
    from sqlalchemy import update

    await _two_tracks(db, user_id)
    await db.execute(
        update(UserSkillState)
        .where(UserSkillState.user_id == user_id)
        .values(fsrs_due=datetime.now(UTC) - timedelta(hours=1))
    )
    await db.commit()


async def test_hoy_cuenta_solo_los_repasos_de_la_ruta_activa(client, db_session):
    """§7 de 43.4 (2026-10-17): la tarjeta de repaso de Hoy contaba los
    repasos vencidos de todas las rutas, no los de la activa."""
    import uuid

    headers = await _register(client)
    user_id = uuid.UUID((await client.get(f"{BASE}/auth/me", headers=headers)).json()["id"])
    await _due_in_both(db_session, user_id)

    sin_ruta = await client.get(f"{BASE}/progress/dashboard", headers=headers)
    assert sin_ruta.json()["reviews_due"] == 2  # sin ruta activa, todas

    await client.patch(f"{BASE}/auth/me", json={"target_track_id": "ra_a"}, headers=headers)
    con_ruta = await client.get(f"{BASE}/progress/dashboard", headers=headers)
    assert con_ruta.json()["reviews_due"] == 1
