"""questions.elo_updates: cuántas respuestas reales movieron el Elo del ítem.

Regla del dueño del 2026-10-12 («inmutabilidad del aprendizaje»): una vez que
`elo_rating` contiene evidencia de respuestas reales, ninguna sincronización de
contenido puede devolverlo a un prior editorial. `content_loader` corre en cada
arranque, así que necesita saber qué preguntas ya aprendieron; `responses` no
basta porque los duelos y los exámenes mueven el Elo sin crear fila allí.

Relleno de las filas existentes, conservador (ante la duda, «ya aprendió»):
- el número de filas de `responses` de la pregunta (incluye las de placement,
  que no mueven el Elo: cuenta de más, nunca de menos), y
- al menos 1 si el rating ya no es el 1500 por defecto (lo movió un duelo o un
  examen; ninguna pregunta del banco trae `difficulty`, así que el loader no
  pudo ponerlo ahí).

Columna nueva con `server_default`: el código anterior la ignora, así que es
segura con despliegues solapados.

Revision ID: 20261012_question_elo_updates
Revises: 20261012_paddle_events
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261012_question_elo_updates"
down_revision = "20261012_paddle_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("elo_updates", sa.Integer(), nullable=False, server_default="0"),
    )
    op.execute(
        """
        UPDATE questions SET elo_updates = GREATEST(
            (SELECT count(*) FROM responses r WHERE r.question_id = questions.id),
            CASE WHEN elo_rating <> 1500.0 THEN 1 ELSE 0 END
        )
        """
    )


def downgrade() -> None:
    op.drop_column("questions", "elo_updates")
