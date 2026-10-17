"""lessons.code_runtime: en qué runtime se prueba el ejemplo (43.7, ADR-65 D9).

`python`, `sql` o `js` cuando el playground del navegador puede ejecutar el
ejemplo de la lección; NULL si no (shell, YAML…). Lo rellena `content_loader`,
que corre en cada deploy; hasta entonces las lecciones no ofrecen el botón.

Revision ID: 20261017_lesson_code_runtime
Revises: 20261017_project_progress
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261017_lesson_code_runtime"
down_revision = "20261017_project_progress"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("lessons", sa.Column("code_runtime", sa.String(length=16), nullable=True))


def downgrade() -> None:
    op.drop_column("lessons", "code_runtime")
