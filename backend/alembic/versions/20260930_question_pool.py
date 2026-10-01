"""pool on questions (37.18): reserved mock-exam bank, separate from practice.

ADR-53 §4: a certification's mock exam must draw from a bank reserved for
that purpose (6x the exam length), never the same questions the learner
already saw in practice or spaced review — otherwise the score partly
measures memorized answers, not mastery. Today `mock_exam._questions_by_domain`
draws from the exact same pool `quiz._select_question` serves for practice
(see AUTONOMOUS_STATE.md row 37.18), so a "simulacro" score is inflated by
recall. This column is the mechanism that separates the two pools; it does
not by itself populate the reserved bank — that is authored content, a
separate step.

Every existing question defaults to "practica" (explicit, not NULL, so a
query can never silently include a row nobody classified yet).

Revision ID: 20260930_question_pool
Revises: 20260927_iap_provider
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260930_question_pool"
down_revision = "20260927_iap_provider"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("pool", sa.String(16), nullable=False, server_default="practica"),
    )


def downgrade() -> None:
    op.drop_column("questions", "pool")
