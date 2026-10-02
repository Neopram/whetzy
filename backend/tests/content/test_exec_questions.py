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
import tempfile
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
    # Every track, not a hardcoded track01-03. The list was written when only
    # those three had executable questions, and it silently stopped being true:
    # track04 and track06 already carry exec questions that this harness has
    # never run, so their advertised answers were never checked against CPython.
    # 17.3 adds many more, and content that claims "run this" while nothing ever
    # ran it is exactly what this file exists to prevent.
    questions_root = root / "questions"
    for track_dir in sorted(p for p in questions_root.iterdir() if p.is_dir()):
        qdir = track_dir
        for qfile in sorted(qdir.rglob("*.json")):
            payload = json.loads(qfile.read_text(encoding="utf-8"))
            items = payload if isinstance(payload, list) else payload.get("questions", [])
            for q in items:
                if q.get("type") in EXEC_TYPES:
                    questions.append(q)
    return questions


def _load_reference_solutions() -> dict[str, Any]:
    return json.loads(REFERENCE_SOLUTIONS_PATH.read_text(encoding="utf-8"))


def _build_code_to_run(
    question: dict[str, Any], reference: dict[str, Any], lang: str = "es"
) -> str:
    """Reproduces the frontend's `codeToRun` construction (QuizScreen.tsx
    handleRun) for one language.

    The two languages are not always the same program: `question_en` carries
    its own fenced block, and where the printed output is a message rather
    than a demo literal it uses English identifiers and English strings
    (11.12). `fill_en` / `fixed_en` in the sidecar override the Spanish
    reference for exactly those; everywhere else the same fill serves both.
    """
    field = "question_es" if lang == "es" else "question_en"
    if question["type"] == "fill_blank_exec":
        code = _extract_code_block(question[field])
        assert code is not None, f"{question['id']}: no fenced code block in {field}"
        fill = reference["fill"] if lang == "es" else reference.get("fill_en", reference["fill"])
        return code.replace("___", fill, 1)
    # fix_bug: the student edits the buggy code directly; the reference
    # solution is the fixed program, run as-is (mirrors userInput after a
    # correct fix).
    return reference["fixed"] if lang == "es" else reference.get("fixed_en", reference["fixed"])


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
    # Each program runs in its own empty directory: the file exercises write
    # `notas.txt` to the current directory, as they do in the browser (Pyodide's
    # in-memory filesystem), and must not leave it in the repository.
    with tempfile.TemporaryDirectory() as cwd:
        return subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            encoding="utf-8",
            errors="strict",
            env=env,
            cwd=cwd,
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
        """The core guarantee: run each exec question's reference program in real
        CPython and assert its stdout equals the answer that question publishes,
        exactly (after trim — mirrors the frontend's
        `result.output.trim() === expected` comparison).

        Both languages are checked independently. They are not always the same
        program: `question_en` carries its own fenced block, and where the
        printed output is a message rather than a demo literal it uses English
        identifiers and English strings (11.12), so `correct_answer_en` differs
        from `correct_answer_es`. Comparing one run against both answers, as
        this test used to, would have silently required them to be identical —
        i.e. required the English learner to read Spanish code.
        """
        failures: list[str] = []
        checked = 0

        for question in EXEC_QUESTIONS:
            qid = question["id"]
            reference = REFERENCE_SOLUTIONS.get(qid)
            if reference is None:
                # Reported by test_every_exec_question_has_a_reference_solution.
                continue

            for lang in ("es", "en"):
                expected = (question.get(f"correct_answer_{lang}") or "").strip()
                if self._verify_one(qid, question, reference, lang, expected, failures):
                    checked += 1

        assert checked > 0, "no exec questions were actually executed — check content path resolution"
        assert failures == [], (
            f"{len(failures)} of {checked + len(failures)} exec question/language pairs "
            "failed reference verification:\n" + "\n".join(failures)
        )

    def _verify_one(
        self,
        qid: str,
        question: dict[str, Any],
        reference: dict[str, Any],
        lang: str,
        expected: str,
        failures: list[str],
    ) -> bool:
        """Run one question's reference program in one language. Returns True
        when its stdout matched that language's published answer."""
        try:
            code = _build_code_to_run(question, reference, lang)
        except AssertionError as e:
            failures.append(str(e))
            return False

        try:
            proc = _run_in_cpython(code)
        except subprocess.TimeoutExpired:
            failures.append(
                f"{qid} [{lang}]: reference solution timed out after {PER_QUESTION_TIMEOUT_S}s"
            )
            return False

        if proc.returncode != 0:
            failures.append(
                f"{qid} [{lang}]: reference solution raised an error instead of "
                f"running cleanly:\n{(proc.stderr or '').strip()[-500:]}"
            )
            return False

        if proc.stdout is None:
            # Defensive: a captured subprocess should always yield a string. If
            # the platform hands back None, report it as this pair's failure
            # with context instead of raising AttributeError and aborting the
            # verdict on every other question.
            failures.append(
                f"{qid} [{lang}]: subprocess returned no captured stdout "
                f"(rc={proc.returncode}, stderr={(proc.stderr or '')!r})"
            )
            return False

        actual = proc.stdout.strip()
        if actual != expected:
            failures.append(
                f"{qid} [{lang}]: stdout {actual!r} != correct_answer_{lang} {expected!r}"
            )
            return False
        return True

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


