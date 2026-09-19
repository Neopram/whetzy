"""Payment models for Whetzy (H.29: Grecia fiscal residency + Paddle MoR)."""

from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class PaymentRail(str, enum.Enum):
    """Payment rail selection (H.29: Grecia scenario)."""
    PADDLE_MOR = "paddle_mor"  # Paddle as merchant (primary)
    IAP = "iap"  # Apple/Google IAP (secondary, mobile only)
    STRIPE = "stripe"  # Fallback (not available in Grecia without AFM)


class InstructorPayoutMethod(str, enum.Enum):
    """How instructors receive payouts (depends H.29 + 21.2)."""
    PADDLE = "paddle"  # Paddle payout (automatic, EUR/USD)
    WISE = "wise"  # Wise account (international, lower fees)
    BANK_EU = "bank_eu"  # IBAN in EU (higher fees, slower)


class PaymentRailConfig(Base):
    """Global payment rail configuration (H.29 decision point)."""
    __tablename__ = "payment_rail_config"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    fiscal_residency = Column(String(50), default="grecia")  # "italia" or "grecia"
    tax_rate_percent = Column(Float, default=22.0)  # 22% Grecia, 5% Italia forfettario
    
    primary_rail = Column(Enum(PaymentRail), default=PaymentRail.PADDLE_MOR)
    secondary_rail = Column(Enum(PaymentRail), default=PaymentRail.IAP)
    
    # Paddle config
    paddle_vendor_id = Column(String(50), nullable=True)  # Set by admin
    paddle_api_key = Column(String(500), nullable=True, default="")  # env var
    paddle_commission_percent = Column(Float, default=7.5)  # 7.5% Paddle
    
    # IAP config (secondary)
    iap_enabled = Column(Boolean, default=True)  # mobile only
    iap_commission_percent = Column(Float, default=15.0)  # Apple Small Business
    
    # Total effective rate = tax + commission
    effective_rate_percent = Column(Float, default=29.5)  # 22% + 7.5%
    
    # Instructor split (after all commissions)
    instructor_share_percent = Column(Float, default=70.0)  # 70% instructor, 30% platform
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<PaymentRailConfig fiscal={self.fiscal_residency} rail={self.primary_rail} tax={self.tax_rate_percent}%>"


class StripeCustomer(Base):
    """Stripe customer mapping (if ever activated in future)."""
    __tablename__ = "stripe_customers"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True)
    stripe_customer_id = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PaddleSubscription(Base):
    """Paddle subscription tracking (primary via Paddle webhooks)."""
    __tablename__ = "paddle_subscriptions"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"))
    paddle_subscription_id = Column(String(100), unique=True)  # From Paddle
    paddle_plan_id = Column(String(100))  # pro_monthly or plus_monthly
    status = Column(String(20), default="active")  # active, past_due, canceled
    
    billing_cycle_start = Column(DateTime)
    billing_cycle_end = Column(DateTime)
    
    amount_cents = Column(Integer)  # €10.00 = 1000 cents
    currency = Column(String(3), default="EUR")  # EUR or USD based on user region
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InstructorPayout(Base):
    """Instructor payouts (28.7 - scheduled monthly)."""
    __tablename__ = "instructor_payouts"
    
    id = Column(String(36), primary_key=True)
    instructor_id = Column(String(36), ForeignKey("instructors.id"))
    
    period_start = Column(DateTime)  # Monthly: 1st
    period_end = Column(DateTime)    # Monthly: 30/31
    
    gross_earnings_cents = Column(Integer)  # Before Paddle commission
    paddle_commission_cents = Column(Integer)  # 7.5% of gross
    tax_amount_cents = Column(Integer)  # 22% (Grecia) or withheld by Paddle
    net_payout_cents = Column(Integer)  # After commission + tax
    
    payout_method = Column(Enum(InstructorPayoutMethod), default=InstructorPayoutMethod.PADDLE)
    payout_address = Column(String(255))  # IBAN or Wise recipient ID
    
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    payout_date = Column(DateTime, nullable=True)
    
    notes = Column(Text, nullable=True)  # DAC7, tax ID, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    instructor = relationship("Instructor", back_populates="payouts")


class PaymentWebhook(Base):
    """Webhook log for Paddle (audit trail)."""
    __tablename__ = "payment_webhooks"
    
    id = Column(String(36), primary_key=True)
    event_type = Column(String(50))  # subscription.created, subscription.updated, etc.
    webhook_id = Column(String(100), unique=True)  # Paddle webhook ID
    payload = Column(Text)  # JSON (encrypted at rest in future)
    status = Column(String(20), default="pending")  # pending, processed, failed
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# Relationships (add to existing models)
# class Instructor(Base):
#     payouts = relationship("InstructorPayout", back_populates="instructor")
#     payout_method = Column(Enum(InstructorPayoutMethod))
#     payout_address = Column(String(255))

