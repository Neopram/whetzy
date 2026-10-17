"""Perfil público de un alumno por `username` (0.3).

Antes, la pantalla mostraba datos 100% inventados para cualquier handle;
este endpoint es real o 404.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.exam import Certificate
from app.models.project import Project, ProjectSubmission
from app.models.user import User, UserSkillState

BASE = "/api/v1/profiles"


@pytest.fixture(autouse=True)
def _perfiles_publicos_encendidos(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "PUBLIC_PROFILES_ENABLED", True)


async def _user(db: AsyncSession, **kw: object) -> User:
    tag = uuid.uuid4().hex[:8]
    u = User(
        id=uuid.uuid4(),
        email=f"profile-{tag}@whetzy.test",
        username=f"profile{tag}",
        hashed_password=get_password_hash("Passw0rd!"),
        display_name="Public Profile",
        language="es",
        current_streak=12,
        **kw,
    )
    db.add(u)
    await db.commit()
    return u


@pytest.mark.asyncio
async def test_unknown_username_is_404(client) -> None:
    res = await client.get(f"{BASE}/no-such-user-anywhere")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_flag_off_hides_an_existing_profile(client, db_session, monkeypatch) -> None:
    """Sin opt-in no se publica nada: el flag apagado da 404 aunque el alumno exista."""
    from app.core.config import settings

    user = await _user(db_session)
    monkeypatch.setattr(settings, "PUBLIC_PROFILES_ENABLED", False)
    res = await client.get(f"{BASE}/{user.username}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_inactive_user_is_404(client, db_session) -> None:
    user = await _user(db_session, is_active=False)
    res = await client.get(f"{BASE}/{user.username}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_profile_is_visible_without_authentication(client, db_session) -> None:
    """A friend checking a profile may not have an account here."""
    user = await _user(db_session)
    res = await client.get(f"{BASE}/{user.username}")  # no auth headers on purpose
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["username"] == user.username
    assert data["display_name"] == "Public Profile"
    assert data["current_streak"] == 12
    assert data["certificates"] == []
    assert data["projects_completed"] == []


@pytest.mark.asyncio
async def test_mastery_and_skills_mastered_reflect_real_skill_states(
    client, db_session, content_seed
) -> None:
    user = await _user(db_session)
    db_session.add_all([
        UserSkillState(user_id=user.id, skill_id=content_seed["skill_id"], p_known=0.98),
    ])
    await db_session.commit()

    res = await client.get(f"{BASE}/{user.username}")
    data = res.json()
    assert data["mastery_avg"] == 98.0
    assert data["skills_mastered"] == 1


@pytest.mark.asyncio
async def test_revoked_certificates_are_not_shown(client, db_session, content_seed) -> None:
    user = await _user(db_session)
    db_session.add(
        Certificate(
            code="cert-visible",
            user_id=user.id,
            track_id=content_seed["track_id"],
            attempt_id=content_seed.get("attempt_id") or uuid.uuid4(),
            score_pct=90.0,
            questions=10,
        )
    )
    db_session.add(
        Certificate(
            code="cert-revoked",
            user_id=user.id,
            track_id=content_seed["track_id"],
            attempt_id=uuid.uuid4(),
            score_pct=80.0,
            questions=10,
            revoked=True,
        )
    )
    await db_session.commit()

    res = await client.get(f"{BASE}/{user.username}")
    data = res.json()
    assert [c["code"] for c in data["certificates"]] == ["cert-visible"]


@pytest.mark.asyncio
async def test_incomplete_project_submissions_are_not_shown(client, db_session) -> None:
    user = await _user(db_session)
    project = Project(
        id=uuid.uuid4(), slug="rest-api-fastapi", track_id="track01", runtime="python",
        name_es="API REST con FastAPI", name_en="REST API with FastAPI",
    )
    db_session.add(project)
    await db_session.flush()
    db_session.add(ProjectSubmission(project_id=project.id, user_id=user.id, completed=False))
    await db_session.commit()

    res = await client.get(f"{BASE}/{user.username}")
    data = res.json()
    assert data["projects_completed"] == []


@pytest.mark.asyncio
async def test_unverified_completed_project_is_not_shown(client, db_session) -> None:
    """43.6: un proyecto Python/JS se valida en el navegador; hasta que haya
    sandbox su finalización no es evidencia y no sale en la página pública."""
    from datetime import UTC, datetime

    user = await _user(db_session)
    project = Project(
        id=uuid.uuid4(), slug="rest-api-fastapi", track_id="track01", runtime="python",
        name_es="API REST con FastAPI", name_en="REST API with FastAPI",
    )
    db_session.add(project)
    await db_session.flush()
    db_session.add(
        ProjectSubmission(
            project_id=project.id, user_id=user.id, completed=True,
            completed_at=datetime.now(UTC), verified=False,
        )
    )
    await db_session.commit()

    res = await client.get(f"{BASE}/{user.username}")
    assert res.json()["projects_completed"] == []


@pytest.mark.asyncio
async def test_completed_project_submission_is_shown(client, db_session) -> None:
    from datetime import UTC, datetime

    user = await _user(db_session)
    project = Project(
        id=uuid.uuid4(), slug="rest-api-fastapi", track_id="track01", runtime="python",
        name_es="API REST con FastAPI", name_en="REST API with FastAPI",
    )
    db_session.add(project)
    await db_session.flush()
    db_session.add(
        ProjectSubmission(
            project_id=project.id, user_id=user.id, completed=True,
            completed_at=datetime.now(UTC), verified=True,
        )
    )
    await db_session.commit()

    res = await client.get(f"{BASE}/{user.username}")
    data = res.json()
    assert len(data["projects_completed"]) == 1
    assert data["projects_completed"][0]["slug"] == "rest-api-fastapi"
    assert data["projects_completed"][0]["name_es"] == "API REST con FastAPI"


@pytest.mark.asyncio
async def test_public_profile_leaks_nothing_beyond_the_claim(client, db_session) -> None:
    """The page is public, so what it carries is a privacy decision (red line 5):
    no email, no password hash, no internal ids."""
    user = await _user(db_session)
    res = await client.get(f"{BASE}/{user.username}")
    data = res.json()
    assert set(data) == {
        "username", "display_name", "avatar_emoji", "joined_at",
        "current_streak", "mastery_avg", "skills_mastered",
        "certificates", "projects_completed",
    }
