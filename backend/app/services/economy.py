"""Economy services: credits, referrals, promo codes."""

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import ClassVar

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

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
    async def expire_old_credits(db: AsyncSession) -> int:
        """Job: expire credits older than 90 days. Returns count."""
        expiring = await db.execute(
            select(CreditLedger).where(
                and_(
                    CreditLedger.amount > 0,
                    CreditLedger.expires_at < datetime.now(UTC),
                )
            )
        )
        lots = expiring.scalars().all()
        
        count = 0
        for lot in lots:
            expired = CreditLedger(
                user_id=lot.user_id,
                amount=-lot.amount,
                reason=CreditReasonEnum.EXPIRE.value,
                lot_id=lot.id,
                idempotency_key=f"expire:{lot.id}",
            )
            db.add(expired)
            count += 1
        
        await db.flush()
        return count


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
        referred_user_id: uuid.UUID
    ) -> uuid.UUID | None:
        """Register a referral. Returns referrer_id if found."""
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
        return ref_code.user_id

    # Escalera de créditos por número de referidos activados (ECONOMIA.md §3)
    _CREDIT_LADDER: ClassVar[list[tuple[int, int]]] = [(1, 50), (3, 100), (10, 200), (25, 500)]

    @staticmethod
    async def activate_referral(db: AsyncSession, referred_user_id: uuid.UUID) -> bool:
        """Activate referral after user completes onboarding."""
        result = await db.execute(
            select(Referral).where(
                and_(
                    Referral.referred_id == referred_user_id,
                    Referral.status == "pending"
                )
            )
        )
        referral = result.scalar()
        if not referral:
            return False

        referral.status = "activated"
        referral.activated_at = datetime.now(UTC)
        await db.flush()
        return True

    @staticmethod
    async def credit_matured_referrals(
        db: AsyncSession,
        delay_days: int = 7,
    ) -> int:
        """Credit referrers whose referred users activated ≥ delay_days ago.

        Returns the number of referrals credited this run.
        """
        cutoff = datetime.now(UTC) - timedelta(days=delay_days)
        result = await db.execute(
            select(Referral).where(
                and_(
                    Referral.status == "activated",
                    Referral.activated_at <= cutoff,
                )
            )
        )
        matured = list(result.scalars().all())
        credited = 0

        for referral in matured:
            count_result = await db.execute(
                select(func.count()).select_from(Referral).where(
                    and_(
                        Referral.referrer_id == referral.referrer_id,
                        Referral.status == "credited",
                    )
                )
            )
            already_credited = count_result.scalar() or 0

            credits = ReferralService._ladder_credits(already_credited + 1)
            await CreditsService.grant_credits(
                db,
                user_id=referral.referrer_id,
                amount=credits,
                reason=CreditReasonEnum.REFERRAL_ACTIVATED.value,
                ref_type="referral",
                ref_id=str(referral.id),
            )
            referral.status = "credited"
            referral.credited_at = datetime.now(UTC)
            credited += 1

        if credited:
            await db.flush()
        return credited

    @classmethod
    def _ladder_credits(cls, nth: int) -> int:
        """Credits for the nth credited referral (1-indexed)."""
        credits = cls._CREDIT_LADDER[0][1]
        for threshold, amount in cls._CREDIT_LADDER:
            if nth >= threshold:
                credits = amount
        return credits


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
