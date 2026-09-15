"""Add lessons table.

Stores short instructional content (150-300 words ES/EN + worked example)
tied to one skill. Delivered before adaptive quiz — instruction-before-practice
(Sweller worked-example effect). Multiple lessons per skill via `order` column.

Revision ID: p6q7r8s9t0u1
Revises: o5p6q7r8s9t0
Create Date: 2026-09-15 10:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "p6q7r8s9t0u1"
down_revision = "o5p6q7r8s9t0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lessons",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "skill_id",
            sa.String(64),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title_es", sa.String(200), nullable=False),
        sa.Column("title_en", sa.String(200), nullable=False),
        sa.Column("body_es", sa.Text, nullable=False),
        sa.Column("body_en", sa.Text, nullable=False),
        sa.Column("example_code", sa.Text, nullable=True),
        sa.Column("example_output", sa.Text, nullable=True),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("order", sa.Integer, nullable=False, server_default="1"),
    )
    op.create_index("ix_lessons_skill_id", "lessons", ["skill_id"])


def downgrade() -> None:
    op.drop_index("ix_lessons_skill_id", "lessons")
    op.drop_table("lessons")
