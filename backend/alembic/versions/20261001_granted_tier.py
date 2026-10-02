"""granted_tier on users: plan time won through the referral ladder (ADR-35, 29.3).

ECONOMIA.md §3.3 pays the 3rd credited referral with one month of Pro and the
10th with six months of Pro Max, «entitlement en servidor». The subscription
columns (subscription_tier/status/expires_at, is_premium) belong to the
payment rails: Paddle, Stripe and RevenueCat webhooks overwrite them, so a
grant written there would vanish at the next webhook, and a grant ending would
cut a paid plan. Two separate columns keep the grant apart; ``user_meets_tier``
takes the higher of the two while each is in date.

Revision ID: 20261001_granted_tier
Revises: 20261001_paddle_subscription_id
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261001_granted_tier"
down_revision = "20261001_paddle_subscription_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("granted_tier", sa.String(16), nullable=True))
    op.add_column(
        "users", sa.Column("granted_tier_expires_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("users", "granted_tier_expires_at")
    op.drop_column("users", "granted_tier")
