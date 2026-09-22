"""Add is_admin column and create admin superuser."""
from uuid import uuid4
from alembic import op
from sqlalchemy import text
import sqlalchemy as sa

revision = '20260922_setup_admin'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_admin column if it doesn't exist
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))
    
    # Create admin user
    connection = op.get_bind()
    result = connection.execute(
        text("SELECT 1 FROM users WHERE email = 'admin@whetzy.com' LIMIT 1")
    )
    if not result.fetchone():
        admin_id = str(uuid4())
        try:
            connection.execute(
                text(
                    f"INSERT INTO users ("
                    f"id, email, username, hashed_password, display_name, avatar_emoji, "
                    f"is_premium, is_active, email_verified, is_admin, role, created_at"
                    f") VALUES ("
                    f"'{admin_id}', 'admin@whetzy.com', 'admin', "
                    f"'$2b$12$a7zErNi.HHmnhMMgKVUniOlaT4Fq/xCcK9Cqr4BQyVtNeMLYDM3ya', "
                    f"'Admin', '👑', true, true, true, true, 'superuser', now()"
                    f")"
                )
            )
            connection.commit()
        except Exception:
            connection.rollback()


def downgrade() -> None:
    op.drop_column('users', 'is_admin')
