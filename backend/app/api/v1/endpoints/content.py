"""Content administration endpoints (question editing, versioning)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.models.content import Question
from app.schemas.content import QuestionPatch

router = APIRouter()


def _require_admin_key(x_admin_key: str = Header(default="")) -> None:
    key = settings.CONTENT_ADMIN_KEY
    if not key or x_admin_key != key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.patch(
    "/questions/{question_id}",
    status_code=200,
    dependencies=[Depends(_require_admin_key)],
)
async def patch_question(
    question_id: str,
    payload: QuestionPatch,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    """Edit a question's content fields and bump its content_version.

    Only the fields present in the payload are updated.  The version is
    always incremented so existing responses remain accurately linked to the
    content that was shown at answer time.
    """
    row = await db.scalar(select(Question).where(Question.id == question_id))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    changed = payload.model_dump(exclude_unset=True)
    if not changed:
        return {"id": question_id, "content_version": row.content_version, "updated_fields": []}

    for field, value in changed.items():
        setattr(row, field, value)
    row.content_version += 1
    await db.commit()
    await db.refresh(row)

    return {
        "id": question_id,
        "content_version": row.content_version,
        "updated_fields": list(changed.keys()),
    }
