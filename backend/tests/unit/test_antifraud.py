"""Tests for anti-fraud service (29.5)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.antifraud import DeviceFingerprint, FraudReviewQueue
from app.models.economy import Referral
from app.models.user import User
from app.services.antifraud import (
    AntiFraudService,
    normalize_email,
)


def _make_user(email: str = "test@example.com", verified: bool = True) -> User:
    return User(
        id=uuid4(),
        email=email,
        username=f"user_{uuid4().hex[:8]}",
        hashed_password="x",
        display_name="Test",
        email_verified=verified,
        age_confirmed=True,
    )


@pytest.mark.asyncio
async def test_registration_does_not_require_verified_email(db_session: AsyncSession):
    """El código se registra al terminar el onboarding, antes de verificar el
    email: exigirlo aquí perdía el referido de todo el que no entraba con OAuth.
    La verificación cuenta en la activación (test_referral_program)."""
    user = _make_user(verified=False)
    db_session.add(user)
    await db_session.flush()

    allowed, reason = await AntiFraudService.validate_registration(
        db_session,
        referred_user_id=user.id,
        referred_email=user.email,
        referrer_id=uuid4(),
    )
    assert allowed
    assert reason == "ok"


@pytest.mark.asyncio
async def test_email_verified_passes(db_session: AsyncSession):
    assert await AntiFraudService.check_email_verified(db_session, uuid4()) is False

    user = _make_user(verified=True)
    db_session.add(user)
    await db_session.flush()
    assert await AntiFraudService.check_email_verified(db_session, user.id) is True


@pytest.mark.asyncio
async def test_disposable_email_blocked(db_session: AsyncSession):
    user = _make_user(email="test@mailinator.com", verified=True)
    db_session.add(user)
    await db_session.flush()

    allowed, reason = await AntiFraudService.validate_registration(
        db_session,
        referred_user_id=user.id,
        referred_email=user.email,
        referrer_id=uuid4(),
    )
    assert not allowed
    assert reason == "disposable_email"


def test_disposable_domains():
    assert AntiFraudService.is_disposable_email("a@mailinator.com")
    assert AntiFraudService.is_disposable_email("a@yopmail.com")
    assert AntiFraudService.is_disposable_email("a@guerrillamail.com")
    assert not AntiFraudService.is_disposable_email("a@gmail.com")
    assert not AntiFraudService.is_disposable_email("a@company.org")


def test_normalize_email():
    assert normalize_email("User@GMAIL.COM") == "user@gmail.com"
    assert normalize_email("us.er+tag@gmail.com") == "user@gmail.com"
    assert normalize_email("user+tag@googlemail.com") == "user@gmail.com"
    assert normalize_email("user+tag@example.com") == "user@example.com"
    assert normalize_email("  User@Example.COM  ") == "user@example.com"


@pytest.mark.asyncio
async def test_self_referral_same_id(db_session: AsyncSession):
    user_id = uuid4()
    result = await AntiFraudService.check_self_referral(
        db_session, referrer_id=user_id, referred_id=user_id,
        referred_email="a@b.com"
    )
    assert result is True


@pytest.mark.asyncio
async def test_self_referral_same_normalized_email(db_session: AsyncSession):
    referrer = _make_user(email="john.doe+ref@gmail.com")
    referred = _make_user(email="johndoe@gmail.com")
    db_session.add_all([referrer, referred])
    await db_session.flush()

    result = await AntiFraudService.check_self_referral(
        db_session,
        referrer_id=referrer.id,
        referred_id=referred.id,
        referred_email=referred.email,
    )
    assert result is True


@pytest.mark.asyncio
async def test_self_referral_different_email_passes(db_session: AsyncSession):
    referrer = _make_user(email="alice@example.com")
    referred = _make_user(email="bob@example.com")
    db_session.add_all([referrer, referred])
    await db_session.flush()

    result = await AntiFraudService.check_self_referral(
        db_session,
        referrer_id=referrer.id,
        referred_id=referred.id,
        referred_email=referred.email,
    )
    assert result is False


@pytest.mark.asyncio
async def test_device_rate_limit(db_session: AsyncSession):
    user1 = _make_user(email="u1@example.com")
    user2 = _make_user(email="u2@example.com")
    db_session.add_all([user1, user2])
    await db_session.flush()

    assert not await AntiFraudService.check_device_rate_limit(
        db_session, "device-abc", "1.2.3.4"
    )

    await AntiFraudService.record_device(db_session, user1.id, "device-abc", "1.2.3.4")

    assert await AntiFraudService.check_device_rate_limit(
        db_session, "device-abc", "1.2.3.4"
    )

    assert not await AntiFraudService.check_device_rate_limit(
        db_session, "device-xyz", "5.6.7.8"
    )


@pytest.mark.asyncio
async def test_device_rate_limit_same_ip_different_device(db_session: AsyncSession):
    user = _make_user()
    db_session.add(user)
    await db_session.flush()

    await AntiFraudService.record_device(db_session, user.id, "device-a", "1.2.3.4")
    assert await AntiFraudService.check_device_rate_limit(
        db_session, "device-b", "1.2.3.4"
    )


@pytest.mark.asyncio
async def test_velocity_cap(db_session: AsyncSession):
    referrer = _make_user(email="referrer@example.com")
    db_session.add(referrer)
    await db_session.flush()

    for i in range(5):
        referred = _make_user(email=f"referred{i}@example.com")
        db_session.add(referred)
        await db_session.flush()
        db_session.add(
            Referral(
                referrer_id=referrer.id,
                referred_id=referred.id,
                status="activated",
                activated_at=datetime.now(UTC),
            )
        )
    await db_session.flush()

    exceeded = await AntiFraudService.check_velocity(db_session, referrer.id)
    assert exceeded is True


@pytest.mark.asyncio
async def test_velocity_under_cap(db_session: AsyncSession):
    referrer = _make_user(email="referrer2@example.com")
    db_session.add(referrer)
    await db_session.flush()

    for i in range(3):
        referred = _make_user(email=f"ref2_{i}@example.com")
        db_session.add(referred)
        await db_session.flush()
        db_session.add(
            Referral(
                referrer_id=referrer.id,
                referred_id=referred.id,
                status="activated",
                activated_at=datetime.now(UTC),
            )
        )
    await db_session.flush()

    exceeded = await AntiFraudService.check_velocity(db_session, referrer.id)
    assert exceeded is False


@pytest.mark.asyncio
async def test_flag_for_review_idempotent(db_session: AsyncSession):
    referrer_id = uuid4()
    await AntiFraudService.flag_for_review(
        db_session, referrer_id, "velocity_exceeded", 6
    )
    await AntiFraudService.flag_for_review(
        db_session, referrer_id, "velocity_exceeded", 7
    )

    result = await db_session.execute(
        select(FraudReviewQueue).where(
            FraudReviewQueue.referrer_id == referrer_id
        )
    )
    entries = result.scalars().all()
    assert len(entries) == 1


@pytest.mark.asyncio
async def test_full_validation_happy_path(db_session: AsyncSession):
    referrer = _make_user(email="ref@example.com")
    referred = _make_user(email="new@example.com")
    db_session.add_all([referrer, referred])
    await db_session.flush()

    allowed, reason = await AntiFraudService.validate_registration(
        db_session,
        referred_user_id=referred.id,
        referred_email=referred.email,
        referrer_id=referrer.id,
        device_fingerprint="device-happy",
        ip_address="10.0.0.1",
    )
    assert allowed
    assert reason == "ok"

    result = await db_session.execute(
        select(DeviceFingerprint).where(
            DeviceFingerprint.user_id == referred.id
        )
    )
    assert result.scalar() is not None


@pytest.mark.asyncio
async def test_farm_simulation_100_same_device(db_session: AsyncSession):
    """100 registrations from the same device → only 1st activation allowed."""
    referrer = _make_user(email="farmer@example.com")
    db_session.add(referrer)
    await db_session.flush()

    allowed_count = 0
    for i in range(100):
        referred = _make_user(email=f"farm{i}@example.com")
        db_session.add(referred)
        await db_session.flush()

        allowed, _ = await AntiFraudService.validate_registration(
            db_session,
            referred_user_id=referred.id,
            referred_email=referred.email,
            referrer_id=referrer.id,
            device_fingerprint="same-device-for-all",
            ip_address="192.168.1.1",
        )
        if allowed:
            allowed_count += 1

    assert allowed_count == 1
