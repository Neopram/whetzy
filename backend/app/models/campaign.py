"""Campaign tracking model (Serie 26 — Distribución Masiva ES).

Stores campaign metadata and click events for distribution channels.
Links: YouTube (YT-ES-*), Dev.to (DEV-ES-*), LinkedIn (LI-ES-*)

Endpoint: GET /api/v1/admin/campaigns/{code}/stats
Returns: Campaign cohort (signups, retention, conversion)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.db import Base


class CampaignStatus(str, Enum):
    """Campaign lifecycle."""
    DRAFT = "draft"  # Planning phase
    ACTIVE = "active"  # Live on channels
    PAUSED = "paused"  # Temporarily halted
    ARCHIVED = "archived"  # Historical (no longer promoted)


class CampaignChannel(str, Enum):
    """Distribution channel."""
    YOUTUBE = "youtube"
    DEV_TO = "devto"
    LINKEDIN = "linkedin"
    EMAIL = "email"
    REDDIT = "reddit"
    TWITTER = "twitter"
    ORGANIC = "organic"  # Direct traffic / referral


class Campaign(Base):
    """Campaign record (parent of clicks)."""

    __tablename__ = "campaigns"
    __table_args__ = (
        Index("ix_campaigns_code", "code"),
        Index("ix_campaigns_channel", "channel"),
        Index("ix_campaigns_status", "status"),
        Index("ix_campaigns_created_at", "created_at"),
        UniqueConstraint("code", name="uq_campaign_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Campaign identifier (YT-ES-PROD, DEV-ES-1, etc.)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)

    # Human-readable name
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Distribution channel
    channel: Mapped[CampaignChannel] = mapped_column(
        SQLEnum(CampaignChannel), nullable=False, default=CampaignChannel.ORGANIC
    )

    # Current status
    status: Mapped[CampaignStatus] = mapped_column(
        SQLEnum(CampaignStatus), nullable=False, default=CampaignStatus.DRAFT
    )

    # Campaign metadata (notes, URLs, targeting)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # URL to campaign asset (YouTube video, Dev.to article, etc.)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Series reference (26.0, 26.1, etc.)
    series: Mapped[str] = mapped_column(String(16), nullable=False, default="26.0")

    # Dates
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    launched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship: clicks on this campaign
    clicks: Mapped[list[CampaignClick]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Campaign {self.code!r} ({self.channel.value})>"


class CampaignClick(Base):
    """Individual click event from campaign."""

    __tablename__ = "campaign_clicks"
    __table_args__ = (
        Index("ix_campaign_clicks_campaign_id", "campaign_id"),
        Index("ix_campaign_clicks_user_id", "user_id"),
        Index("ix_campaign_clicks_created_at", "created_at"),
        Index("ix_campaign_clicks_source", "source"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Foreign key to campaign
    # Sin `index=True`: el indice ya esta declarado arriba en `__table_args__`
    # con ese mismo nombre, y SQLAlchemy genera `ix_campaign_clicks_campaign_id`
    # para los dos. Declararlo dos veces hace que `create_all` reviente con
    # «index ... already exists». No se vio hasta hoy porque este modulo no
    # estaba importado en `app/models/__init__.py`, asi que nunca se creaba.
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    campaign: Mapped[Campaign] = relationship(back_populates="clicks")

    # User who clicked (nullable for anonymous clicks)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Click source (banner, external link, direct paste, etc.)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="url_param")

    # User agent / device info (for analytics)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Referrer (if available)
    referrer: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CampaignClick campaign={self.campaign_id!r} user={self.user_id!r}>"
