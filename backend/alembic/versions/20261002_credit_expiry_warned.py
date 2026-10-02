"""users.credit_expiry_warned_for: one expiry warning per date (ECONOMIA §2.4).

The economy promises an email 7 days before ≥ 200 credits expire. The periodic
loop runs every hour; this column holds the expiry date already warned about, so
the warning goes out once per date, like ``renewal_reminder_for`` for renewals.

Revision ID: 20261002_credit_expiry_warned
Revises: 20261002_email_preferences
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261002_credit_expiry_warned"
down_revision = "20261002_email_preferences"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("credit_expiry_warned_for", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("users", "credit_expiry_warned_for")
