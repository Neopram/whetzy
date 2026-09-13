"""Executes every `fill_blank_exec` / `fix_bug` question's reference solution in
CPython and asserts its stdout matches `correct_answer_es` / `correct_answer_en`
exactly.

This is the only thing standing between the content bank and shipping a
"run the code" question whose own advertised answer is wrong. Each question's
question_es carries a fenced ```python code block, exactly like the frontend
renders it (see frontend/src/pages/QuizScreen.tsx `parseQuestion`); this test
reconstructs the same `codeToRun` the frontend builds before handing it to
Pyodide (blank-fill for `fill_blank_exec`, the fixed program for `fix_bug`,
looked up from the reference-solutions sidecar next to this file) and runs it
for real in a subprocess, with a hard per-question timeout so a reference
solution with an accidental infinite loop cannot hang CI.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from app.services.content_loader import _content_root

CODE_FENCE_RE = re.compile(r"```[a-zA-Z]*\n?([\s\S]*?)```")
PER_QUESTION_TIMEOUT_S = 8
EXEC_TYPES = {"fill_blank_exec", "fix_bug"}
MIN_NEW_EXEC_QUESTIONS = 90

REFERENCE_SOLUTIONS_PATH = Path(__file__).parent / "exec_reference_solutions.json"

# Question ids that shipped before ledger item 11.4 — used only to report how
# many *new* exec questions this change adds, on top of the pre-existing bank.
PRE_EXISTING_EXEC_IDS = {
    "q010101ex001",
    "q010103ex001",
    "q010201ex001",
    "q010202ex001",
    "q010301ex001",
    "q010202fb001",
    "q010301fb001",
}


def _extract_code_block(text: str) -> str | None:
    """Mirrors `parseQuestion` in frontend/src/pages/QuizScreen.tsx exactly."""
    m = CODE_FENCE_RE.search(text)
    if not m:
        return None
    return re.sub(r"\n$", "", m.group(1))


def _load_exec_questions() -> list[dict[str, Any]]:
    """Every fill_blank_exec / fix_bug question under content/questions/track01-03."""
    root = _content_root()
    questions: list[dict[str, Any]] = []
    for track_dir in ("track01_python_basics", "track02_python_intermediate", "track03_python_advanced"):
        qdir = root / "questions" / track_dir
        if not qdir.is_dir():
            continue
        for qfile in sorted(qdir.rglob("*.json")):
            payload = json.loads(qfile.read_text(encoding="utf-8"))
            items = payload if isinstance(payload, list) else payload.get("questions", [])
            for q in items:
                if q.get("type") in EXEC_TYPES:
                    questions.append(q)
    return questions


def _load_reference_solutions() -> dict[str, Any]:
    return json.loads(REFERENCE_SOLUTIONS_PATH.read_text(encoding="utf-8"))


def _build_code_to_run(question: dict[str, Any], reference: dict[str, Any]) -> str:
    """Reproduces the frontend's `codeToRun` construction (QuizScreen.tsx handleRun)."""
    if question["type"] == "fill_blank_exec":
        code = _extract_code_block(question["question_es"])
        assert code is not None, f"{question['id']}: no fenced code block in question_es"
        fill = reference["fill"]
        return code.replace("___", fill, 1)
    # fix_bug: the student edits the buggy code directly; the reference
    # solution is the fixed program, run as-is (mirrors userInput after a
    # correct fix).
    return reference["fixed"]


def _run_in_cpython(code: str) -> subprocess.CompletedProcess[str]:
    """Runs `code` as a real CPython subprocess — the literal ledger requirement:
    "ejecuta el código de referencia en CPython y compara stdout". A hard
    per-question timeout means one runaway reference solution cannot hang CI.
    """
    # UTF-8 on BOTH sides, explicitly. The content is Spanish: half these
    # programs print accented text. Without this, on a machine whose locale is
    # cp1252 (any default Windows box) the child still emits UTF-8 bytes while
    # `text=True` decodes them with cp1252 — the decode raises inside
    # subprocess's reader THREAD, which dies silently, and `run` hands back
    # `stdout=None` with returncode 0 and empty stderr. That looks like "the
    # program printed nothing" rather than an error, so it would mask real
    # mismatches instead of reporting them. Linux CI (UTF-8 locale) would never
    # show it.
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        encoding="utf-8",
        errors="strict",
        env=env,
        timeout=PER_QUESTION_TIMEOUT_S,
        check=False,
    )


EXEC_QUESTIONS = _load_exec_questions()
REFERENCE_SOLUTIONS = _load_reference_solutions()


