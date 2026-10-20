"""Back-office de soporte (44.1, `docs/PLAN_BACKOFFICE.md` B1–B3, B6, B7).

Buscar usuarios y abrir su ficha. Solo el dueño, solo con la verificación en
dos pasos activa, el listado enmascara el email y abrir una ficha queda en el
registro de administración (`admin_action_log`, acción `view`).
"""

from __future__ import annotations

import itertools
import uuid

import pytest
from sqlalchemy import select

from app.core.security import create_access_token, get_password_hash
from app.models.admin import AdminActionLog
from app.models.auth import AuditLog, User2FA
from app.models.user import User

USERS = "/api/v1/admin/users"
_ip = itertools.count(10)


def _h(u: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(u.id)}", "X-Forwarded-For": f"203.0.113.{next(_ip) % 250 + 1}"}


async def _with_2fa(db_session, u: User) -> User:
    db_session.add(User2FA(user_id=u.id, secret_key="JBSWY3DPEHPK3PXP", backup_codes=[], enabled=True))
    await db_session.commit()
    return u


async def _alumno(db_session, username: str, email: str) -> User:
    u = User(
        id=uuid.uuid4(), email=email, username=username,
        hashed_password=get_password_hash("Passw0rd!"), display_name=username, language="es",
    )
    db_session.add(u)
    await db_session.commit()
    return u


# ── B1/B7: quién entra ─────────────────────────────────────────────────────────


async def test_un_alumno_no_entra(client, user):
    r = await client.get(USERS, params={"q": "abc"}, headers=_h(user))
    assert r.status_code == 403


async def test_el_dueno_sin_2fa_no_entra_y_se_le_dice_por_que(client, owner):
    r = await client.get(USERS, params={"q": "abc"}, headers=_h(owner))
    assert r.status_code == 403
    assert r.json()["detail"] == "2fa_required"


async def test_sin_sesion_401(client):
    r = await client.get(USERS, params={"q": "abc"})
    assert r.status_code == 401


# ── B2: búsqueda ───────────────────────────────────────────────────────────────


async def test_buscar_con_menos_de_3_caracteres_es_422(client, db_session, owner):
    await _with_2fa(db_session, owner)
    r = await client.get(USERS, params={"q": "ab"}, headers=_h(owner))
    assert r.status_code == 422


async def test_busca_por_email_usuario_o_prefijo_de_id_y_enmascara_el_email(client, db_session, owner):
    await _with_2fa(db_session, owner)
    ana = await _alumno(db_session, "anabanana", "federica.lopez@gmail.com")
    await _alumno(db_session, "otro_usuario", "otro@example.com")

    for q in ("federica", "anaban", str(ana.id)[:8]):
        r = await client.get(USERS, params={"q": q}, headers=_h(owner))
        assert r.status_code == 200, r.text
        body = r.json()
        assert [i["username"] for i in body["items"]] == ["anabanana"], q
        item = body["items"][0]
        assert item["email_masked"] == "fe***@gmail.com"
        assert "federica" not in r.text  # el email completo no viaja en el listado
        assert item["status"] == "active"
        assert set(item) == {"id", "username", "email_masked", "created_at", "status"}


async def test_la_busqueda_pagina_de_20_en_20(client, db_session, owner):
    await _with_2fa(db_session, owner)
    for n in range(23):
        await _alumno(db_session, f"pagina{n:02d}", f"pagina{n:02d}@example.com")
    p1 = (await client.get(USERS, params={"q": "pagina"}, headers=_h(owner))).json()
    p2 = (await client.get(USERS, params={"q": "pagina", "page": 2}, headers=_h(owner))).json()
    assert (p1["total"], len(p1["items"]), len(p2["items"])) == (23, 20, 3)
    assert not {i["id"] for i in p1["items"]} & {i["id"] for i in p2["items"]}


