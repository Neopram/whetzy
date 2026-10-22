"""User, per-skill learning state, and earned-badge models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import false, func

from app.core.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)

    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_emoji: Mapped[str] = mapped_column(String(16), default="🦉", nullable=False)

    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    streak_freeze_available: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    last_active: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    language: Mapped[str] = mapped_column(String(2), default="es", nullable=False)
    # Incremented on password change/reset to invalidate existing tokens (ASVS V3.3).
    jwt_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Push notification preferences (P.13)
    push_streak_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_streak_reminder_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Correos de marketing (hoy, el de reactivación con código): la política
    # publicada promete que todos se pueden cancelar (`legal.privacyCanSpam`).
    marketing_emails_opt_out: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )
    # 24.8: el perfil público `/u/<handle>` es privado por defecto; solo existe
    # si la persona lo activa (y el flag global PUBLIC_PROFILES_ENABLED lo permite).
    public_profile_opt_in: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )
    # Fin de periodo para el que ya salió el recordatorio de renovación (los
    # Términos lo prometen 7 días antes): uno por periodo, no uno por vuelta.
    renewal_reminder_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Caducidad de créditos de la que ya se avisó (ECONOMIA §2.4): un aviso por fecha.
    credit_expiry_warned_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Stripe subscription (7.2)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    subscription_status: Mapped[str | None] = mapped_column(String(32), nullable=True)  # active|canceled|past_due|trialing
    subscription_tier: Mapped[str | None] = mapped_column(String(16), nullable=True)  # plus|pro|creator (ADR-41)
    subscription_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Which rail last wrote the fields above (17.14): "stripe" | "revenuecat".
    # RevenueCat reuses this same entitlement contract instead of its own
    # columns — see the migration's docstring for why.
    subscription_provider: Mapped[str | None] = mapped_column(String(16), nullable=True)
    # Id de la suscripción en Paddle (`sub_...`): hace falta para cancelarla
    # cuando el alumno borra su cuenta (19.12).
    paddle_subscription_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    eu_withdrawal_waiver_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Tiempo de plan ganado con la escalera de referidos (ADR-35, ECONOMIA §3.3):
    # aparte de las columnas de suscripción, que reescriben los webhooks de pago.
    # `user_meets_tier` se queda con el mayor de los dos mientras esté en fecha.
    granted_tier: Mapped[str | None] = mapped_column(String(16), nullable=True)  # plus|pro
    granted_tier_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def active_granted_tier(self) -> str | None:
        """Plan ganado con referidos (ADR-57) si sigue en fecha. Un plan ganado
        sin fecha de fin cuenta como caducado, nunca como gratis para siempre."""
        until = self.granted_tier_expires_at
        if self.granted_tier is None or until is None:
            return None
        if until.tzinfo is None:
            until = until.replace(tzinfo=UTC)
        return self.granted_tier if until > datetime.now(UTC) else None

    @property
    def active_granted_until(self) -> datetime | None:
        return self.granted_tier_expires_at if self.active_granted_tier else None

    @property
    def is_owner(self) -> bool:
        """El panel de administración es solo del dueño (#202)."""
        return self.role == "owner"

    @property
    def public_profiles_enabled(self) -> bool:
        """Si el servidor publica perfiles (flag global). El interruptor de
        Perfil solo se enseña con esto en True."""
        from app.core.config import settings

        return settings.PUBLIC_PROFILES_ENABLED

    @property
    def tutor_deep_access(self) -> bool:
        """«A fondo» del tutor: solo Pro Max o superior (dueño, 2026-10-21)."""
        from app.core.entitlements import user_meets_tier

        return user_meets_tier(self, "pro")

    @property
    def can_create_courses(self) -> bool:
        """«Instructor» es para creadores (dueño, 2026-10-16): plan Creador, o el
        dueño y los admins, que montan el catálogo propio. La misma regla que
        `create_course` aplica con `CREATOR_PLAN_REQUIRED`. El import va aquí
        porque entitlements importa este módulo."""
        from app.core.entitlements import user_meets_tier

        return self.is_admin or self.is_owner or user_meets_tier(self, "creator")
    role: Mapped[str] = mapped_column(String(32), default="user", nullable=False)

    # Onboarding (24.3 / 34.11): índice de la opción elegida en cada pregunta
    # de segmento (0-2). NULL = no respondido. Se usa para decidir el primer
    # paso (prueba de nivel si ya programa) y para segmentar cohortes.
    onboarding_experience: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    onboarding_goal: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    onboarding_weekly_time: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    # 43.3 (ADR-65 D2): cuándo terminó el onboarding. Antes era una marca en
    # el localStorage y otro navegador lo repetía.
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # D-20 (dueño, 2026-10-12): la ruta que eligió en el onboarding, en el
    # servidor. Antes solo vivía en el localStorage del dispositivo.
    target_track_id: Mapped[str | None] = mapped_column(
        String(20), ForeignKey("tracks.id", ondelete="SET NULL"), nullable=True
    )
    # 43.3 (D2): la certificación relacionada que eligió en el onboarding,
    # aparte de la ruta de aprendizaje.
    target_certification_id: Mapped[str | None] = mapped_column(
        String(20), ForeignKey("tracks.id", ondelete="SET NULL"), nullable=True
    )
    # D-23: de dónde vino el alta (utm / referral / paid / direct), primer
    # contacto y una sola vez: se fija la primera vez y no se reescribe.
    # `signup_campaign` guarda el utm_campaign (o utm_source) tal cual, sin
    # terceros ni nada que identifique a la persona.
    signup_source: Mapped[str | None] = mapped_column(String(16), nullable=True)
    signup_campaign: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Ligas opcionales (35.4): fuera de la clasificación, sin sumar XP de liga
    # y sin aparecer en la de nadie. El XP y el nivel propios siguen igual.
    leagues_opt_out: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )

    # Age gate (19.11): user confirmed they are ≥16 years old at registration (ADR-70).
    age_confirmed: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )

    # CCPA/CPRA opt-out (21.3): user opted out of sale/sharing of personal data.
    ccpa_opt_out: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )

    skill_states: Mapped[list[UserSkillState]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    badges: Mapped[list[UserBadge]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.username!r}>"


class UserSkillState(Base):
    """Per-user, per-skill mastery/scheduling state combining BKT, Elo and FSRS."""

    __tablename__ = "user_skill_states"
    __table_args__ = (UniqueConstraint("user_id", "skill_id", name="uq_user_skill_state"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True
    )

    p_known: Mapped[float] = mapped_column(Float, default=0.1, nullable=False)
    elo_rating: Mapped[float] = mapped_column(Float, default=1500.0, nullable=False)
    fsrs_stability: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fsrs_difficulty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fsrs_due: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Counted apart from wrong answers so accuracy never reads an honest
    # "I don't know" as a failure the learner made.
    unknown_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default="0"
    )
    # 42.9 / ADR-63: the share of `attempts` that came from practice — the only
    # source that counts for the evidence gate (`domain_thresholds.is_mastered`).
    # Duels, test-outs and the placement test add to `attempts` only.
    practice_attempts: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default="0"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="skill_states")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UserSkillState user={self.user_id} skill={self.skill_id} p={self.p_known:.2f}>"


class UserBadge(Base):
    __tablename__ = "user_badges"
    __table_args__ = (UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    badge_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("badges.id", ondelete="CASCADE"), nullable=False, index=True
    )
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="badges")
