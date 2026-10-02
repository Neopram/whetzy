"""Economy services: credits, referrals, promo codes."""

import asyncio
import logging
import secrets
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.antifraud import FraudReviewQueue
from app.models.content import Module, Skill
from app.models.session import StudySession
from app.models.user import User, UserSkillState
from app.services.antifraud import AntiFraudService

logger = logging.getLogger("whetzy.referrals")

# ── Programa de referidos (ADR-35, ECONOMIA §3) ──────────────────────────────
REFERRAL_WELCOME_CREDITS = 200  # al referido, al registrarse con código (§3.2)
REFERRAL_WELCOME_DAYS = 30  # sin diagnóstico; con él, 90 como cualquier lote
REFERRAL_CREDITS = 300  # al referente, por cada activación abonada (§3.2)
REFERRAL_CREDIT_DELAY_DAYS = 7  # entre activación y abono (§3.1)
REFERRAL_MONTHLY_CAP = 10  # activaciones abonables por referente y mes (§3.3)
REFERRAL_STREAK_DAYS = 3  # condición (d) del §3.1
REFERRAL_VELOCITY_PER_WEEK = 5  # por encima, cola de revisión (§3.5)
REFERRAL_FRAUD_PAUSE = 0.05  # dos semanas seguidas por encima → pausa (§3.5)
REFERRAL_LOOP_SECONDS = 6 * 3600
# Hitos de la escalera, acumulativa (§3.3): n.º de abonados → premio. La
# certificación del hito 10 está HUMAN-BLOCKED por importe (ADR-15): mientras,
# 6 meses de Pro Max, como dice la propia tabla.
REFERRAL_MILESTONES: tuple[tuple[int, str], ...] = (
    (3, "pro_month"),
    (10, "pro_max_6_months"),
    (25, "ambassador_badge"),
)
# premio → (tier interno, días). `plus` es Pro y `pro` es Pro Max (ADR-41).
REFERRAL_PLAN_REWARDS: dict[str, tuple[str, int]] = {
    "pro_month": ("plus", 30),
    "pro_max_6_months": ("pro", 183),
}

# Alphabet without ambiguous chars: 0, O, 1, I, L removed.
_SAFE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"

from app.models.economy import (
    CreditLedger,
    CreditReasonEnum,
    PromoCode,
    PromoCodeRedemption,
    Referral,
    ReferralCode,
)


