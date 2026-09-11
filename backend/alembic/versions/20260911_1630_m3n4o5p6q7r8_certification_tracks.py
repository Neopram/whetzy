"""Certification track data model (10.1): domains, exam weights, simulacro blueprint.

A certification track (e.g. AWS Cloud Practitioner) reuses the existing
Track -> Module -> Skill -> Question hierarchy — it's just a Track row with
is_certification=True plus an exam blueprint (provider, question count,
duration, passing score). New Domains table groups a cert track's skills
into official exam domains with published weights, for per-domain coverage
(10.2) and per-domain simulacro reporting (10.3). All new columns are
nullable or default-False, so the 7 existing core tracks are unaffected.

Revision ID: m3n4o5p6q7r8
Revises: l2m3n4o5p6q7
Create Date: 2026-09-11 16:30
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "m3n4o5p6q7r8"
down_revision = "l2m3n4o5p6q7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "domains",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "track_id",
            sa.String(length=64),
            sa.ForeignKey("tracks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name_es", sa.String(length=150), nullable=False),
        sa.Column("name_en", sa.String(length=150), nullable=False),
        sa.Column("weight_pct", sa.Float(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_domains_track_id", "domains", ["track_id"])

    op.add_column(
        "tracks",
        sa.Column("is_certification", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column("tracks", sa.Column("cert_provider", sa.String(length=64), nullable=True))
    op.add_column("tracks", sa.Column("exam_question_count", sa.Integer(), nullable=True))
    op.add_column("tracks", sa.Column("exam_duration_minutes", sa.Integer(), nullable=True))
    op.add_column("tracks", sa.Column("passing_score_pct", sa.Float(), nullable=True))

    op.add_column(
        "skills",
        sa.Column(
            "domain_id",
            sa.String(length=64),
            sa.ForeignKey("domains.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_skills_domain_id", "skills", ["domain_id"])


def downgrade() -> None:
    op.drop_index("ix_skills_domain_id", table_name="skills")
    op.drop_column("skills", "domain_id")

    op.drop_column("tracks", "passing_score_pct")
    op.drop_column("tracks", "exam_duration_minutes")
    op.drop_column("tracks", "exam_question_count")
    op.drop_column("tracks", "cert_provider")
    op.drop_column("tracks", "is_certification")

    op.drop_index("ix_domains_track_id", table_name="domains")
    op.drop_table("domains")
