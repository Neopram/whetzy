"""UGC moderation between users: reporting and blocking (19.11, App Store 1.2/1.2.1).

Minimal on purpose: no moderation queue, no automatic action on a report —
just a record for the owner to review, and a block that the social surfaces
(duels, leagues) read to hide each other from blocked pairs.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.user import User

VALID_REPORT_REASONS = frozenset({"inappropriate_name", "harassment", "spam", "other"})
#: Dónde se vio al usuario reportado/bloqueado, para el panel del dueño.
VALID_REPORT_CONTEXTS = frozenset({"duel", "league", "profile", "other"})


class UserReport(Base):
    __tablename__ = "user_reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reported_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(String(32), nullable=False)
    context: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    reporter: Mapped[User] = relationship("User", foreign_keys=[reporter_id])
    reported: Mapped[User] = relationship("User", foreign_keys=[reported_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UserReport {self.id} {self.reporter_id}->{self.reported_id} reason={self.reason}>"


class UserBlock(Base):
    __tablename__ = "user_blocks"
    __table_args__ = (UniqueConstraint("blocker_id", "blocked_id", name="uq_user_blocks_pair"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    blocker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    blocked_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    blocker: Mapped[User] = relationship("User", foreign_keys=[blocker_id])
    blocked: Mapped[User] = relationship("User", foreign_keys=[blocked_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UserBlock {self.id} {self.blocker_id}->{self.blocked_id}>"
