"""Anti-fraud service for referral and credit system (29.5).

Controls from ECONOMIA.md §3.5 and where each one runs:
1. Email verified before activation counts — ReferralService.activate_ready_referrals
2. Device+IP hashing — max 1 per device/IP per 30 days — validate_registration
3. Self-referral detection (same normalized email or device) — validate_registration
4. Disposable email domain blocklist — validate_registration
5. 7-day delay — ReferralService.credit_matured_referrals
6. Velocity cap: >5 activations/week → manual review — activate_ready_referrals
7. Clawback on refund/ban/fraud — not wired: there is no ban or fraud-confirmation
   flow to trigger it (MAPA_PRODUCTO §5.1)
"""

import hashlib
import hmac
import os
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.antifraud import DeviceFingerprint, FraudReviewQueue
from app.models.economy import Referral
from app.models.user import User

_HASH_SALT = os.environ.get("ANTIFRAUD_SALT", "whetzy-antifraud-default-salt")

DISPOSABLE_DOMAINS: set[str] = {
    "mailinator.com",
    "guerrillamail.com",
    "guerrillamailblock.com",
    "tempmail.com",
    "throwaway.email",
    "temp-mail.org",
    "fakeinbox.com",
    "sharklasers.com",
    "guerrillamail.info",
    "grr.la",
    "guerrillamail.net",
    "guerrillamail.de",
    "trbvm.com",
    "dispostable.com",
    "yopmail.com",
    "yopmail.fr",
    "cool.fr.nf",
    "jetable.fr.nf",
    "nospam.ze.tc",
    "nomail.xl.cx",
    "mega.zik.dj",
    "speed.1s.fr",
    "courriel.fr.nf",
    "moncourrier.fr.nf",
    "monemail.fr.nf",
    "monmail.fr.nf",
    "trashmail.com",
    "trashmail.me",
    "trashmail.net",
    "trashymail.com",
    "10minutemail.com",
    "10minutemail.co.za",
    "bccto.me",
    "armyspy.com",
    "cuvox.de",
    "dayrep.com",
    "einrot.com",
    "fleckens.hu",
    "gustr.com",
    "jourrapide.com",
    "rhyta.com",
    "superrito.com",
    "teleworm.us",
    "maildrop.cc",
    "discard.email",
    "tempail.com",
    "mohmal.com",
    "getnada.com",
    "emailondeck.com",
    "33mail.com",
    "mailnesia.com",
    "spamgourmet.com",
    "mytemp.email",
    "tempinbox.com",
    "tempr.email",
}


def _hash_value(value: str) -> str:
    return hmac.new(
        _HASH_SALT.encode(),
        value.lower().strip().encode(),
        hashlib.sha256,
    ).hexdigest()


def normalize_email(email: str) -> str:
    local, _, domain = email.lower().strip().partition("@")
    if domain in ("gmail.com", "googlemail.com"):
        local = local.split("+")[0].replace(".", "")
        domain = "gmail.com"
    elif "+" in local:
        local = local.split("+")[0]
    return f"{local}@{domain}"


