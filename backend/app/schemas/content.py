from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TrackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name_es: str
    name_en: str
    order: int
    icon: str
    color: str
    total_questions: int

    # Certification tracks only. A learning track leaves these null, which is
    # how the client knows not to offer a mock exam for it rather than keeping
    # its own list of which tracks are certifications.
    is_certification: bool = False
    cert_provider: str | None = None
    exam_question_count: int | None = None
    exam_duration_minutes: int | None = None


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
    level: int = 1


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
    For sql_exec, `code_es`/`code_en` carry the full SQL script with `___`
    as the student's blank (fill_blank_exec embeds its code in question prose).
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
    code_es: str | None = None
    code_en: str | None = None
    expected_time_ms: int

    @model_validator(mode="after")
    def _hide_answer_for_server_graded_fill_blank(self) -> QuestionPublic:
        # S.3 (fuga de respuestas): `correct_answer_es/en` is legitimate here
        # only for the client-graded exec types, where the client needs the
        # expected stdout to run locally via Pyodide. Plain "fill_blank" is
        # graded server-side (quiz.py compares `answer_text` against this same
        # column) — the model's own `from_attributes` copy pulled it through
        # unconditionally, handing the exact free-text answer to the client
        # before they typed anything.
        if self.type == "fill_blank":
            self.correct_answer_es = None
            self.correct_answer_en = None
        return self


class LessonRead(BaseModel):
    """Lesson payload — instructional content before adaptive practice."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    skill_id: str
    title_es: str
    title_en: str
    body_es: str
    body_en: str
    example_code: str | None = None
    example_output: str | None = None
    source: str
    order: int = 1
