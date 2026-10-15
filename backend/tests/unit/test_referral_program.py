"""Programa de referidos de punta a punta (ADR-35, ECONOMIA.md §3).

Registro con 200 créditos de bienvenida, activación con las cuatro condiciones
del §3.1, abono de 300 a los 7 días con tope de 10 al mes, hitos de la escalera
(1 mes de Pro, 6 meses de Pro Max, insignia «Embajador») y la pausa por fraude.
Hasta el 2026-10-01 nada de esto corría: `activate_referral` y
`credit_matured_referrals` solo los llamaban los tests.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.entitlements import effective_tier, user_meets_tier
from app.models.antifraud import FraudReviewQueue
from app.models.content import Module, Skill, Track
from app.models.economy import CreditLedger, CreditReasonEnum, Referral
from app.models.gamification import Badge
from app.models.session import StudySession
from app.models.user import User, UserBadge, UserSkillState
from app.schemas.user import UserRead
from app.services.economy import (
    REFERRAL_CREDITS,
    REFERRAL_MONTHLY_CAP,
    REFERRAL_WELCOME_CREDITS,
    CreditsService,
    ReferralService,
    grant_plan_time,
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
    }
    fields.update(kw)
    return User(**fields)


async def _module(db: AsyncSession, threshold: float = 0.7) -> list[str]:
    db.add(Track(id="trk_ref", name_es="T", name_en="T", order=1, icon="t", color="#000000"))
    db.add(
        Module(
            id="m_ref", track_id="trk_ref", name_es="M", name_en="M", order=1,
            description_es="", description_en="", min_mastery_to_unlock=threshold,
        )
    )
    ids = ["sk_ref1", "sk_ref2"]
    for i, sid in enumerate(ids):
        db.add(Skill(id=sid, module_id="m_ref", name_es=sid, name_en=sid, order=i))
    await db.flush()
    return ids


async def _ready_referred(db: AsyncSession, skills: list[str], **kw: object) -> User:
    """Un referido que cumple las cuatro condiciones del §3.1."""
    fields: dict[str, object] = {
        "email_verified": True, "onboarding_experience": 0, "max_streak": 3,
    }
    fields.update(kw)
    u = _user(**fields)
    db.add(u)
    for sid in skills:
        db.add(UserSkillState(user_id=u.id, skill_id=sid, p_known=0.9, attempts=5))
    await db.flush()
    return u


async def _refer(db: AsyncSession, referrer: User, referred: User) -> Referral:
    code = await ReferralService.get_or_create_referral_code(db, referrer.id)
    assert await ReferralService.register_referral(db, code, referred.id) == referrer.id
    await db.flush()
    return (
        await db.execute(select(Referral).where(Referral.referred_id == referred.id))
    ).scalar_one()


async def _status(db: AsyncSession, referral: Referral) -> str:
    await db.refresh(referral)
    return referral.status


# ── Registro y bienvenida ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_registration_gives_welcome_credits_that_expire_in_30_days(db_session: AsyncSession):
    referrer, referred = _user(), _user()
    db_session.add_all([referrer, referred])
    referral = await _refer(db_session, referrer, referred)

    assert referral.status == "pending"
    assert await CreditsService.get_balance(db_session, referred.id) == REFERRAL_WELCOME_CREDITS
    lot = (
        await db_session.execute(
            select(CreditLedger).where(CreditLedger.reason == CreditReasonEnum.REFERRAL_WELCOME.value)
        )
    ).scalar_one()
    expires = lot.expires_at.replace(tzinfo=UTC) if lot.expires_at.tzinfo is None else lot.expires_at
    assert timedelta(days=29) < expires - datetime.now(UTC) <= timedelta(days=30)


@pytest.mark.asyncio
async def test_balance_reports_the_first_lot_to_expire(
    client: AsyncClient, db_session: AsyncSession, user: User, auth_headers: dict[str, str]
):
    """El saldo decía siempre «caducan en 90 días»; la bienvenida caduca a los 30."""
    r = (await client.get("/api/v1/economy/balance", headers=auth_headers)).json()
    assert (r["balance"], r["expires_in_days"]) == (0, 0)

    await CreditsService.grant_credits(db_session, user.id, 100, "promo_code", ref_id="p")
    await CreditsService.grant_credits(
        db_session, user.id, REFERRAL_WELCOME_CREDITS, CreditReasonEnum.REFERRAL_WELCOME.value,
        ref_id="w", expires_in_days=30,
    )
    await db_session.commit()
    r = (await client.get("/api/v1/economy/balance", headers=auth_headers)).json()
    assert (r["balance"], r["expires_in_days"]) == (300, 30)

    # Gastado el lote de 30 días (FIFO: lo que caduca antes, primero), manda el de 90.
    assert await CreditsService.spend_fifo(db_session, user.id, 200, "spend_freeze", ref_id="f")
    await db_session.commit()
    r = (await client.get("/api/v1/economy/balance", headers=auth_headers)).json()
    assert (r["balance"], r["expires_in_days"]) == (100, 90)


@pytest.mark.asyncio
async def test_diagnostic_extends_welcome_credits_to_90_days(db_session: AsyncSession):
    skills = await _module(db_session)
    referrer = _user()
    db_session.add(referrer)
    referred = await _ready_referred(db_session, skills, email_verified=False)
    referral = await _refer(db_session, referrer, referred)

    await ReferralService.activate_ready_referrals(db_session, now=datetime.now(UTC))

    assert await _status(db_session, referral) == "pending"  # sin email no se activa…
    lot = (
        await db_session.execute(
            select(CreditLedger).where(CreditLedger.reason == CreditReasonEnum.REFERRAL_WELCOME.value)
        )
    ).scalar_one()
    expires = lot.expires_at.replace(tzinfo=UTC) if lot.expires_at.tzinfo is None else lot.expires_at
    assert expires - datetime.now(UTC) > timedelta(days=80)  # …pero el lote ya no caduca a los 30


@pytest.mark.asyncio
async def test_endpoint_registers_referral_before_email_is_verified(
    client: AsyncClient, db_session: AsyncSession, user: User, auth_headers: dict[str, str]
):
    """El fallo de antes: el onboarding llama aquí antes de que nadie abra el
    correo de verificación, y exigirlo perdía el referido (403 tragado)."""
    assert user.email_verified is False
    referrer = _user()
    db_session.add(referrer)
    await db_session.commit()
    code = await ReferralService.get_or_create_referral_code(db_session, referrer.id)
    await db_session.commit()

    r = await client.post(
        "/api/v1/economy/referral/activate", json={"referral_code": code}, headers=auth_headers
    )

    assert r.status_code == 200, r.text
    assert r.json()["activated"] is True
    status = (
        await db_session.execute(select(Referral.status).where(Referral.referred_id == user.id))
    ).scalar_one()
    assert status == "pending"


@pytest.mark.asyncio
async def test_referral_code_endpoint_persists_the_code(
    client: AsyncClient, db_session: AsyncSession, user: User, auth_headers: dict[str, str]
):
    """El endpoint no hacía commit: cada visita a la Cartera daba un código
    distinto y ninguno servía para registrarse."""
    first = (await client.get("/api/v1/economy/referral/code", headers=auth_headers)).json()["code"]
    # El cliente de test comparte sesión entre peticiones: el rollback hace de
    # «se cerró la sesión», que es lo que borraba el código sin commit.
    await db_session.rollback()
    second = (await client.get("/api/v1/economy/referral/code", headers=auth_headers)).json()["code"]
    assert first == second

    referred = _user()
    db_session.add(referred)
    await db_session.commit()
    assert await ReferralService.register_referral(db_session, first, referred.id) == user.id


# ── Activación: las cuatro condiciones ─────────────────────────────────────


@pytest.mark.asyncio
async def test_ready_referral_activates(db_session: AsyncSession):
    skills = await _module(db_session)
    referrer = _user()
    db_session.add(referrer)
    referral = await _refer(db_session, referrer, await _ready_referred(db_session, skills))

    assert await ReferralService.activate_ready_referrals(db_session, now=NOW) == 1
    assert await _status(db_session, referral) == "activated"
    assert await ReferralService.activate_ready_referrals(db_session, now=NOW) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("override", "missing"),
    [
        ({"email_verified": False}, "email_verified"),
        ({"onboarding_experience": None}, "diagnostic"),
        ({"max_streak": 2}, "streak"),
    ],
)
async def test_each_condition_blocks_activation(
    db_session: AsyncSession, override: dict[str, object], missing: str
):
    skills = await _module(db_session)
    referrer = _user()
    db_session.add(referrer)
    referred = await _ready_referred(db_session, skills, **override)
    referral = await _refer(db_session, referrer, referred)

    assert await ReferralService.activation_missing(db_session, referred) == [missing]
    assert await ReferralService.activate_ready_referrals(db_session, now=NOW) == 0
    assert await _status(db_session, referral) == "pending"


@pytest.mark.asyncio
async def test_module_counts_as_completed_with_the_apps_own_rule(db_session: AsyncSession):
    """Media de dominio de las skills del módulo ≥ min_mastery_to_unlock, la
    misma regla con la que Rutas lo pinta «completado»."""
    skills = await _module(db_session, threshold=0.7)
    u = _user()
    db_session.add(u)
    db_session.add(UserSkillState(user_id=u.id, skill_id=skills[0], p_known=0.99, attempts=9))
    await db_session.flush()
    assert await ReferralService.module_completed(db_session, u.id) is False  # (0.99 + 0) / 2

    db_session.add(UserSkillState(user_id=u.id, skill_id=skills[1], p_known=0.5, attempts=3))
    await db_session.flush()
    assert await ReferralService.module_completed(db_session, u.id) is True  # (0.99 + 0.5) / 2


@pytest.mark.asyncio
async def test_diagnostic_is_the_placement_for_those_sent_to_it(db_session: AsyncSession):
    """El onboarding solo manda a la prueba de nivel a quien ya programa."""
    beginner = _user(onboarding_experience=0)
    coder = _user(onboarding_experience=1)
    db_session.add_all([beginner, coder])
    await db_session.flush()
    assert await ReferralService.diagnostic_done(db_session, beginner) is True
    assert await ReferralService.diagnostic_done(db_session, coder) is False

    db_session.add(StudySession(user_id=coder.id, mode="placement"))  # empezada, sin terminar
    await db_session.flush()
    assert await ReferralService.diagnostic_done(db_session, coder) is False

    db_session.add(StudySession(user_id=coder.id, mode="placement", ended_at=NOW))
    await db_session.flush()
    assert await ReferralService.diagnostic_done(db_session, coder) is True


@pytest.mark.asyncio
async def test_velocity_over_five_a_week_goes_to_review(db_session: AsyncSession):
    skills = await _module(db_session)
    referrer = _user()
    db_session.add(referrer)
    referrals = [
        await _refer(db_session, referrer, await _ready_referred(db_session, skills))
        for _ in range(6)
    ]

    assert await ReferralService.activate_ready_referrals(db_session, now=datetime.now(UTC)) == 5
    assert [await _status(db_session, r) for r in referrals].count("pending") == 1
    queued = (
        await db_session.execute(
            select(func.count(FraudReviewQueue.id)).where(FraudReviewQueue.referrer_id == referrer.id)
        )
    ).scalar_one()
    assert queued == 1


# ── Abono, tope y escalera ─────────────────────────────────────────────────


async def _activated(db: AsyncSession, referrer: User, n: int, days_ago: int = 8) -> list[Referral]:
    out = []
    for _ in range(n):
        referred = _user()
        db.add(referred)
        await db.flush()
        referral = await _refer(db, referrer, referred)
        referral.status = "activated"
        referral.activated_at = NOW - timedelta(days=days_ago)
        out.append(referral)
    await db.flush()
    return out


@pytest.mark.asyncio
async def test_credit_waits_seven_days_then_pays_300(db_session: AsyncSession):
    referrer = _user()
    db_session.add(referrer)
    [young] = await _activated(db_session, referrer, 1, days_ago=6)

    assert await ReferralService.credit_matured_referrals(db_session, now=NOW) == 0
    young.activated_at = NOW - timedelta(days=7)
    await db_session.flush()
    assert await ReferralService.credit_matured_referrals(db_session, now=NOW) == 1
    assert await _status(db_session, young) == "credited"
    assert await CreditsService.get_balance(db_session, referrer.id) == REFERRAL_CREDITS
    assert await ReferralService.credit_matured_referrals(db_session, now=NOW) == 0  # una vez


@pytest.mark.asyncio
async def test_monthly_cap_of_ten_leaves_the_rest_for_next_month(db_session: AsyncSession):
    referrer = _user()
    db_session.add(referrer)
    referrals = await _activated(db_session, referrer, REFERRAL_MONTHLY_CAP + 1)

    assert await ReferralService.credit_matured_referrals(db_session, now=NOW) == REFERRAL_MONTHLY_CAP
    statuses = [await _status(db_session, r) for r in referrals]
    assert statuses.count("activated") == 1

    next_month = datetime(2026, 11, 2, tzinfo=UTC)
    assert await ReferralService.credit_matured_referrals(db_session, now=next_month) == 1


@pytest.mark.asyncio
async def test_third_credit_grants_a_month_of_pro(db_session: AsyncSession):
    referrer = _user()
    db_session.add(referrer)
    await _activated(db_session, referrer, 2)
    await ReferralService.credit_matured_referrals(db_session, now=NOW)
    await db_session.refresh(referrer)
    assert referrer.granted_tier is None

    await _activated(db_session, referrer, 1)
    await ReferralService.credit_matured_referrals(db_session, now=NOW)
    await db_session.refresh(referrer)
    assert referrer.granted_tier == "plus"
    until = referrer.granted_tier_expires_at
    until = until.replace(tzinfo=UTC) if until.tzinfo is None else until
    assert until == NOW + timedelta(days=30)


@pytest.mark.asyncio
async def test_tenth_credit_grants_six_months_of_pro_max(db_session: AsyncSession):
    referrer = _user()
    db_session.add(referrer)
    await _activated(db_session, referrer, 10)
    assert await ReferralService.credit_matured_referrals(db_session, now=NOW) == 10
    await db_session.refresh(referrer)
    assert referrer.granted_tier == "pro"  # Pro Max (ADR-41)
    until = referrer.granted_tier_expires_at
    until = until.replace(tzinfo=UTC) if until.tzinfo is None else until
    assert until == NOW + timedelta(days=183)


@pytest.mark.asyncio
async def test_twenty_fifth_credit_awards_the_ambassador_badge(db_session: AsyncSession):
    db_session.add(
        Badge(
            id="ambassador", name_es="Embajador", name_en="Ambassador", icon="🤝",
            description_es="", description_en="",
            criteria_type="referrals_credited", criteria_value=25,
        )
    )
    referrer = _user()
    db_session.add(referrer)
    await _activated(db_session, referrer, 24)
    for month in (NOW, datetime(2026, 11, 2, tzinfo=UTC), datetime(2026, 12, 2, tzinfo=UTC)):
        await ReferralService.credit_matured_referrals(db_session, now=month)
    assert not (await db_session.execute(select(UserBadge).where(UserBadge.user_id == referrer.id))).first()

    await _activated(db_session, referrer, 1)
    await ReferralService.credit_matured_referrals(db_session, now=datetime(2026, 12, 3, tzinfo=UTC))
    badge = (
        await db_session.execute(select(UserBadge.badge_id).where(UserBadge.user_id == referrer.id))
    ).scalar_one()
    assert badge == "ambassador"


@pytest.mark.asyncio
async def test_deleted_referred_account_is_rejected_not_paid(db_session: AsyncSession):
    referrer = _user()
    db_session.add(referrer)
    [referral] = await _activated(db_session, referrer, 1)
    referred = await db_session.get(User, referral.referred_id)
    referred.is_active = False
    await db_session.flush()

    assert await ReferralService.credit_matured_referrals(db_session, now=NOW) == 0
    assert await _status(db_session, referral) == "rejected"
    assert await CreditsService.get_balance(db_session, referrer.id) == 0


# ── Tiempo de plan ganado frente al plan de pago ──────────────────────────


def test_same_plan_extends_and_a_higher_one_replaces_without_shortening():
    u = _user()
    grant_plan_time(u, "plus", 30, NOW)
    grant_plan_time(u, "plus", 30, NOW)
    assert (u.granted_tier, u.granted_tier_expires_at) == ("plus", NOW + timedelta(days=60))
    grant_plan_time(u, "pro", 10, NOW)
    assert (u.granted_tier, u.granted_tier_expires_at) == ("pro", NOW + timedelta(days=60))


def test_grant_and_paid_plan_take_the_higher_and_survive_each_other():
    u = _user(is_premium=True, subscription_tier="plus", subscription_status="active")
    grant_plan_time(u, "pro", 30, datetime.now(UTC))
    assert effective_tier(u) == "pro" and user_meets_tier(u, "pro")

    # Un webhook de cancelación limpia la suscripción: el plan ganado sigue.
    u.is_premium, u.subscription_tier = False, None
    assert user_meets_tier(u, "pro")

    # Y al caducar el plan ganado, vuelve a free sin tocar nada más.
    u.granted_tier_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    assert effective_tier(u) == "free" and u.active_granted_tier is None


@pytest.mark.asyncio
async def test_user_read_keeps_paid_premium_apart_from_the_grant(db_session: AsyncSession):
    """`is_premium` es el plan de pago: el checkout lo usa para decir «ya tienes
    suscripción» y para dar por llegado un pago. Si incluyera el plan ganado,
    quien lo tiene no podría pagar y el sondeo tras pagar acertaría antes del
    cobro. El plan ganado sale aparte, y solo en fecha."""
    u = _user()
    grant_plan_time(u, "plus", 30, datetime.now(UTC))
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)

    read = UserRead.model_validate(u)
    assert read.is_premium is False
    assert read.granted_tier == "plus" and read.granted_tier_expires_at is not None

    u.granted_tier_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    read = UserRead.model_validate(u)
    assert (read.granted_tier, read.granted_tier_expires_at) == (None, None)


# ── Pausa (§3.5) ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_manual_pause_stops_activation_and_payout(db_session: AsyncSession, monkeypatch):
    skills = await _module(db_session)
    referrer = _user()
    db_session.add(referrer)
    pending = await _refer(db_session, referrer, await _ready_referred(db_session, skills))
    [matured] = await _activated(db_session, referrer, 1)
    monkeypatch.setattr(settings, "REFERRALS_PAUSED", True)

    assert await ReferralService.activate_ready_referrals(db_session, now=NOW) == 0
    assert await ReferralService.credit_matured_referrals(db_session, now=NOW) == 0
    assert await _status(db_session, pending) == "pending"
    assert await _status(db_session, matured) == "activated"


@pytest.mark.asyncio
async def test_fraud_over_five_percent_two_weeks_running_pauses_the_program(db_session: AsyncSession):
    referrer = _user()
    db_session.add(referrer)
    await db_session.flush()
    now = datetime.now(UTC)
    for weeks_ago in (0, 1):
        when = now - timedelta(days=7 * weeks_ago + 1)
        for _ in range(10):
            referred = _user()
            db_session.add(referred)
            db_session.add(
                Referral(referrer_id=referrer.id, referred_id=referred.id, created_at=when)
            )
        db_session.add(
            FraudReviewQueue(referrer_id=referrer.id, reason="velocity_exceeded",
                             activation_count=6, created_at=when)
        )
    await db_session.flush()
    # 1 de 10 = 10 % las dos semanas → pausa
    assert await ReferralService.program_paused(db_session, now) is True

    # Una sola semana por encima no basta
    old = (
        await db_session.execute(
            select(FraudReviewQueue).where(FraudReviewQueue.created_at < now - timedelta(days=7))
        )
    ).scalar_one()
    await db_session.delete(old)
    await db_session.flush()
    assert await ReferralService.program_paused(db_session, now) is False


# ── Clawback (§3.5) ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_clawback_recovers_the_300_and_closes_the_referral(db_session: AsyncSession):
    referrer = _user()
    db_session.add(referrer)
    [referral] = await _activated(db_session, referrer, 1)
    await ReferralService.credit_matured_referrals(db_session, now=NOW)
    assert await CreditsService.get_balance(db_session, referrer.id) == REFERRAL_CREDITS

    result = await ReferralService.clawback(db_session, referral.id, "fraud", now=NOW)
    assert (result["recovered_credits"], result["unrecovered_credits"]) == (300, 0)
    assert await _status(db_session, referral) == "clawed_back"
    assert await CreditsService.get_balance(db_session, referrer.id) == 0
    with pytest.raises(ValueError, match="already_closed"):
        await ReferralService.clawback(db_session, referral.id, "fraud", now=NOW)


@pytest.mark.asyncio
async def test_clawback_never_leaves_a_negative_balance(db_session: AsyncSession):
    """Lo ya gastado no se recupera como deuda: se cobraría de premios futuros
    sin que el usuario lo vea."""
    referrer = _user()
    db_session.add(referrer)
    [referral] = await _activated(db_session, referrer, 1)
    await ReferralService.credit_matured_referrals(db_session, now=NOW)
    assert await CreditsService.spend_fifo(db_session, referrer.id, 200, "spend_freeze", ref_id="f")

    result = await ReferralService.clawback(db_session, referral.id, "refund", now=NOW)
    assert (result["recovered_credits"], result["unrecovered_credits"]) == (100, 200)
    assert await CreditsService.get_balance(db_session, referrer.id) == 0
    await CreditsService.grant_credits(db_session, referrer.id, 50, "promo_code", ref_id="later")
    assert await CreditsService.get_balance(db_session, referrer.id) == 50


@pytest.mark.asyncio
async def test_clawback_recalculates_the_ladder_without_paying_a_milestone_twice(db_session: AsyncSession):
    referrer = _user()
    db_session.add(referrer)
    referrals = await _activated(db_session, referrer, 3)
    await ReferralService.credit_matured_referrals(db_session, now=NOW)
    await db_session.refresh(referrer)
    assert referrer.granted_tier == "plus"

    result = await ReferralService.clawback(db_session, referrals[0].id, "ban", now=NOW)
    assert result["milestone_revoked"] == "pro_month"
    await db_session.refresh(referrer)
    assert referrer.granted_tier is None  # bajó de 3 abonados: el mes de Pro se va

    # Un abono nuevo vuelve a llegar a 3: un mes, no dos.
    await _activated(db_session, referrer, 1)
    await ReferralService.credit_matured_referrals(db_session, now=NOW)
    await db_session.refresh(referrer)
    until = referrer.granted_tier_expires_at
    until = until.replace(tzinfo=UTC) if until.tzinfo is None else until
    assert (referrer.granted_tier, until) == ("plus", NOW + timedelta(days=30))


@pytest.mark.asyncio
async def test_activated_but_not_credited_is_closed_without_touching_credits(db_session: AsyncSession):
    referrer = _user()
    db_session.add(referrer)
    [referral] = await _activated(db_session, referrer, 1, days_ago=2)
    result = await ReferralService.clawback(db_session, referral.id, "fraud", now=NOW)
    assert (result["recovered_credits"], result["unrecovered_credits"]) == (0, 0)
    assert await _status(db_session, referral) == "clawed_back"
    # Ya no madura: no se abona nunca.
    assert await ReferralService.credit_matured_referrals(db_session, now=NOW + timedelta(days=30)) == 0


@pytest.mark.asyncio
async def test_admin_clawback_endpoint(client: AsyncClient, db_session: AsyncSession):
    from app.core.security import create_access_token

    admin, plain, referrer = _user(role="owner"), _user(), _user()
    db_session.add_all([admin, plain, referrer])
    [referral] = await _activated(db_session, referrer, 1)
    await ReferralService.credit_matured_referrals(db_session, now=NOW)
    await db_session.commit()
    url = f"/api/v1/admin/economy/referrals/{referral.id}/clawback"

    def auth(u: User) -> dict[str, str]:
        return {"Authorization": f"Bearer {create_access_token(u.id)}"}

    assert (await client.post(url, json={"reason": "fraud"}, headers=auth(plain))).status_code == 403
    assert (await client.post(url, json={"reason": "whim"}, headers=auth(admin))).status_code == 422
    r = await client.post(url, json={"reason": "fraud"}, headers=auth(admin))
    assert r.status_code == 200 and r.json()["recovered_credits"] == 300
    assert (await client.post(url, json={"reason": "fraud"}, headers=auth(admin))).status_code == 409
    missing = f"/api/v1/admin/economy/referrals/{uuid.uuid4()}/clawback"
    assert (await client.post(missing, json={"reason": "fraud"}, headers=auth(admin))).status_code == 404
    listed = (await client.get("/api/v1/admin/economy/referrals?status=clawed_back", headers=auth(admin))).json()
    assert [x["id"] for x in listed["referrals"]] == [str(referral.id)]
