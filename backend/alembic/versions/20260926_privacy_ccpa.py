"""Add ccpa_opt_out column to users table (21.3).

Revision ID: 20260926_privacy_ccpa
Revises: 20260926_projects
Create Date: 2026-09-26
"""

from alembic import op
import sqlalchemy as sa

revision = "20260926_privacy_ccpa"
down_revision = "20260926_projects"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "ccpa_opt_out",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "ccpa_opt_out")
