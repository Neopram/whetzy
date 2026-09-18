"""Analytics event log (5.4).

Creates the analytics_events table for typed user-action tracking.

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-09-08 09:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "i9j0k1l2m3n4"
down_revision = "h8i9j0k1l2m3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analytics_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("properties", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analytics_user_type", "analytics_events", ["user_id", "event_type"])
    op.create_index("ix_analytics_created_at", "analytics_events", ["created_at"])
    op.create_index("ix_analytics_events_event_type", "analytics_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_analytics_events_event_type", table_name="analytics_events")
    op.drop_index("ix_analytics_created_at", table_name="analytics_events")
    op.drop_index("ix_analytics_user_type", table_name="analytics_events")
    op.drop_table("analytics_events")
