"""Executes every lesson's `example_code` and asserts its stdout matches
`example_output` exactly, plus the shape rules a lesson has to satisfy before
it can ship (task 17.1).

A lesson is the one place in the product that *teaches* rather than tests, so a
lesson whose worked example does not actually produce the output printed next to
it is worse than no lesson at all: the learner trusts it, and it is wrong. Every
example is therefore run for real — Python in a CPython subprocess, SQL in
sqlite3 formatted exactly like `sql-worker.js` renders it — with a hard
per-lesson timeout so one runaway example cannot hang CI.

The body-length bar (150-300 words in BOTH languages) is not cosmetic. Below
~150 words a "lesson" is a definition with an example stapled to it, which is
what the first 15 were; above ~300 it stops being readable on the phone this
product is built for. Red line 3 applies with no exception: nothing ships in one
language, so ES and EN are checked independently rather than "ES exists, assume
EN".
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from app.services.content_loader import _content_root

PER_LESSON_TIMEOUT_S = 8
MIN_BODY_WORDS = 150
MAX_BODY_WORDS = 300

# Ratchet, same idiom as MIN_NEW_EXEC_QUESTIONS in test_exec_questions.py: it
# rises as authoring lands and never falls, so a session cannot quietly delete
# lessons to make a run green. 17.1 closes when this equals the skill count and
# `test_every_skill_has_a_lesson` is turned from a report into an assertion.
MIN_LESSONS = 15


def _load_lessons() -> list[tuple[Path, dict[str, Any]]]:
    root = _content_root()
    lessons: list[tuple[Path, dict[str, Any]]] = []
    for lfile in sorted((root / "lessons").rglob("*.json")):
        payload = json.loads(lfile.read_text(encoding="utf-8"))
        items = payload if isinstance(payload, list) else [payload]
        for lesson in items:
            lessons.append((lfile, lesson))
    return lessons


def _all_skill_ids() -> set[str]:
    tracks = json.loads(
        (_content_root() / "curriculum" / "tracks.json").read_text(encoding="utf-8")
    )
    return {
        skill["id"]
        for track in tracks["tracks"]
        for module in track.get("modules", [])
        for skill in module.get("skills", [])
    }


LESSONS = _load_lessons()
SKILL_IDS = _all_skill_ids()


def _lesson_id(case: tuple[Path, dict[str, Any]]) -> str:
    return str(case[1].get("id", case[0].name))


def _word_count(text: str) -> int:
    return len(text.split())


def _run_in_cpython(code: str) -> subprocess.CompletedProcess[str]:
    """Runs `code` as a real CPython subprocess.

    PYTHONIOENCODING is forced on both sides for the same reason as in
    test_exec_questions.py: this content is Spanish, and on a cp1252 Windows box
    the child's UTF-8 bytes would fail to decode inside subprocess's reader
    thread, handing back `stdout=None` with returncode 0 — which reads as "the
    program printed nothing" instead of an error, masking real mismatches.
    """
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=PER_LESSON_TIMEOUT_S,
        env=env,
        # Explicitly not check=True: a lesson whose example raises must be
        # reported as that lesson's failure with its stderr attached, not as a
        # CalledProcessError that says nothing about which lesson broke.
        check=False,
    )


def _format_like_sql_worker(results: list[tuple[list[str], list[tuple[Any, ...]]]]) -> str:
    """Reproduces frontend/public/sql-worker.js output format.

    Kept byte-identical to the worker on purpose: a lesson's printed output has
    to be what the learner will see if they press Run, not a prettier version of
    it. Mirrors `_worker_format` in test_sql_exec_questions.py.
    """
    if not results:
        return "(no rows)"
    parts: list[str] = []
    for cols, rows in results:
        lines = [" | ".join(cols)]
        lines.append("-+-".join("-" * len(c) for c in cols))
        for row in rows:
            lines.append(" | ".join(str(v) for v in row))
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


def _run_sql(code: str) -> str:
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    results: list[tuple[list[str], list[tuple[Any, ...]]]] = []
    try:
        for stmt in [s.strip() for s in code.split(";") if s.strip()]:
            cursor.execute(stmt)
            if cursor.description:
                cols = [d[0] for d in cursor.description]
                results.append((cols, cursor.fetchall()))
    finally:
        conn.close()
    return _format_like_sql_worker(results)


def _is_sql(lesson: dict[str, Any]) -> bool:
    """SQL lessons declare it; everything else is Python.

    Explicit field rather than sniffing the code, so a Python example that
    happens to contain the word SELECT in a string is not run against sqlite3.
    """
    return str(lesson.get("language", "python")).lower() == "sql"


# ── Shape ─────────────────────────────────────────────────────────────────────


def test_there_are_lessons_to_check() -> None:
    assert len(LESSONS) >= MIN_LESSONS, (
        f"{len(LESSONS)} lessons found, ratchet is {MIN_LESSONS} — lessons were "
        "deleted, or the content root moved"
    )


def test_lesson_ids_are_unique_and_match_their_filename() -> None:
    seen: dict[str, Path] = {}
    problems: list[str] = []
    for path, lesson in LESSONS:
        lesson_id = lesson.get("id")
        if not lesson_id:
            problems.append(f"{path.name}: no id")
            continue
        if lesson_id in seen:
            problems.append(f"{lesson_id}: also in {seen[lesson_id].name}")
        seen[lesson_id] = path
        if path.stem != lesson_id:
            problems.append(f"{path.name}: id is {lesson_id}")
    assert not problems, "\n".join(problems)


def test_every_lesson_points_at_a_real_skill() -> None:
    problems = [
        f"{lesson.get('id')}: skill_id {lesson.get('skill_id')!r} is not in tracks.json"
        for _path, lesson in LESSONS
        if lesson.get("skill_id") not in SKILL_IDS
    ]
    assert not problems, "\n".join(problems)


def test_at_most_one_lesson_per_skill() -> None:
    by_skill: dict[str, list[str]] = {}
    for _path, lesson in LESSONS:
        by_skill.setdefault(str(lesson.get("skill_id")), []).append(str(lesson.get("id")))
    duplicated = {s: ids for s, ids in by_skill.items() if len(ids) > 1}
    assert not duplicated, f"more than one lesson for the same skill: {duplicated}"


def test_lesson_coverage_is_reported(capsys: pytest.CaptureFixture[str]) -> None:
    """Reports skills-with-a-lesson. 17.1 closes when this is 281/281 and this
    test becomes an assertion instead of a report."""
    covered = {str(lesson.get("skill_id")) for _p, lesson in LESSONS}
    with capsys.disabled():
        print(
            f"\n[lessons] {len(covered)}/{len(SKILL_IDS)} skills have a lesson "
            f"({100 * len(covered) / max(1, len(SKILL_IDS)):.1f}%)"
        )
    assert covered <= SKILL_IDS


# ── Red line 3: nothing ships in one language ─────────────────────────────────


@pytest.mark.parametrize("case", LESSONS, ids=_lesson_id)
def test_both_languages_are_present(case: tuple[Path, dict[str, Any]]) -> None:
    _path, lesson = case
    for field in ("title_es", "title_en", "body_es", "body_en"):
        value = lesson.get(field)
        assert isinstance(value, str) and value.strip(), (
            f"{lesson.get('id')}: {field} is empty — nothing ships in one language"
        )


@pytest.mark.parametrize("case", LESSONS, ids=_lesson_id)
def test_body_length_is_within_the_bar(case: tuple[Path, dict[str, Any]]) -> None:
    _path, lesson = case
    problems: list[str] = []
    for field in ("body_es", "body_en"):
        words = _word_count(str(lesson.get(field, "")))
        if not MIN_BODY_WORDS <= words <= MAX_BODY_WORDS:
            problems.append(
                f"{field} is {words} words, needs {MIN_BODY_WORDS}-{MAX_BODY_WORDS}"
            )
    assert not problems, f"{lesson.get('id')}: " + "; ".join(problems)


@pytest.mark.parametrize("case", LESSONS, ids=_lesson_id)
def test_the_two_languages_are_not_the_same_text(case: tuple[Path, dict[str, Any]]) -> None:
    """Content is written natively in both, never translated by copy-paste — an
    identical body means one language was left as a placeholder."""
    _path, lesson = case
    assert lesson["body_es"].strip() != lesson["body_en"].strip(), (
        f"{lesson.get('id')}: body_es and body_en are identical"
    )


# ── Sourcing ──────────────────────────────────────────────────────────────────

URL_RE = re.compile(r"https?://\S+")


@pytest.mark.parametrize("case", LESSONS, ids=_lesson_id)
def test_every_lesson_cites_a_resolvable_looking_source(
    case: tuple[Path, dict[str, Any]]
) -> None:
    """Shape only — no network.

    Deliberate: scripts/check_content_sources.py is the one that fetches, and it
    is manual precisely so a docs-site outage cannot turn the build red. What
    this asserts is that there IS a citation and that it points somewhere.
    """
    _path, lesson = case
    source = str(lesson.get("source", "")).strip()
    assert source, f"{lesson.get('id')}: no source — every lesson cites its source"
    assert URL_RE.search(source), f"{lesson.get('id')}: source has no URL: {source!r}"


# ── The example actually runs ─────────────────────────────────────────────────


@pytest.mark.parametrize("case", LESSONS, ids=_lesson_id)
def test_example_code_produces_example_output(case: tuple[Path, dict[str, Any]]) -> None:
    _path, lesson = case
    code = str(lesson.get("example_code", "")).strip()
    assert code, f"{lesson.get('id')}: no example_code"
    expected = str(lesson.get("example_output", "")).rstrip("\n")

    if _is_sql(lesson):
        actual = _run_sql(code).rstrip("\n")
        assert actual == expected, (
            f"{lesson.get('id')}: SQL example output mismatch\n"
            f"--- expected ---\n{expected}\n--- actual ---\n{actual}"
        )
        return

    proc = _run_in_cpython(code)
    assert proc.returncode == 0, (
        f"{lesson.get('id')}: example_code raised\n{proc.stderr}"
    )
    actual = (proc.stdout or "").rstrip("\n")
    assert actual == expected, (
        f"{lesson.get('id')}: example output mismatch\n"
        f"--- expected ---\n{expected}\n--- actual ---\n{actual}"
    )
