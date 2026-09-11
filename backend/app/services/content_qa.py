"""Content QA agent (5.2).

Validates multiple-choice questions for:
  - Structural integrity (4 options, valid correct_index, no duplicates, source present)
  - Semantic quality (LLM pass): plausible distractors, difficulty calibration,
    citation grounding

Public interface:
    qa_question(question) -> QAResult        — validate one Question object
    qa_questions(questions) -> list[QAResult] — validate a list
    qa_question_by_id(db, question_id) -> QAResult

QAResult.passed is True iff there are no CRITICAL or HIGH issues.
The LLM pass is skipped when NullProvider is active; structural checks always run.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from app.models.content import Question

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ── Issue severity ─────────────────────────────────────────────────────────────


class Severity(str, Enum):
    CRITICAL = "CRITICAL"   # structural defect — question cannot be used
    HIGH = "HIGH"           # semantic defect — likely confuses learners
    MEDIUM = "MEDIUM"       # style/quality — usable but should be fixed
    LOW = "LOW"             # minor suggestion


@dataclass
class Issue:
    severity: Severity
    code: str
    message: str


@dataclass
class QAResult:
    question_id: str
    passed: bool
    score: float  # 0.0 (terrible) … 1.0 (perfect)
    issues: list[Issue] = field(default_factory=list)
    llm_checked: bool = False

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.HIGH)


# ── Deterministic checks ───────────────────────────────────────────────────────

def _structural_check(q: Question) -> list[Issue]:
    issues: list[Issue] = []

    # options length
    opts_es = q.options_es or []
    opts_en = q.options_en or []
    if len(opts_es) != 4:
        issues.append(Issue(Severity.CRITICAL, "OPT_COUNT_ES",
                             f"options_es has {len(opts_es)} items, expected 4"))
    if len(opts_en) != 4:
        issues.append(Issue(Severity.CRITICAL, "OPT_COUNT_EN",
                             f"options_en has {len(opts_en)} items, expected 4"))

    # correct_index range
    ci = q.correct_index
    if ci is None or not (0 <= ci <= 3):
        issues.append(Issue(Severity.CRITICAL, "CORRECT_INDEX",
                             f"correct_index={ci} is out of range 0-3"))

    # duplicate options (case-insensitive)
    if len(opts_es) == 4:
        lower = [o.lower().strip() for o in opts_es]
        if len(set(lower)) < 4:
            issues.append(Issue(Severity.HIGH, "DUPLICATE_OPTIONS_ES",
                                 "options_es contains duplicate entries"))
    if len(opts_en) == 4:
        lower = [o.lower().strip() for o in opts_en]
        if len(set(lower)) < 4:
            issues.append(Issue(Severity.HIGH, "DUPLICATE_OPTIONS_EN",
                                 "options_en contains duplicate entries"))

    # trivially short question stem
    if q.question_es and len(q.question_es.strip()) < 10:
        issues.append(Issue(Severity.HIGH, "SHORT_STEM_ES",
                             "question_es stem is too short (< 10 chars)"))
    if q.question_en and len(q.question_en.strip()) < 10:
        issues.append(Issue(Severity.HIGH, "SHORT_STEM_EN",
                             "question_en stem is too short (< 10 chars)"))

    # trivially short distractor (an option that is ≤ 1 word and all caps → likely placeholder)
    if len(opts_es) == 4:
        for i, o in enumerate(opts_es):
            if re.fullmatch(r"[A-Z]{1,3}", o.strip()):
                issues.append(Issue(Severity.HIGH, "PLACEHOLDER_OPTION_ES",
                                     f"options_es[{i}] looks like a placeholder: '{o}'"))
    if len(opts_en) == 4:
        for i, o in enumerate(opts_en):
            if re.fullmatch(r"[A-Z]{1,3}", o.strip()):
                issues.append(Issue(Severity.HIGH, "PLACEHOLDER_OPTION_EN",
                                     f"options_en[{i}] looks like a placeholder: '{o}'"))

    # missing source citation
    if not q.source or not q.source.strip():
        issues.append(Issue(Severity.MEDIUM, "NO_SOURCE",
                             "source field is empty — citation required for content pipeline"))

    # missing explanation
    if not q.explanation_es or len(q.explanation_es.strip()) < 5:
        issues.append(Issue(Severity.MEDIUM, "NO_EXPLANATION_ES",
                             "explanation_es is missing or too short"))
    if not q.explanation_en or len(q.explanation_en.strip()) < 5:
        issues.append(Issue(Severity.MEDIUM, "NO_EXPLANATION_EN",
                             "explanation_en is missing or too short"))

    # invalid difficulty_tier
    if q.difficulty_tier not in ("easy", "medium", "hard"):
        issues.append(Issue(Severity.MEDIUM, "BAD_DIFFICULTY_TIER",
                             f"difficulty_tier='{q.difficulty_tier}' not in {{easy,medium,hard}}"))

    # correct option same as distractor (comparing correct against others)
    if len(opts_es) == 4 and ci is not None and 0 <= ci <= 3:
        correct = opts_es[ci].lower().strip()
        for j, o in enumerate(opts_es):
            if j != ci and o.lower().strip() == correct:
                issues.append(Issue(Severity.CRITICAL, "CORRECT_IS_DUPLICATE_ES",
                                     "correct option is identical to a distractor (options_es)"))
                break

    return issues


# ── LLM-based semantic check ───────────────────────────────────────────────────

_QA_SYSTEM_PROMPT = """\
You are a bilingual (Spanish + English) educational content quality reviewer.

