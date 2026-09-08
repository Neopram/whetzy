from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TrackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name_es: str
    name_en: str
    order: int
    icon: str
    color: str
    total_questions: int


class ModuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    track_id: str
    name_es: str
    name_en: str
    order: int
    description_es: str
    description_en: str
    min_mastery_to_unlock: float


class SkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    module_id: str
    name_es: str
    name_en: str
    order: int


class GlossaryTermRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    track_id: str
    term_es: str
    term_en: str
    definition_es: str
    definition_en: str
    source: str | None = None
    order: int


class QuestionRead(BaseModel):
    """Full internal representation, correct answer included.

    Only ever returned from trusted/internal contexts (e.g. review of one's
    own answered question) — never as the "next question to answer" payload.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    skill_id: str
    type: str
    difficulty_tier: str
    question_es: str
    question_en: str
    options_es: list[str] | None = None
    options_en: list[str] | None = None
    correct_index: int
    explanation_es: str
    explanation_en: str
    elo_rating: float
    discrimination: float
    guessing: float
    expected_time_ms: int


class QuestionPatch(BaseModel):
    """Partial update for a question's content fields.

    All fields are optional — only supplied fields are written.
    Submitting this payload always bumps `content_version` on the question.
    """

    question_es: str | None = Field(default=None, min_length=1)
    question_en: str | None = Field(default=None, min_length=1)
    options_es: list[str] | None = None
    options_en: list[str] | None = None
    correct_index: int | None = None
    correct_answer_es: str | None = None
    correct_answer_en: str | None = None
    explanation_es: str | None = None
    explanation_en: str | None = None
    source: str | None = None
    difficulty_tier: str | None = None


class QuestionPublic(BaseModel):
    """Question payload sent to the client before it is answered.

    Deliberately omits `correct_index` and the explanations.
    For exec types (fill_blank_exec, fix_bug) `correct_answer_es/en` carries
    the expected stdout so the client can grade locally via Pyodide.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    skill_id: str
    type: str
    difficulty_tier: str
    question_es: str
    question_en: str
    options_es: list[str] | None = None
    options_en: list[str] | None = None
    correct_answer_es: str | None = None
    correct_answer_en: str | None = None
    expected_time_ms: int
