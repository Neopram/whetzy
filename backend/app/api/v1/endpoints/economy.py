"""Economy endpoints: credits, referrals, promo codes."""


import uuid
from dataclasses import asdict
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.rate_limiter import InMemoryRateLimiter
from app.core.security import get_current_user
from app.models.economy import ReferralCode
from app.models.user import User
from app.services import learning_rewards as lr
from app.services import streak_shop
from app.services.antifraud import AntiFraudService
from app.services.economy import (
    REFERRAL_CREDITS,
    REFERRAL_MILESTONES,
    REFERRAL_MONTHLY_CAP,
    REFERRAL_WELCOME_CREDITS,
    CreditsService,
    PromoCodeService,
    ReferralService,
)
from app.services.mastery_report import MASTERY_REPORT_PRICE

_promo_limiter = InMemoryRateLimiter()

_NATIVE_PLATFORMS = {"ios", "android"}

router = APIRouter(tags=["economy"])


# Pydantic schemas
class CreditBalanceResponse(BaseModel):
    balance: int
    currency: str = "credits"
    # Días hasta que caduque el primer lote con saldo (0 = nada que caduque).
    expires_in_days: int = 0


class ReferralCodeResponse(BaseModel):
    code: str
    share_url: str


class PromoCodeRedeemRequest(BaseModel):
    code: str


class PromoCodeRedeemResponse(BaseModel):
    credits: int
    balance: int
    message: str


class ReferralActivateRequest(BaseModel):
    referral_code: str | None = None


class StreakFreezeQuoteResponse(BaseModel):
    price: int
    balance: int
    held: int
    max_held: int
    purchases_this_week: int
    max_per_week: int
    can_buy: bool
    blocked_by: Literal["insufficient_credits", "max_held", "weekly_limit"] | None


class StreakFreezeBuyRequest(BaseModel):
    # UUID generado por el cliente en cada intento: reintentar con el mismo no
    # cobra dos veces (streak_shop.buy).
    request_id: uuid.UUID


class StreakFreezeBuyResponse(StreakFreezeQuoteResponse):
    replayed: bool


# Endpoints
@router.get("/balance", response_model=CreditBalanceResponse)
async def get_credit_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CreditBalanceResponse:
    """Get current credit balance for the user."""
    balance = await CreditsService.get_balance(db, current_user.id)
    return CreditBalanceResponse(
        balance=balance,
        expires_in_days=await CreditsService.days_to_next_expiry(db, current_user.id),
    )


@router.get("/referral/code", response_model=ReferralCodeResponse)
async def get_referral_code(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReferralCodeResponse:
    """Get or create referral code for user."""
    code = await ReferralService.get_or_create_referral_code(db, current_user.id)
    # Sin commit el código nuevo se perdía al cerrar la sesión: cada visita a la
    # Cartera enseñaba uno distinto y ninguno existía (2026-10-01).
    await db.commit()
    return ReferralCodeResponse(
        code=code,
        share_url=f"https://whetzy.com/r/{code}",
    )


@router.post("/promo/redeem", response_model=PromoCodeRedeemResponse)
async def redeem_promo_code(
    request: PromoCodeRedeemRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromoCodeRedeemResponse:
    """Redeem a promo code (web only — native clients rejected)."""
    platform = (http_request.headers.get("X-Platform") or "").lower()
    if platform in _NATIVE_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Promo codes can only be redeemed from the web app",
        )

    if not await AntiFraudService.check_email_verified(db, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="email_not_verified",
        )

    if AntiFraudService.is_disposable_email(current_user.email or ""):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="disposable_email",
        )

    if not await _promo_limiter.is_allowed(
        f"promo:{current_user.id}", limit=5, window_seconds=600
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many redemption attempts. Try again in a few minutes.",
        )

    credits = await PromoCodeService.redeem_code(db, current_user.id, request.code)
    if credits is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")
    
    new_balance = await CreditsService.get_balance(db, current_user.id)
    await db.commit()
    
    return PromoCodeRedeemResponse(
        credits=credits,
        balance=new_balance,
        message=f"Claimed {credits} credits!",
    )


