"""SQLAlchemy models. Import this module (or any symbol from it) before
calling `Base.metadata.create_all` / running Alembic autogenerate so every
mapped class is registered on `Base.metadata`.
"""

from app.core.db import Base
from app.models.content import GlossaryTerm, Module, Question, Skill, Track
from app.models.duel import Duel
from app.models.email_verification import EmailVerificationToken
from app.models.gamification import Badge, League, LeagueEntry, Mission, UserMission
from app.models.password_reset import PasswordResetToken
from app.models.session import Response, StudySession
from app.models.user import User, UserBadge, UserSkillState

__all__ = [
    "Base",
    "User",
    "UserSkillState",
    "UserBadge",
    "Track",
    "Module",
    "Skill",
    "Question",
    "GlossaryTerm",
    "League",
    "LeagueEntry",
    "Badge",
    "Mission",
    "UserMission",
    "StudySession",
    "Response",
    "Duel",
    "PasswordResetToken",
    "EmailVerificationToken",
]
