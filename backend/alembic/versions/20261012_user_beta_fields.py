"""users: ruta elegida y origen del alta (D-20 y D-23 del dueño, 2026-10-12).

- `target_track_id`: la ruta que el alumno eligió en el onboarding. Antes solo
  vivía en el `localStorage` del dispositivo (`selectedTrackId`), así que se
  perdía al cambiar de navegador. FK a `tracks` con `ON DELETE SET NULL`.
- `signup_source` (utm / referral / paid / direct) y `signup_campaign`
  (utm_campaign o utm_source tal cual): de dónde vino el alta, primer contacto,
  sin terceros. Se fijan una vez y no se reescriben.

Tres columnas nuevas y nulas, sin relleno: el código anterior las ignora, así
que es segura con despliegues solapados.

Revision ID: 20261012_user_beta_fields
Revises: 20261012_question_elo_updates
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261012_user_beta_fields"
down_revision = "20261012_question_elo_updates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("target_track_id", sa.String(length=20), nullable=True))
    op.create_foreign_key(
        "fk_users_target_track_id_tracks",
        "users",
        "tracks",
        ["target_track_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column("users", sa.Column("signup_source", sa.String(length=16), nullable=True))
    op.add_column("users", sa.Column("signup_campaign", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "signup_campaign")
    op.drop_column("users", "signup_source")
    op.drop_constraint("fk_users_target_track_id_tracks", "users", type_="foreignkey")
    op.drop_column("users", "target_track_id")