@router.post("/referral/activate")
async def activate_referral(
    request: ReferralActivateRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    """Register referral during onboarding (status ``pending``).

    Activation and payout happen later, in ``referral_program_loop`` (ADR-35):
    the referred user verifies the email, completes the diagnostic, finishes a
    module and reaches a 3-day streak; the referrer is paid 7 days after.
    ``activated`` in the response means «registered», kept for the client
    contract.
    """
    if not request.referral_code:
        return {"activated": False, "message": "No referral code provided"}

    ref_result = await db.execute(
        select(ReferralCode).where(ReferralCode.code == request.referral_code)
    )
    ref_code_obj = ref_result.scalar()
    if not ref_code_obj:
        return {"activated": False, "message": "Invalid referral code"}

    device_fp = http_request.headers.get("X-Device-Fingerprint")
    ip_addr = http_request.headers.get("X-Forwarded-For", http_request.client.host if http_request.client else "")

    allowed, reason = await AntiFraudService.validate_registration(
        db,
        referred_user_id=current_user.id,
        referred_email=current_user.email or "",
        referrer_id=ref_code_obj.user_id,
        device_fingerprint=device_fp,
        ip_address=ip_addr or None,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=reason,
        )

    referrer_id = await ReferralService.register_referral(
        db, request.referral_code, current_user.id
    )
    await db.commit()

    if not referrer_id:
        return {"activated": False, "message": "Invalid referral code"}

    return {"activated": True, "referrer_id": str(referrer_id)}


@router.get("/prices")
async def get_credit_prices(response: Response) -> dict[str, object]:
    """Public endpoint: credit value mapping.

    Solo lo que el código hace: la Cartera pinta esta lista tal cual. Grifos:
    los de aprendizaje (services/learning_rewards, 2026-10-02) y el programa de
    referidos (ADR-35); el código promocional va aparte. Proyecto entregado y
    simulacro aprobado no están: no hay un hecho verificable que pagar
    (learning_rewards, docstring). Sumideros: lo que llama a spend_fifo.
    """
    response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=86400"
    return {
        "credit_value_usd": 0.01,
        "grifos": [
            {
                "event": "referral_activated",
                "credits": REFERRAL_CREDITS,
                "cap": f"{REFERRAL_MONTHLY_CAP}/month",
                # Hitos acumulados de la escalera: n.º de referidos abonados → premio.
                "milestones": [{"at": at, "reward": reward} for at, reward in REFERRAL_MILESTONES],
            },
            {"event": "referral_welcome", "credits": REFERRAL_WELCOME_CREDITS, "cap": "once"},
            {"event": "diagnostic_done", "credits": lr.DIAGNOSTIC_CREDITS, "cap": "once"},
            {"event": "module_done", "credits": lr.MODULE_CREDITS, "cap": "per_module"},
            {"event": "skill_skipped", "credits": lr.SKILL_SKIPPED_CREDITS, "cap": f"{lr.SKILL_SKIPPED_MONTHLY_CAP}/month"},
            {"event": "streak_7", "credits": lr.STREAK_7_CREDITS, "cap": "per_week"},
            {"event": "streak_30", "credits": lr.STREAK_30_CREDITS, "cap": "per_month"},
        ],
        # Tope de lo que se gana aprendiendo al mes; los referidos tienen el suyo.
        "learning_monthly_cap": lr.LEARNING_MONTHLY_CAP,
        "sumideros": [
            {"item": "freeze_streak_1day", "cost": streak_shop.FREEZE_PRICE_CREDITS},
            {"item": "mastery_report", "cost": MASTERY_REPORT_PRICE},
        ],
    }


@router.get("/streak-freeze", response_model=StreakFreezeQuoteResponse)
async def get_streak_freeze_quote(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreakFreezeQuoteResponse:
    """Precio, saldo, comodines guardados y si se puede comprar uno ahora."""
    q = await streak_shop.quote(db, current_user)
    return StreakFreezeQuoteResponse(**asdict(q))


@router.post("/streak-freeze", response_model=StreakFreezeBuyResponse)
async def buy_streak_freeze(
    body: StreakFreezeBuyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreakFreezeBuyResponse:
    """Compra un comodín de racha con créditos (35.3). 409 con el motivo si un
    tope o el saldo lo impiden; el mismo `request_id` nunca cobra dos veces."""
    try:
        q, replayed = await streak_shop.buy(db, current_user, body.request_id)
    except streak_shop.FreezePurchaseError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.reason) from exc
    await db.commit()
    return StreakFreezeBuyResponse(**asdict(q), replayed=replayed)
