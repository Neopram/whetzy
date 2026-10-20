from __future__ import annotations

from typing import Any

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


# All types graded by the server comparing submitted output against the stored
# expected value — sending that value to the client in advance lets anyone skip
# execution and forge a correct answer from the network response (B2).
_SERVER_GRADED_TYPES: frozenset[str] = frozenset(
    {"fill_blank", "fill_blank_exec", "fix_bug", "sql_exec", "js_exec"}
)


class InteractivePublic(BaseModel):
    """Lo que el widget necesita para pintarse (40.1); `target` no viaja.

    Como `correct_index`, el objetivo se queda en el servidor hasta que el
    alumno responde: con él delante, el estado correcto se escribe solo. Llega
    después en `QuizAnswerResponse.widget_target`, para que el cliente vuelva a
    corregir y avise si su veredicto no es el del servidor.
    """

    widget: str
    params: dict[str, Any]
    checker: str


class QuestionPublic(BaseModel):
    """Question payload sent to the client before it is answered.

    Deliberately omits `correct_index`, the explanations, and — for all
    server-graded exec types — the expected output (`correct_answer_es/en`).
    The client still runs code locally via Pyodide for UX, but the server
    always grades by comparing the submitted output against its own stored
    value; never trusting the client's verdict.
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
    # Sin `target`: `InteractivePublic` no tiene ese campo y Pydantic lo descarta.
    interactive: InteractivePublic | None = None
    expected_time_ms: int

    @model_validator(mode="after")
    def _hide_expected_output(self) -> QuestionPublic:
        # B2: never send the expected output to the client; the server keeps it
        # to grade the submitted exec_output / answer_text on its own.
        if self.type in _SERVER_GRADED_TYPES:
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
    # 43.7: runtime del playground para «Probar este código» (None: no se ofrece).
    code_runtime: str | None = None
    source: str
    order: int = 1