class TestExecQuestionCorpus:
    def test_at_least_ninety_new_exec_questions_shipped(self) -> None:
        """Red line for ledger 11.4: >= 90 new exec questions across tracks 01-03."""
        ids = {q["id"] for q in EXEC_QUESTIONS}
        new_ids = ids - PRE_EXISTING_EXEC_IDS
        assert len(new_ids) >= MIN_NEW_EXEC_QUESTIONS, (
            f"only {len(new_ids)} new exec questions found, need >= {MIN_NEW_EXEC_QUESTIONS}"
        )

    def test_every_exec_question_has_a_reference_solution(self) -> None:
        missing = [q["id"] for q in EXEC_QUESTIONS if q["id"] not in REFERENCE_SOLUTIONS]
        assert missing == [], f"exec questions with no verifiable reference solution: {missing}"

    def test_exec_ratio_in_tracks_01_03_meets_target(self) -> None:
        """Ledger 11.4's headline goal: exec ratio in tracks 01-03 >= 15%."""
        root = _content_root()
        total = 0
        exec_total = 0
        for track_dir in ("track01_python_basics", "track02_python_intermediate", "track03_python_advanced"):
            qdir = root / "questions" / track_dir
            for qfile in sorted(qdir.rglob("*.json")):
                payload = json.loads(qfile.read_text(encoding="utf-8"))
                items = payload if isinstance(payload, list) else payload.get("questions", [])
                for q in items:
                    total += 1
                    if q.get("type") in EXEC_TYPES:
                        exec_total += 1
        ratio = exec_total / total
        assert ratio >= 0.15, f"exec ratio in tracks 01-03 is {ratio:.4f} ({exec_total}/{total}), need >= 0.15"

    def test_every_reference_solution_matches_correct_answer(self) -> None:
        """The core guarantee: run the reference program for every exec question in
        real CPython and assert its stdout equals the shipped correct_answer_es /
        correct_answer_en, exactly (after trim — mirrors the frontend's
        `result.output.trim() === expected` comparison).
        """
        failures: list[str] = []
        checked = 0

        for question in EXEC_QUESTIONS:
            qid = question["id"]
            reference = REFERENCE_SOLUTIONS.get(qid)
            if reference is None:
                # Reported by test_every_exec_question_has_a_reference_solution.
                continue

            try:
                code = _build_code_to_run(question, reference)
            except AssertionError as e:
                failures.append(str(e))
                continue

            try:
                proc = _run_in_cpython(code)
            except subprocess.TimeoutExpired:
                failures.append(f"{qid}: reference solution timed out after {PER_QUESTION_TIMEOUT_S}s")
                continue

            if proc.returncode != 0:
                failures.append(
                    f"{qid}: reference solution raised an error instead of running "
                    f"cleanly:\n{proc.stderr.strip()[-500:]}"
                )
                continue

            if proc.stdout is None:
                # Defensive: a captured subprocess should always yield a
                # string. If the platform hands back None (seen on Windows
                # under load), report it as this question's failure with
                # context instead of raising AttributeError and aborting the
                # whole corpus check — one flaky process must not hide the
                # verdict on the other 110.
                failures.append(
                    f"{qid}: subprocess returned no captured stdout "
                    f"(rc={proc.returncode}, stderr={(proc.stderr or '')!r})"
                )
                continue

            actual = proc.stdout.strip()
            expected_es = (question.get("correct_answer_es") or "").strip()
            expected_en = (question.get("correct_answer_en") or "").strip()

            if actual != expected_es:
                failures.append(
                    f"{qid}: stdout {actual!r} != correct_answer_es {expected_es!r}"
                )
                continue
            if actual != expected_en:
                failures.append(
                    f"{qid}: stdout {actual!r} != correct_answer_en {expected_en!r}"
                )
                continue

            checked += 1

        assert checked > 0, "no exec questions were actually executed — check content path resolution"
        assert failures == [], (
            f"{len(failures)}/{checked + len(failures)} exec question(s) failed reference "
            "verification:\n" + "\n".join(failures)
        )

    @pytest.mark.parametrize("track_dir", [
        "track01_python_basics",
        "track02_python_intermediate",
        "track03_python_advanced",
    ])
    def test_exec_questions_are_bilingual_and_cite_a_source(self, track_dir: str) -> None:
        """Red lines 2 & 3 scoped to the new exec content specifically."""
        root = _content_root()
        qdir = root / "questions" / track_dir
        for qfile in sorted(qdir.rglob("*.json")):
            payload = json.loads(qfile.read_text(encoding="utf-8"))
            items = payload if isinstance(payload, list) else payload.get("questions", [])
            for q in items:
                if q.get("type") not in EXEC_TYPES:
                    continue
                assert q.get("source"), f"{q['id']}: missing source"
                assert q.get("question_es"), f"{q['id']}: missing question_es"
                assert q.get("question_en"), f"{q['id']}: missing question_en"
                assert q.get("correct_answer_es"), f"{q['id']}: missing correct_answer_es"
                assert q.get("correct_answer_en"), f"{q['id']}: missing correct_answer_en"
