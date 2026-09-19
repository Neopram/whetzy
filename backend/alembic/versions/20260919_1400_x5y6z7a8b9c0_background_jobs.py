"""Add background jobs table (Series 22.6).

Revision ID: x5y6z7a8b9c0
Revises: w3x4y5z6a7b8
Create Date: 2026-09-19 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "x5y6z7a8b9c0"
down_revision = "w3x4y5z6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create jobs table for async background work (email, exports, etc.)."""
    op.create_table(
        "jobs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            server_default="queued",
            nullable=False,
        ),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_jobs_user_status",
        "jobs",
        ["user_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_jobs_status_created",
        "jobs",
        ["status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop jobs table."""
    op.drop_index("idx_jobs_status_created", table_name="jobs")
    op.drop_index("idx_jobs_user_status", table_name="jobs")
    op.drop_table("jobs")
