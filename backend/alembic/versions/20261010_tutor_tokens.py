"""tutor_usage.tokens_used: cupo por tokens del tutor, aparte del conteo de
explicaciones (S.17, plan de la noche 2026-10-04).

Antes solo se contaban explicaciones (`explanations`), no tokens: una
conversación larga (`conversation_history`) cuesta mucho más al LLM que una
corta aunque las dos cuenten como "una explicación" para el cupo diario de
Plus. Esta columna guarda el total acumulado de tokens del día, igual que
`explanations` -- se cuenta en todos los planes, incluido Pro Max (sin
límite de explicaciones por ADR-49, pero su coste real también hay que
poder verlo).

Nullable no: tiene `server_default="0"`, así que una fila existente de
`tutor_usage` (puede haberlas de antes de este deploy) se rellena a 0 sola,
sin backfill aparte -- es la cifra correcta para un día en el que todavía
no existía esta columna.

ID corto a propósito (19 caracteres): `20261004_study_session_current_question`
(39 caracteres, del #127) desbordó el `varchar(32)` de `alembic_version` y
tumbó producción el 2026-10-10 (#165, hotfix).

Rebasada sobre `20261010_oauth_pkce` (hotfix, 2026-10-11): el #170 (S.14) y
este PR (S.17) nacieron del mismo padre (`20261004_current_question_id`) en
ramas distintas y el #170 se fusionó primero en `master`. El PR de esta
migración (#173) se fusionó sin rebasar: `master` quedó con DOS cabezas de
Alembic (`20261010_oauth_pkce` y `20261010_tutor_tokens`), lo que hace que
`alembic upgrade head` falle en el próximo deploy automático. Hotfix igual
que el #165.

Revision ID: 20261010_tutor_tokens
Revises: 20261010_oauth_pkce
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261010_tutor_tokens"
down_revision = "20261010_oauth_pkce"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tutor_usage",
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("tutor_usage", "tokens_used")
