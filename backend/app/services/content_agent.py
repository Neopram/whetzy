"""Content author agent (5.1).

Generates up to N multiple-choice questions from a source document using the
configured LLM (Groq by default).  Each generated question is validated against
the schema and inserted into the database under the specified skill.

Public interface:
    generate_questions(db, skill_id, source_text, source_citation, n) -> list[Question]

The agent uses a JSON-mode-like prompt with a strict output format.  It falls
back to NullProvider when no LLM key is configured, but in that case it returns
an empty list (can't generate questions without an LLM).
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Question, Skill
from app.services.ai.provider import get_provider

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a bilingual (Spanish + English) educational content author for Whetzy,
a professional learning platform.

You must output ONLY a valid JSON array — no markdown fences, no prose before or
after.  Each element must be a JSON object with exactly these keys:

  "question_es"    string   Question stem in Spanish (≤ 200 chars)
  "question_en"    string   Question stem in English (≤ 200 chars)
  "options_es"     array    Exactly 4 answer options in Spanish
  "options_en"     array    Exactly 4 answer options in English
  "correct_index"  integer  0-based index of the correct option (0–3)
  "explanation_es" string   1-3 sentence explanation in Spanish, citing source
  "explanation_en" string   1-3 sentence explanation in English, citing source
  "difficulty_tier" string  One of: "easy", "medium", "hard"

Rules:
- All questions must be answerable from the provided source text (no invented facts).
- Distractors must be plausible but clearly wrong given the source.
- Do NOT repeat questions.
- The correct option must NOT always be at the same index.
- Output only the JSON array, nothing else.
"""

_USER_TEMPLATE = """\
Source citation: {citation}

Source text:
---
{source_text}
---

Generate exactly {n} multiple-choice questions from the source text above.
"""


class _GeneratedQ(BaseModel):
    question_es: str = Field(min_length=5, max_length=500)
    question_en: str = Field(min_length=5, max_length=500)
    options_es: list[str] = Field(min_length=4, max_length=4)
    options_en: list[str] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3)
    explanation_es: str = Field(default="", max_length=2000)
    explanation_en: str = Field(default="", max_length=2000)
    difficulty_tier: str = Field(default="medium")

    @field_validator("difficulty_tier")
    @classmethod
    def _validate_tier(cls, v: str) -> str:
        if v not in ("easy", "medium", "hard"):
            return "medium"
        return v

    @field_validator("options_es", "options_en")
    @classmethod
    def _four_options(cls, v: list[str]) -> list[str]:
        if len(v) != 4:
            raise ValueError("exactly 4 options required")
        return v


def _extract_json(text: str) -> list[dict[str, Any]]:
    """Extract a JSON array from raw LLM output, tolerating minor formatting."""
    text = text.strip()
    # strip markdown fences
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text.strip())
    # find first [ and last ]
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("No JSON array found in LLM output")
    return json.loads(text[start : end + 1])  # type: ignore[no-any-return]


def _make_question_id(skill_id: str, n: int) -> str:
    return f"{skill_id}_{uuid.uuid4().hex[:8]}_{n:03d}"


async def generate_questions(
    db: AsyncSession,
    skill_id: str,
    source_text: str,
    source_citation: str,
    n: int = 10,
) -> list[Question]:
    """Generate *n* MCQ questions from *source_text* and insert under *skill_id*.

    Returns the list of inserted Question objects (may be fewer than *n* if
    some LLM outputs fail validation).  Returns [] if LLM is not configured.
    """
    from app.services.ai.provider import NullProvider

    provider = get_provider()
    if isinstance(provider, NullProvider):
        logger.warning("content_agent: no LLM configured — returning empty list")
        return []

    # Verify skill exists
    skill = await db.scalar(select(Skill).where(Skill.id == skill_id))
    if skill is None:
        raise ValueError(f"Skill '{skill_id}' not found")

    user_msg = _USER_TEMPLATE.format(
        citation=source_citation,
        source_text=source_text[:12000],  # cap to avoid token limits
        n=n,
    )

    raw = await provider.complete(
        _SYSTEM_PROMPT,
        user_msg,
        max_tokens=4000,
    )

    try:
        raw_items = _extract_json(raw)
    except (ValueError, json.JSONDecodeError) as exc:
        logger.error("content_agent: JSON parse error — %s\nRaw output: %.500s", exc, raw)
        return []

    inserted: list[Question] = []
    for i, item in enumerate(raw_items):
        try:
            parsed = _GeneratedQ.model_validate(item)
        except ValidationError as exc:
            logger.warning("content_agent: question %d validation failed: %s", i, exc)
            continue

        q = Question(
            id=_make_question_id(skill_id, i),
            skill_id=skill_id,
            type="mcq",
            difficulty_tier=parsed.difficulty_tier,
            question_es=parsed.question_es,
            question_en=parsed.question_en,
            options_es=parsed.options_es,
            options_en=parsed.options_en,
            correct_index=parsed.correct_index,
            explanation_es=parsed.explanation_es,
            explanation_en=parsed.explanation_en,
            source=source_citation,
        )
        db.add(q)
        inserted.append(q)

    if inserted:
        await db.commit()
        for q in inserted:
            await db.refresh(q)

    logger.info(
        "content_agent: generated %d/%d questions for skill '%s'", len(inserted), n, skill_id
    )
    return inserted
