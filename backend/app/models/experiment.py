"""Experimentos A/B y sus asignaciones (24.14).

Usaba `PgUUID` con `server_default=func.gen_random_uuid()`, que es especifico de
Postgres: en los tests, que corren sobre SQLite, cualquier INSERT moria con
`unknown function: gen_random_uuid()`. El resto de modelos del repo generan el
UUID en Python, que funciona en los dos sitios.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="draft")
    variant_a_label: Mapped[str] = mapped_column(String(100), nullable=False)
    variant_b_label: Mapped[str] = mapped_column(String(100), nullable=False)
    hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assignments: Mapped[list["ExperimentAssignment"]] = relationship(
        back_populates="experiment"
    )

    def is_active(self) -> bool:
        now = datetime.now(timezone.utc)
        return self.status == "active" and (self.started_at or now) <= now

    def is_ended(self) -> bool:
        return self.status == "ended" or (
            self.ended_at is not None and datetime.now(timezone.utc) > self.ended_at
        )


class ExperimentAssignment(Base):
    __tablename__ = "experiment_assignments"
    __table_args__ = (
        UniqueConstraint("experiment_id", "user_id", name="uq_experiment_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    variant: Mapped[str] = mapped_column(String(10), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    experiment: Mapped[Experiment] = relationship(back_populates="assignments")

    def is_variant_a(self) -> bool:
        return self.variant == "A"

    def is_variant_b(self) -> bool:
        return self.variant == "B"
