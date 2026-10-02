"""email preferences on users: marketing opt-out and renewal reminder bookkeeping.

- ``marketing_emails_opt_out``: the published privacy policy promises that every
  email can be unsubscribed from (`legal.privacyCanSpam`). Until now the only
  mechanism was a ``mailto:`` header to a no-reply address that nobody processed.
  The reactivation email (a promo code) is marketing: it is sent only to users who
  have not opted out, and carries a one-click unsubscribe link (RFC 8058).
- ``renewal_reminder_for``: the billing period end a renewal reminder was already
  sent for. The published Terms promise a reminder at least 7 days before each
  renewal (`legal.termsP6renewal`); this keeps it to one per period.

Revision ID: 20261002_email_preferences
Revises: 20261001_granted_tier
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261002_email_preferences"
down_revision = "20261001_granted_tier"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "marketing_emails_opt_out", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "users", sa.Column("renewal_reminder_for", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("users", "renewal_reminder_for")
    op.drop_column("users", "marketing_emails_opt_out")
