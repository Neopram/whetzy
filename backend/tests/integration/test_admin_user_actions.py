"""Back-office: las cinco acciones sobre una cuenta (44.2, `docs/PLAN_BACKOFFICE.md` B4, B6).

Cada acción exige motivo (422 si falta o está en blanco), hace su efecto y deja
una fila en `admin_action_log` con el motivo y los datos. Un plan regalado no
pasa de 90 días; suspender cierra además las sesiones abiertas.
"""

from __future__ import annotations

import itertools
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.security import create_access_token, get_password_hash
from app.models.admin import AdminActionLog
from app.models.auth import LoginAttempt, RefreshToken, User2FA
from app.models.email_verification import EmailVerificationToken
from app.models.user import User

USERS = "/api/v1/admin/users"
_ip = itertools.count(10)


def _h(u: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(u.id)}", "X-Forwarded-For": f"203.0.114.{next(_ip) % 250 + 1}"}


@pytest.fixture
async def owner2fa(db_session, owner):
    db_session.add(User2FA(user_id=owner.id, secret_key="JBSWY3DPEHPK3PXP", backup_codes=[], enabled=True))
    await db_session.commit()
    return owner


@pytest.fixture
async def ana(db_session):
    u = User(
        id=uuid.uuid4(), email="ana.accion@example.com", username="anaaccion",
        hashed_password=get_password_hash("Passw0rd!"), display_name="Ana", language="es",
    )
    db_session.add(u)
    await db_session.commit()
    return u


async def _act(client, owner, target, action, **body):
    return await client.post(f"{USERS}/{target.id}/actions/{action}", json=body, headers=_h(owner))


async def _log(db_session) -> list[AdminActionLog]:
    return list((await db_session.execute(select(AdminActionLog).order_by(AdminActionLog.id))).scalars().all())


# ── motivo obligatorio y guardas comunes ───────────────────────────────────────


@pytest.mark.parametrize("reason", [None, "", "   "])
async def test_sin_motivo_es_422_y_no_hace_nada(client, db_session, owner2fa, ana, reason):
    body = {} if reason is None else {"reason": reason}
    r = await _act(client, owner2fa, ana, "suspend", **body)
    assert r.status_code == 422
    await db_session.refresh(ana)
    assert ana.is_active is True
    assert await _log(db_session) == []


async def test_accion_desconocida_404(client, owner2fa, ana):
    r = await _act(client, owner2fa, ana, "impersonate", reason="probar")
    assert r.status_code == 404


async def test_un_alumno_no_puede_actuar(client, db_session, user, ana):
    r = await _act(client, user, ana, "suspend", reason="no")
    assert r.status_code == 403
    await db_session.refresh(ana)
    assert ana.is_active is True


async def test_el_dueno_sin_2fa_no_puede_actuar(client, owner, ana):
    r = await _act(client, owner, ana, "suspend", reason="sin 2fa")
    assert r.status_code == 403
    assert r.json()["detail"] == "2fa_required"


async def test_usuario_que_no_existe_404(client, db_session, owner2fa):
    r = await client.post(f"{USERS}/{uuid.uuid4()}/actions/suspend", json={"reason": "x"}, headers=_h(owner2fa))
    assert r.status_code == 404
    assert await _log(db_session) == []


# ── las cinco acciones ─────────────────────────────────────────────────────────


async def test_reenviar_verificacion(client, db_session, owner2fa, ana, monkeypatch):
    sent: list[str] = []
    monkeypatch.setattr("app.services.email.send_email_verification", lambda to, **_: sent.append(to))
    r = await _act(client, owner2fa, ana, "resend_verification", reason="no le llegó el correo")
    assert r.status_code == 200, r.text
    assert sent == ["ana.accion@example.com"]
    tokens = (await db_session.execute(select(EmailVerificationToken).where(EmailVerificationToken.user_id == ana.id))).scalars().all()
    assert len([t for t in tokens if not t.used]) == 1
    [row] = await _log(db_session)
    assert (row.action, row.reason, row.target_user_id, row.actor_id) == ("resend_verification", "no le llegó el correo", ana.id, owner2fa.id)


async def test_reenviar_verificacion_a_quien_ya_esta_verificado_409(client, db_session, owner2fa, ana):
    ana.email_verified = True
    await db_session.commit()
    r = await _act(client, owner2fa, ana, "resend_verification", reason="por si acaso")
    assert r.status_code == 409
    assert await _log(db_session) == []


