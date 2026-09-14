"""Timed certification mock exam attempts (10.3).

Stores one sitting per row: the frozen question selection, the server-side
deadline and the graded report. Server-side because a timed mock whose clock
lives in the browser is not timed, and the time limit is the property the
exercise exists to rehearse.

Additive only: a new table, no changes to existing ones.

Revision ID: n4o5p6q7r8s9
Revises: m3n4o5p6q7r8
Create Date: 2026-09-14 09:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "n4o5p6q7r8s9"
down_revision = "m3n4o5p6q7r8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mock_exam_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("track_id", sa.String(length=64), nullable=False),
        sa.Column("question_ids", sa.JSON(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("report", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="in_progress"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_mock_exam_attempts_user_id", "mock_exam_attempts", ["user_id"], unique=False
    )
    op.create_index(
        "ix_mock_exam_attempts_track_id", "mock_exam_attempts", ["track_id"], unique=False
    )
    op.create_index(
        "ix_mock_exam_attempts_status", "mock_exam_attempts", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_mock_exam_attempts_status", table_name="mock_exam_attempts")
    op.drop_index("ix_mock_exam_attempts_track_id", table_name="mock_exam_attempts")
    op.drop_index("ix_mock_exam_attempts_user_id", table_name="mock_exam_attempts")
    op.drop_table("mock_exam_attempts")
