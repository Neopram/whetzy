"""Trabajos periódicos del backend: lo que tiene que pasar sin que nadie lo pida.

Hasta el 2026-10-01 tres de ellos existían como funciones y nadie los ejecutaba:

- el **recordatorio de renovación** 7 días antes, que prometen los Términos
  publicados (`legal.termsP6renewal`); `send_renewal_reminder` no la llamaba nadie;
- la **liquidación mensual a instructores** del día 15, programada con APScheduler,
  que no está en `requirements.txt`: el `ImportError` lo dejaba en un aviso del log
  (y el job que encolaba llevaba un `user_id` inventado que la FK de `jobs` rechaza);
- el **correo de reactivación** a los 14 días de inactividad (29.7): el handler
  `reactivation_check` existía y nada encolaba ese job.

`periodic_jobs_loop` corre cada hora, un solo worker por vuelta (advisory lock,
como `referral_program_loop`). Cada trabajo es idempotente por su cuenta: correrlo
dos veces en la misma hora no manda dos correos ni liquida dos veces.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User

logger = logging.getLogger("whetzy.periodic")

PERIODIC_LOOP_SECONDS = 3600
_PERIODIC_LOCK_KEY = 290_304

# Recordatorio de renovación: «al menos 7 días antes» (Términos). Se manda en
# cuanto el fin de periodo entra en la ventana de 7 días; la vuelta es horaria.
RENEWAL_NOTICE_DAYS = 7
# Solo los raíles web: App Store y Google Play avisan ellos de sus renovaciones.
RENEWAL_PROVIDERS = ("paddle", "stripe")

# Reactivación (ECONOMIA §2.2): 200 créditos que caducan en 72 h, uno cada 60 días.
REACTIVATION_INACTIVE_DAYS = 14
REACTIVATION_CREDITS = 200
REACTIVATION_CODE_HOURS = 72
REACTIVATION_EVERY_DAYS = 60

# Caducidad de créditos (ECONOMIA §2.4): aviso 7 días antes si caducan ≥ 200.
CREDIT_EXPIRY_NOTICE_DAYS = 7
CREDIT_EXPIRY_NOTICE_MIN = 200

# Retención publicada en la política de privacidad (legal.privacyRetentionSecurity):
# IP y navegador de inicios de sesión, auditoría y sesiones, 90 días; las huellas
# del antifraude de referidos, 30 (docs/legal/antifraud-legal-basis.md).
SECURITY_LOG_RETENTION_DAYS = 90
DEVICE_FINGERPRINT_RETENTION_DAYS = 30

# Liquidación a instructores: el día 15 de cada mes (MARKETPLACE.md), mínimo 50 €.
PAYOUT_DAY = 15
PAYOUT_MIN_CENTS = 5000


def _aware(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def _plan_name(tier: str | None) -> str:
    return {"plus": "Pro", "pro": "Pro Max", "creator": "Creador"}.get(tier or "", "Pro")


def _plan_amount(tier: str | None) -> str:
    price = {
        "plus": settings.PLAN_PRICE_PLUS_USD,
        "pro": settings.PLAN_PRICE_PRO_USD,
        "creator": settings.PLAN_PRICE_CREATOR_USD,
    }.get(tier or "", settings.PLAN_PRICE_PLUS_USD)
    return f"{price:.2f} $"


def _format_date(moment: datetime, lang: str) -> str:
    months = {
        "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
               "septiembre", "octubre", "noviembre", "diciembre"],
        "en": ["January", "February", "March", "April", "May", "June", "July", "August",
               "September", "October", "November", "December"],
    }
    if lang == "en":
        return f"{months['en'][moment.month - 1]} {moment.day}, {moment.year}"
    return f"{moment.day} de {months['es'][moment.month - 1]} de {moment.year}"


async def send_renewal_reminders(db: AsyncSession, now: datetime | None = None) -> int:
    """Un correo por periodo a cada suscripción web activa que se renueva en
    ≤ 7 días. Una cancelada al final del periodo queda en `canceled` y no se
    avisa de una renovación que no va a pasar. Returns the number sent."""
    from app.services.email import send_renewal_reminder

    now = now or datetime.now(UTC)
    due = (
        await db.execute(
            select(User).where(
                and_(
                    User.is_active.is_(True),
                    User.subscription_status == "active",
                    User.subscription_provider.in_(RENEWAL_PROVIDERS),
                    User.subscription_expires_at > now,
                    User.subscription_expires_at <= now + timedelta(days=RENEWAL_NOTICE_DAYS),
                )
            )
        )
    ).scalars().all()
    sent = 0
    for user in due:
        period_end = _aware(user.subscription_expires_at)  # type: ignore[arg-type]
        already = user.renewal_reminder_for
        if already is not None and _aware(already) == period_end:
            continue
        lang = user.language if user.language in ("es", "en") else "es"
        send_renewal_reminder(
            to=user.email,
            name=user.display_name,
            plan_name=_plan_name(user.subscription_tier),
            renewal_date=_format_date(period_end, lang),
            amount=_plan_amount(user.subscription_tier),
            lang=lang,
        )
        user.renewal_reminder_for = period_end
        sent += 1
    if sent:
        await db.flush()
    return sent


async def send_reactivation_offers(db: AsyncSession, now: datetime | None = None) -> int:
    """Código de 200 créditos (72 h) a quien lleva ≥ 14 días sin estudiar, uno
    cada 60 días. Es marketing: solo a emails verificados y a quien no se ha dado
    de baja, y lleva enlace de baja de un clic. Returns the number sent."""
    from app.core.security import create_unsubscribe_token
    from app.models.economy import PromoCode
    from app.services.economy import PromoCodeService
    from app.services.email import send_reactivation

    now = now or datetime.now(UTC)
    cutoff = now - timedelta(days=REACTIVATION_INACTIVE_DAYS)
    inactive = (
        await db.execute(
            select(User).where(
                User.is_active.is_(True),
                User.email_verified.is_(True),
                User.marketing_emails_opt_out.is_(False),
                User.created_at < cutoff,
                (User.last_active < cutoff) | (User.last_active.is_(None)),
            )
        )
    ).scalars().all()
    if not inactive:
        return 0
    # campaign_id guarda el usuario destinatario: así se deduplica (29.7).
    recent = set(
        (
            await db.execute(
                select(PromoCode.campaign_id).where(
                    PromoCode.code_type == "reactivation",
                    PromoCode.created_at > now - timedelta(days=REACTIVATION_EVERY_DAYS),
                    PromoCode.campaign_id.is_not(None),
                )
            )
        ).scalars().all()
    )
    sent = 0
    for user in inactive:
        if str(user.id) in recent:
            continue
        codes = await PromoCodeService.generate_batch(
            db,
            code_type="reactivation",
            credits=REACTIVATION_CREDITS,
            count=1,
            max_uses=1,
            expires_at=now + timedelta(hours=REACTIVATION_CODE_HOURS),
            campaign_id=str(user.id),
            created_by="reactivation_job",
        )
        token = create_unsubscribe_token(user.id)
        send_reactivation(
            to=user.email,
            name=user.display_name,
            code=codes[0].code,
            credits=REACTIVATION_CREDITS,
            unsubscribe_url=f"{settings.API_PUBLIC_BASE_URL}{settings.API_V1_PREFIX}/email/unsubscribe?token={token}",
            lang=user.language if user.language in ("es", "en") else "es",
        )
        sent += 1
    if sent:
        await db.flush()
    return sent


async def expire_credits(db: AsyncSession, now: datetime | None = None) -> int:
    from app.services.economy import CreditsService

    return await CreditsService.expire_old_credits(db, now)


async def send_credit_expiry_warnings(db: AsyncSession, now: datetime | None = None) -> int:
    """Un correo por fecha de caducidad a quien pierde ≥ 200 créditos en los
    próximos 7 días (§2.4). Es retención: emails verificados, sin baja, con enlace
    de baja de un clic. Returns the number sent."""
    from app.core.security import create_unsubscribe_token
    from app.services.economy import CreditsService
    from app.services.email import send_credit_expiry_warning

    now = now or datetime.now(UTC)
    lots = await CreditsService.lots_with_remaining(
        db, expires_after=now, expires_before=now + timedelta(days=CREDIT_EXPIRY_NOTICE_DAYS)
    )
    per_user: dict[Any, tuple[int, datetime]] = {}
    for lot, remaining in lots:
        total, first = per_user.get(lot.user_id, (0, _aware(lot.expires_at)))  # type: ignore[arg-type]
        per_user[lot.user_id] = (total + remaining, min(first, _aware(lot.expires_at)))  # type: ignore[arg-type]
    sent = 0
    for user_id, (credits, first) in per_user.items():
        if credits < CREDIT_EXPIRY_NOTICE_MIN:
            continue
        user = await db.get(User, user_id)
        if (
            user is None
            or not user.is_active
            or not user.email_verified
            or user.marketing_emails_opt_out
        ):
            continue
        warned = user.credit_expiry_warned_for
        if warned is not None and _aware(warned) == first:
            continue
        lang = user.language if user.language in ("es", "en") else "es"
        token = create_unsubscribe_token(user.id)
        send_credit_expiry_warning(
            to=user.email,
            name=user.display_name,
            credits=credits,
            expiry_date=_format_date(first, lang),
            unsubscribe_url=f"{settings.API_PUBLIC_BASE_URL}{settings.API_V1_PREFIX}/email/unsubscribe?token={token}",
            lang=lang,
        )
        user.credit_expiry_warned_for = first
        sent += 1
    if sent:
        await db.flush()
    return sent


async def purge_security_logs(db: AsyncSession, now: datetime | None = None) -> dict[str, int]:
    """Borra lo que la política de privacidad dice que no se guarda más de 90
    días (30 las huellas del antifraude). Hasta el 2026-10-02 estas tablas solo
    se vaciaban al borrar la cuenta: la IP de cada inicio de sesión se quedaba
    para siempre."""
    from sqlalchemy import delete

    from app.models.antifraud import DeviceFingerprint
    from app.models.auth import AuditLog, LoginAttempt, UserSession

    now = now or datetime.now(UTC)
    cutoff = now - timedelta(days=SECURITY_LOG_RETENTION_DAYS)
    fp_cutoff = now - timedelta(days=DEVICE_FINGERPRINT_RETENTION_DAYS)
    deleted = {}
    for name, stmt in (
        ("login_attempts", delete(LoginAttempt).where(LoginAttempt.created_at < cutoff)),
        ("audit_log", delete(AuditLog).where(AuditLog.timestamp < cutoff)),
        # Una sesión vive como mucho 30 días (REFRESH_TOKEN_EXPIRE_DAYS): con 90
        # sin actividad ya no hay nada que mostrar ni que cerrar.
        ("user_sessions", delete(UserSession).where(UserSession.last_activity < cutoff)),
        ("device_fingerprints", delete(DeviceFingerprint).where(DeviceFingerprint.created_at < fp_cutoff)),
    ):
        result = await db.execute(stmt)
        deleted[name] = int(getattr(result, "rowcount", 0) or 0)
    # El clic de campaña cuenta para siempre; el navegador y la página de origen
    # que lo acompañan, no: sobrevivían incluso al borrado de la cuenta.
    from sqlalchemy import update

    from app.models.campaign import CampaignClick

    result = await db.execute(
        update(CampaignClick)
        .where(
            CampaignClick.created_at < cutoff,
            (CampaignClick.user_agent.is_not(None)) | (CampaignClick.referrer.is_not(None)),
        )
        .values(user_agent=None, referrer=None)
        .execution_options(synchronize_session="fetch")
    )
    deleted["campaign_clicks_browser"] = int(getattr(result, "rowcount", 0) or 0)
    return deleted


async def process_monthly_payouts(db: AsyncSession, now: datetime | None = None) -> dict[str, int]:
    """El día 15 pasa a `processing` las liquidaciones pendientes de ≥ 50 €
    (28.7); el pago lo hace el dueño desde esa lista. Fuera del día 15 no hace
    nada, y el día 15 lo ya pasado a `processing` no vuelve a contar."""
    from app.models.instructor import InstructorPayout

    now = now or datetime.now(UTC)
    if now.day != PAYOUT_DAY:
        return {"processed_count": 0, "total_paid_cents": 0, "filtered_out_count": 0}
    pending = (
        await db.execute(
            select(InstructorPayout)
            .where(InstructorPayout.status == "pending", InstructorPayout.earnings_cents > 0)
            .order_by(InstructorPayout.instructor_id)
        )
    ).scalars().all()
    valid = [p for p in pending if p.earnings_cents >= PAYOUT_MIN_CENTS]
    for payout in valid:
        payout.status = "processing"
    if valid:
        await db.flush()
        logger.info(
            "Liquidación del día %d: %d instructores, %.2f €",
            PAYOUT_DAY, len(valid), sum(p.earnings_cents for p in valid) / 100,
        )
    return {
        "processed_count": len(valid),
        "total_paid_cents": sum(p.earnings_cents for p in valid),
        "filtered_out_count": len(pending) - len(valid),
    }


async def _learning_credits(db: AsyncSession, now: datetime | None = None) -> int:
    from app.services.learning_rewards import award_recently_active

    return await award_recently_active(db, now)


async def _try_lock(lock_db: AsyncSession) -> bool:
    """Lock de sesión en una conexión aparte, sin commit hasta soltarlo: el
    trabajo hace commit tras cada tarea y un lock de transacción se soltaría en
    el primero. En SQLite (tests) no hay workers que coordinar."""
    if lock_db.get_bind().dialect.name != "postgresql":
        return True
    got = await lock_db.execute(select(func.pg_try_advisory_lock(_PERIODIC_LOCK_KEY)))
    return bool(got.scalar())


async def _unlock(lock_db: AsyncSession) -> None:
    if lock_db.get_bind().dialect.name == "postgresql":
        await lock_db.execute(select(func.pg_advisory_unlock(_PERIODIC_LOCK_KEY)))


async def run_periodic_jobs(db: AsyncSession, now: datetime | None = None) -> dict[str, Any]:
    """Una vuelta: cada trabajo en su propia transacción, para que el fallo de
    uno no deshaga lo que ya hizo otro (un correo enviado no se «des-envía»)."""
    results: dict[str, Any] = {}
    for name, job in (
        ("renewal_reminders", send_renewal_reminders),
        ("reactivation_offers", send_reactivation_offers),
        ("payouts", process_monthly_payouts),
        ("credits_expired", expire_credits),
        ("credit_expiry_warnings", send_credit_expiry_warnings),
        ("security_log_retention", purge_security_logs),
        ("learning_credits", _learning_credits),
    ):
        try:
            results[name] = await job(db, now)
            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception("periodic job %s failed", name)
            results[name] = "error"
    return results


async def periodic_jobs_loop(
    db_factory: Callable[..., Any], interval_seconds: int = PERIODIC_LOOP_SECONDS
) -> None:
    """Bucle de fondo, una vuelta por hora. Con varios workers de gunicorn
    corre uno por proceso, pero solo uno entra en cada vuelta."""
    while True:
        try:
            async with db_factory() as lock_db:
                if await _try_lock(lock_db):
                    try:
                        async with db_factory() as db:
                            results = await run_periodic_jobs(db)
                        logger.info("periodic_jobs_loop %s", results)
                    finally:
                        await _unlock(lock_db)
                await lock_db.commit()
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            break
        except Exception:  # el bucle sobrevive a cualquier error
            logger.exception("periodic_jobs_loop error")
            await asyncio.sleep(interval_seconds)
