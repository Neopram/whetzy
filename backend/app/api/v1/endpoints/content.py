"""Content administration endpoints (question editing, versioning, AI generation)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.models.content import Question
from app.schemas.content import QuestionPatch
from app.services import content_agent, content_qa

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


class GenerateRequest(BaseModel):
    skill_id: str
    source_text: str = Field(min_length=50, max_length=20000)
    source_citation: str = Field(min_length=5, max_length=500)
    n: int = Field(default=10, ge=1, le=20)


class GeneratedQuestionOut(BaseModel):
    id: str
    question_es: str
    question_en: str
    options_es: list[str]
    options_en: list[str]
    correct_index: int
    explanation_es: str
    explanation_en: str
    difficulty_tier: str
    source: str | None


@router.post(
    "/generate",
    status_code=201,
    response_model=list[GeneratedQuestionOut],
    dependencies=[Depends(_require_admin_key)],
)
async def generate_questions(
    payload: GenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> list[GeneratedQuestionOut]:
    """Generate MCQ questions from a source document using the AI author agent.

    Requires X-Admin-Key. Returns the inserted questions (may be fewer than
    *n* if some outputs fail validation). Returns 503 if no LLM is configured.
    """
    try:
        questions = await content_agent.generate_questions(
            db,
            skill_id=payload.skill_id,
            source_text=payload.source_text,
            source_citation=payload.source_citation,
            n=payload.n,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="LLM error") from exc

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM not configured or returned no valid questions",
        )

    return [
        GeneratedQuestionOut(
            id=q.id,
            question_es=q.question_es,
            question_en=q.question_en,
            options_es=q.options_es or [],
            options_en=q.options_en or [],
            correct_index=q.correct_index or 0,
            explanation_es=q.explanation_es,
            explanation_en=q.explanation_en,
            difficulty_tier=q.difficulty_tier,
            source=q.source,
        )
        for q in questions
    ]


# ── QA endpoints ──────────────────────────────────────────────────────────────


class IssueOut(BaseModel):
    severity: str
    code: str
    message: str


class QAResultOut(BaseModel):
    question_id: str
    passed: bool
    score: float
    llm_checked: bool
    issues: list[IssueOut]


class QASingleRequest(BaseModel):
    question_id: str
    source_text: str | None = None


class QABatchRequest(BaseModel):
    question_ids: list[str] = Field(min_length=1, max_length=50)
    source_text: str | None = None


@router.post(
    "/qa",
    status_code=200,
    response_model=QAResultOut,
    dependencies=[Depends(_require_admin_key)],
)
async def qa_single(
    payload: QASingleRequest,
    db: AsyncSession = Depends(get_db),
) -> QAResultOut:
    """Run QA checks on a single question by ID."""
    try:
        result = await content_qa.qa_question_by_id(db, payload.question_id, payload.source_text)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return QAResultOut(
        question_id=result.question_id,
        passed=result.passed,
        score=result.score,
        llm_checked=result.llm_checked,
        issues=[IssueOut(severity=i.severity.value, code=i.code, message=i.message)
                for i in result.issues],
    )


@router.post(
    "/qa/batch",
    status_code=200,
    response_model=list[QAResultOut],
    dependencies=[Depends(_require_admin_key)],
)
async def qa_batch(
    payload: QABatchRequest,
    db: AsyncSession = Depends(get_db),
) -> list[QAResultOut]:
    """Run QA checks on up to 50 questions by ID."""
    from sqlalchemy import select

    rows = (await db.scalars(
        select(Question).where(Question.id.in_(payload.question_ids))
    )).all()

    found_ids = {r.id for r in rows}
    missing = [qid for qid in payload.question_ids if qid not in found_ids]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questions not found: {missing}",
        )

    results = await content_qa.qa_questions(list(rows), payload.source_text)
    return [
        QAResultOut(
            question_id=r.question_id,
            passed=r.passed,
            score=r.score,
            llm_checked=r.llm_checked,
            issues=[IssueOut(severity=i.severity.value, code=i.code, message=i.message)
                    for i in r.issues],
        )
        for r in results
    ]
