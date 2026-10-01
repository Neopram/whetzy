"""paddle_subscription_id on users: Paddle Billing web subscriptions (H.29).

The web rail is Paddle Billing (owner, 2026-10-01: no Stripe). Its webhooks
write the same entitlement columns as Stripe and RevenueCat
(subscription_tier/status/expires_at/provider, is_premium). The only thing
Paddle needs on top is its own subscription id, so that deleting an account
(19.12) can cancel the subscription and stop renewals.

`paddle_subscriptions` exists in models/payment.py but no migration ever
created it; a nullable column here is the smallest change that production
actually has.

Revision ID: 20261001_paddle_subscription_id
Revises: 20260930_question_pool
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261001_paddle_subscription_id"
down_revision = "20260930_question_pool"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("paddle_subscription_id", sa.String(64), nullable=True))
    op.create_unique_constraint("uq_users_paddle_subscription_id", "users", ["paddle_subscription_id"])


def downgrade() -> None:
    op.drop_constraint("uq_users_paddle_subscription_id", "users", type_="unique")
    op.drop_column("users", "paddle_subscription_id")
