"""Tests for monthly payout scheduling and Paddle webhooks (28.7)."""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.instructor import Instructor, InstructorPayout
from app.models.job import Job
from app.models.user import User
from app.services.job_worker import handle_run_payouts


@pytest.mark.asyncio
async def test_payout_job_pending_payouts(db_session: AsyncSession) -> None:
    """Test payout job handles pending instructor payouts."""
    user = User(
        id=uuid.uuid4(),
        email=f"instructor-{uuid.uuid4().hex[:8]}@whetzy.test",
        username=f"instructor{uuid.uuid4().hex[:6]}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name="Test Instructor",
    )
    db_session.add(user)
    await db_session.flush()

    instructor = Instructor(
        id=uuid.uuid4(),
        user_id=user.id,
        display_name="Test Instructor",
    )
    db_session.add(instructor)
    await db_session.flush()

    payout = InstructorPayout(
        id=uuid.uuid4(),
        instructor_id=instructor.id,
        period_start=datetime.now(UTC) - timedelta(days=30),
        period_end=datetime.now(UTC),
        earnings_cents=10000,
        status="pending",
    )
    db_session.add(payout)
    await db_session.commit()

    job = Job(
        id=1,
        user_id=user.id,
        job_type="run_payouts",
        status="running",
        payload={},
    )

    result = await handle_run_payouts(job, db_session)

    assert result["processed_count"] == 1
    assert result["total_paid_cents"] == 10000
    assert result["instructor_count"] == 1
    assert result["filtered_out_count"] == 0

    await db_session.refresh(payout)
    assert payout.status == "processing"


@pytest.mark.asyncio
async def test_payout_job_filters_below_minimum(db_session: AsyncSession) -> None:
    """Test payout job filters out payouts under €50 minimum."""
    user = User(
        id=uuid.uuid4(),
        email=f"instructor-{uuid.uuid4().hex[:8]}@whetzy.test",
        username=f"instructor{uuid.uuid4().hex[:6]}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name="Test Instructor",
    )
    db_session.add(user)
    await db_session.flush()

    instructor = Instructor(
        id=uuid.uuid4(),
        user_id=user.id,
        display_name="Test Instructor",
    )
    db_session.add(instructor)
    await db_session.flush()

    payout = InstructorPayout(
        id=uuid.uuid4(),
        instructor_id=instructor.id,
        period_start=datetime.now(UTC) - timedelta(days=30),
        period_end=datetime.now(UTC),
        earnings_cents=3000,
        status="pending",
    )
    db_session.add(payout)
    await db_session.commit()

    job = Job(
        id=1,
        user_id=user.id,
        job_type="run_payouts",
        status="running",
        payload={},
    )

    result = await handle_run_payouts(job, db_session)

    assert result["processed_count"] == 0
    assert result["total_paid_cents"] == 0
    assert result["instructor_count"] == 0
    assert result["filtered_out_count"] == 1

    await db_session.refresh(payout)
    assert payout.status == "pending"


# Firma de Paddle Billing (developer.paddle.com/webhooks/signature-verification):
# `Paddle-Signature: ts=..;h1=..`, HMAC-SHA256 de "ts:cuerpo" con la clave del
# destino de notificaciones. El formato anterior de estos tests (X-Signature con
# HMAC del cuerpo y la API key) no es el que manda Paddle.
_PADDLE_SECRET = "pdl_ntfset_test"


def _paddle_headers(body: bytes, secret: str = _PADDLE_SECRET) -> dict[str, str]:
    import time

    ts = int(time.time())
    h1 = hmac.new(secret.encode(), f"{ts}:".encode() + body, hashlib.sha256).hexdigest()
    return {"Paddle-Signature": f"ts={ts};h1={h1}", "Content-Type": "application/json"}


def _paddle_body() -> bytes:
    return json.dumps({
        "event_id": "evt_test_123",
        "event_type": "subscription.created",
        "data": {"id": "sub_test_123", "custom_data": {"user_id": str(uuid.uuid4())}},
    }).encode()


@pytest.mark.asyncio
async def test_webhook_paddle_signature_verification(client, monkeypatch) -> None:
    """Una firma válida de Paddle se acepta."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "PADDLE_WEBHOOK_SECRET", _PADDLE_SECRET)
    body = _paddle_body()
    response = await client.post("/api/v1/webhooks/paddle", content=body, headers=_paddle_headers(body))
    assert response.status_code == 200
    assert response.json()["received"] is True


@pytest.mark.asyncio
async def test_webhook_paddle_invalid_signature(client, monkeypatch) -> None:
    """Una firma hecha con otra clave se rechaza."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "PADDLE_WEBHOOK_SECRET", _PADDLE_SECRET)
    body = _paddle_body()
    response = await client.post(
        "/api/v1/webhooks/paddle", content=body, headers=_paddle_headers(body, secret="otra")
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_webhook_paddle_missing_signature(client, monkeypatch) -> None:
    """Sin cabecera de firma se rechaza."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "PADDLE_WEBHOOK_SECRET", _PADDLE_SECRET)
    response = await client.post(
        "/api/v1/webhooks/paddle", content=_paddle_body(), headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 401