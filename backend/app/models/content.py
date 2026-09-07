"""Content hierarchy: Track -> Module -> Skill -> Question."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Track(Base):
    """A top-level learning path, e.g. 'Python Basics' or 'AI Engineering'."""

    __tablename__ = "tracks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name_es: Mapped[str] = mapped_column(String(150), nullable=False)
    name_en: Mapped[str] = mapped_column(String(150), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    icon: Mapped[str] = mapped_column(String(16), default="📘", nullable=False)
    color: Mapped[str] = mapped_column(String(16), default="#6366F1", nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    modules: Mapped[list["Module"]] = relationship(
        back_populates="track", cascade="all, delete-orphan", order_by="Module.order"
    )
    glossary_terms: Mapped[list["GlossaryTerm"]] = relationship(
        back_populates="track", cascade="all, delete-orphan", order_by="GlossaryTerm.order"
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

    track: Mapped["Track"] = relationship(back_populates="modules")
    skills: Mapped[list["Skill"]] = relationship(
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

    module: Mapped["Module"] = relationship(back_populates="skills")
    questions: Mapped[list["Question"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )


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

    track: Mapped["Track"] = relationship(back_populates="glossary_terms")


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
    options_es: Mapped[list | None] = mapped_column(JSON, nullable=True)
    options_en: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # For mcq/true_false/code_output: index into options. NULL for fill_blank,
    # which instead carries the accepted free-text answer in correct_answer_*.
    correct_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    correct_answer_es: Mapped[str | None] = mapped_column(Text, nullable=True)
    correct_answer_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation_es: Mapped[str] = mapped_column(Text, default="", nullable=False)
    explanation_en: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # Canonical source citation (CPython docs, a PEP, a named book+edition, etc.).
    # NULL for legacy questions authored before source citations were required.
    source: Mapped[str | None] = mapped_column(Text, nullable=True)

    elo_rating: Mapped[float] = mapped_column(Float, default=1500.0, nullable=False)
    discrimination: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    guessing: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    expected_time_ms: Mapped[int] = mapped_column(Integer, default=15000, nullable=False)

    skill: Mapped["Skill"] = relationship(back_populates="questions")
