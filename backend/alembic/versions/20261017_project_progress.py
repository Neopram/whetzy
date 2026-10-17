"""project_submissions: código por paso y «verificado» (43.6, ADR-65 D8).

`step_code` guarda el código de cada paso para retomar el proyecto donde se
dejó. `verified` marca un proyecto completado con todos sus pasos validados en
el servidor (hoy, los SQL); los de Python/JS se validan en el navegador y no
salen en el perfil público hasta que haya sandbox. Las filas que ya existían
quedan sin verificar: se completaron creyendo el `passed` del cliente.

Revision ID: 20261017_project_progress
Revises: 20261017_lesson_backfill
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261017_project_progress"
down_revision = "20261017_lesson_backfill"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "project_submissions",
        sa.Column("step_code", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "project_submissions",
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("project_submissions", "verified")
    op.drop_column("project_submissions", "step_code")
