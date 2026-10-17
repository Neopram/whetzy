"""lesson_completions: relleno con lo ya practicado (43.5, ADR-65 D7).

Desde 43.5 practicar ya no cuenta como lección vista: la puerta de práctica
exige la lección abierta (o test-out, o ventaja en la prueba de nivel; H.60).
Hasta ahora `lesson_gate` aceptaba `user_skill_states.attempts > 0` para no
bloquear a quien había practicado antes de que existiera `lesson_completions`
(2026-09-27). Esa excepción se va del código y su efecto queda aquí, una vez:
cada skill con intentos pasa a tener su fila. Sin cambios de esquema; el código
anterior lee la tabla igual.

Revision ID: 20261017_lesson_backfill
Revises: 20261017_onboarding_completed
"""
from __future__ import annotations

from alembic import op

revision = "20261017_lesson_backfill"
down_revision = "20261017_onboarding_completed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "INSERT INTO lesson_completions (user_id, skill_id) "
        "SELECT user_id, skill_id FROM user_skill_states WHERE attempts > 0 "
        "ON CONFLICT (user_id, skill_id) DO NOTHING"
    )


def downgrade() -> None:
    # No se distingue una fila rellenada de una lección abierta de verdad, así
    # que no se borra nada: el código anterior acepta las dos.
    pass
