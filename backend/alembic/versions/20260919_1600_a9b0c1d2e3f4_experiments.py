"""Add experiments table for A/B testing.

Revision ID: a9b0c1d2e3f4
Revises: v0w1x2y3z4a5
Create Date: 2026-09-19

"""
from alembic import op
import sqlalchemy as sa


revision = "a9b0c1d2e3f4"
down_revision = "v0w1x2y3z4a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "experiments",
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("description", sa.String(512)),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("variant_a_label", sa.String(100), nullable=False),
        sa.Column("variant_b_label", sa.String(100), nullable=False),
        sa.Column("hypothesis", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "experiment_assignments",
        sa.Column("id", sa.UUID, primary_key=True),
        sa.Column("experiment_id", sa.UUID, sa.ForeignKey("experiments.id"), nullable=False),
        sa.Column("user_id", sa.UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("variant", sa.String(10), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("experiment_id", "user_id", name="uq_experiment_user"),
    )

    op.create_index("ix_experiments_status", "experiments", ["status"])
    op.create_index("ix_experiment_assignments_experiment", "experiment_assignments", ["experiment_id"])


def downgrade() -> None:
    op.drop_table("experiment_assignments")
    op.drop_table("experiments")
