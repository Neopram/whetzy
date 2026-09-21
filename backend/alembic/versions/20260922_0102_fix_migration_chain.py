"""Fix migration chain after removing conflicting admin migrations."""
from alembic import op
import sqlalchemy as sa

revision = '20260922_0102'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
