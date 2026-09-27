"""Lecciones abiertas por usuario y día UTC (39.4, ADR-50a).

Solo se escribe con el cupo Free encendido y para usuarios a los que se aplica:
es el contador de `FREE_DAILY_LESSONS`, no analítica.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class LessonView(Base):
    __tablename__ = "lesson_views"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    day: Mapped[date] = mapped_column(Date, primary_key=True)
