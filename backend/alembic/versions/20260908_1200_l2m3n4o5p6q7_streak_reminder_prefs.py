"""Streak reminder preferences on users (P.13).

Adds push_streak_enabled (bool default True) and last_streak_reminder_at
(nullable timestamp) to the users table.

Revision ID: l2m3n4o5p6q7
Revises: k1l2m3n4o5p6
Create Date: 2026-09-08 12:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "l2m3n4o5p6q7"
down_revision = "k1l2m3n4o5p6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("push_streak_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("last_streak_reminder_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "last_streak_reminder_at")
    op.drop_column("users", "push_streak_enabled")
