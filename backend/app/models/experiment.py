from datetime import datetime
from uuid import UUID
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PgUUID

from app.database import Base


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(PgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(128), nullable=False, unique=True)
    description = Column(String(512))
    status = Column(String(20), nullable=False, server_default="draft")
    variant_a_label = Column(String(100), nullable=False)
    variant_b_label = Column(String(100), nullable=False)
    hypothesis = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))

    assignments = relationship("ExperimentAssignment", back_populates="experiment")

    def is_active(self) -> bool:
        return self.status == "active" and (self.started_at or datetime.now()) <= datetime.now()

    def is_ended(self) -> bool:
        return self.status == "ended" or (self.ended_at and datetime.now() > self.ended_at)


class ExperimentAssignment(Base):
    __tablename__ = "experiment_assignments"
    __table_args__ = (UniqueConstraint("experiment_id", "user_id", name="uq_experiment_user"),)

    id = Column(PgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    experiment_id = Column(PgUUID(as_uuid=True), ForeignKey("experiments.id"), nullable=False)
    user_id = Column(PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    variant = Column(String(10), nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    experiment = relationship("Experiment", back_populates="assignments")

    def is_variant_a(self) -> bool:
        return self.variant == "A"

    def is_variant_b(self) -> bool:
        return self.variant == "B"
