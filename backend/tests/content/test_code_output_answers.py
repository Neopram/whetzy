"""Runs every Python `code_output` question in CPython and fails when the real
output is one of the *other* options.

`test_exec_questions.py` covers the questions the learner runs; a
`code_output` item is never executed by anyone, so its key is only as good as
whoever wrote it. On 2026-10-01 four were wrong: two `a is b, c is d` items
marked «True False» where CPython 3.10-3.13 print «True True» (a script reuses
equal constants), one printed «facturacion» against options with an accent,
and one printed «creadoinicio» against «creado inicio».

The check is deliberately one-sided. Most options are not literal stdout
(«`[1]` y luego `[1, 2]`», descriptions, pytest scenarios that print nothing),
so "output differs from the key" is noise. "Output is, character for
character, a distractor" is not: the bank is then teaching the wrong answer.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from app.services.content_loader import _content_root

PYTHON_FENCE_RE = re.compile(r"```python\n([\s\S]*?)```")
PER_QUESTION_TIMEOUT_S = 8


def _code(question: dict[str, Any], lang: str) -> str | None:
    if question.get(f"code_{lang}"):
        return str(question[f"code_{lang}"])
    m = PYTHON_FENCE_RE.search(question.get(f"question_{lang}") or "")
    return m.group(1) if m else None


def _norm(text: str) -> str:
    """Same text, whatever the wrapping: backticks around an option, a literal
    «\\n» written in the option for a line break, trailing spaces and the final
    newline that print adds. Inner and leading spaces count («   ana|»)."""
    text = text.rstrip()
    wrapped = text.strip()
    if len(wrapped) >= 2 and wrapped[0] == wrapped[-1] == "`":
        text = wrapped[1:-1]
    text = text.replace("\\n", "\n")
    return "\n".join(line.rstrip() for line in text.strip("\n").split("\n"))


def _run(code: str) -> str | None:
    """stdout of a clean run, in a fresh directory (snippets write f.txt and
    read it back: a shared cwd made one item's answer depend on another's).
    None if it raises or times out: those are judged by their options' text."""
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    with tempfile.TemporaryDirectory() as cwd:
        path = Path(cwd) / "snippet.py"
        path.write_text(code, encoding="utf-8")
        try:
            r = subprocess.run(
                [sys.executable, str(path)],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                timeout=PER_QUESTION_TIMEOUT_S,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return None
    return r.stdout if r.returncode == 0 else None


def _load() -> list[tuple[dict[str, Any], str, str]]:
    cases: list[tuple[dict[str, Any], str, str]] = []
    for qfile in sorted((_content_root() / "questions").rglob("*.json")):
        payload = json.loads(qfile.read_text(encoding="utf-8"))
        items = payload if isinstance(payload, list) else payload.get("questions", [])
        for q in items:
            if not isinstance(q, dict) or q.get("type") != "code_output":
                continue
            if q.get("correct_index") is None:
                continue
            for lang in ("es", "en"):
                code = _code(q, lang)
                if code and q.get(f"options_{lang}"):
                    cases.append((q, lang, code))
    return cases


CASES = _load()


def _check(case: tuple[dict[str, Any], str, str]) -> str | None:
    q, lang, code = case
    out = _run(code)
    if out is None:
        return None
    got = _norm(out)
    options = [_norm(o) for o in q[f"options_{lang}"]]
    marked = q["correct_index"]
    if got == options[marked]:
        return None
    hits = [i for i, o in enumerate(options) if o == got]
    if hits:
        return (
            f"{q['id']} ({lang}): CPython imprime {got!r}, que es la opción {hits[0]}; "
            f"la marcada es la {marked}: {options[marked]!r}"
        )
    return None


def test_code_output_bank_is_not_empty() -> None:
    # Sin esto, un cambio de ruta dejaría la guarda en verde sin ejecutar nada.
    assert len(CASES) > 500, f"solo {len(CASES)} code_output con código Python"


def test_no_code_output_marks_a_distractor_as_its_real_output() -> None:
    with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 2)) as pool:
        failures = [f for f in pool.map(_check, CASES) if f]
    assert failures == [], "\n".join(failures)
