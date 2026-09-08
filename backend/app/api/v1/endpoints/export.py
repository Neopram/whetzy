"""GDPR data-export endpoint — P.7.

Returns a single JSON file containing all user data across every table.
Designed for < 10 s at 10 k responses: one efficient SELECT per table, no N+1.
"""

from __future__ import annotations

import json
from datetime import date, datetime

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.question_report import QuestionReport
from app.models.session import Response as QuizResponse
from app.models.session import StudySession
from app.models.user import User, UserBadge, UserSkillState

router = APIRouter()


def _serialize(value: object) -> object:
    """Convert non-JSON-serializable scalars to strings."""
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if hasattr(value, "__str__") and not isinstance(value, (int, float, bool, str)):
        return str(value)
    return value


def _row_to_dict(row: object) -> dict[str, object]:
    """Serialize a mapped SQLAlchemy instance to a plain dict."""
    data = {}
    mapper = type(row).__mapper__  # type: ignore[attr-defined]
    for col in mapper.columns:
        data[col.key] = _serialize(getattr(row, col.key))
    return data


@router.get(
    "/data",
    summary="GDPR data export — download all your data as JSON",
    response_class=Response,
)
async def export_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    uid = current_user.id

    # --- Profile ---
    profile = _row_to_dict(current_user)
    # Strip sensitive fields
    profile.pop("hashed_password", None)

    # --- Skill states ---
    skill_rows = (
        await db.execute(select(UserSkillState).where(UserSkillState.user_id == uid))
    ).scalars().all()
    skill_states = [_row_to_dict(r) for r in skill_rows]

    # --- Study sessions ---
    session_rows = (
        await db.execute(select(StudySession).where(StudySession.user_id == uid))
    ).scalars().all()
    study_sessions = [_row_to_dict(r) for r in session_rows]

    # --- Responses (one query via session_ids, avoids N+1) ---
    session_ids = [r.id for r in session_rows]
    if session_ids:
        response_rows = (
            await db.execute(
                select(QuizResponse).where(QuizResponse.session_id.in_(session_ids))
            )
        ).scalars().all()
    else:
        response_rows = []
    responses = [_row_to_dict(r) for r in response_rows]

    # --- Badges ---
    badge_rows = (
        await db.execute(select(UserBadge).where(UserBadge.user_id == uid))
    ).scalars().all()
    badges = [_row_to_dict(r) for r in badge_rows]

    # --- Question reports ---
    report_rows = (
        await db.execute(select(QuestionReport).where(QuestionReport.user_id == uid))
    ).scalars().all()
    question_reports = [_row_to_dict(r) for r in report_rows]

    payload = {
        "profile": profile,
        "skill_states": skill_states,
        "study_sessions": study_sessions,
        "responses": responses,
        "badges": badges,
        "question_reports": question_reports,
    }

    body = json.dumps(payload, ensure_ascii=False, indent=2)
    return Response(
        content=body,
        media_type="application/json",
        headers={
            "Content-Disposition": 'attachment; filename="whetzy-data.json"',
        },
    )