You will be given a multiple-choice question and you must evaluate it for quality
defects.  Output ONLY a valid JSON object — no markdown fences, no prose — with:

  "distractor_quality": "ok" | "weak" | "trivial"
      "trivial" = at least one distractor is obviously, comically wrong
      "weak"    = distractors are plausible but too easy (no reasoning needed)
      "ok"      = all distractors require genuine knowledge to reject

  "difficulty_calibration": "ok" | "mislabeled"
      "mislabeled" = the claimed difficulty_tier does not match the actual difficulty

  "citation_grounded": true | false
      false = the question asks about facts NOT present in the source text

  "issues": []   — list of short English strings for any other problems you notice
"""

_QA_USER_TEMPLATE = """\
Source citation: {citation}

Source text:
---
{source_text}
---

Question (ES): {question_es}
Question (EN): {question_en}

Options ES: {options_es}
Options EN: {options_en}

Correct index: {correct_index}
Difficulty tier: {difficulty_tier}

Evaluate the question quality.
"""


async def _llm_check(q: Question, source_text: str | None) -> list[Issue]:
    import json

    from app.services.ai.provider import NullProvider, get_provider

    provider = get_provider()
    if isinstance(provider, NullProvider):
        return []

    opts_es = q.options_es or []
    opts_en = q.options_en or []
    user_msg = _QA_USER_TEMPLATE.format(
        citation=q.source or "(unknown)",
        source_text=(source_text or "(not provided)")[:3000],
        question_es=q.question_es,
        question_en=q.question_en,
        options_es=", ".join(f"{i}. {o}" for i, o in enumerate(opts_es)),
        options_en=", ".join(f"{i}. {o}" for i, o in enumerate(opts_en)),
        correct_index=q.correct_index,
        difficulty_tier=q.difficulty_tier,
    )

    try:
        raw = await provider.complete(_QA_SYSTEM_PROMPT, user_msg, max_tokens=500)
        # strip fences
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw.strip())
        result = json.loads(raw)
    except Exception as exc:  # noqa: BLE001 — LLM call + JSON parse, degrade gracefully to no LLM issues
        logger.warning("content_qa: LLM check failed: %s", exc)
        return []

    issues: list[Issue] = []

    dq = result.get("distractor_quality", "ok")
    if dq == "trivial":
        issues.append(Issue(Severity.HIGH, "TRIVIAL_DISTRACTORS",
                             "LLM flagged distractors as trivially easy"))
    elif dq == "weak":
        issues.append(Issue(Severity.MEDIUM, "WEAK_DISTRACTORS",
                             "LLM flagged distractors as too easy"))

    dc = result.get("difficulty_calibration", "ok")
    if dc == "mislabeled":
        issues.append(Issue(Severity.MEDIUM, "DIFFICULTY_MISLABELED",
                             f"LLM says difficulty_tier='{q.difficulty_tier}' is mislabeled"))

    cg = result.get("citation_grounded", True)
    if not cg:
        issues.append(Issue(Severity.HIGH, "NOT_CITATION_GROUNDED",
                             "LLM says question cannot be answered from the cited source"))

    for extra in result.get("issues", []):
        if isinstance(extra, str) and extra.strip():
            issues.append(Issue(Severity.LOW, "LLM_ISSUE", extra.strip()))

    return issues


# ── Public API ─────────────────────────────────────────────────────────────────

def _score(issues: list[Issue]) -> float:
    """Convert issue list to a 0-1 quality score."""
    deductions = {
        Severity.CRITICAL: 0.4,
        Severity.HIGH: 0.15,
        Severity.MEDIUM: 0.05,
        Severity.LOW: 0.01,
    }
    score = 1.0
    for iss in issues:
        score -= deductions.get(iss.severity, 0)
    return max(0.0, round(score, 3))


async def qa_question(q: Question, source_text: str | None = None) -> QAResult:
    """Run QA checks on a single Question.  LLM check skipped if NullProvider."""
    structural = _structural_check(q)

    llm_issues: list[Issue] = []
    llm_ran = False
    # Only run LLM check if there are no CRITICAL structural defects
    if not any(i.severity == Severity.CRITICAL for i in structural):
        llm_issues = await _llm_check(q, source_text)
        llm_ran = True  # tried (may still be NullProvider → empty list)

    all_issues = structural + llm_issues
    passed = not any(
        i.severity in (Severity.CRITICAL, Severity.HIGH) for i in all_issues
    )
    return QAResult(
        question_id=q.id,
        passed=passed,
        score=_score(all_issues),
        issues=all_issues,
        llm_checked=llm_ran,
    )


async def qa_questions(
    questions: list[Question],
    source_text: str | None = None,
) -> list[QAResult]:
    results = []
    for q in questions:
        results.append(await qa_question(q, source_text))
    return results


async def qa_question_by_id(
    db: AsyncSession,
    question_id: str,
    source_text: str | None = None,
) -> QAResult:
    from sqlalchemy import select

    from app.models.content import Question as Q

    row = await db.scalar(select(Q).where(Q.id == question_id))
    if row is None:
        raise ValueError(f"Question '{question_id}' not found")
    return await qa_question(row, source_text)
