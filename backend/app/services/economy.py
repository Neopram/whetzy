"""Economy services: credits, referrals, promo codes."""

from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.economy import (
    CreditLedger, ReferralCode, Referral, PromoCode,
    PromoCodeRedemption, CreditExpenseCap, CreditReasonEnum
)
from app.models.user import User


class CreditsService:
    """Service for credit ledger management."""

    @staticmethod
    async def grant_credits(
        db: AsyncSession,
        user_id: uuid.UUID,
        amount: int,
        reason: str,
        ref_type: Optional[str] = None,
        ref_id: Optional[str] = None,
        expires_in_days: int = 90,
    ) -> CreditLedger:
        """Grant credits to a user (FIFO lot)."""
        idempotency_key = f"{reason}:{user_id}:{ref_id or 'default'}:{datetime.now(timezone.utc).date()}"
        
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
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_in_days),
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
                    (CreditLedger.expires_at > datetime.now(timezone.utc))
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
        ref_id: Optional[str] = None,
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

        now = datetime.now(timezone.utc)
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
                    CreditLedger.expires_at < datetime.now(timezone.utc),
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
            import string
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
    ) -> Optional[uuid.UUID]:
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
        referral.activated_at = datetime.now(timezone.utc)
        await db.flush()
        return True


class PromoCodeService:
    """Service for promo code management."""

    @staticmethod
    async def redeem_code(
        db: AsyncSession,
        user_id: uuid.UUID,
        code: str,
    ) -> Optional[int]:
        """Redeem a promo code. Returns credits awarded or None."""
        result = await db.execute(
            select(PromoCode).where(PromoCode.code == code)
        )
        promo = result.scalar()
        if not promo:
            return None
        
        # Check expiration
        if promo.expires_at and promo.expires_at < datetime.now(timezone.utc):
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
