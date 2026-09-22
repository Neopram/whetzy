"""Create admin superuser."""
from uuid import uuid4
from alembic import op
from sqlalchemy import text

revision = '20260922_admin'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    
    # Check if admin already exists
    result = connection.execute(
        text("SELECT 1 FROM users WHERE email = 'admin@whetzy.com' LIMIT 1")
    )
    if result.fetchone():
        return  # Already exists, skip
    
    # Insert admin user with explicit UUID
    admin_id = str(uuid4())
    try:
        connection.execute(
            text(
                f"INSERT INTO users (id, email, username, hashed_password, display_name, avatar_emoji, is_premium, is_active, email_verified, role, created_at) "
                f"VALUES ('{admin_id}', 'admin@whetzy.com', 'admin', '$2b$12$a7zErNi.HHmnhMMgKVUniOlaT4Fq/xCcK9Cqr4BQyVtNeMLYDM3ya', 'Admin', '👑', true, true, true, 'superuser', now())"
            )
        )
        connection.commit()
    except Exception:
        connection.rollback()


def downgrade() -> None:
    pass
