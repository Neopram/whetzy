#!/usr/bin/env python3
"""Flags lessons whose own quiz tests a named service their body never covers.

Found by hand in track08 (37.1, 2026-09-28): l080102 taught "five pillars" of
the Well-Architected Framework while its own skill's questions (q080102001,
q080102002) already tested six, including Sustainability. Same pattern in
l080307 (Bedrock tested, never mentioned) and l080203 (IAM Identity Center and
Organizations SCPs tested, never mentioned) - a student reads one thing and
the quiz for that exact skill asks about another. That is a content bug, not
a style nit: lesson and question bank must teach the same material.

Heuristic: for every question whose own question_es/question_en text asks
"qué es/son X" or "what is/are X" about a named AWS/Amazon/Azure/GCP service,
check whether that service's name appears anywhere in the body_es/body_en of
the lesson sharing that question's skill_id. A hit means the lesson likely
never introduces something its own quiz tests directly.

This is a heuristic, not a guard: it has false positives (a service named only
in a wrong-answer option, or covered under a different name/abbreviation the
regex doesn't catch) and it only catches direct "what is X" questions, not
every kind of gap. Read each flagged pair before deciding it's a real defect -
that is what turned up the false positives already discarded when this was
run by hand for track08's write-up in docs/STATUS.md.

Usage:
    python scripts/audit_lesson_quiz_alignment.py             # every track
    python scripts/audit_lesson_quiz_alignment.py track08     # one track
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVICE_PATTERN = re.compile(
    r"\b(?:AWS|Amazon|Azure|Google Cloud|GCP) [A-Z][a-zA-Z0-9]+(?: [A-Z][a-zA-Z0-9]+){0,3}"
)
ASK_PATTERN = re.compile(r"(qué es|qué son|what is|what are)", re.IGNORECASE)
IGNORE_TERMS = {"cloud practitioner", "certified"}


def load_json(path: Path) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def iter_questions(data: object):
    if isinstance(data, list):
        yield from data
    elif isinstance(data, dict):
        qs = data.get("questions", [])
        if isinstance(qs, list):
            yield from qs


def main() -> int:
    track_filter = sys.argv[1] if len(sys.argv) > 1 else None

    def matches_filter(path: Path) -> bool:
        return not track_filter or any(track_filter in part for part in path.parts)

    lessons: dict[str, dict] = {}
    for path in ROOT.glob("content/lessons/*/*.json"):
        if not matches_filter(path):
            continue
        data = load_json(path)
        if isinstance(data, dict) and data.get("skill_id"):
            lessons[data["skill_id"]] = data

    questions_by_skill: dict[str, list[dict]] = {}
    for path in ROOT.glob("content/questions/*/*.json"):
        if not matches_filter(path):
            continue
        data = load_json(path)
        for q in iter_questions(data):
            sk = q.get("skill_id")
            if sk:
                questions_by_skill.setdefault(sk, []).append(q)

    findings = []
    for skill_id, qs in questions_by_skill.items():
        lesson = lessons.get(skill_id)
        if not lesson:
            continue
        lesson_text = (lesson.get("body_es", "") + " " + lesson.get("body_en", "")).lower()
        for q in qs:
            qtext = q.get("question_es", "") + " " + q.get("question_en", "")
            if not ASK_PATTERN.search(qtext):
                continue
            for service in set(SERVICE_PATTERN.findall(qtext)):
                if service.lower() in IGNORE_TERMS:
                    continue
                # A trailing generic word ("Service"/"Servicio") is often
                # dropped or translated differently in the lesson body even
                # when the actual product is covered in depth (Azure OpenAI
                # Service -> lesson says "Azure OpenAI"; Azure Language
                # Service -> lesson says "Azure AI Language"). Check the core
                # name too before flagging.
                core = re.sub(r"\s+(Service|Servicio)$", "", service, flags=re.IGNORECASE)
                if service.lower() not in lesson_text and core.lower() not in lesson_text:
                    findings.append((lesson["id"], skill_id, q["id"], service))

    findings.sort()
    for lesson_id, skill_id, question_id, service in findings:
        print(f"{lesson_id} ({skill_id}) {question_id}: possibly missing '{service}'")
    print(f"\n{len(findings)} flagged instance(s) across {len(lessons)} lesson(s) checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