class AntiFraudService:
    """Validates referral activations against fraud rules."""

    @staticmethod
    async def check_email_verified(db: AsyncSession, user_id: uuid.UUID) -> bool:
        result = await db.execute(
            select(User.email_verified).where(User.id == user_id)
        )
        return bool(result.scalar())

    @staticmethod
    def is_disposable_email(email: str) -> bool:
        _, _, domain = email.lower().strip().partition("@")
        return domain in DISPOSABLE_DOMAINS

    @staticmethod
    async def check_self_referral(
        db: AsyncSession,
        referrer_id: uuid.UUID,
        referred_id: uuid.UUID,
        referred_email: str,
        device_fingerprint: str | None = None,
    ) -> bool:
        """Returns True if this looks like a self-referral."""
        if referrer_id == referred_id:
            return True

        referrer = await db.execute(
            select(User.email).where(User.id == referrer_id)
        )
        referrer_email = referrer.scalar()
        if referrer_email and normalize_email(referrer_email) == normalize_email(
            referred_email
        ):
            return True

        if device_fingerprint:
            fp_hash = _hash_value(device_fingerprint)
            existing = await db.execute(
                select(DeviceFingerprint).where(
                    and_(
                        DeviceFingerprint.user_id == referrer_id,
                        DeviceFingerprint.fingerprint_hash == fp_hash,
                    )
                )
            )
            if existing.scalar():
                return True

        return False

    @staticmethod
    async def check_device_rate_limit(
        db: AsyncSession,
        device_fingerprint: str,
        ip_address: str,
        window_days: int = 30,
    ) -> bool:
        """Returns True if device/IP has already activated within the window."""
        cutoff = datetime.now(UTC) - timedelta(days=window_days)
        fp_hash = _hash_value(device_fingerprint)
        ip_hash = _hash_value(ip_address)

        result = await db.execute(
            select(func.count()).where(
                and_(
                    (DeviceFingerprint.fingerprint_hash == fp_hash)
                    | (DeviceFingerprint.ip_hash == ip_hash),
                    DeviceFingerprint.created_at >= cutoff,
                )
            )
        )
        count = result.scalar() or 0
        return count > 0

    @staticmethod
    async def record_device(
        db: AsyncSession,
        user_id: uuid.UUID,
        device_fingerprint: str,
        ip_address: str,
    ) -> None:
        db.add(
            DeviceFingerprint(
                user_id=user_id,
                fingerprint_hash=_hash_value(device_fingerprint),
                ip_hash=_hash_value(ip_address),
            )
        )
        await db.flush()

    @staticmethod
    async def check_velocity(
        db: AsyncSession,
        referrer_id: uuid.UUID,
        max_per_week: int = 5,
    ) -> bool:
        """Returns True if referrer has exceeded velocity cap (needs review)."""
        week_ago = datetime.now(UTC) - timedelta(days=7)
        result = await db.execute(
            select(func.count())
            .select_from(Referral)
            .where(
                and_(
                    Referral.referrer_id == referrer_id,
                    Referral.status.in_(["activated", "credited"]),
                    Referral.activated_at >= week_ago,
                )
            )
        )
        count = result.scalar() or 0
        return count >= max_per_week

    @staticmethod
    async def flag_for_review(
        db: AsyncSession,
        referrer_id: uuid.UUID,
        reason: str,
        activation_count: int,
    ) -> None:
        existing = await db.execute(
            select(FraudReviewQueue).where(
                and_(
                    FraudReviewQueue.referrer_id == referrer_id,
                    FraudReviewQueue.status == "pending",
                )
            )
        )
        if existing.scalar():
            return

        db.add(
            FraudReviewQueue(
                referrer_id=referrer_id,
                reason=reason,
                activation_count=activation_count,
            )
        )
        await db.flush()

    @staticmethod
    async def validate_registration(
        db: AsyncSession,
        referred_user_id: uuid.UUID,
        referred_email: str,
        referrer_id: uuid.UUID,
        device_fingerprint: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[bool, str]:
        """Controles al registrar el referido (ECONOMIA §3.5). Returns (allowed, reason).

        El email verificado y la velocidad van en la activación, no aquí: el
        código se registra al terminar el onboarding, antes de que nadie haya
        abierto el correo de verificación, y exigirlo aquí perdía el referido
        de todo el que no entraba con OAuth (2026-10-01).
        """
        if AntiFraudService.is_disposable_email(referred_email):
            return False, "disposable_email"

        if await AntiFraudService.check_self_referral(
            db, referrer_id, referred_user_id, referred_email, device_fingerprint
        ):
            return False, "self_referral"

        if (
            device_fingerprint
            and ip_address
            and await AntiFraudService.check_device_rate_limit(
                db, device_fingerprint, ip_address
            )
        ):
            return False, "device_rate_limited"

        if device_fingerprint and ip_address:
            await AntiFraudService.record_device(
                db, referred_user_id, device_fingerprint, ip_address
            )

        return True, "ok"
