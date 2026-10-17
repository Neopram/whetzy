"""users: `onboarding_completed_at` y `target_certification_id` (43.3, ADR-65 D2).

Antes el onboarding se daba por hecho con una marca en el `localStorage` del
navegador (`whetzy_onboarded_<id>`): en otro navegador, otro móvil o tras borrar
datos, el alumno lo repetía. Ahora vive en el servidor.

Relleno: las cuentas que ya respondieron el onboarding (alguna de sus
respuestas o la ruta elegida, que el cliente solo envía al terminarlo) quedan
con su `created_at`.

`target_certification_id`: la certificación relacionada que el alumno elige en
el onboarding, aparte de su ruta de aprendizaje (`target_track_id`). FK a
`tracks` con `ON DELETE SET NULL`, como `target_track_id`.

Columnas nulas, así que el código anterior la ignora y es
segura con despliegues solapados.

Revision ID: 20261017_onboarding_completed
Revises: 20261012_user_beta_fields
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261017_onboarding_completed"
down_revision = "20261012_user_beta_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.execute(
        "UPDATE users SET onboarding_completed_at = created_at "
        "WHERE onboarding_goal IS NOT NULL OR onboarding_experience IS NOT NULL "
        "OR target_track_id IS NOT NULL"
    )
    op.add_column(
        "users", sa.Column("target_certification_id", sa.String(length=20), nullable=True)
    )
    op.create_foreign_key(
        "fk_users_target_certification_id_tracks",
        "users",
        "tracks",
        ["target_certification_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_users_target_certification_id_tracks", "users", type_="foreignkey")
    op.drop_column("users", "target_certification_id")
    op.drop_column("users", "onboarding_completed_at")
