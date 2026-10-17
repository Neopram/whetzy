"""Multi-step project models (18.8 / 19.6)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.db import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    track_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    runtime: Mapped[str] = mapped_column(
        Enum("python", "sql", "js", name="project_runtime"), nullable=False
    )
    name_es: Mapped[str] = mapped_column(String(300), nullable=False)
    name_en: Mapped[str] = mapped_column(String(300), nullable=False)
    description_es: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description_en: Mapped[str] = mapped_column(Text, nullable=False, default="")
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    source_license: Mapped[str] = mapped_column(String(64), nullable=False, default="MIT")
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    steps: Mapped[list[ProjectStep]] = relationship(
        back_populates="project", cascade="all, delete-orphan",
        order_by="ProjectStep.step_number",
    )
    submissions: Mapped[list[ProjectSubmission]] = relationship(
        back_populates="project", cascade="all, delete-orphan",
    )


class ProjectStep(Base):
    __tablename__ = "project_steps"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title_es: Mapped[str] = mapped_column(String(300), nullable=False)
    title_en: Mapped[str] = mapped_column(String(300), nullable=False)
    instructions_es: Mapped[str] = mapped_column(Text, nullable=False, default="")
    instructions_en: Mapped[str] = mapped_column(Text, nullable=False, default="")
    starter_code: Mapped[str] = mapped_column(Text, nullable=False, default="")
    test_code: Mapped[str] = mapped_column(Text, nullable=False, default="")
    solution_code: Mapped[str] = mapped_column(Text, nullable=False, default="")

    project: Mapped[Project] = relationship(back_populates="steps")


class ProjectSubmission(Base):
    __tablename__ = "project_submissions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    current_step: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # 43.6: el código de cada paso ({"1": "...", ...}) para retomar donde se dejó.
    step_code: Mapped[dict[str, str]] = mapped_column(
        JSON, nullable=False, default=dict, server_default="{}"
    )
    # 43.6: completado con todos los pasos validados en el servidor (hoy, solo SQL).
    # Python/JS se validan en el navegador y no cuentan como evidencia.
    verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    project: Mapped[Project] = relationship(back_populates="submissions")
