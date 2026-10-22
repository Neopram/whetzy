"""user_skill_states.practice_attempts: la evidencia que cuenta para la puerta (42.9).

ADR-63 §3: «dominada» pide ≥ 7 respuestas de PRÁCTICA. Hasta hoy solo existía
`attempts`, que mezcla práctica, duelo, test-out y prueba de nivel.

El relleno es exacto, no una aproximación. Toda respuesta de práctica deja una
fila en `responses` dentro de una `study_sessions` que no es de prueba de nivel;
el duelo y el test-out no dejan ninguna. Así que se cuentan esas filas por
(usuario, skill), con `attempts` como techo.

Revision ID: 20261022_evidence_por_fuente
Revises: 20261020_admin_action_log
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261022_evidence_por_fuente"
down_revision = "20261020_admin_action_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_skill_states",
        sa.Column("practice_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.execute(
        """
        UPDATE user_skill_states
        SET practice_attempts = LEAST(
            user_skill_states.attempts,
            (
                SELECT COUNT(*)
                FROM responses r
                JOIN study_sessions s ON s.id = r.session_id
                JOIN questions q ON q.id = r.question_id
                WHERE s.user_id = user_skill_states.user_id
                  AND q.skill_id = user_skill_states.skill_id
                  AND s.mode <> 'placement'
            )
        )
        """
    )


def downgrade() -> None:
    op.drop_column("user_skill_states", "practice_attempts")
