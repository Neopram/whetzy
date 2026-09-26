"""Add bootcamp tables (19.4).

Revision ID: 20260926_bootcamps
Revises: 20260926_antifraud
Create Date: 2026-09-26
"""

import sqlalchemy as sa

from alembic import op

revision = "20260926_bootcamps"
down_revision = "20260926_antifraud"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bootcamps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("name_es", sa.String(200), nullable=False),
        sa.Column("name_en", sa.String(200), nullable=False),
        sa.Column("description_es", sa.Text(), nullable=False, server_default=""),
        sa.Column("description_en", sa.Text(), nullable=False, server_default=""),
        sa.Column("duration_weeks", sa.Integer(), nullable=False),
        sa.Column("daily_goal_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("icon", sa.String(32), nullable=False, server_default="rocket"),
        sa.Column("color", sa.String(16), nullable=False, server_default="#6366f1"),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bootcamps_slug", "bootcamps", ["slug"], unique=True)

    op.create_table(
        "bootcamp_weeks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("bootcamp_id", sa.Uuid(), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("track_id", sa.String(64), nullable=False),
        sa.Column("title_es", sa.String(200), nullable=False, server_default=""),
        sa.Column("title_en", sa.String(200), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["bootcamp_id"], ["bootcamps.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_bootcamp_weeks_bootcamp_id", "bootcamp_weeks", ["bootcamp_id"])

    op.create_table(
        "bootcamp_enrollments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("bootcamp_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("current_week", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["bootcamp_id"], ["bootcamps.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_bootcamp_enrollments_bootcamp_id", "bootcamp_enrollments", ["bootcamp_id"])
    op.create_index("ix_bootcamp_enrollments_user_id", "bootcamp_enrollments", ["user_id"])


def downgrade() -> None:
    op.drop_table("bootcamp_enrollments")
    op.drop_table("bootcamp_weeks")
    op.drop_table("bootcamps")
