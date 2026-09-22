"""Create admin superuser."""
from uuid import uuid4
from alembic import op
from sqlalchemy import text

revision = '20260922_admin'
down_revision = '20260922_add_is_admin'
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
    
    # Insert admin user - ONLY core fields that definitely exist
    admin_id = str(uuid4())
    try:
        connection.execute(
            text(
                f"INSERT INTO users ("
                f"id, email, username, hashed_password, display_name, "
                f"is_premium, is_active, email_verified, role, created_at"
                f") VALUES ("
                f"'{admin_id}', 'admin@whetzy.com', 'admin', "
                f"'$2b$12$a7zErNi.HHmnhMMgKVUniOlaT4Fq/xCcK9Cqr4BQyVtNeMLYDM3ya', "
                f"'Admin', true, true, true, 'superuser', now()"
                f")"
            )
        )
        connection.commit()
    except Exception:
        connection.rollback()


def downgrade() -> None:
    pass
