"""mastery_reports: the mastery report bought with credits (ECONOMIA §2.3).

A dated snapshot of the learner's mastery, published under an unguessable code
like a certificate. ``request_id`` makes the purchase idempotent: a retried
request returns the same report and never charges twice.

Revision ID: 20261002_mastery_reports
Revises: 20261002_credit_expiry_warned
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261002_mastery_reports"
down_revision = "20261002_credit_expiry_warned"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mastery_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id"),
    )
    op.create_index("ix_mastery_reports_code", "mastery_reports", ["code"], unique=True)
    op.create_index("ix_mastery_reports_user_id", "mastery_reports", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_mastery_reports_user_id", table_name="mastery_reports")
    op.drop_index("ix_mastery_reports_code", table_name="mastery_reports")
    op.drop_table("mastery_reports")