class CreditsService:
    """Service for credit ledger management."""

    @staticmethod
    async def grant_credits(
        db: AsyncSession,
        user_id: uuid.UUID,
        amount: int,
        reason: str,
        ref_type: str | None = None,
        ref_id: str | None = None,
        expires_in_days: int = 90,
    ) -> CreditLedger:
        """Grant credits to a user (FIFO lot)."""
        idempotency_key = f"{reason}:{user_id}:{ref_id or 'default'}:{datetime.now(UTC).date()}"
        
        # Check if already granted today (idempotency)
        existing = await db.execute(
            select(CreditLedger).where(
                CreditLedger.idempotency_key == idempotency_key
            )
        )
        already = existing.scalar_one_or_none()
        if already is not None:
            return already
        
        lot = CreditLedger(
            user_id=user_id,
            amount=amount,
            reason=reason,
            ref_type=ref_type,
            ref_id=ref_id,
            idempotency_key=idempotency_key,
            expires_at=datetime.now(UTC) + timedelta(days=expires_in_days),
        )
        db.add(lot)
        await db.flush()
        return lot

    @staticmethod
    async def get_balance(db: AsyncSession, user_id: uuid.UUID) -> int:
        """Get current credit balance (non-expired only)."""
        result = await db.execute(
            select(func.sum(CreditLedger.amount)).where(
                and_(
                    CreditLedger.user_id == user_id,
                    (CreditLedger.expires_at.is_(None)) | 
                    (CreditLedger.expires_at > datetime.now(UTC))
                )
            )
        )
        balance = result.scalar() or 0
        return max(0, balance)

    @staticmethod
    async def days_to_next_expiry(db: AsyncSession, user_id: uuid.UUID) -> int:
        """Días hasta que caduque el primer lote con saldo; 0 si no hay saldo
        que caduque. La Cartera decía siempre «90» (un valor por defecto), y el
        lote de bienvenida de un referido caduca a los 30 (ECONOMIA §3.2)."""
        now = datetime.now(UTC)
        spent_per_lot = (
            select(
                CreditLedger.lot_id.label("lot_id"),
                func.sum(CreditLedger.amount).label("spent"),
            )
            .where(CreditLedger.lot_id.is_not(None))
            .group_by(CreditLedger.lot_id)
            .subquery()
        )
        lots = await db.execute(
            select(CreditLedger.expires_at)
            .outerjoin(spent_per_lot, spent_per_lot.c.lot_id == CreditLedger.id)
            .where(
                CreditLedger.user_id == user_id,
                CreditLedger.amount > 0,
                CreditLedger.expires_at > now,
                CreditLedger.amount + func.coalesce(spent_per_lot.c.spent, 0) > 0,
            )
            .order_by(CreditLedger.expires_at.asc())
            .limit(1)
        )
        first = lots.scalar()
        if first is None:
            return 0
        if first.tzinfo is None:
            first = first.replace(tzinfo=UTC)
        return max(1, -(-int((first - now).total_seconds()) // 86400))

    @staticmethod
    async def spend_fifo(
        db: AsyncSession,
        user_id: uuid.UUID,
        amount: int,
        reason: str,
        ref_type: str = "purchase",
        ref_id: str | None = None,
    ) -> bool:
        """Gasta creditos consumiendo primero los lotes que caducan antes.

        Tres cosas que la version anterior hacia mal:

        1. Consumia mirando `lot.amount`, que es el importe con el que se abrio
           el lote y no baja nunca —el gasto es una fila aparte con `lot_id`—,
           asi que el mismo lote se podia gastar entero dos veces. Aqui el
           restante de cada lote se calcula sumandole sus gastos.
        2. El gasto nacia sin `expires_at`. Cuando el lote caducaba, su importe
           positivo salia de la suma del saldo y el gasto negativo se quedaba:
           el usuario pagaba dos veces por lo mismo. Ahora el gasto hereda la
           caducidad de su lote y los dos salen juntos.
        3. La clave de idempotencia llevaba un timestamp, asi que dos lotes
           consumidos en la misma llamada chocaban en el indice unico —y, peor,
           reintentar la misma compra creaba un segundo cargo, que es
           exactamente lo que esa clave existe para impedir.
        """
        balance = await CreditsService.get_balance(db, user_id)
        if balance < amount:
            return False

        now = datetime.now(UTC)
        spent_per_lot = (
            select(
                CreditLedger.lot_id.label("lot_id"),
                func.sum(CreditLedger.amount).label("spent"),
            )
            .where(CreditLedger.lot_id.is_not(None))
            .group_by(CreditLedger.lot_id)
            .subquery()
        )

        lots = await db.execute(
            select(
                CreditLedger,
                func.coalesce(spent_per_lot.c.spent, 0),
            )
            .outerjoin(spent_per_lot, spent_per_lot.c.lot_id == CreditLedger.id)
            .where(
                and_(
                    CreditLedger.user_id == user_id,
                    CreditLedger.amount > 0,
                    (CreditLedger.expires_at.is_(None))
                    | (CreditLedger.expires_at > now),
                )
            )
            # Primero lo que caduca antes; los lotes sin caducidad al final, que
            # si no se quedan sin gastar hasta que caduca todo lo demas.
            .order_by(
                CreditLedger.expires_at.asc().nullslast(),
                CreditLedger.created_at.asc(),
            )
        )

        remaining = amount
        for lot, spent in lots.all():
            if remaining <= 0:
                break
            available = lot.amount + spent  # `spent` es <= 0
            if available <= 0:
                continue
            consume = min(available, remaining)
            db.add(
                CreditLedger(
                    user_id=user_id,
                    amount=-consume,
                    reason=reason,
                    ref_type=ref_type,
                    ref_id=ref_id,
                    lot_id=lot.id,
                    expires_at=lot.expires_at,
                    idempotency_key=(
                        f"spend:{user_id}:{reason}:{ref_id}:lot{lot.id}"
                        if ref_id is not None
                        # Sin `ref_id` la operacion no tiene identidad y no se
                        # puede deduplicar: se le da una clave unica para no
                        # chocar, y quien quiera idempotencia que pase ref_id.
                        else f"spend:{user_id}:{reason}:{uuid.uuid4()}:lot{lot.id}"
                    ),
                )
            )
            remaining -= consume

        await db.flush()
        return remaining == 0

    @staticmethod
    async def lots_with_remaining(
        db: AsyncSession,
        *,
        expires_after: datetime,
        expires_before: datetime,
        user_id: uuid.UUID | None = None,
    ) -> list[tuple[CreditLedger, int]]:
        """Lotes con saldo que caducan en (expires_after, expires_before], con lo
        que les queda. Un lote ya cerrado con su asiento `expire` queda a 0."""
        spent_per_lot = (
            select(
                CreditLedger.lot_id.label("lot_id"),
                func.sum(CreditLedger.amount).label("spent"),
            )
            .where(CreditLedger.lot_id.is_not(None))
            .group_by(CreditLedger.lot_id)
            .subquery()
        )
        query = (
            select(CreditLedger, CreditLedger.amount + func.coalesce(spent_per_lot.c.spent, 0))
            .outerjoin(spent_per_lot, spent_per_lot.c.lot_id == CreditLedger.id)
            .where(
                CreditLedger.amount > 0,
                CreditLedger.expires_at > expires_after,
                CreditLedger.expires_at <= expires_before,
                CreditLedger.amount + func.coalesce(spent_per_lot.c.spent, 0) > 0,
            )
            .order_by(CreditLedger.expires_at.asc())
        )
        if user_id is not None:
            query = query.where(CreditLedger.user_id == user_id)
        return [(lot, int(remaining)) for lot, remaining in (await db.execute(query)).all()]

    @staticmethod
    async def expire_old_credits(db: AsyncSession, now: datetime | None = None) -> int:
        """Cierra cada lote vencido con un asiento `expire` por **lo que le
        quedaba** (§2.4: nunca se borra nada). Returns lotes cerrados.

        La versión anterior (sin llamar desde ningún sitio hasta el 2026-10-02)
        escribía `-lot.amount`, el importe original, sin `expires_at`: el lote
        salía del saldo al vencer y ese negativo se quedaba restando para siempre,
        y lo ya gastado del lote se cobraba dos veces. Aquí el asiento hereda la
        caducidad del lote, como los gastos (spend_fifo), así que el saldo no
        cambia al escribirlo: es contabilidad, no un segundo cobro.
        """
        now = now or datetime.now(UTC)
        lots = await CreditsService.lots_with_remaining(
            db, expires_after=datetime(1970, 1, 1, tzinfo=UTC), expires_before=now
        )
        for lot, remaining in lots:
            db.add(
                CreditLedger(
                    user_id=lot.user_id,
                    amount=-remaining,
                    reason=CreditReasonEnum.EXPIRE.value,
                    ref_type="expire",
                    lot_id=lot.id,
                    expires_at=lot.expires_at,
                    idempotency_key=f"expire:{lot.id}",
                )
            )
        await db.flush()
        return len(lots)


class ReferralService:
    """Service for referral management."""

    @staticmethod
    async def get_or_create_referral_code(db: AsyncSession, user_id: uuid.UUID) -> str:
        """Get or create a referral code for a user."""
        result = await db.execute(
            select(ReferralCode).where(ReferralCode.user_id == user_id)
        )
        ref_code = result.scalar()
        
        if not ref_code:
            # Generate unique code (base32, exclude confusing chars)
            import random
            alphabet = 'ACDEFGHJKMNPQRTWXYZ234567'  # Exclude 0,O,1,I,L,B,S
            code = ''.join(random.choice(alphabet) for _ in range(8))
            
            ref_code = ReferralCode(user_id=user_id, code=code)
            db.add(ref_code)
            await db.flush()
        
        return ref_code.code

    @staticmethod
    async def register_referral(
        db: AsyncSession,
        referrer_code: str,
        referred_user_id: uuid.UUID,
    ) -> uuid.UUID | None:
        """Register a referral (status ``pending``) and give the referred user
        the welcome credits (ECONOMIA §3.2). Returns referrer_id if found."""
        result = await db.execute(
            select(ReferralCode).where(ReferralCode.code == referrer_code)
        )
        ref_code = result.scalar()
        if not ref_code:
            return None

        # Check if referred already has a referrer
        existing = await db.execute(
            select(Referral).where(Referral.referred_id == referred_user_id)
        )
        if existing.scalar():
            return None

        referral = Referral(
            referrer_id=ref_code.user_id,
            referred_id=referred_user_id,
            status="pending",
        )
        db.add(referral)
        await db.flush()
        # Caducan a los 30 días si no completa el diagnóstico; al completarlo,
        # el job los alarga a los 90 de cualquier otro lote.
        await CreditsService.grant_credits(
            db,
            user_id=referred_user_id,
            amount=REFERRAL_WELCOME_CREDITS,
            reason=CreditReasonEnum.REFERRAL_WELCOME.value,
            ref_type="referral",
            ref_id=str(referral.id),
            expires_in_days=REFERRAL_WELCOME_DAYS,
        )
        return ref_code.user_id

    # ── Activación (ECONOMIA §3.1) ───────────────────────────────────────

    @staticmethod
    async def diagnostic_done(db: AsyncSession, user: User) -> bool:
        """(b) del §3.1. El onboarding solo manda a la prueba de nivel a quien
        dice que ya programa (`onboarding_experience` ≥ 1): para ese, hace falta
        una prueba terminada; para el que empieza de cero, su diagnóstico es el
        propio onboarding. Exigir la prueba a todos dejaría fuera a cada
        principiante, que nunca la ve."""
        placement_done = (
            await db.execute(
                select(func.count(StudySession.id)).where(
                    StudySession.user_id == user.id,
                    StudySession.mode == "placement",
                    StudySession.ended_at.is_not(None),
                )
            )
        ).scalar_one() or 0
        if placement_done:
            return True
        return bool(user.onboarding_experience == 0)

    @staticmethod
    async def module_completed(db: AsyncSession, user_id: uuid.UUID) -> bool:
        """(c) del §3.1, con la misma regla con la que la app pinta un módulo
        como «completado» (services/progress.py): la media de dominio de sus
        skills llega a `min_mastery_to_unlock`."""
        touched = select(Skill.module_id).join(
            UserSkillState, UserSkillState.skill_id == Skill.id
        ).where(UserSkillState.user_id == user_id)
        rows = await db.execute(
            select(
                Module.min_mastery_to_unlock,
                func.count(Skill.id),
                func.coalesce(func.sum(UserSkillState.p_known), 0.0),
            )
            .join(Skill, Skill.module_id == Module.id)
            .outerjoin(
                UserSkillState,
                and_(UserSkillState.skill_id == Skill.id, UserSkillState.user_id == user_id),
            )
            .where(Module.id.in_(touched))
            .group_by(Module.id, Module.min_mastery_to_unlock)
        )
        return any(n and total / n >= threshold for threshold, n, total in rows.all())

    @staticmethod
    async def activation_missing(db: AsyncSession, referred: User) -> list[str]:
        """Lo que le falta al referido para activarse; vacío = activable."""
        missing: list[str] = []
        if not referred.email_verified:
            missing.append("email_verified")
        if not await ReferralService.diagnostic_done(db, referred):
            missing.append("diagnostic")
        if not await ReferralService.module_completed(db, referred.id):
            missing.append("first_module")
        if referred.max_streak < REFERRAL_STREAK_DAYS:
            missing.append("streak")
        return missing

    @staticmethod
    async def _extend_welcome(db: AsyncSession, referral: Referral, now: datetime) -> None:
        """Diagnóstico hecho: el lote de bienvenida deja de caducar a los 30
        días y pasa a los 90 de cualquier lote (§3.2)."""
        lots = await db.execute(
            select(CreditLedger).where(
                CreditLedger.reason == CreditReasonEnum.REFERRAL_WELCOME.value,
                CreditLedger.ref_id == str(referral.id),
                CreditLedger.expires_at > now,
            )
        )
        for lot in lots.scalars().all():
            created = lot.created_at if lot.created_at.tzinfo else lot.created_at.replace(tzinfo=UTC)
            full = created + timedelta(days=90)
            expires = lot.expires_at
            if expires is not None and expires.tzinfo is None:
                expires = expires.replace(tzinfo=UTC)
            if expires is None or expires < full:
                lot.expires_at = full

    @staticmethod
    async def activate_ready_referrals(db: AsyncSession, now: datetime | None = None) -> int:
        """pending → activated para cada referido que cumple las cuatro
        condiciones del §3.1. Un referente por encima de 5 activaciones en 7
        días va a la cola de revisión y su referido espera (§3.5). Returns the
        number activated this run."""
        now = now or datetime.now(UTC)
        if await ReferralService.program_paused(db, now):
            return 0
        pending = (
            await db.execute(
                select(Referral)
                .where(Referral.status == "pending")
                .order_by(Referral.created_at)
                .with_for_update(skip_locked=True)
            )
        ).scalars().all()
        activated = 0
        for referral in pending:
            referred = await db.get(User, referral.referred_id)
            if referred is None or not referred.is_active:
                continue
            if await ReferralService.diagnostic_done(db, referred):
                await ReferralService._extend_welcome(db, referral, now)
            if await ReferralService.activation_missing(db, referred):
                continue
            if await AntiFraudService.check_velocity(db, referral.referrer_id):
                await AntiFraudService.flag_for_review(
                    db, referral.referrer_id, "velocity_exceeded", REFERRAL_VELOCITY_PER_WEEK
                )
                continue
            referral.status = "activated"
            referral.activated_at = now
            await db.flush()  # la siguiente vuelta cuenta esta activación
            activated += 1
        return activated

    # ── Abono y escalera (ECONOMIA §3.2–3.3) ─────────────────────────────

    @staticmethod
    async def credit_matured_referrals(
        db: AsyncSession,
        delay_days: int = REFERRAL_CREDIT_DELAY_DAYS,
        now: datetime | None = None,
    ) -> int:
        """activated → credited a los `delay_days`: 300 créditos al referente y,
        al llegar a 3, 10 y 25 abonados, su premio de la escalera. Tope de 10
        abonos por referente y mes natural; lo que pasa del tope espera al mes
        siguiente. Returns the number of referrals credited this run."""
        now = now or datetime.now(UTC)
        if await ReferralService.program_paused(db, now):
            return 0
        cutoff = now - timedelta(days=delay_days)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        matured = (
            await db.execute(
                select(Referral)
                .where(
                    and_(
                        Referral.status == "activated",
                        Referral.activated_at <= cutoff,
                    )
                )
                .order_by(Referral.activated_at)
                .with_for_update(skip_locked=True)
            )
        ).scalars().all()
        credited = 0

        for referral in matured:
            referred = await db.get(User, referral.referred_id)
            if referred is not None and not referred.is_active:
                # Cuenta borrada antes del abono: no hay activación que pagar.
                referral.status = "rejected"
                await db.flush()
                continue
            this_month = (
                await db.execute(
                    select(func.count()).select_from(Referral).where(
                        Referral.referrer_id == referral.referrer_id,
                        Referral.status == "credited",
                        Referral.credited_at >= month_start,
                    )
                )
            ).scalar() or 0
            if this_month >= REFERRAL_MONTHLY_CAP:
                continue
            already_credited = (
                await db.execute(
                    select(func.count()).select_from(Referral).where(
                        Referral.referrer_id == referral.referrer_id,
                        Referral.status == "credited",
                    )
                )
            ).scalar() or 0

            await CreditsService.grant_credits(
                db,
                user_id=referral.referrer_id,
                amount=REFERRAL_CREDITS,
                reason=CreditReasonEnum.REFERRAL_ACTIVATED.value,
                ref_type="referral",
                ref_id=str(referral.id),
            )
            referral.status = "credited"
            referral.credited_at = now
            await db.flush()  # el siguiente cuenta este abono (tope y escalera)
            await ReferralService._apply_milestone(
                db, referral.referrer_id, already_credited + 1, now
            )
            credited += 1

        if credited:
            await db.flush()
        return credited

    @staticmethod
    async def _apply_milestone(
        db: AsyncSession, referrer_id: uuid.UUID, nth: int, now: datetime
    ) -> str | None:
        """Premio del hito `nth` de la escalera (acumulativa: cada hito una vez)."""
        reward = dict(REFERRAL_MILESTONES).get(nth)
        if reward is None:
            return None
        referrer = await db.get(User, referrer_id)
        if referrer is None:
            return None
        if reward in REFERRAL_PLAN_REWARDS:
            tier, days = REFERRAL_PLAN_REWARDS[reward]
            grant_plan_time(referrer, tier, days, now)
        elif reward == "ambassador_badge":
            from app.services.gamification.service import award_badges

            await award_badges(db, referrer)
        await db.flush()
        return reward

    # ── Pausa (ECONOMIA §3.5) ────────────────────────────────────────────

    @staticmethod
    async def _fraud_rate(db: AsyncSession, start: datetime, end: datetime) -> float:
        """Misma definición que el scorecard de admin: marcas de la cola de
        revisión sobre referidos registrados en la ventana."""
        flags = (
            await db.execute(
                select(func.count(FraudReviewQueue.id)).where(
                    FraudReviewQueue.created_at >= start, FraudReviewQueue.created_at < end
                )
            )
        ).scalar() or 0
        referrals = (
            await db.execute(
                select(func.count(Referral.id)).where(
                    Referral.created_at >= start, Referral.created_at < end
                )
            )
        ).scalar() or 0
        return flags / referrals if referrals else 0.0

    @staticmethod
    async def program_paused(db: AsyncSession, now: datetime | None = None) -> bool:
        """Pausa manual (`REFERRALS_PAUSED`) o fraude > 5 % dos semanas seguidas."""
        if settings.REFERRALS_PAUSED:
            return True
        now = now or datetime.now(UTC)
        week = timedelta(days=7)
        last = await ReferralService._fraud_rate(db, now - week, now)
        before = await ReferralService._fraud_rate(db, now - 2 * week, now - week)
        if last > REFERRAL_FRAUD_PAUSE and before > REFERRAL_FRAUD_PAUSE:
            logger.error(
                "Programa de referidos pausado: fraude %.1f %% y %.1f %% las dos últimas "
                "semanas (> %.0f %%). Revisa la cola en admin.",
                before * 100, last * 100, REFERRAL_FRAUD_PAUSE * 100,
            )
            return True
        return False


def grant_plan_time(user: User, tier: str, days: int, now: datetime) -> None:
    """Suma tiempo de plan ganado (`granted_tier`). El mismo plan se alarga desde
    donde acabe; uno mayor lo sustituye sin acortar lo que quedaba."""
    from app.core.entitlements import _TIER_RANK

    current = user.active_granted_tier
    until = user.granted_tier_expires_at
    if until is not None and until.tzinfo is None:
        until = until.replace(tzinfo=UTC)
    if current is None or until is None:
        user.granted_tier = tier
        user.granted_tier_expires_at = now + timedelta(days=days)
    elif _TIER_RANK.get(tier, 0) > _TIER_RANK.get(current, 0):
        user.granted_tier = tier
        user.granted_tier_expires_at = max(until, now + timedelta(days=days))
    else:
        user.granted_tier_expires_at = until + timedelta(days=days)


# Clave del advisory lock de Postgres para el bucle de referidos (arbitraria, fija).
_REFERRAL_LOCK_KEY = 290_303


async def _single_runner(db: AsyncSession) -> bool:
    """Una sola vuelta a la vez entre workers: FOR UPDATE SKIP LOCKED ya impide
    abonar dos veces la misma fila, pero dos vueltas repartiéndose filas
    podrían contar el mismo hito de la escalera. El lock se suelta al cerrar
    la transacción. En SQLite (tests) no hay workers que coordinar."""
    if db.bind.dialect.name != "postgresql":
        return True
    got = await db.execute(
        select(func.pg_try_advisory_xact_lock(_REFERRAL_LOCK_KEY))
    )
    return bool(got.scalar())


async def referral_program_loop(
    db_factory: Callable[..., Any], interval_seconds: int = REFERRAL_LOOP_SECONDS
) -> None:
    """Bucle de fondo: activa referidos y abona los maduros cada 6 h.

    Como `account_purge_loop`, sin APScheduler (no está instalado en
    producción). Con varios workers de gunicorn corre uno por proceso, pero
    solo uno entra en cada vuelta (`_single_runner`) y las filas van con FOR
    UPDATE SKIP LOCKED: nadie abona dos veces.
    """
    while True:
        try:
            async with db_factory() as db:
                activated = credited = 0
                if await _single_runner(db):
                    activated = await ReferralService.activate_ready_referrals(db)
                    credited = await ReferralService.credit_matured_referrals(db)
                await db.commit()
            if activated or credited:
                logger.info("referral_program_loop activated=%d credited=%d", activated, credited)
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            break
        except Exception:  # el bucle sobrevive a cualquier error
            logger.exception("referral_program_loop error")
            await asyncio.sleep(interval_seconds)


class PromoCodeService:
    """Service for promo code management."""

    @staticmethod
    def _generate_code(length: int = 8) -> str:
        return "".join(secrets.choice(_SAFE_ALPHABET) for _ in range(length))

    @staticmethod
    async def generate_batch(
        db: AsyncSession,
        *,
        code_type: str,
        credits: int,
        count: int,
        max_uses: int | None = None,
        expires_at: datetime | None = None,
        language: str | None = None,
        campaign_id: str | None = None,
        created_by: str = "admin",
    ) -> list[PromoCode]:
        codes: list[PromoCode] = []
        for _ in range(count):
            code = PromoCodeService._generate_code()
            promo = PromoCode(
                code=code,
                code_type=code_type,
                credits=credits,
                max_uses=max_uses,
                language=language,
                expires_at=expires_at,
                campaign_id=campaign_id,
                created_by=created_by,
            )
            db.add(promo)
            codes.append(promo)
        await db.flush()
        return codes

    @staticmethod
    async def redeem_code(
        db: AsyncSession,
        user_id: uuid.UUID,
        code: str,
    ) -> int | None:
        """Redeem a promo code. Returns credits awarded or None."""
        result = await db.execute(
            select(PromoCode).where(PromoCode.code == code)
        )
        promo = result.scalar()
        if not promo:
            return None
        
        # Check expiration
        if promo.expires_at and promo.expires_at < datetime.now(UTC):
            return None
        
        # Check max uses
        if promo.max_uses and promo.current_uses >= promo.max_uses:
            return None
        
        # Check user hasn't redeemed this before
        existing = await db.execute(
            select(PromoCodeRedemption).where(
                and_(
                    PromoCodeRedemption.user_id == user_id,
                    PromoCodeRedemption.promo_code_id == promo.id,
                )
            )
        )
        if existing.scalar():
            return None
        
        # Grant credits
        lot = await CreditsService.grant_credits(
            db,
            user_id,
            promo.credits,
            CreditReasonEnum.PROMO_CODE.value,
            ref_type="promo_code",
            ref_id=code,
        )
        
        # Track redemption
        redemption = PromoCodeRedemption(
            user_id=user_id,
            promo_code_id=promo.id,
            credit_ledger_id=lot.id,
        )
        db.add(redemption)
        
        # Update promo code usage
        promo.current_uses += 1
        
        await db.flush()
        return promo.credits
