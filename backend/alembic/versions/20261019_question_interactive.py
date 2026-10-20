"""questions.interactive: la especificación de una pregunta `interactive` (40.1).

`{widget, params, target, checker}` en JSON; NULL en los demás tipos. Lo
rellena `content_loader` en cada deploy. Hasta que haya preguntas de este tipo
en `content/` (40.2, D1 de `docs/PLAN_UI_AVANZADA.md`) la columna queda vacía.

Revision ID: 20261019_question_interactive
Revises: 20261017_lesson_code_runtime
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261019_question_interactive"
down_revision = "20261017_lesson_code_runtime"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("interactive", sa.JSON(none_as_null=True), nullable=True))


def downgrade() -> None:
    op.drop_column("questions", "interactive")