async def test_cerrar_sesiones(client, db_session, owner2fa, ana):
    before = ana.jwt_version
    db_session.add(RefreshToken(
        user_id=ana.id, token_hash="h" * 64, family_id=uuid.uuid4(),
        expires_at=datetime.now(UTC) + timedelta(days=7),
    ))
    await db_session.commit()
    old_token = create_access_token(ana.id)
    assert (await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {old_token}"})).status_code == 200

    r = await _act(client, owner2fa, ana, "close_sessions", reason="perdió el móvil")
    assert r.status_code == 200, r.text
    await db_session.refresh(ana)
    assert ana.jwt_version == before + 1
    tokens = (await db_session.execute(select(RefreshToken).where(RefreshToken.user_id == ana.id))).scalars().all()
    assert tokens and all(t.revoked for t in tokens)
    [row] = await _log(db_session)
    assert row.action == "close_sessions"


async def test_desbloquear(client, db_session, owner2fa, ana):
    now = datetime.now(UTC)
    for i in range(6):
        db_session.add(LoginAttempt(email=ana.email, ip=f"198.51.100.{i}", success=False, created_at=now))
    db_session.add(LoginAttempt(email="otra@example.com", ip="198.51.100.9", success=False, created_at=now))
    await db_session.commit()

    r = await _act(client, owner2fa, ana, "unlock", reason="se bloqueó probando")
    assert r.status_code == 200, r.text
    left = (await db_session.execute(select(LoginAttempt.email).where(LoginAttempt.success.is_(False)))).scalars().all()
    assert left == ["otra@example.com"]  # solo los fallos de esta persona
    [row] = await _log(db_session)
    assert (row.action, row.data) == ("unlock", {"cleared": 6})


async def test_regalar_plan(client, db_session, owner2fa, ana):
    r = await _act(client, owner2fa, ana, "grant_plan", reason="probador del piloto", tier="pro", days=30)
    assert r.status_code == 200, r.text
    await db_session.refresh(ana)
    assert ana.granted_tier == "pro"
    expires = ana.granted_tier_expires_at.replace(tzinfo=ana.granted_tier_expires_at.tzinfo or UTC)
    assert timedelta(days=29, hours=23) < expires - datetime.now(UTC) <= timedelta(days=30)
    [row] = await _log(db_session)
    assert row.action == "grant_plan"
    assert row.data["tier"] == "pro" and row.data["days"] == 30


@pytest.mark.parametrize(("tier", "days"), [("pro", 91), ("pro", 0), ("creator", 10), ("gold", 10)])
async def test_regalar_plan_fuera_de_limites_422(client, db_session, owner2fa, ana, tier, days):
    r = await _act(client, owner2fa, ana, "grant_plan", reason="x", tier=tier, days=days)
    assert r.status_code == 422
    await db_session.refresh(ana)
    assert ana.granted_tier is None
    assert await _log(db_session) == []


async def test_suspender_invalida_la_sesion_y_reactivar(client, db_session, owner2fa, ana):
    token = create_access_token(ana.id)
    me = {"Authorization": f"Bearer {token}"}
    assert (await client.get("/api/v1/auth/me", headers=me)).status_code == 200

    r = await _act(client, owner2fa, ana, "suspend", reason="abuso del duelo")
    assert r.status_code == 200, r.text
    await db_session.refresh(ana)
    assert ana.is_active is False
    assert (await client.get("/api/v1/auth/me", headers=me)).status_code in (401, 403)

    r = await _act(client, owner2fa, ana, "reactivate", reason="aclarado por correo")
    assert r.status_code == 200, r.text
    await db_session.refresh(ana)
    assert ana.is_active is True
    # La sesión vieja sigue muerta: hay que volver a entrar.
    assert (await client.get("/api/v1/auth/me", headers=me)).status_code == 401
    assert [row.action for row in await _log(db_session)] == ["suspend", "reactivate"]


async def test_el_dueno_no_se_suspende_a_si_mismo(client, db_session, owner2fa):
    r = await _act(client, owner2fa, owner2fa, "suspend", reason="error")
    assert r.status_code == 409
    await db_session.refresh(owner2fa)
    assert owner2fa.is_active is True
