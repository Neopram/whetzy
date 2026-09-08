"""SQLAlchemy models. Import this module (or any symbol from it) before
calling `Base.metadata.create_all` / running Alembic autogenerate so every
mapped class is registered on `Base.metadata`.
"""

from app.core.db import Base
from app.models.analytics import AnalyticsEvent
from app.models.content import GlossaryTerm, Module, Question, Skill, Track
from app.models.duel import Duel
from app.models.email_verification import EmailVerificationToken
from app.models.gamification import Badge, League, LeagueEntry, Mission, UserMission
from app.models.password_reset import PasswordResetToken
from app.models.question_report import QuestionReport
from app.models.session import Response, StudySession
from app.models.user import User, UserBadge, UserSkillState

__all__ = [
    "AnalyticsEvent",
    "Badge",
    "Base",
    "Duel",
    "EmailVerificationToken",
    "GlossaryTerm",
    "League",
    "LeagueEntry",
    "Mission",
    "Module",
    "PasswordResetToken",
    "Question",
    "QuestionReport",
    "Response",
    "Skill",
    "StudySession",
    "Track",
    "User",
    "UserBadge",
    "UserMission",
    "UserSkillState",
]
