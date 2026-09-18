"""Add question_reports table for defective-question reporting (P.6).

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-08 06:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "question_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.String(64), nullable=False),
        sa.Column("reason", sa.String(50), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_question_reports_user_id", "question_reports", ["user_id"])
    op.create_index("ix_question_reports_question_id", "question_reports", ["question_id"])


def downgrade() -> None:
    op.drop_index("ix_question_reports_question_id", table_name="question_reports")
    op.drop_index("ix_question_reports_user_id", table_name="question_reports")
    op.drop_table("question_reports")
