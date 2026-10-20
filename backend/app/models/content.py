"""Content hierarchy: Track -> Module -> Skill -> Question."""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Track(Base):
    """A top-level learning path, e.g. 'Python Basics' or 'AI Engineering'.

    A certification track (`is_certification=True`) is the same Track row
    shape as the 7 core tracks — it just carries extra exam-blueprint fields
    (provider, question count, duration, passing score) and groups its
    skills into `Domain`s with official exam weights."""

    __tablename__ = "tracks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name_es: Mapped[str] = mapped_column(String(150), nullable=False)
    name_en: Mapped[str] = mapped_column(String(150), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    icon: Mapped[str] = mapped_column(String(16), default="📘", nullable=False)
    color: Mapped[str] = mapped_column(String(16), default="#6366F1", nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    is_certification: Mapped[bool] = mapped_column(default=False, nullable=False)
    cert_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Practice-exam blueprint (simulacro): number of questions, time limit,
    # and passing threshold as published by the certifying body. NULL for
    # non-certification tracks.
    exam_question_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exam_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    passing_score_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Un track que sale de `tracks.json` se retira (False), no se borra: el
    # borrado iba en cascada hasta respuestas, intentos y certificados (S.12).
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true(), nullable=False
    )

    modules: Mapped[list[Module]] = relationship(
        back_populates="track", cascade="all, delete-orphan", order_by="Module.order"
    )
    glossary_terms: Mapped[list[GlossaryTerm]] = relationship(
        back_populates="track", cascade="all, delete-orphan", order_by="GlossaryTerm.order"
    )
    domains: Mapped[list[Domain]] = relationship(
        back_populates="track", cascade="all, delete-orphan", order_by="Domain.order"
    )


class Module(Base):
    """A unit within a track. Unlocks once the previous module's average
    skill mastery reaches `min_mastery_to_unlock`."""

    __tablename__ = "modules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    track_id: Mapped[str] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name_es: Mapped[str] = mapped_column(String(150), nullable=False)
    name_en: Mapped[str] = mapped_column(String(150), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    description_es: Mapped[str] = mapped_column(Text, default="", nullable=False)
    description_en: Mapped[str] = mapped_column(Text, default="", nullable=False)
    min_mastery_to_unlock: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    track: Mapped[Track] = relationship(back_populates="modules")
    skills: Mapped[list[Skill]] = relationship(
        back_populates="module", cascade="all, delete-orphan", order_by="Skill.order"
    )


class Skill(Base):
    """An atomic, assessable unit of knowledge within a module."""

    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    module_id: Mapped[str] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name_es: Mapped[str] = mapped_column(String(150), nullable=False)
    name_en: Mapped[str] = mapped_column(String(150), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Exam domain this skill counts towards, for certification tracks only.
    # NULL for the 7 core tracks and for cert skills not yet mapped.
    domain_id: Mapped[str | None] = mapped_column(
        ForeignKey("domains.id", ondelete="SET NULL"), nullable=True, index=True
    )

    module: Mapped[Module] = relationship(back_populates="skills")
    domain: Mapped[Domain | None] = relationship(back_populates="skills")
    questions: Mapped[list[Question]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )


class Domain(Base):
    """An official exam domain within a certification track, e.g. AWS Cloud
    Practitioner's 'Cloud Concepts' or 'Security and Compliance'.

    `weight_pct` mirrors the certifying body's published exam blueprint
    (weights across a track's domains sum to 100) and drives the per-domain
    coverage check (10.2) and the per-domain simulacro report (10.3)."""

    __tablename__ = "domains"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    track_id: Mapped[str] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name_es: Mapped[str] = mapped_column(String(150), nullable=False)
    name_en: Mapped[str] = mapped_column(String(150), nullable=False)
    weight_pct: Mapped[float] = mapped_column(Float, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    track: Mapped[Track] = relationship(back_populates="domains")
    skills: Mapped[list[Skill]] = relationship(back_populates="domain")


class GlossaryTerm(Base):
    """A canonical domain term for a track, defined natively in ES and EN.

    Reference content — surfaced in the track glossary, independent of the
    question banks. `source` cites where the definition is grounded (a book +
    edition, a PEP, CPython docs, an RFC, a canonical paper, …)."""

    __tablename__ = "glossary_terms"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    track_id: Mapped[str] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    term_es: Mapped[str] = mapped_column(String(200), nullable=False)
    term_en: Mapped[str] = mapped_column(String(200), nullable=False)
    definition_es: Mapped[str] = mapped_column(Text, nullable=False)
    definition_en: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    track: Mapped[Track] = relationship(back_populates="glossary_terms")


class Question(Base):
    """A single assessable item. `elo_rating`/`discrimination`/`guessing`
    are continuously recalibrated from real response data (Elo + IRT)."""

    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    skill_id: Mapped[str] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(20), default="mcq", nullable=False)
    difficulty_tier: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)

    question_es: Mapped[str] = mapped_column(Text, nullable=False)
    question_en: Mapped[str] = mapped_column(Text, nullable=False)
    options_es: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    options_en: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    # For mcq/true_false/code_output: index into options. NULL for fill_blank,
    # which instead carries the accepted free-text answer in correct_answer_*.
    correct_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    correct_answer_es: Mapped[str | None] = mapped_column(Text, nullable=True)
    correct_answer_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Runnable code template for sql_exec questions (the full SQL script with
    # ___ as the student's blank). fill_blank_exec/fix_bug embed code inside
    # question_es/question_en as a fenced block instead (so these stay NULL).
    code_es: Mapped[str | None] = mapped_column(Text, nullable=True)
    code_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    # `interactive` (40.1): {widget, params, target, checker}. El servidor corrige
    # el `widget_state` del alumno contra `target` (services/widgets/checkers.py);
    # NULL en los demás tipos.
    interactive: Mapped[dict[str, Any] | None] = mapped_column(JSON(none_as_null=True), nullable=True)
    explanation_es: Mapped[str] = mapped_column(Text, default="", nullable=False)
    explanation_en: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # Canonical source citation (CPython docs, a PEP, a named book+edition, etc.).
    # NULL for legacy questions authored before source citations were required.
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    # "practica" (default) or "simulacro" (ADR-53 §4: reserved mock-exam bank,
    # 6x the exam length, never served by quiz._select_question — only by
    # mock_exam._questions_by_domain). Never confuse with SelectionReason.pool
    # in quiz.py, an unrelated skill-selection-strategy label ("review",
    # "new_skill", ...) on the response, not this column on the question.
    pool: Mapped[str] = mapped_column(String(16), default="practica", nullable=False)

    elo_rating: Mapped[float] = mapped_column(Float, default=1500.0, nullable=False)
    # Veces que una respuesta real movió `elo_rating` (quiz, duelo o examen).
    # Mientras sea 0 el rating es solo el prior editorial y el loader puede
    # sembrarlo; en cuanto vale > 0 ninguna sincronización de contenido lo toca
    # (regla «inmutabilidad del aprendizaje» del dueño, 2026-10-12). También es
    # el contador de interacciones del ítem para la K decreciente de `elo.py`.
    elo_updates: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    discrimination: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    guessing: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    expected_time_ms: Mapped[int] = mapped_column(Integer, default=15000, nullable=False)
    # Bumped by 1 each time the question text/options/answer are edited.
    # Responses carry the version that was active at answer time, preserving
    # historical accuracy even after corrections.
    content_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    skill: Mapped[Skill] = relationship(back_populates="questions")


class Lesson(Base):
    """Short instructional lesson tied to one skill.

    Delivered before the adaptive quiz so learners see instruction before
    practice (Sweller's worked-example effect). Contains the concept
    explanation, a worked example with expected output, and a canonical source.
    Multiple lessons per skill are allowed (order column sorts them).
    """

    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    skill_id: Mapped[str] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title_es: Mapped[str] = mapped_column(String(200), nullable=False)
    title_en: Mapped[str] = mapped_column(String(200), nullable=False)
    body_es: Mapped[str] = mapped_column(Text, nullable=False)
    body_en: Mapped[str] = mapped_column(Text, nullable=False)
    example_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    example_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 43.7: python | sql | js si el ejemplo se puede probar en el playground.
    code_runtime: Mapped[str | None] = mapped_column(String(16), nullable=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    skill: Mapped[Skill] = relationship()
