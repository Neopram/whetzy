from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.services.username_filter import contains_blocked_word


def _reject_blocked_word(value: str) -> str:
    if contains_blocked_word(value):
        raise ValueError("That name isn't allowed")
    return value


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")
    display_name: str = Field(min_length=1, max_length=100)
    language: str = Field(default="es", pattern="^(es|en)$")


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    age_confirmed: bool = False

    # 43.2 (ADR-65 D10): antes de validar, fuera los espacios que deja el
    # autocompletado del móvil, y el email en minúsculas: `Maria@Gmail.COM` se
    # guardaba tal cual y quien entraba con `maria@gmail.com` no la encontraba.
    @field_validator("email", "username", "display_name", mode="before")
    @classmethod
    def _recortar(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email", mode="before")
    @classmethod
    def _email_en_minusculas(cls, value: object) -> object:
        return value.lower() if isinstance(value, str) else value

    # Solo al escribir (19.11): `UserRead` también hereda de `UserBase` pero
    # lee de `from_attributes`, y un filtro aquí reventaría leer una cuenta ya
    # existente si la lista de palabras cambia después de crearla.
    _validar_username = field_validator("username")(_reject_blocked_word)
    _validar_display_name = field_validator("display_name")(_reject_blocked_word)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    avatar_emoji: str | None = Field(default=None, max_length=16)
    language: str | None = Field(default=None, pattern="^(es|en)$")

    @field_validator("display_name")
    @classmethod
    def _sin_palabra_bloqueada(cls, value: str | None) -> str | None:
        if value is not None:
            _reject_blocked_word(value)
        return value


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    avatar_emoji: str
    level: int
    total_xp: int
    current_streak: int
    max_streak: int
    streak_freeze_available: int
    last_active: datetime | None = None
    created_at: datetime
    # Plan de pago. El checkout decide con él si ya hay suscripción y si el
    # pago llegó: no incluye el plan ganado con referidos, que va aparte.
    is_premium: bool
    # Plan ganado con referidos (ADR-57), solo mientras está en fecha.
    granted_tier: str | None = Field(
        default=None, validation_alias=AliasChoices("active_granted_tier", "granted_tier")
    )
    granted_tier_expires_at: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices("active_granted_until", "granted_tier_expires_at"),
    )
    email_verified: bool = False
    # Correos de ofertas (reactivación): False si el usuario se dio de baja.
    marketing_emails_opt_out: bool = False
    onboarding_experience: int | None = None
    onboarding_goal: int | None = None
    onboarding_weekly_time: int | None = None
    onboarding_completed_at: datetime | None = None
    target_track_id: str | None = None
    target_certification_id: str | None = None
    # Qué enlaces ve en Perfil (auditoría de pantallas, 2026-10-16): «Instructor»
    # solo para creadores y «Admin» solo para el dueño. Calculados del modelo.
    can_create_courses: bool = False
    is_owner: bool = False
    # Ola 2: si el tutor le ofrece «A fondo» (Pro Max o superior).
    tutor_deep_access: bool = False


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str | None = None
    type: str | None = None
    exp: int | None = None
    iat: int | None = None
    jvs: int | None = None  # jwt_version for revocation (ASVS V3.3)


class RefreshRequest(BaseModel):
    refresh_token: str


class UserSkillStateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill_id: str
    p_known: float
    elo_rating: float
    fsrs_stability: float
    fsrs_difficulty: float
    fsrs_due: datetime | None = None
    attempts: int
    correct_count: int


class UserBadgeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    badge_id: str
    earned_at: datetime
