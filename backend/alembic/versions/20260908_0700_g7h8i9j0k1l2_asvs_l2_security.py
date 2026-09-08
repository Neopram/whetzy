"""ASVS L2 security hardening: jwt_version on users table.

Adds jwt_version column (default 1) so tokens can be invalidated on
password change/reset without a blocklist (ASVS V3.3 / V2.1.5).

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2026-09-08 07:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "g7h8i9j0k1l2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("jwt_version", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("users", "jwt_version")
