"""Integration tests for the GDPR data export — P.7.

Red line 5 is "GDPR real: exportar y borrar de verdad". Two ways this endpoint
can break that promise quietly:
  * it omits a table, so the export is incomplete but looks fine;
  * it includes somebody else's rows, which turns a privacy feature into a
    data leak.
Both are asserted here, plus that the password hash never leaves the server.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

import pytest

from app.models.question_report import QuestionReport
from app.models.session import Response as QuizResponse
from app.models.session import StudySession
from app.models.user import User, UserBadge, UserSkillState

BASE = "/api/v1/export"

EXPECTED_SECTIONS = {
    "profile",
    "skill_states",
    "study_sessions",
    "responses",
    "badges",
    "question_reports",
}


async def seed_user_data(db, user_id: uuid.UUID, content_seed: dict, *, marker: str) -> dict:
    """Give a user one row in every exported table."""
    session = StudySession(
        id=uuid.uuid4(),
        user_id=user_id,
        mode="study",
        started_at=datetime.now(UTC),
    )
    db.add(session)
    await db.flush()

    response = QuizResponse(
        id=uuid.uuid4(),
        session_id=session.id,
        question_id=content_seed["question_id"],
        correct=True,
        grade=3,
        response_time_ms=1234,
    )
    db.add(response)
    db.add(UserSkillState(user_id=user_id, skill_id=content_seed["skill_id"], p_known=0.42))
    db.add(UserBadge(user_id=user_id, badge_id=f"badge_{marker}"))
    db.add(
        QuestionReport(
            id=uuid.uuid4(),
            user_id=user_id,
            question_id=content_seed["question_id"],
            reason="wrong_answer",
            notes=f"comment_{marker}",
        )
    )
    await db.commit()
    return {"session_id": str(session.id), "response_id": str(response.id)}


@pytest.fixture
async def seeded(db_session, user: User, content_seed: dict) -> dict:
    return await seed_user_data(db_session, user.id, content_seed, marker="mine")


class TestAuth:
    @pytest.mark.asyncio
    async def test_requires_authentication(self, client) -> None:
        resp = await client.get(f"{BASE}/data")
        assert resp.status_code == 401


class TestEnvelope:
    @pytest.mark.asyncio
    async def test_returns_a_json_attachment(self, client, auth_headers) -> None:
        resp = await client.get(f"{BASE}/data", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")
        assert resp.headers["content-disposition"] == 'attachment; filename="whetzy-data.json"'

    @pytest.mark.asyncio
    async def test_every_section_is_present_even_when_empty(
        self, client, auth_headers
    ) -> None:
        """A brand-new user must still get the full envelope, not a partial one."""
        resp = await client.get(f"{BASE}/data", headers=auth_headers)
        data = resp.json()
        assert set(data) == EXPECTED_SECTIONS
        for key in EXPECTED_SECTIONS - {"profile"}:
            assert data[key] == []

    @pytest.mark.asyncio
    async def test_body_is_valid_json(self, client, auth_headers) -> None:
        resp = await client.get(f"{BASE}/data", headers=auth_headers)
        assert json.loads(resp.content.decode("utf-8"))


class TestProfile:
    @pytest.mark.asyncio
    async def test_password_hash_is_never_exported(
        self, client, auth_headers, user: User
    ) -> None:
        resp = await client.get(f"{BASE}/data", headers=auth_headers)
        assert "hashed_password" not in resp.json()["profile"]
        # And not anywhere else in the document either.
        assert user.hashed_password not in resp.text
        assert "hashed_password" not in resp.text

    @pytest.mark.asyncio
    async def test_profile_carries_the_identifying_fields(
        self, client, auth_headers, user: User
    ) -> None:
        profile = (await client.get(f"{BASE}/data", headers=auth_headers)).json()["profile"]
        assert profile["email"] == user.email
        assert profile["username"] == user.username
        assert profile["id"] == str(user.id)

    @pytest.mark.asyncio
    async def test_datetimes_are_iso_strings(self, client, auth_headers) -> None:
        profile = (await client.get(f"{BASE}/data", headers=auth_headers)).json()["profile"]
        created = profile.get("created_at")
        assert isinstance(created, str)
        datetime.fromisoformat(created)  # must round-trip


class TestCompleteness:
    @pytest.mark.asyncio
    async def test_exports_a_row_from_every_table(
        self, client, auth_headers, seeded: dict
    ) -> None:
        data = (await client.get(f"{BASE}/data", headers=auth_headers)).json()
        assert len(data["study_sessions"]) == 1
        assert len(data["responses"]) == 1
        assert len(data["skill_states"]) == 1
        assert len(data["badges"]) == 1
        assert len(data["question_reports"]) == 1

    @pytest.mark.asyncio
    async def test_response_rows_are_reachable_from_the_sessions(
        self, client, auth_headers, seeded: dict
    ) -> None:
        data = (await client.get(f"{BASE}/data", headers=auth_headers)).json()
        assert data["responses"][0]["session_id"] == seeded["session_id"]
        assert data["study_sessions"][0]["id"] == seeded["session_id"]

    @pytest.mark.asyncio
    async def test_answer_details_survive_the_export(
        self, client, auth_headers, seeded: dict
    ) -> None:
        row = (await client.get(f"{BASE}/data", headers=auth_headers)).json()["responses"][0]
        assert row["correct"] is True
        assert row["response_time_ms"] == 1234

    @pytest.mark.asyncio
    async def test_free_text_comment_is_included(
        self, client, auth_headers, seeded: dict
    ) -> None:
        """User-authored text is exactly the kind of personal data GDPR is about."""
        reports = (await client.get(f"{BASE}/data", headers=auth_headers)).json()[
            "question_reports"
        ]
        assert reports[0]["notes"] == "comment_mine"


class TestIsolation:
    @pytest.mark.asyncio
    async def test_no_other_users_rows_are_exported(
        self, client, auth_headers, db_session, user: User, content_seed: dict, seeded: dict
    ) -> None:
        """The failure that turns a privacy feature into a leak."""
        stranger = User(
            id=uuid.uuid4(),
            email=f"other-{uuid.uuid4().hex[:6]}@whetzy.test",
            username=f"other{uuid.uuid4().hex[:6]}",
            hashed_password="x",
            display_name="Other",
            language="en",
        )
        db_session.add(stranger)
        await db_session.commit()
        theirs = await seed_user_data(db_session, stranger.id, content_seed, marker="theirs")

        resp = await client.get(f"{BASE}/data", headers=auth_headers)
        data = resp.json()

        assert len(data["study_sessions"]) == 1
        assert len(data["responses"]) == 1
        assert len(data["badges"]) == 1
        assert len(data["question_reports"]) == 1

        # Nothing belonging to the stranger appears anywhere in the document.
        assert theirs["session_id"] not in resp.text
        assert theirs["response_id"] not in resp.text
        assert "comment_theirs" not in resp.text
        assert str(stranger.id) not in resp.text
        assert stranger.email not in resp.text

    @pytest.mark.asyncio
    async def test_a_user_with_no_sessions_gets_no_responses(
        self, client, auth_headers, db_session, content_seed: dict
    ) -> None:
        """Guards the `if session_ids:` branch — an empty IN () must not
        degrade into 'match everything'."""
        stranger = User(
            id=uuid.uuid4(),
            email=f"other-{uuid.uuid4().hex[:6]}@whetzy.test",
            username=f"other{uuid.uuid4().hex[:6]}",
            hashed_password="x",
            display_name="Other",
            language="en",
        )
        db_session.add(stranger)
        await db_session.commit()
        await seed_user_data(db_session, stranger.id, content_seed, marker="theirs")

        data = (await client.get(f"{BASE}/data", headers=auth_headers)).json()
        assert data["responses"] == []
        assert data["study_sessions"] == []
