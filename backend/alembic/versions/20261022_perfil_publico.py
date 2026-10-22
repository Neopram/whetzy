"""users.public_profile_opt_in: el perfil público es privado por defecto (24.8).

Antes `/u/<handle>` solo se cortaba con el flag global `PUBLIC_PROFILES_ENABLED`:
encendido, cualquier cuenta activa quedaba publicada sin que la persona lo
hubiera pedido. Ahora hace falta además su opt-in. `server_default` false:
las cuentas existentes quedan privadas, nadie se publica por la migración.

Revision ID: 20261022_perfil_publico
Revises: 20261022_track_blueprint
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261022_perfil_publico"
down_revision = "20261022_track_blueprint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "public_profile_opt_in",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "public_profile_opt_in")
