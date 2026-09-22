"""Add is_admin column and create admin superuser."""
from uuid import uuid4
from alembic import op
from sqlalchemy import text, inspect
import sqlalchemy as sa

revision = '20260922_setup_admin'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if is_admin column already exists
    connection = op.get_bind()
    inspector = inspect(connection)
    columns = {col['name'] for col in inspector.get_columns('users')}
    
    # Add is_admin column if it doesn't already exist
    if 'is_admin' not in columns:
        op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    
    # Create admin user only if it doesn't exist
    result = connection.execute(
        text("SELECT id FROM users WHERE email = 'admin@whetzy.com' LIMIT 1")
    )
    if not result.fetchone():
        admin_id = str(uuid4())
        try:
            # Use parameterized queries to avoid SQL injection and encoding issues
            connection.execute(
                text(
                    "INSERT INTO users ("
                    "id, email, username, hashed_password, display_name, avatar_emoji, "
                    "is_premium, is_active, email_verified, is_admin, role, created_at"
                    ") VALUES ("
                    ":id, :email, :username, :hashed_password, :display_name, :avatar_emoji, "
                    ":is_premium, :is_active, :email_verified, :is_admin, :role, now()"
                    ")"
                ),
                {
                    'id': admin_id,
                    'email': 'admin@whetzy.com',
                    'username': 'admin',
                    'hashed_password': '$2b$12$a7zErNi.HHmnhMMgKVUniOlaT4Fq/xCcK9Cqr4BQyVtNeMLYDM3ya',
                    'display_name': 'Admin',
                    'avatar_emoji': '👑',
                    'is_premium': True,
                    'is_active': True,
                    'email_verified': True,
                    'is_admin': True,
                    'role': 'superuser',
                }
            )
            connection.commit()
        except Exception as e:
            connection.rollback()
            # Alembic migrations should not raise exceptions; log and continue
            print(f"Warning: Could not create admin user: {e}")


def downgrade() -> None:
    op.drop_column('users', 'is_admin')
