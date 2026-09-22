"""Create admin superuser."""
from uuid import uuid4
from alembic import op
from sqlalchemy.orm import Session
from sqlalchemy import insert
from datetime import datetime

revision = '20260922_admin'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get the connection and create a session
    connection = op.get_bind()
    
    # Insert admin user using raw SQL with explicit UUID
    admin_id = str(uuid4())
    connection.execute(
        f"""
        INSERT INTO users (
            id, email, username, hashed_password, display_name, 
            avatar_emoji, is_premium, is_active, email_verified, 
            role, created_at
        ) VALUES (
            '{admin_id}',
            'admin@whetzy.com',
            'admin',
            '$2b$12$a7zErNi.HHmnhMMgKVUniOlaT4Fq/xCcK9Cqr4BQyVtNeMLYDM3ya',
            'Admin',
            '👑',
            true,
            true,
            true,
            'superuser',
            now()
        )
        ON CONFLICT DO NOTHING
        """
    )
    connection.commit()


def downgrade() -> None:
    pass
