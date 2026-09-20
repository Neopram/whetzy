"""SQLAlchemy models. Import this module (or any symbol from it) before
calling `Base.metadata.create_all` / running Alembic autogenerate so every
mapped class is registered on `Base.metadata`.

**Todo modulo de `app/models/` tiene que aparecer aqui.** Un modulo que
falte no esta en `Base.metadata`, y entonces `alembic --autogenerate`
compara la base contra un metadata incompleto y propone **borrar** sus
tablas. Paso con siete —admin, campaign, economy, experiment, instructor,
oauth, payment— que tenian migraciones aplicadas y datos en produccion.
`tests/test_modelos_registrados.py` lo vigila.
"""

from app.core.db import Base
from app.models.admin import GDPRRequest
from app.models.analytics import AnalyticsEvent
from app.models.auth import AuditLog, LoginAttempt, RefreshToken, User2FA, UserSession
from app.models.campaign import Campaign, CampaignClick
from app.models.content import Domain, GlossaryTerm, Module, Question, Skill, Track
from app.models.duel import Duel
from app.models.economy import (
    CreditExpenseCap,
    CreditLedger,
    PromoCode,
    PromoCodeRedemption,
    Referral,
    ReferralCode,
)
from app.models.email_verification import EmailVerificationToken
from app.models.exam import MockExamAttempt
from app.models.experiment import Experiment, ExperimentAssignment
from app.models.gamification import Badge, League, LeagueEntry, Mission, UserMission
from app.models.instructor import (
    Instructor,
    InstructorCourse,
    InstructorEnrollment,
    InstructorPayout,
)
from app.models.job import Job
from app.models.oauth import OAuthAccount, OAuthState
from app.models.password_reset import PasswordResetToken
from app.models.payment import (
    InstructorPayoutMethod,
    PaddleSubscription,
    PaymentRailConfig,
    PaymentWebhook,
    StripeCustomer,
)
from app.models.push_subscription import PushSubscription
from app.models.question_report import QuestionReport
from app.models.session import Response, StudySession
from app.models.user import User, UserBadge, UserSkillState

__all__ = [
    "AnalyticsEvent",
    "AuditLog",
    "Badge",
    "Base",
    "Campaign",
    "CampaignClick",
    "CreditExpenseCap",
    "CreditLedger",
    "Domain",
    "Duel",
    "EmailVerificationToken",
    "Experiment",
    "ExperimentAssignment",
    "GDPRRequest",
    "GlossaryTerm",
    "Instructor",
    "InstructorCourse",
    "InstructorEnrollment",
    "InstructorPayout",
    "InstructorPayoutMethod",
    "Job",
    "League",
    "LeagueEntry",
    "LoginAttempt",
    "Mission",
    "MockExamAttempt",
    "Module",
    "OAuthAccount",
    "OAuthState",
    "PaddleSubscription",
    "PasswordResetToken",
    "PaymentRailConfig",
    "PaymentWebhook",
    "PromoCode",
    "PromoCodeRedemption",
    "PushSubscription",
    "Question",
    "QuestionReport",
    "Referral",
    "ReferralCode",
    "RefreshToken",
    "Response",
    "Skill",
    "StripeCustomer",
    "StudySession",
    "Track",
    "User",
    "User2FA",
    "UserBadge",
    "UserMission",
    "UserSession",
    "UserSkillState",
]
