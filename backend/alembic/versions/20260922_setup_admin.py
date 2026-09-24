"""Add is_admin column.

Hasta el 2026-09-24 esta migracion tambien insertaba `admin@whetzy.com` con un
hash de contrasena versionado en el repo, rol `superuser` (que `/admin` no
acepta: pide `owner` o `admin`) y un `connection.commit()` que rompia la
transaccion de Alembic y dejaba `alembic_version` sin avanzar en la primera
pasada. Ahora solo crea la columna; la cuenta de dueno la crea
`app.services.bootstrap_owner` desde `OWNER_EMAIL`/`OWNER_PASSWORD`, y
`20260924_owner_role` corrige las bases donde la insercion antigua ya corrio.
"""
from alembic import op
from sqlalchemy import inspect
import sqlalchemy as sa

revision = '20260922_setup_admin'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {col['name'] for col in inspect(op.get_bind()).get_columns('users')}
    if 'is_admin' not in columns:
        op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    op.drop_column('users', 'is_admin')
