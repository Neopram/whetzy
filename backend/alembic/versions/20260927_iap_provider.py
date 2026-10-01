"""subscription_provider on users (17.14): which rail last wrote the entitlement.

Stripe and RevenueCat/IAP both write the same subscription_tier/status/
expires_at/is_premium fields (that shared contract is the "PaymentProvider
abstraction" the ledger row asks for — a second Python interface wrapping
both would duplicate it, not add anything, and risks regressing the live,
tested Stripe path for no gain). This column alone answers "which rail
granted the user's current access" for support/debugging, something the
existing stripe_* columns can't answer on their own once a user has been
on more than one rail (e.g. canceled Stripe, later bought IAP: the old
stripe_customer_id stays set and would misleadingly suggest Stripe is
still the source).

Revision ID: 20260927_iap_provider
Revises: 20260927_lesson_completions
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260927_iap_provider"
down_revision = "20260927_lesson_completions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("subscription_provider", sa.String(16), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "subscription_provider")
