"""Borrado de cuenta con 30 días de gracia (ledger 19.12).

Lo que prometen los textos legales publicados (whetzy.com/privacy §4, claves
i18n `legal.privacyP4`; ADR-55) y la pantalla `/delete-account`:

- Pedir el borrado desactiva la cuenta al momento («eliminación suave»).
- Durante 30 días es un periodo de gracia: volver a iniciar sesión la recupera.
- A los 30 días los datos de la cuenta se eliminan de forma permanente.

La solicitud vive en `gdpr_requests` (`request_type="deletion"`), la misma tabla
que ya lista el panel de administración (`/admin/gdpr/deletions`): `pending`
mientras corre la gracia, `cancelled` si el alumno vuelve, `completed` al purgar.

Purgar no borra la fila de `users`: diez tablas la referencian sin
`ON DELETE CASCADE` (registros económicos, de pago y antifraude), y un DELETE
fallaría en Postgres en cuanto existiera una sola de esas filas. En su lugar se
borran los datos personales y de aprendizaje del alumno y la fila de `users` se
anonimiza de forma irreversible (sin email, sin nombre, sin contraseña). Lo que
queda —apuntes económicos y de pago, duelos que también son de otro alumno,
el propio registro de la solicitud— ya no se puede asociar a una persona.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import Base
from app.models.admin import GDPRRequest
from app.models.auth import LoginAttempt
from app.models.user import User
from app.services import paddle_billing

logger = logging.getLogger("whetzy")

GRACE_PERIOD = timedelta(days=30)
PURGE_INTERVAL_SECONDS = 6 * 60 * 60

# Datos personales o de aprendizaje del alumno: se borran al purgar. Los hijos
# van antes que sus padres (certificates → mock_exam_attempts) para no depender
# de que la base tenga el CASCADE que declara el modelo.
_OWNED_TABLES: tuple[str, ...] = (
    "certificates",
    "mock_exam_attempts",
    "user_skill_states",
    "user_badges",
    "user_missions",
    "league_entries",
    "lesson_completions",
    "lesson_views",
    "experiment_assignments",
    "project_submissions",
    "bootcamp_enrollments",
    "instructor_enrollments",
    "question_reports",
    "tutor_usage",
    "jobs",
    "push_subscriptions",
    "oauth_accounts",
    "refresh_tokens",
    "user_sessions",
    "user_2fa",
    "email_verification_tokens",
    "password_reset_tokens",
    "device_fingerprints",
    "mastery_reports",
)

# Trazas que se conservan pero dejan de apuntar a la persona.
_DETACHED_TABLES: tuple[str, ...] = ("analytics_events", "audit_log", "campaign_clicks")

# Se conservan a propósito: con la fila de `users` anonimizada ya no señalan a
# nadie, y su existencia es obligación contable o es también de otra persona.
# `test_every_table_pointing_at_users_is_classified` exige que toda tabla con
# clave a `users` esté en una de estas listas o en `_purge_user`.
_KEPT_TABLES: dict[str, str] = {
    "certification_purchases": "registro de pago",
    "credit_ledger": "registro económico",
    "credit_expense_caps": "registro económico",
    "paddle_subscriptions": "registro de pago",
    "stripe_customers": "registro de pago",
    "promo_code_redemptions": "registro económico",
    "referral_codes": "registro económico",
    "referrals": "registro económico de dos personas",
    "fraud_review_queue": "antifraude",
    "duels": "también es del otro alumno",
    "gdpr_requests": "prueba de que la solicitud se cumplió",
}
_HANDLED_IN_PURGE: frozenset[str] = frozenset(
    {"responses", "study_sessions", "user_blocks", "user_reports", "instructors"}
)


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(ts: datetime) -> datetime:
    """SQLite devuelve fechas sin zona; Postgres, con ella."""
    return ts if ts.tzinfo is not None else ts.replace(tzinfo=UTC)


async def _pending_request(db: AsyncSession, user_id: uuid.UUID) -> GDPRRequest | None:
    result = await db.execute(
        select(GDPRRequest)
        .where(
            GDPRRequest.user_id == user_id,
            GDPRRequest.request_type == "deletion",
            GDPRRequest.status == "pending",
        )
        .order_by(GDPRRequest.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def request_deletion(db: AsyncSession, user: User) -> datetime:
    """Desactiva la cuenta y abre (o reutiliza) la solicitud de borrado.

    Devuelve la fecha a partir de la cual se purgará. Invalida los tokens
    emitidos (`jwt_version`) para que la sesión abierta deje de valer ya.
    """
    pending = await _pending_request(db, user.id)
    if pending is None:
        pending = GDPRRequest(user_id=user.id, request_type="deletion", status="pending")
        db.add(pending)
        await db.flush()
        await db.refresh(pending)
    user.is_active = False
    user.jwt_version += 1
    await db.execute(
        update(Base.metadata.tables["refresh_tokens"])
        .where(Base.metadata.tables["refresh_tokens"].c.user_id == user.id)
        .values(revoked=True)
    )
    await db.commit()
    if user.paddle_subscription_id and user.subscription_provider == "paddle":
        # Sin más cobros durante la gracia: se cancela al final del periodo ya
        # pagado. Si Paddle no responde, el borrado sigue (queda en el log).
        await paddle_billing.cancel_subscription(user.paddle_subscription_id)
    return _aware(pending.created_at) + GRACE_PERIOD


async def restore_if_pending(
    db: AsyncSession, user: User, now: datetime | None = None
) -> bool:
    """Si la cuenta está en su periodo de gracia, la recupera y devuelve True.

    Una cuenta desactivada por otro motivo (suspensión) o cuya gracia ya venció
    no se toca: devuelve False y el login sigue denegado.
    """
    if user.is_active:
        return False
    pending = await _pending_request(db, user.id)
    if pending is None:
        return False
    now = now or _now()
    if _aware(pending.created_at) + GRACE_PERIOD <= now:
        return False
    pending.status = "cancelled"
    pending.completed_at = now
    user.is_active = True
    await db.commit()
    logger.info("account_deletion_cancelled user=%s", user.id)
    return True


async def _purge_user(db: AsyncSession, user: User, now: datetime) -> None:
    uid = user.id
    tables = Base.metadata.tables

    responses = tables["responses"]
    sessions = tables["study_sessions"]
    await db.execute(
        delete(responses).where(
            responses.c.session_id.in_(select(sessions.c.id).where(sessions.c.user_id == uid))
        )
    )
    await db.execute(delete(sessions).where(sessions.c.user_id == uid))
    for name in _OWNED_TABLES:
        table = tables[name]
        await db.execute(delete(table).where(table.c.user_id == uid))
    for name in _DETACHED_TABLES:
        table = tables[name]
        await db.execute(update(table).where(table.c.user_id == uid).values(user_id=None))
    await db.execute(delete(LoginAttempt).where(LoginAttempt.email == user.email))
    blocks = tables["user_blocks"]
    await db.execute(
        delete(blocks).where((blocks.c.blocker_id == uid) | (blocks.c.blocked_id == uid))
    )
    # Lo que el alumno denunció lo escribió él; lo denunciado sobre él es de
    # moderación y sin la persona ya no identifica a nadie.
    reports = tables["user_reports"]
    await db.execute(delete(reports).where(reports.c.reporter_id == uid))
    # La ficha de instructor la referencian cursos y liquidaciones: se queda la
    # fila y se borra lo que describe a la persona.
    instructors = tables["instructors"]
    await db.execute(
        update(instructors)
        .where(instructors.c.user_id == uid)
        .values(display_name="—", bio=None, avatar_url=None, website=None)
    )

    user.email = f"deleted-{uid.hex}@deleted.invalid"
    user.username = f"deleted_{uid.hex[:16]}"
    user.display_name = "—"
    user.avatar_emoji = "👤"
    user.hashed_password = None
    user.email_verified = False
    user.is_active = False
    user.jwt_version += 1
    user.stripe_customer_id = None
    user.stripe_subscription_id = None
    user.paddle_subscription_id = None
    user.is_premium = False
    user.subscription_status = None
    user.subscription_tier = None
    user.subscription_expires_at = None
    user.subscription_provider = None
    user.eu_withdrawal_waiver_at = None
    user.last_active = None
    user.last_streak_reminder_at = None
    user.push_streak_enabled = False
    user.leagues_opt_out = True
    user.onboarding_experience = None
    user.onboarding_goal = None
    user.onboarding_weekly_time = None
    user.target_track_id = None
    user.signup_source = None
    user.signup_campaign = None
    user.total_xp = 0
    user.level = 1
    user.current_streak = 0
    user.max_streak = 0


async def purge_due(db: AsyncSession, now: datetime | None = None) -> int:
    """Purga las cuentas cuya gracia venció. Devuelve cuántas purgó.

    Idempotente y segura con varios procesos a la vez: una solicitud ya
    `completed` no se vuelve a tocar, y cada cuenta va en su propio savepoint
    para que un fallo en una no deje a medias ni bloquee a las demás.
    """
    now = now or _now()
    cutoff = now - GRACE_PERIOD
    rows = (
        await db.execute(
            select(GDPRRequest).where(
                GDPRRequest.request_type == "deletion",
                GDPRRequest.status == "pending",
            )
        )
    ).scalars().all()

    purged = 0
    for request in rows:
        if _aware(request.created_at) > cutoff:
            continue
        user = await db.get(User, request.user_id)
        if user is None:
            continue
        try:
            async with db.begin_nested():
                await _purge_user(db, user, now)
                request.status = "completed"
                request.completed_at = now
        except Exception:  # una cuenta rota no puede frenar el resto
            logger.exception("account_purge_failed user=%s", request.user_id)
            continue
        purged += 1
        logger.info("account_purged user=%s", request.user_id)
    await db.commit()
    return purged


async def account_purge_loop(
    db_factory: Callable[..., Any], interval_seconds: int = PURGE_INTERVAL_SECONDS
) -> None:
    """Bucle de fondo: purga lo vencido cada `interval_seconds`.

    No depende de APScheduler (no está instalado en producción: el log de
    arranque lo avisa). Si arrancan varios procesos, cada uno corre el suyo;
    `purge_due` es idempotente.
    """
    while True:
        try:
            async with db_factory() as db:
                count = await purge_due(db)
            if count:
                logger.info("account_purge_loop purged=%d", count)
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            break
        except Exception:  # el bucle sobrevive a cualquier error
            logger.exception("account_purge_loop error")
            await asyncio.sleep(interval_seconds)
