"""Create admin@whetzy.com user if not exists.

Revision ID: c0d1e2f3g4h5
Revises: b1c2d3e4f5a6
Create Date: 2026-09-22 00:00:00.000000

"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from alembic import op
import sqlalchemy as sa

revision = "c0d1e2f3g4h5"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None

ADMIN_PASSWORD_HASH = "$2b$12$a7zErNi.HHmnhMMgKVUniOlaT4Fq/xCcK9Cqr4BQyVtNeMLYDM3ya"

def upgrade() -> None:
    """Create admin user if not exists."""
    conn = op.get_bind()
    
    stmt = sa.text("""
        INSERT INTO users (id, email, username, hashed_password, display_name, language, email_verified, is_active, is_admin, created_at)
        VALUES (:id, :email, :username, :hashed_password, :display_name, :language, :email_verified, :is_active, :is_admin, :created_at)
        ON CONFLICT (email) DO NOTHING
    """)
    
    conn.execute(
        stmt,
        {
            "id": str(uuid.uuid4()),
            "email": "admin@whetzy.com",
            "username": "admin",
            "hashed_password": ADMIN_PASSWORD_HASH,
            "display_name": "Admin",
            "language": "es",
            "email_verified": True,
            "is_active": True,
            "is_admin": True,
            "created_at": datetime.now(UTC),
        },
    )


def downgrade() -> None:
    """Remove admin user."""
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM users WHERE email = 'admin@whetzy.com'"))
