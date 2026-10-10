"""Uso diario del tutor por usuario (38.6, ADR-49).

Una fila por usuario y día UTC. Sirve para el cupo de Pro y para medir el coste
real del tutor ilimitado de Pro Max, así que se cuenta en todos los planes.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TutorUsage(Base):
    __tablename__ = "tutor_usage"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    explanations: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    # 41.17: cupo por tokens, aparte del conteo de explicaciones -- una
    # conversación larga (conversation_history) cuesta mucho más que una
    # corta aunque las dos cuenten como "una explicación". Se cuenta en
    # todos los planes, igual que explanations, incluido Pro Max (ilimitado
    # en explicaciones por ADR-49, pero su coste real también hay que verlo).
    tokens_used: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
