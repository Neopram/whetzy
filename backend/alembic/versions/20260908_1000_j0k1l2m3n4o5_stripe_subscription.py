"""Stripe subscription columns on users (7.2).

Adds stripe_customer_id, stripe_subscription_id, subscription_status,
subscription_tier, subscription_expires_at to the users table.

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-09-08 10:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "j0k1l2m3n4o5"
down_revision = "i9j0k1l2m3n4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("stripe_customer_id", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("stripe_subscription_id", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("subscription_status", sa.String(32), nullable=True))
    op.add_column("users", sa.Column("subscription_tier", sa.String(16), nullable=True))
    op.add_column(
        "users",
        sa.Column("subscription_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_stripe_customer_id", "users", ["stripe_customer_id"], unique=True)
    op.create_unique_constraint("uq_users_stripe_subscription_id", "users", ["stripe_subscription_id"])


def downgrade() -> None:
    op.drop_constraint("uq_users_stripe_subscription_id", "users", type_="unique")
    op.drop_index("ix_users_stripe_customer_id", table_name="users")
    op.drop_column("users", "subscription_expires_at")
    op.drop_column("users", "subscription_tier")
    op.drop_column("users", "subscription_status")
    op.drop_column("users", "stripe_subscription_id")
    op.drop_column("users", "stripe_customer_id")
