"""Trabajos periódicos (services/periodic.py): lo que prometen los Términos y la
economía y hasta el 2026-10-01 no ejecutaba nadie — recordatorio de renovación,
reactivación y liquidación del día 15 — y la baja de los correos de marketing."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_unsubscribe_token,
    verify_token,
)
from app.models.economy import CreditLedger, PromoCode
from app.models.instructor import Instructor, InstructorPayout
from app.models.user import User
from app.services import email as email_service
from app.services.periodic import (
    REACTIVATION_CREDITS,
    process_monthly_payouts,
    run_periodic_jobs,
    send_credit_expiry_warnings,
    send_reactivation_offers,
    send_renewal_reminders,
)

NOW = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)


def _user(**kw: object) -> User:
    uid = uuid.uuid4()
    fields: dict[str, object] = {
        "id": uid,
        "email": f"u{uid.hex[:10]}@example.com",
        "username": f"u{uid.hex[:10]}",
        "hashed_password": "x",
        "display_name": "Ana",
        "language": "es",
        "created_at": NOW - timedelta(days=60),
    }
    fields.update(kw)
    return User(**fields)


@pytest.fixture
def outbox(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    sent: list[dict[str, object]] = []
    monkeypatch.setattr(email_service, "send_renewal_reminder", lambda **kw: sent.append({"kind": "renewal", **kw}))
    monkeypatch.setattr(email_service, "send_reactivation", lambda **kw: sent.append({"kind": "reactivation", **kw}))
    monkeypatch.setattr(
        email_service, "send_credit_expiry_warning", lambda **kw: sent.append({"kind": "expiry", **kw})
    )
    return sent


def _subscriber(**kw: object) -> User:
    fields: dict[str, object] = {
        "is_premium": True, "subscription_status": "active", "subscription_provider": "paddle",
        "subscription_tier": "plus", "subscription_expires_at": NOW + timedelta(days=5),
    }
    fields.update(kw)
    return _user(**fields)


# ── Recordatorio de renovación (Términos: «al menos 7 días antes») ─────────


@pytest.mark.asyncio
async def test_renewal_reminder_once_per_period(db_session: AsyncSession, outbox: list):
    u = _subscriber()
    db_session.add(u)
    await db_session.flush()

    assert await send_renewal_reminders(db_session, NOW) == 1
    assert await send_renewal_reminders(db_session, NOW + timedelta(hours=1)) == 0
    [mail] = outbox
    assert (mail["plan_name"], mail["amount"], mail["lang"]) == ("Pro", "14.99 $", "es")
    assert mail["renewal_date"] == "25 de octubre de 2026"

    # Renovó: el periodo siguiente tiene su propio aviso.
    u.subscription_expires_at = NOW + timedelta(days=35)
    await db_session.flush()
    assert await send_renewal_reminders(db_session, NOW + timedelta(days=29)) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "override",
    [
        {"subscription_status": "canceled"},  # cancelada al final del periodo: no se renueva
        {"subscription_provider": "revenuecat"},  # las tiendas avisan ellas
        {"subscription_expires_at": NOW + timedelta(days=10)},  # aún no toca
        {"subscription_expires_at": NOW - timedelta(days=1)},  # ya pasó
        {"is_active": False},
    ],
)
async def test_renewal_reminder_skips_what_will_not_renew_soon(
    db_session: AsyncSession, outbox: list, override: dict[str, object]
):
    db_session.add(_subscriber(**override))
    await db_session.flush()
    assert await send_renewal_reminders(db_session, NOW) == 0
    assert outbox == []


# ── Reactivación (ECONOMIA §2.2: 200 créditos, 72 h, uno cada 60 días) ─────


@pytest.mark.asyncio
async def test_reactivation_sends_a_200_credit_code_with_one_click_unsubscribe(
    db_session: AsyncSession, outbox: list
):
    u = _user(email_verified=True, last_active=NOW - timedelta(days=20))
    db_session.add(u)
    await db_session.flush()

    assert await send_reactivation_offers(db_session, NOW) == 1
    [mail] = outbox
    assert mail["credits"] == REACTIVATION_CREDITS == 200
    code = (await db_session.execute(select(PromoCode).where(PromoCode.code == mail["code"]))).scalar_one()
    expires = code.expires_at if code.expires_at.tzinfo else code.expires_at.replace(tzinfo=UTC)
    assert (code.credits, expires) == (200, NOW + timedelta(hours=72))
    token = str(mail["unsubscribe_url"]).split("token=")[1]
    assert verify_token(token, expected_type="unsubscribe").sub == str(u.id)

    # Uno cada 60 días: a los 30 no se repite, a los 61 sí.
    assert await send_reactivation_offers(db_session, NOW + timedelta(days=30)) == 0
    assert await send_reactivation_offers(db_session, NOW + timedelta(days=61)) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "override",
    [
        {"marketing_emails_opt_out": True},  # se dio de baja
        {"email_verified": False},  # nunca confirmó que el correo es suyo
        {"last_active": NOW - timedelta(days=3)},  # estudia
        {"created_at": NOW - timedelta(days=5), "last_active": None},  # recién llegado
        {"is_active": False},
    ],
)
async def test_reactivation_respects_consent_and_activity(
    db_session: AsyncSession, outbox: list, override: dict[str, object]
):
    fields: dict[str, object] = {"email_verified": True, "last_active": NOW - timedelta(days=20)}
    fields.update(override)
    db_session.add(_user(**fields))
    await db_session.flush()
    assert await send_reactivation_offers(db_session, NOW) == 0
    assert outbox == []


# ── Aviso de caducidad de créditos (ECONOMIA §2.4) ────────────────────────


async def _lot(db: AsyncSession, user: User, amount: int, expires_at: datetime) -> CreditLedger:
    lot = CreditLedger(
        user_id=user.id, amount=amount, reason="promo_code",
        idempotency_key=f"t:{uuid.uuid4()}", expires_at=expires_at,
    )
    db.add(lot)
    await db.flush()
    return lot


@pytest.mark.asyncio
async def test_expiry_warning_once_per_date_and_only_from_200(db_session: AsyncSession, outbox: list):
    u = _user(email_verified=True)
    db_session.add(u)
    await db_session.flush()
    soon = NOW + timedelta(days=5)
    await _lot(db_session, u, 150, soon)
    assert await send_credit_expiry_warnings(db_session, NOW) == 0  # 150 < 200

    await _lot(db_session, u, 80, NOW + timedelta(days=6))
    later = await _lot(db_session, u, 500, NOW + timedelta(days=30))  # fuera de la ventana
    assert await send_credit_expiry_warnings(db_session, NOW) == 1
    [mail] = outbox
    assert (mail["credits"], mail["expiry_date"]) == (230, "25 de octubre de 2026")
    assert "token=" in str(mail["unsubscribe_url"])
    assert await send_credit_expiry_warnings(db_session, NOW + timedelta(hours=1)) == 0
    # Otra fecha, otro aviso.
    assert await send_credit_expiry_warnings(db_session, later.expires_at - timedelta(days=2)) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "override", [{"marketing_emails_opt_out": True}, {"email_verified": False}, {"is_active": False}]
)
async def test_expiry_warning_respects_consent(
    db_session: AsyncSession, outbox: list, override: dict[str, object]
):
    fields: dict[str, object] = {"email_verified": True}
    fields.update(override)
    u = _user(**fields)
    db_session.add(u)
    await db_session.flush()
    await _lot(db_session, u, 300, NOW + timedelta(days=3))
    assert await send_credit_expiry_warnings(db_session, NOW) == 0
    assert outbox == []


@pytest.mark.asyncio
async def test_spent_credits_do_not_count_toward_the_warning(db_session: AsyncSession, outbox: list):
    u = _user(email_verified=True)
    db_session.add(u)
    await db_session.flush()
    lot = await _lot(db_session, u, 300, NOW + timedelta(days=3))
    db_session.add(CreditLedger(
        user_id=u.id, amount=-150, reason="spend_freeze", lot_id=lot.id,
        idempotency_key=f"t:{uuid.uuid4()}", expires_at=lot.expires_at,
    ))
    await db_session.flush()
    assert await send_credit_expiry_warnings(db_session, NOW) == 0


# ── Liquidación del día 15 (28.7) ──────────────────────────────────────────


async def _payout(db: AsyncSession, cents: int) -> InstructorPayout:
    owner = _user()
    db.add(owner)
    await db.flush()
    instructor = Instructor(id=uuid.uuid4(), user_id=owner.id, display_name="Ins")
    db.add(instructor)
    await db.flush()
    p = InstructorPayout(
        id=uuid.uuid4(), instructor_id=instructor.id, period_start=NOW - timedelta(days=30),
        period_end=NOW, earnings_cents=cents, status="pending",
    )
    db.add(p)
    await db.flush()
    return p


@pytest.mark.asyncio
async def test_payouts_only_on_the_15th_and_only_over_50_eur(db_session: AsyncSession):
    big, small = await _payout(db_session, 7500), await _payout(db_session, 4999)

    assert (await process_monthly_payouts(db_session, datetime(2026, 10, 14, tzinfo=UTC)))["processed_count"] == 0
    result = await process_monthly_payouts(db_session, datetime(2026, 10, 15, 3, tzinfo=UTC))
    assert (result["processed_count"], result["total_paid_cents"], result["filtered_out_count"]) == (1, 7500, 1)
    assert (big.status, small.status) == ("processing", "pending")
    # Varias vueltas el mismo día 15 no liquidan dos veces.
    again = await process_monthly_payouts(db_session, datetime(2026, 10, 15, 4, tzinfo=UTC))
    assert again["processed_count"] == 0


@pytest.mark.asyncio
async def test_one_failing_job_does_not_undo_the_others(
    db_session: AsyncSession, outbox: list, monkeypatch: pytest.MonkeyPatch
):
    db_session.add(_subscriber())
    await db_session.commit()

    async def boom(db: AsyncSession, now: datetime | None = None) -> int:
        raise RuntimeError("caído")

    monkeypatch.setattr("app.services.periodic.send_reactivation_offers", boom)
    results = await run_periodic_jobs(db_session, NOW)
    assert results["renewal_reminders"] == 1 and results["reactivation_offers"] == "error"
    assert len(outbox) == 1


def test_main_starts_the_periodic_loop():
    """Si alguien quita el bucle del arranque, los tres trabajos vuelven a no
    correr nunca, como hasta el 2026-10-01."""
    from pathlib import Path

    main = (Path(__file__).resolve().parents[2] / "app" / "main.py").read_text(encoding="utf-8")
    assert "asyncio.create_task(periodic_jobs_loop(" in main
    assert "from apscheduler" not in main


# ── Baja de los correos de marketing ───────────────────────────────────────


@pytest.mark.asyncio
async def test_unsubscribe_link_and_one_click(client: AsyncClient, db_session: AsyncSession):
    u = _user()
    db_session.add(u)
    await db_session.commit()

    page = await client.get(f"/api/v1/email/unsubscribe?token={create_unsubscribe_token(u.id)}")
    assert page.status_code == 200 and "Te has dado de baja" in page.text
    await db_session.refresh(u)
    assert u.marketing_emails_opt_out is True

    u.marketing_emails_opt_out = False
    await db_session.commit()
    r = await client.post(f"/api/v1/email/unsubscribe?token={create_unsubscribe_token(u.id)}")
    assert r.status_code == 200
    await db_session.refresh(u)
    assert u.marketing_emails_opt_out is True


@pytest.mark.asyncio
async def test_tokens_are_not_interchangeable(client: AsyncClient, db_session: AsyncSession):
    """Un token de sesión no da de baja a nadie, y uno de baja no abre sesión."""
    u = _user()
    db_session.add(u)
    await db_session.commit()

    r = await client.get(f"/api/v1/email/unsubscribe?token={create_access_token(u.id)}")
    assert r.status_code == 400
    with pytest.raises(HTTPException):
        verify_token(create_unsubscribe_token(u.id), expected_type="access")
    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {create_unsubscribe_token(u.id)}"}
    )
    assert me.status_code == 401


@pytest.mark.asyncio
async def test_settings_switch_turns_offers_on_and_off(client: AsyncClient, db_session: AsyncSession):
    user = _user()
    db_session.add(user)
    await db_session.commit()
    auth_headers = {"Authorization": f"Bearer {create_access_token(user.id)}"}
    r = await client.patch("/api/v1/email/preferences", json={"marketing": False}, headers=auth_headers)
    assert r.json() == {"marketing": False}
    me = (await client.get("/api/v1/auth/me", headers=auth_headers)).json()
    assert me["marketing_emails_opt_out"] is True
    r = await client.patch("/api/v1/email/preferences", json={"marketing": True}, headers=auth_headers)
    assert r.json() == {"marketing": True}


def test_only_marketing_mail_claims_one_click():
    """RFC 8058: One-Click exige una URL https; antes todos los correos lo
    anunciaban con un mailto."""
    plain = email_service._unsubscribe_headers(None)
    assert plain == {"List-Unsubscribe": plain["List-Unsubscribe"]}
    assert plain["List-Unsubscribe"].startswith("<mailto:")
    marketing = email_service._unsubscribe_headers("https://api.example/u?token=t")
    assert marketing["List-Unsubscribe"].startswith("<https://api.example/u?token=t>")
    assert marketing["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"


def test_reactivation_mail_reaches_the_provider_with_the_unsubscribe_link(
    monkeypatch: pytest.MonkeyPatch,
):
    sent: list[dict[str, object]] = []
    monkeypatch.setattr(email_service, "resolve_provider", lambda: "resend")
    monkeypatch.setattr(
        email_service, "_send_resend",
        lambda to, subject, html, unsubscribe_url=None: sent.append(
            {"html": html, "unsubscribe_url": unsubscribe_url}
        ),
    )
    email_service.send_reactivation(
        to="ana@example.com", name="Ana", code="ABCD2345", credits=200,
        unsubscribe_url="https://api.example/u?token=t", lang="es",
    )
    [mail] = sent
    assert mail["unsubscribe_url"] == "https://api.example/u?token=t"
    assert 'href="https://api.example/u?token=t"' in str(mail["html"])
    assert "200 créditos" in str(mail["html"]) and "Yo → Cartera" in str(mail["html"])


# ── Retención de registros de seguridad (política de privacidad) ───────────


@pytest.mark.asyncio
async def test_security_logs_are_kept_90_days_and_fingerprints_30(db_session: AsyncSession):
    """La política publicada dice 90 días para IP y navegador de los inicios de
    sesión, la auditoría y las sesiones; 30 para las huellas del antifraude.
    Hasta el 2026-10-02 solo se borraban con la cuenta."""
    import hashlib

    from app.models.antifraud import DeviceFingerprint
    from app.models.auth import AuditLog, LoginAttempt, UserSession
    from app.services.periodic import purge_security_logs

    u = _user()
    db_session.add(u)
    await db_session.flush()
    old, recent = NOW - timedelta(days=91), NOW - timedelta(days=89)
    for when in (old, recent):
        db_session.add(LoginAttempt(email=u.email, ip="203.0.113.7", success=True, created_at=when))
        db_session.add(AuditLog(user_id=u.id, action="login_success", ip="203.0.113.7", timestamp=when))
        db_session.add(UserSession(
            user_id=u.id, fingerprint=hashlib.sha256(str(when).encode()).hexdigest(), ip="203.0.113.7",
            user_agent="UA", created_at=when, last_activity=when,
        ))
    db_session.add(DeviceFingerprint(user_id=u.id, fingerprint_hash="a" * 64, ip_hash="b" * 64, created_at=NOW - timedelta(days=31)))
    db_session.add(DeviceFingerprint(user_id=u.id, fingerprint_hash="c" * 64, ip_hash="d" * 64, created_at=NOW - timedelta(days=29)))
    await db_session.flush()

    deleted = await purge_security_logs(db_session, NOW)
    assert deleted == {"login_attempts": 1, "audit_log": 1, "user_sessions": 1, "device_fingerprints": 1}
    for model in (LoginAttempt, AuditLog, UserSession, DeviceFingerprint):
        assert len((await db_session.execute(select(model))).scalars().all()) == 1
    assert await purge_security_logs(db_session, NOW) == dict.fromkeys(deleted, 0)


def test_privacy_policy_states_the_retention_the_code_applies():
    """Si alguien cambia el plazo en el código y no en la política (o al revés),
    lo publicado deja de ser verdad."""
    import json
    from pathlib import Path

    from app.services.periodic import SECURITY_LOG_RETENTION_DAYS

    root = Path(__file__).resolve().parents[3]
    for lang in ("es", "en"):
        legal = json.loads((root / "frontend" / "src" / "i18n" / lang / "common.json").read_text(encoding="utf-8"))["legal"]
        assert str(SECURITY_LOG_RETENTION_DAYS) in legal["privacyRetentionSecurity"], lang
