"""Add eu_withdrawal_waiver_at to users (21.4).

Revision ID: 20260926_eu_withdrawal
Revises: 20260926_privacy_ccpa
Create Date: 2026-09-26
"""

from alembic import op
import sqlalchemy as sa

revision = "20260926_eu_withdrawal"
down_revision = "20260926_privacy_ccpa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("eu_withdrawal_waiver_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "eu_withdrawal_waiver_at")
