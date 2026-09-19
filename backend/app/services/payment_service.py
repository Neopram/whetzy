"""Payment service for Whetzy (H.29: Grecia + Paddle MoR)."""

from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.payment import (
    PaymentRailConfig, PaddleSubscription, InstructorPayout, InstructorPayoutMethod
)


class PaymentService:
    """
    Payment operations using Paddle as Merchant of Record.
    
    H.29 Decision: Grecia fiscal residency + Paddle 7.5% commission
    Total effective rate: 22% (tax) + 7.5% (Paddle) = 29.5%
    """
    
    GRECIA_TAX_RATE = Decimal("0.22")  # 22%
    PADDLE_COMMISSION = Decimal("0.075")  # 7.5%
    INSTRUCTOR_SHARE = Decimal("0.70")  # 70% to instructor, 30% to platform
    PLATFORM_SHARE = Decimal("0.30")
    
    @staticmethod
    async def get_config(db: AsyncSession) -> PaymentRailConfig:
        """Get current payment configuration (H.29 decision)."""
        stmt = select(PaymentRailConfig).limit(1)
        result = await db.execute(stmt)
        config = result.scalars().first()
        
        if not config:
            # Default: Grecia + Paddle (H.29 decision)
            config = PaymentRailConfig(
                fiscal_residency="grecia",
                tax_rate_percent=22.0,
                primary_rail="paddle_mor",
                secondary_rail="iap",
                paddle_commission_percent=7.5,
                effective_rate_percent=29.5
            )
            db.add(config)
            await db.commit()
        
        return config
    
    @staticmethod
    def calculate_instructor_payout(gross_course_revenue_cents: int) -> dict:
        """
        Calculate instructor payout after commission and tax.
        
        Example: User pays €10 (1000 cents) for instructor course
        - Paddle receives: €10 (Paddle is merchant)
        - Platform commission: €0.75 (7.5%)
        - Net to Whetzy: €9.25
        - Instructor share (70%): €6.475 (after commission)
        - Tax withheld (22%, Grecia): calculated on instructor net
        
        Returns:
            {
                "gross_cents": 1000,
                "paddle_commission_cents": 75,
                "instructor_gross_cents": 925,
                "tax_cents": 203,  # 22% of 925
                "instructor_net_cents": 722,
                "platform_keep_cents": 203  # Platform share + tax withheld
            }
        """
        gross = Decimal(gross_course_revenue_cents)
        
        # Paddle takes commission first (they're the merchant)
        paddle_commission = gross * PaymentService.PADDLE_COMMISSION
        
        # Net after Paddle commission goes to split
        after_paddle = gross - paddle_commission
        
        # Instructor gets 70%, platform gets 30%
        instructor_gross = after_paddle * PaymentService.INSTRUCTOR_SHARE
        platform_share = after_paddle * PaymentService.PLATFORM_SHARE
        
        # Tax on instructor gross (22% Grecia)
        # Note: Actual tax withholding depends on H.29 entidad + instructor tax ID
        tax_withheld = instructor_gross * PaymentService.GRECIA_TAX_RATE
        instructor_net = instructor_gross - tax_withheld
        
        return {
            "gross_cents": int(gross),
            "paddle_commission_cents": int(paddle_commission),
            "instructor_gross_cents": int(instructor_gross),
            "tax_withheld_cents": int(tax_withheld),
            "instructor_net_cents": int(instructor_net),
            "platform_keep_cents": int(platform_share + tax_withheld),
        }
    
    @staticmethod
    def calculate_subscription_revenue(plan_price_cents: int, months: int = 1) -> dict:
        """
        Calculate platform revenue from subscription.
        
        Example: Pro plan €10/month → Paddle takes 7.5%
        - Revenue to platform: €9.25
        - Créditos granted: 100 (Pro plan = 100 créditos/mes)
        
        Returns:
            {
                "user_pays_cents": 1000,
                "paddle_takes_cents": 75,
                "platform_revenue_cents": 925,
                "credits_granted": 100
            }
        """
        total_price = Decimal(plan_price_cents) * months
        paddle_take = total_price * PaymentService.PADDLE_COMMISSION
        platform_revenue = total_price - paddle_take
        
        # Credits mapping (100 = Pro, 300 = Plus)
        credits_per_month = 100 if plan_price_cents == 1000 else 300
        total_credits = credits_per_month * months
        
        return {
            "user_pays_cents": int(total_price),
            "paddle_takes_cents": int(paddle_take),
            "platform_revenue_cents": int(platform_revenue),
            "credits_granted": total_credits,
        }
    
    @staticmethod
    async def schedule_instructor_payout(
        db: AsyncSession,
        instructor_id: str,
        period_start: str,  # YYYY-MM-01
        period_end: str,    # YYYY-MM-30
        gross_earnings_cents: int,
        payout_method: InstructorPayoutMethod = InstructorPayoutMethod.PADDLE,
        payout_address: str = None,
    ):
        """
        Schedule monthly payout for instructor (28.7).
        
        Calculation: gross_earnings_cents → minus Paddle commission → minus tax
        
        Returns: InstructorPayout record (status=pending until cron executes)
        """
        payout_calc = PaymentService.calculate_instructor_payout(gross_earnings_cents)
        
        payout = InstructorPayout(
            instructor_id=instructor_id,
            period_start=period_start,
            period_end=period_end,
            gross_earnings_cents=payout_calc["gross_cents"],
            paddle_commission_cents=payout_calc["paddle_commission_cents"],
            tax_amount_cents=payout_calc["tax_withheld_cents"],
            net_payout_cents=payout_calc["instructor_net_cents"],
            payout_method=payout_method,
            payout_address=payout_address,
            status="pending"
        )
        db.add(payout)
        await db.commit()
        
        return payout


# Endpoint example (backend/app/api/v1/endpoints/payments.py)
"""
@router.post("/payments/calculate-instructor-payout")
async def calc_payout(gross_cents: int, db: AsyncSession = Depends(get_db)):
    result = PaymentService.calculate_instructor_payout(gross_cents)
    return result

@router.get("/payments/config")
async def get_config(db: AsyncSession = Depends(get_db)):
    config = await PaymentService.get_config(db)
    return {
        "fiscal_residency": config.fiscal_residency,
        "effective_rate_percent": config.effective_rate_percent,
        "primary_rail": config.primary_rail,
    }
"""

