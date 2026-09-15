"""Content loader: ingests the curriculum (tracks.json) and every question
bank file under content/questions/** into the database.

Idempotent: re-running upserts tracks/modules/skills/questions by primary key,
so it is safe to run on every deploy or manually via `python -m app.services.content_loader`.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal, init_db
from app.models.content import (
    Domain,
    GlossaryTerm,
    Lesson,
    Module,
    Question,
    Skill,
    Track,
)


def _content_root() -> Path:
    # Override with CONTENT_DIR (e.g. /app/content in Docker); else infer
    # from the repo layout: backend/app/services/content_loader.py -> repo/content.
    env_dir = os.getenv("CONTENT_DIR")
    if env_dir:
        return Path(env_dir)
    return Path(__file__).resolve().parents[3] / "content"


async def _upsert_track(db: AsyncSession, data: dict[str, Any]) -> None:
    track = await db.get(Track, data["id"])
    if track is None:
        track = Track(id=data["id"])
        db.add(track)
    track.name_es = data["name_es"]
    track.name_en = data["name_en"]
    track.order = data.get("order", 0)
    track.icon = data.get("icon", "📘")
    track.color = data.get("color", "#1CB0F6")

    # Certification metadata (10.1's schema, populated since 10.3). A learning
    # track leaves all of this null; only a certification track carries a
    # published exam blueprint to mirror.
    cert = data.get("certification")
    track.is_certification = bool(data.get("is_certification"))
    if cert:
        track.cert_provider = cert.get("provider")
        track.exam_question_count = cert.get("exam_question_count")
        track.exam_duration_minutes = cert.get("exam_duration_minutes")
        track.passing_score_pct = cert.get("passing_score_pct")

    for m_order, m in enumerate(data.get("modules", []), start=1):
        module = await db.get(Module, m["id"])
        if module is None:
            module = Module(id=m["id"], track_id=track.id)
            db.add(module)
        module.track_id = track.id
        module.name_es = m["name_es"]
        module.name_en = m["name_en"]
        module.order = m.get("order", m_order)
        module.description_es = m.get("description_es", "")
        module.description_en = m.get("description_en", "")
        module.min_mastery_to_unlock = m.get("min_mastery_to_unlock", 0.7)

        # One exam domain per module, for certification tracks. The domain id is
        # derived from the module id rather than stored separately: a module IS
        # a domain in a certification track, and inventing a second identifier
        # would let the two drift apart.
        domain_id: str | None = None
        if m.get("exam_domain") is not None:
            domain_id = f"dom{module.id[3:]}"
            domain = await db.get(Domain, domain_id)
            if domain is None:
                domain = Domain(id=domain_id, track_id=track.id)
                db.add(domain)
            domain.track_id = track.id
            # The published blueprint names the domain in English; the Spanish
            # side reuses the module's own name, which is already native ES.
            domain.name_en = m["exam_domain"]
            domain.name_es = m["name_es"]
            domain.weight_pct = float(m["exam_weight_pct"])
            domain.order = m.get("order", m_order)

        for s_order, s in enumerate(m.get("skills", []), start=1):
            skill = await db.get(Skill, s["id"])
            if skill is None:
                skill = Skill(id=s["id"], module_id=module.id)
                db.add(skill)
            skill.module_id = module.id
            skill.name_es = s["name_es"]
            skill.name_en = s["name_en"]
            skill.order = s.get("order", s_order)
            skill.domain_id = domain_id


async def _upsert_question(db: AsyncSession, q: dict[str, Any]) -> bool:
    """Returns True if the question was ingested, False if skipped (unknown skill)."""
    skill = await db.get(Skill, q["skill_id"])
    if skill is None:
        return False

    question = await db.get(Question, q["id"])
    if question is None:
        question = Question(id=q["id"], skill_id=q["skill_id"])
        db.add(question)
    question.skill_id = q["skill_id"]
    question.type = q.get("type", "mcq")
    question.difficulty_tier = q.get("difficulty_tier", "medium")
    question.question_es = q["question_es"]
    question.question_en = q["question_en"]
    question.options_es = q.get("options_es")
    question.options_en = q.get("options_en")
    question.correct_index = q.get("correct_index")
    question.correct_answer_es = q.get("correct_answer_es")
    question.correct_answer_en = q.get("correct_answer_en")
    question.explanation_es = q.get("explanation_es", "")
    question.explanation_en = q.get("explanation_en", "")
    question.source = q.get("source")
    question.expected_time_ms = q.get("expected_time_ms", 15000)
    # Preserve content_version — only set on new rows; admin PATCHes bump it and
    # must not be silently reverted by a redeploy (see DECISIONS.md P.9).
    if question.content_version is None or question.content_version == 0:
        question.content_version = 1
    if "difficulty" in q:  # IRT difficulty (-3..3) -> seed Elo rating
        question.elo_rating = 1500.0 + float(q["difficulty"]) * 120.0
    if "discrimination" in q:
        question.discrimination = float(q["discrimination"])
    if "guessing" in q:
        question.guessing = float(q["guessing"])
    return True


async def _upsert_glossary_term(db: AsyncSession, t: dict[str, Any], order: int) -> bool:
    """Returns True if ingested, False if skipped (unknown track)."""
    track = await db.get(Track, t["track_id"])
    if track is None:
        return False

    term = await db.get(GlossaryTerm, t["id"])
    if term is None:
        term = GlossaryTerm(id=t["id"], track_id=t["track_id"])
        db.add(term)
    term.track_id = t["track_id"]
    term.term_es = t["term_es"]
    term.term_en = t["term_en"]
    term.definition_es = t["definition_es"]
    term.definition_en = t["definition_en"]
    term.source = t.get("source")
    term.order = t.get("order", order)
    return True


async def _upsert_lesson(db: AsyncSession, data: dict[str, Any]) -> bool:
    """Returns True if ingested, False if skipped (unknown skill)."""
    skill = await db.get(Skill, data["skill_id"])
    if skill is None:
        return False

    lesson = await db.get(Lesson, data["id"])
    if lesson is None:
        lesson = Lesson(id=data["id"], skill_id=data["skill_id"])
        db.add(lesson)
    lesson.skill_id = data["skill_id"]
    lesson.title_es = data["title_es"]
    lesson.title_en = data["title_en"]
    lesson.body_es = data["body_es"]
    lesson.body_en = data["body_en"]
    lesson.example_code = data.get("example_code")
    lesson.example_output = data.get("example_output")
    lesson.source = data["source"]
    lesson.order = data.get("order", 1)
    return True


async def load_content(db: AsyncSession) -> dict[str, Any]:
    root = _content_root()
    stats = {"tracks": 0, "questions": 0, "skipped": 0, "files": 0, "glossary": 0, "lessons": 0}

    # 1) Curriculum
    tracks_file = root / "curriculum" / "tracks.json"
    curriculum = json.loads(tracks_file.read_text(encoding="utf-8"))
    for track_data in curriculum.get("tracks", []):
        await _upsert_track(db, track_data)
        stats["tracks"] += 1
    await db.flush()

    # 2) Question banks
    questions_dir = root / "questions"
    for qfile in sorted(questions_dir.rglob("*.json")):
        payload = json.loads(qfile.read_text(encoding="utf-8"))
        items = payload if isinstance(payload, list) else payload.get("questions", [])
        stats["files"] += 1
        for q in items:
            ok = await _upsert_question(db, q)
            stats["questions" if ok else "skipped"] += 1

    # 3) Glossary (bilingual domain terms per track). Optional dir.
    glossary_dir = root / "glossary"
    if glossary_dir.is_dir():
        for gfile in sorted(glossary_dir.glob("*.json")):
            payload = json.loads(gfile.read_text(encoding="utf-8"))
            is_list = isinstance(payload, list)
            terms = payload if is_list else payload.get("terms", [])
            file_track_id = None if is_list else payload.get("track_id")
            stats["files"] += 1
            for order, t in enumerate(terms, start=1):
                # track_id may be declared once at file level or per term.
                t = {**t, "track_id": t.get("track_id", file_track_id)}
                ok = await _upsert_glossary_term(db, t, order)
                if ok:
                    stats["glossary"] += 1
                else:
                    stats["skipped"] += 1
        await db.flush()

    # 4) Lessons (instructional content per skill). Optional dir.
    lessons_dir = root / "lessons"
    if lessons_dir.is_dir():
        for lfile in sorted(lessons_dir.rglob("*.json")):
            payload = json.loads(lfile.read_text(encoding="utf-8"))
            # One file per lesson is the shape content/lessons/ actually uses, so a
            # bare lesson object has to count. Without this it matched neither branch
            # and became an empty list: every lesson silently failed to load while
            # the run still reported success.
            if isinstance(payload, list):
                items = payload
            elif "lessons" in payload:
                items = payload["lessons"]
            else:
                items = [payload]
            stats["files"] += 1
            for item in items:
                ok = await _upsert_lesson(db, item)
                if ok:
                    stats["lessons"] += 1
                else:
                    stats["skipped"] += 1
        await db.flush()

    # 5) Denormalized question count per track (explicit join — async has no lazy load)
    await db.flush()
    counts = await db.execute(
        select(Module.track_id, func.count(Question.id))
        .select_from(Question)
        .join(Skill, Question.skill_id == Skill.id)
        .join(Module, Skill.module_id == Module.id)
        .group_by(Module.track_id)
    )
    count_by_track = {track_id: n for track_id, n in counts.all()}
    tracks = (await db.execute(select(Track))).scalars().all()
    for track in tracks:
        track.total_questions = count_by_track.get(track.id, 0)

    await db.commit()
    return stats


async def main() -> None:
    await init_db()
    async with AsyncSessionLocal() as db:
        stats = await load_content(db)
    print(f"Content loaded: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
