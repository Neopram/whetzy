"""Integration tests for auth hardening in login, refresh, and logout endpoints."""

from __future__ import annotations

import uuid

import pytest
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.auth import AuditLog, LoginAttempt
from app.models.user import User


@pytest.mark.asyncio
async def test_login_with_lockout_triggers_429(
    client, db_session: AsyncSession
) -> None:
    """Test that login with lockout triggers 429 status."""
    # Create a test user
    email = f"lockout-test-{uuid.uuid4().hex[:6]}@test.whetzy"
    password = "TestPassword123!"
    user = User(
        id=uuid.uuid4(),
        email=email,
        username=f"lockouttest{uuid.uuid4().hex[:4]}",
        hashed_password=get_password_hash(password),
        display_name="Lockout Test",
        language="en",
    )
    db_session.add(user)
    await db_session.commit()

    # Create 5 failed login attempts to trigger lockout
    for i in range(5):
        attempt = LoginAttempt(email=email, ip="127.0.0.1", success=False)
        db_session.add(attempt)
    await db_session.commit()

    # Try to login - should get 429 (Too Many Requests)
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    
    assert response.status_code == 429
    assert "temporarily locked" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_successful_login_records_attempt_and_creates_session(
    client, db_session: AsyncSession
) -> None:
    """Test that successful login records attempt and creates session."""
    # Create a test user
    email = f"success-test-{uuid.uuid4().hex[:6]}@test.whetzy"
    password = "TestPassword123!"
    user = User(
        id=uuid.uuid4(),
        email=email,
        username=f"successtest{uuid.uuid4().hex[:4]}",
        hashed_password=get_password_hash(password),
        display_name="Success Test",
        language="en",
    )
    db_session.add(user)
    await db_session.commit()

    # Login successfully
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

    # Verify login attempt was recorded
    result = await db_session.execute(
        sqlalchemy.select(LoginAttempt).where(
            LoginAttempt.email == email, LoginAttempt.success == True
        )
    )
    attempts = result.scalars().all()
    assert len(attempts) > 0

    # Verify audit log entry was created
    result = await db_session.execute(
        sqlalchemy.select(AuditLog).where(
            AuditLog.action == "login_success", AuditLog.user_id == user.id
        )
    )
    audit_logs = result.scalars().all()
    assert len(audit_logs) > 0


@pytest.mark.asyncio
async def test_failed_login_records_attempt(
    client, db_session: AsyncSession
) -> None:
    """Test that failed login records attempt."""
    # Create a test user
    email = f"failed-test-{uuid.uuid4().hex[:6]}@test.whetzy"
    password = "TestPassword123!"
    user = User(
        id=uuid.uuid4(),
        email=email,
        username=f"failedtest{uuid.uuid4().hex[:4]}",
        hashed_password=get_password_hash(password),
        display_name="Failed Test",
        language="en",
    )
    db_session.add(user)
    await db_session.commit()

    # Try to login with wrong password
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "WrongPassword123!"},
    )
    
    assert response.status_code == 401

    # Verify failed attempt was recorded
    result = await db_session.execute(
        sqlalchemy.select(LoginAttempt).where(
            LoginAttempt.email == email, LoginAttempt.success == False
        )
    )
    attempts = result.scalars().all()
    assert len(attempts) > 0

    # Verify audit log entry was created
    result = await db_session.execute(
        sqlalchemy.select(AuditLog).where(
            AuditLog.action == "login_failed"
        )
    )
    audit_logs = result.scalars().all()
    assert len(audit_logs) > 0


@pytest.mark.asyncio
async def test_audit_trail_is_created(
    client, db_session: AsyncSession
) -> None:
    """Test that audit trail is created for login, refresh, and logout."""
    # Create a test user
    email = f"audit-test-{uuid.uuid4().hex[:6]}@test.whetzy"
    password = "TestPassword123!"
    user = User(
        id=uuid.uuid4(),
        email=email,
        username=f"auditest{uuid.uuid4().hex[:4]}",
        hashed_password=get_password_hash(password),
        display_name="Audit Test",
        language="en",
    )
    db_session.add(user)
    await db_session.commit()

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    tokens = response.json()

    # Verify login_success audit log
    result = await db_session.execute(
        sqlalchemy.select(AuditLog).where(
            AuditLog.action == "login_success", AuditLog.user_id == user.id
        )
    )
    login_logs = result.scalars().all()
    assert len(login_logs) > 0
    assert login_logs[-1].result == "success"

    # Refresh token
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert response.status_code == 200

    # Verify refresh audit log
    result = await db_session.execute(
        sqlalchemy.select(AuditLog).where(
            AuditLog.action == "refresh_token_issued", AuditLog.user_id == user.id
        )
    )
    refresh_logs = result.scalars().all()
    assert len(refresh_logs) > 0

    # Logout
    response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 200

    # Verify logout audit log
    result = await db_session.execute(
        sqlalchemy.select(AuditLog).where(
            AuditLog.action == "logout", AuditLog.user_id == user.id
        )
    )
    logout_logs = result.scalars().all()
    assert len(logout_logs) > 0
    assert logout_logs[-1].result == "success"


