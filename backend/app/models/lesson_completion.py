"""Lecciones vistas alguna vez, para exigirlas antes del quiz (32.4).

Independiente del cupo Free (`lesson_views` / `content_quota.py`): esto se
escribe siempre que haya sesión, tenga o no cupo aplicado el usuario -- solo
importa si la fila existe, nunca el día. `lesson_views` no sirve para esto:
solo se escribe cuando el cupo Free está encendido y le aplica al usuario, así
que para todos los demás (Pro, Pro Max, dueño, admin, o con el flag apagado)
estaría siempre vacía.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class LessonCompletion(Base):
    __tablename__ = "lesson_completions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
