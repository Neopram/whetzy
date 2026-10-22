from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PublicCertificateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    track_name_es: str
    track_name_en: str
    issued_at: datetime


class PublicProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name_es: str
    name_en: str
    completed_at: datetime


class PublicProfileRead(BaseModel):
    """Perfil público de un alumno por `username` (0.3).

    Privado por defecto (24.8): solo se sirve si la persona activó
    `User.public_profile_opt_in` y el flag global lo permite. Nunca lleva el
    correo. Sin autenticación, como un certificado por su código.
    """

    model_config = ConfigDict(from_attributes=True)

    username: str
    display_name: str
    avatar_emoji: str
    joined_at: datetime
    current_streak: int
    mastery_avg: float
    skills_mastered: int
    certificates: list[PublicCertificateRead]
    projects_completed: list[PublicProjectRead]
