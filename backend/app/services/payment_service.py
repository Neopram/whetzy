"""Payment service for Whetzy (H.29: Grecia + Paddle MoR)."""

import logging
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instructor import InstructorPayout
from app.models.payment import (
    PaymentRailConfig,
)

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Payment operations using Paddle as Merchant of Record.
    
    H.29 Decision: Grecia fiscal residency + Paddle 7.5% commission
    Total effective rate: 22% (tax) + 7.5% (Paddle) = 29.5%
    """
    
    GRECIA_TAX_RATE = Decimal("0.22")  # 22%
    PADDLE_COMMISSION = Decimal("0.075")  # 7.5%
    # ADR-41 (dueño, 2026-09-24): de cada venta de un bootcamp/curso, el
    # creador se queda el 80 % y Whetzy el 20 %. Se aplica sobre lo que queda
    # tras la comisión de Paddle, como antes el 70/30.
    INSTRUCTOR_SHARE = Decimal("0.80")
    PLATFORM_SHARE = Decimal("0.20")
    
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
    def calculate_instructor_payout(gross_course_revenue_cents: int) -> dict[str, int]:
        """
        Calculate instructor payout after commission and tax.
        
        Example: User pays €10 (1000 cents) for instructor course
        - Paddle receives: €10 (Paddle is merchant)
        - Platform commission: €0.75 (7.5%)
        - Net to Whetzy: €9.25
        - Instructor share (80%): €7.40 (after commission)
        - Tax withheld (22%, Grecia): calculated on instructor net
        
        Returns:
            {
                "gross_cents": 1000,
                "paddle_commission_cents": 75,
                "instructor_gross_cents": 740,   # 80% of 925
                "tax_withheld_cents": 162,       # 22% of 740
                "instructor_net_cents": 577,
                "platform_keep_cents": 347       # 20% of 925 + tax withheld
            }
        """
        gross = Decimal(gross_course_revenue_cents)
        
        # Paddle takes commission first (they're the merchant)
        paddle_commission = gross * PaymentService.PADDLE_COMMISSION
        
        # Net after Paddle commission goes to split
        after_paddle = gross - paddle_commission
        
        # Instructor gets 80%, platform gets 20% (ADR-41)
        instructor_gross = after_paddle * PaymentService.INSTRUCTOR_SHARE
        platform_share = after_paddle * PaymentService.PLATFORM_SHARE
        
        # Tax on instructor gross (22% Grecia)
        # Note: Actual tax withholding depends on H.29 entidad + instructor tax ID
        tax_withheld = instructor_gross * PaymentService.GRECIA_TAX_RATE
        instructor_net = instructor_gross - tax_withheld
        
        logger.info(
            f"PaymentService.calculate_instructor_payout | "
            f"gross_cents={int(gross)} paddle_commission={int(paddle_commission)} "
            f"instructor_gross={int(instructor_gross)} tax_withheld={int(tax_withheld)} "
            f"instructor_net={int(instructor_net)}"
        )
        
        return {
            "gross_cents": int(gross),
            "paddle_commission_cents": int(paddle_commission),
            "instructor_gross_cents": int(instructor_gross),
            "tax_withheld_cents": int(tax_withheld),
            "instructor_net_cents": int(instructor_net),
            "platform_keep_cents": int(platform_share + tax_withheld),
        }
    
    @staticmethod
    def calculate_subscription_revenue(plan_price_cents: int, months: int = 1) -> dict[str, int]:
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
        period_start: datetime,
        period_end: datetime,
        gross_earnings_cents: int,
    ) -> InstructorPayout:
        """
        Schedule payout for instructor after course enrollment.
        
        Calculation: gross_earnings_cents → minus Paddle commission → minus tax
        
        Returns: InstructorPayout record (status=pending until cron processes)
        """
        payout_calc = PaymentService.calculate_instructor_payout(gross_earnings_cents)
        
        payout = InstructorPayout(
            instructor_id=instructor_id,
            period_start=period_start,
            period_end=period_end,
            earnings_cents=payout_calc["instructor_net_cents"],
            status="pending"
        )
        
        logger.info(
            f"PaymentService.schedule_instructor_payout | "
            f"instructor_id={instructor_id} gross_cents={gross_earnings_cents} "
            f"net_cents={payout_calc['instructor_net_cents']} payout_id={payout.id}"
        )
        
        db.add(payout)
        await db.commit()
        
        return payout