# ── Que no se pueda acertar sin hacer el ejercicio (2026-10-01) ─────────────────
#
# Lo de arriba solo comprueba que la solución buena da la salida publicada. Nunca
# comprobó lo contrario, y el 2026-10-01 había 216 ejercicios que daban
# «correcto» pulsando Ejecutar sin escribir nada:
# - 172 `fill_blank_exec` y 31 `js_exec` sin hueco: el programa entero imprimía
#   la respuesta;
# - 5 `except ___:` donde el hueco vacío deja un `except:` válido;
# - 8 `fix_bug` cuyo código con el bug ya imprimía lo esperado (el bug era de
#   seguridad, no de salida).
# Y 13 `js_exec` imposibles: 6 usaban `ANSWER` en vez de `___`.
# Estos tests fijan que vuelva a ser imposible.

JS_EXEC_TYPE = "js_exec"
BLANK_TYPES = {"fill_blank_exec", JS_EXEC_TYPE}


def _all_questions_of(types: set[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for qfile in sorted((_content_root() / "questions").rglob("*.json")):
        payload = json.loads(qfile.read_text(encoding="utf-8"))
        items = payload if isinstance(payload, list) else payload.get("questions", [])
        out.extend(q for q in items if q.get("type") in types)
    return out


def _code_for(question: dict[str, Any], lang: str) -> str | None:
    """Lo mismo que `resolveCode` del frontend: `code_xx` o el bloque del enunciado."""
    return question.get(f"code_{lang}") or _extract_code_block(question.get(f"question_{lang}") or "")


def _run_js(code: str) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["node", "-e", code], capture_output=True, encoding="utf-8",
            timeout=PER_QUESTION_TIMEOUT_S, check=False,
        )
    except FileNotFoundError:
        return None


class TestNoFreeAnswers:
    def test_every_fill_in_question_has_a_blank(self) -> None:
        """Sin `___` el frontend ejecuta el programa tal cual: lo escrito no cuenta."""
        missing = [
            f"{q['id']} [{lang}]"
            for q in _all_questions_of(BLANK_TYPES)
            for lang in ("es", "en")
            if "___" not in (_code_for(q, lang) or "")
        ]
        assert missing == [], f"{len(missing)} ejecutables sin hueco ___: {missing[:20]}"

    def test_no_placeholder_the_frontend_never_replaces(self) -> None:
        """`ANSWER` (o similares) no lo sustituye nadie: el ejercicio es imposible."""
        bad = [
            q["id"]
            for q in _all_questions_of(BLANK_TYPES | {"fix_bug"})
            if re.search(r"\bANSWER\b", _code_for(q, "es") or "")
        ]
        assert bad == [], f"marcador que el frontend no reemplaza: {bad}"

    def test_an_empty_python_blank_is_never_correct(self) -> None:
        failures: list[str] = []
        for q in _all_questions_of({"fill_blank_exec"}):
            for lang in ("es", "en"):
                code = _code_for(q, lang)
                expected = (q.get(f"correct_answer_{lang}") or "").strip()
                if not code or "___" not in code:
                    continue  # lo informa test_every_fill_in_question_has_a_blank
                proc = _run_in_cpython(code.replace("___", "", 1))
                if proc.returncode == 0 and (proc.stdout or "").strip() == expected:
                    failures.append(f"{q['id']} [{lang}]")
        assert failures == [], f"el hueco vacío ya da la respuesta: {failures}"

    def test_an_unfixed_bug_is_never_correct(self) -> None:
        """En `fix_bug` el editor arranca con el código con el bug: ejecutarlo sin
        tocar nada no puede imprimir la respuesta."""
        failures: list[str] = []
        for q in _all_questions_of({"fix_bug"}):
            for lang in ("es", "en"):
                code = _code_for(q, lang)
                expected = (q.get(f"correct_answer_{lang}") or "").strip()
                if not code:
                    continue
                proc = _run_in_cpython(code)
                if proc.returncode == 0 and (proc.stdout or "").strip() == expected:
                    failures.append(f"{q['id']} [{lang}]")
        assert failures == [], f"el código sin arreglar ya da la respuesta: {failures}"

    def test_an_empty_js_blank_is_never_correct(self) -> None:
        questions = _all_questions_of({JS_EXEC_TYPE})
        if _run_js("1") is None:
            pytest.skip("node no está instalado")
        failures = []
        for q in questions:
            code = _code_for(q, "es")
            expected = (q.get("correct_answer_es") or "").strip()
            if not code or "___" not in code:
                continue
            proc = _run_js(code.replace("___", "", 1))
            if proc is not None and proc.returncode == 0 and proc.stdout.strip() == expected:
                failures.append(q["id"])
        assert failures == [], f"el hueco vacío ya da la respuesta: {failures}"

    def test_fill_blank_answers_fit_in_one_line(self) -> None:
        """`fill_blank` se responde en un campo de una línea: una respuesta con
        saltos de línea no se puede escribir."""
        multi = [
            q["id"]
            for q in _all_questions_of({"fill_blank"})
            if any("\n" in (q.get(f"correct_answer_{lang}") or "").strip() for lang in ("es", "en"))
        ]
        assert multi == [], f"respuestas de varias líneas en fill_blank: {multi}"
