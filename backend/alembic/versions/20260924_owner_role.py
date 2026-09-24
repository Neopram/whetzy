"""Corregir la cuenta que creaba la version antigua de 20260922_setup_admin.

Dos arreglos de datos, ambos no-op en una base nueva:

1. `role = 'superuser'` no existe para la app: `/admin` exige `owner` o
   `admin` (`endpoints/admin.py`), asi que esa cuenta entraba y recibia 403.
   Pasa a `owner`.
2. El hash de la contrasena estuvo versionado en el repo. Cualquier cuenta que
   lo conserve lo pierde (`NULL` = el login lo trata como contrasena
   incorrecta, como a las cuentas solo-OAuth). Se compara el valor exacto: si
   alguien ya cambio esa contrasena, no se toca. La contrasena buena se fija
   con `OWNER_EMAIL`/`OWNER_PASSWORD` (ver `app/services/bootstrap_owner.py`).

Revision ID: 20260924_owner_role
Revises: 20260922_setup_admin
"""
from alembic import op
from sqlalchemy import text

revision = '20260924_owner_role'
down_revision = '20260922_setup_admin'
branch_labels = None
depends_on = None

_LEAKED_HASH = '$2b$12$a7zErNi.HHmnhMMgKVUniOlaT4Fq/xCcK9Cqr4BQyVtNeMLYDM3ya'


def upgrade() -> None:
    op.execute(text("UPDATE users SET role = 'owner', is_admin = true WHERE role = 'superuser'"))
    op.execute(
        text("UPDATE users SET hashed_password = NULL WHERE hashed_password = :h").bindparams(h=_LEAKED_HASH)
    )


def downgrade() -> None:
    # Irreversible a proposito: no se restaura un rol que la app no entiende
    # ni una contrasena publicada.
    pass
