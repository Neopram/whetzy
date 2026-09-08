"""Question-report endpoints — P.6 defective-question reporting."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.content import Question
from app.models.question_report import VALID_REASONS, QuestionReport
from app.models.user import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ReportQuestionRequest(BaseModel):
    question_id: str
    reason: str
    notes: str | None = None

    @field_validator("reason")
    @classmethod
    def reason_must_be_valid(cls, v: str) -> str:
        if v not in VALID_REASONS:
            raise ValueError(f"reason must be one of {sorted(VALID_REASONS)}")
        return v


class ReportCreatedResponse(BaseModel):
    id: str
    message: str


class ReportItem(BaseModel):
    id: str
    user_id: str
    question_id: str
    reason: str
    notes: str | None
    created_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/question",
    response_model=ReportCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report a defective question",
)
async def report_question(
    payload: ReportQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportCreatedResponse:
    # Verify question exists
    result = await db.execute(select(Question).where(Question.id == payload.question_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question '{payload.question_id}' not found.",
        )

    report = QuestionReport(
        user_id=current_user.id,
        question_id=payload.question_id,
        reason=payload.reason,
        notes=payload.notes,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return ReportCreatedResponse(
        id=str(report.id),
        message="Report submitted. Thank you for helping improve question quality.",
    )


@router.get(
    "/question/{question_id}",
    response_model=list[ReportItem],
    summary="List reports for a question (admin visibility)",
)
async def list_question_reports(
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ReportItem]:
    result = await db.execute(
        select(QuestionReport)
        .where(QuestionReport.question_id == question_id)
        .order_by(QuestionReport.created_at.desc())
    )
    reports = result.scalars().all()
    return [
        ReportItem(
            id=str(r.id),
            user_id=str(r.user_id),
            question_id=r.question_id,
            reason=r.reason,
            notes=r.notes,
            created_at=r.created_at.isoformat(),
        )
        for r in reports
    ]