async def test_buscar_no_queda_en_el_registro(client, db_session, owner):
    # B6 registra las acciones y abrir fichas; una búsqueda no expone a nadie.
    await _with_2fa(db_session, owner)
    await client.get(USERS, params={"q": "nadie"}, headers=_h(owner))
    assert (await db_session.execute(select(AdminActionLog))).scalars().all() == []


# ── B3/B6: ficha y registro ────────────────────────────────────────────────────


async def test_abrir_la_ficha_la_registra_como_view(client, db_session, owner):
    await _with_2fa(db_session, owner)
    ana = await _alumno(db_session, "anaficha", "ana.ficha@example.com")
    db_session.add(AuditLog(user_id=ana.id, action="login", result="failed", ip="198.51.100.7"))
    await db_session.commit()

    r = await client.get(f"{USERS}/{ana.id}", headers=_h(owner))
    assert r.status_code == 200, r.text
    ficha = r.json()
    assert ficha["account"]["email"] == "ana.ficha@example.com"  # la ficha sí da el email («copiar email», B8)
    assert ficha["account"]["status"] == "active"
    assert ficha["plan"]["subscription_tier"] is None
    assert ficha["progress"]["skills_practiced"] == 0
    assert [e["action"] for e in ficha["security"]["recent_events"]] == ["login"]
    assert ficha["gdpr"]["pending"] == []
    # B5: nada de contraseñas
    assert "password" not in r.text and "hashed" not in r.text

    rows = (await db_session.execute(select(AdminActionLog))).scalars().all()
    assert len(rows) == 1
    row = rows[0]
    assert (row.actor_id, row.target_user_id, row.action, row.reason) == (owner.id, ana.id, "view", None)
    assert row.ip


async def test_ficha_de_un_id_que_no_existe_404_sin_registro(client, db_session, owner):
    await _with_2fa(db_session, owner)
    r = await client.get(f"{USERS}/{uuid.uuid4()}", headers=_h(owner))
    assert r.status_code == 404
    assert (await db_session.execute(select(AdminActionLog))).scalars().all() == []


async def test_un_alumno_no_abre_fichas_ni_deja_rastro(client, db_session, user):
    otro = await _alumno(db_session, "victima", "victima@example.com")
    r = await client.get(f"{USERS}/{otro.id}", headers=_h(user))
    assert r.status_code == 403
    assert (await db_session.execute(select(AdminActionLog))).scalars().all() == []


@pytest.mark.parametrize(
    ("email", "masked"),
    [("federica@gmail.com", "fe***@gmail.com"), ("ab@x.io", "a***@x.io"), ("a@x.io", "a***@x.io")],
)
def test_mascara_de_email(email, masked):
    from app.api.v1.endpoints.admin_users import mask_email

    assert mask_email(email) == masked


# ── B6: leer el registro (44.3, pestaña «Registro») ───────────────────────────

LOG = "/api/v1/admin/action-log"


async def test_el_registro_se_lee_del_mas_nuevo_al_mas_viejo(client, db_session, owner):
    await _with_2fa(db_session, owner)
    ana = await _alumno(db_session, "analog", "ana.log@example.com")
    await client.get(f"{USERS}/{ana.id}", headers=_h(owner))
    await client.post(f"{USERS}/{ana.id}/actions/unlock", json={"reason": "probando"}, headers=_h(owner))

    r = await client.get(LOG, headers=_h(owner))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 2
    assert [i["action"] for i in body["items"]] == ["unlock", "view"]
    first = body["items"][0]
    assert (first["actor_username"], first["target_username"], first["reason"]) == (owner.username, "analog", "probando")
    assert first["data"] == {"cleared": 0}


async def test_el_registro_es_solo_del_dueno_con_2fa(client, db_session, owner, user):
    assert (await client.get(LOG, headers=_h(user))).status_code == 403
    r = await client.get(LOG, headers=_h(owner))
    assert (r.status_code, r.json()["detail"]) == (403, "2fa_required")
