"""study_sessions.current_question_id: solo se puede responder la pregunta
servida, una vez (S.4, plan de la noche 2026-10-04).

Antes nada guardaba qué pregunta era la que `/quiz/start` o el
`next_question` de `/quiz/answer` acababan de servir: el endpoint aceptaba
cualquier `question_id` de la base, tantas veces como se quisiera. Esta
columna guarda la pregunta pendiente; `/quiz/answer` la exige y la mueve a
la siguiente tras cada respuesta, así que un `question_id` ya respondido
deja de coincidir sin otra columna para "una vez".

Nullable y sin backfill a propósito, pero no gratis: una sesión en curso en
el momento del despliegue tiene `current_question_id = NULL`, y
`quiz.py:592` compara `session.current_question_id != req.question_id` sin
tratar NULL aparte — `None` nunca coincide con un `question_id` real, así
que esa sesión recibe un 409 en su siguiente `/quiz/answer` (no "el camino
normal"). Es aceptable: el alumno pierde la respuesta a esa una pregunta en
vuelo y puede reintentar, y ADR-45 ya avisa de ~1 min de 502/503 en cada
deploy a master, así que las sesiones activas justo en ese minuto son
pocas.

Rebasada tras abrir el PR: esta migración se escribió sobre
`20261002_newsletter_subscribers` (migración 54), pero S.12
(`tracks_is_active`) se fusionó primero reclamando ese mismo número — esta
pasa a depender de esa, 55 en la cadena real.

Revision ID: 20261004_current_question_id
Revises: 20261004_tracks_is_active
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261004_current_question_id"
down_revision = "20261004_tracks_is_active"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "study_sessions",
        sa.Column("current_question_id", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("study_sessions", "current_question_id")
