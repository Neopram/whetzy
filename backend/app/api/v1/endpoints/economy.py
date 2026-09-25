"""Economy endpoints: credits, referrals, promo codes."""


import uuid
from dataclasses import asdict
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services import streak_shop
from app.services.economy import CreditsService, PromoCodeService, ReferralService

router = APIRouter(tags=["economy"])


# Pydantic schemas
class CreditBalanceResponse(BaseModel):
    balance: int
    currency: str = "credits"
    expires_in_days: int = 90


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
    return CreditBalanceResponse(balance=balance)


@router.get("/referral/code", response_model=ReferralCodeResponse)
async def get_referral_code(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReferralCodeResponse:
    """Get or create referral code for user."""
    code = await ReferralService.get_or_create_referral_code(db, current_user.id)
    return ReferralCodeResponse(
        code=code,
        share_url=f"https://whetzy.com/r/{code}",
    )


@router.post("/promo/redeem", response_model=PromoCodeRedeemResponse)
async def redeem_promo_code(
    request: PromoCodeRedeemRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PromoCodeRedeemResponse:
    """Redeem a promo code."""
    # Only web clients can redeem codes
    # Check platform header (for 29.4 anti-fraud)
    
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    """Register referral during onboarding."""
    if not request.referral_code:
        return {"activated": False, "message": "No referral code provided"}
    
    referrer_id = await ReferralService.register_referral(
        db, request.referral_code, current_user.id
    )
    await db.commit()
    
    if not referrer_id:
        return {"activated": False, "message": "Invalid referral code"}
    
    return {"activated": True, "referrer_id": str(referrer_id)}


@router.get("/prices")
async def get_credit_prices(response: Response) -> dict[str, object]:
    """Public endpoint: credit value mapping."""
    response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=86400"
    return {
        "credit_value_usd": 0.01,
        "grifos": [
            {"event": "onboarding_done", "credits": 50, "cap": "once"},
            {"event": "module_done", "credits": 100, "cap": "per_module"},
            {"event": "streak_7", "credits": 70, "cap": "per_week"},
            {"event": "streak_30", "credits": 300, "cap": "per_month"},
            {"event": "referral_activated", "credits": 300, "cap": "10/month"},
            {"event": "referral_welcome", "credits": 200, "cap": "once"},
        ],
        "sumideros": [
            {"item": "mock_exam", "cost": 500},
            {"item": "freeze_streak_1day", "cost": streak_shop.FREEZE_PRICE_CREDITS},
            {"item": "domain_report_pdf", "cost": 300},
            {"item": "marketplace_course", "cost": 1000},
        ]
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
