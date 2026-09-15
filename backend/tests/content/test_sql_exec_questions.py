"""Verifies every sql_exec question in the content bank.

For each question:
  1. code_es / code_en is present (SQL template with ___ blank)
  2. correct_answer_es / correct_answer_en is present
  3. source is cited
  4. Running the SQL (with blank filled from the reference fill sidecar) in
     an in-memory SQLite DB produces output that exactly matches the expected
     answer — same output format as the sql-worker.js (text table).

The output format mirrors sql-worker.js:
  cols joined by ' | '
  separator: each col name length dashes, joined by '-+-'
  rows: values joined by ' | '
If the query returns no rows: '(no rows)'
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from app.services.content_loader import _content_root

FILLS_PATH = Path(__file__).parent / "sql_exec_reference_fills.json"


def _worker_format(results: list[tuple[list[str], list[tuple]]]) -> str:
    """Reproduces sql-worker.js output format."""
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


def _run_sql(code: str) -> tuple[str, str | None]:
    """Execute SQL in an in-memory SQLite DB. Returns (output, error)."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    results: list[tuple[list[str], list[tuple]]] = []
    try:
        for stmt in [s.strip() for s in code.split(";") if s.strip()]:
            cursor.execute(stmt)
            if cursor.description:
                cols = [d[0] for d in cursor.description]
                rows = cursor.fetchall()
                results.append((cols, rows))
    except Exception as exc:
        conn.close()
        return "", str(exc)
    conn.close()
    if not results:
        return "(no rows)", None
    return _worker_format(results), None


def _load_sql_exec_questions() -> list[dict[str, Any]]:
    root = _content_root()
    questions: list[dict[str, Any]] = []
    for qfile in sorted(root.rglob("questions/**/*.json")):
        payload = json.loads(qfile.read_text(encoding="utf-8"))
        items = payload if isinstance(payload, list) else payload.get("questions", [])
        for q in items:
            if q.get("type") == "sql_exec":
                questions.append(q)
    return questions


SQL_EXEC_QUESTIONS = _load_sql_exec_questions()
REFERENCE_FILLS = json.loads(FILLS_PATH.read_text(encoding="utf-8"))


class TestSqlExecQuestions:
    def test_sql_exec_questions_exist(self) -> None:
        assert len(SQL_EXEC_QUESTIONS) >= 11, (
            f"expected >= 11 sql_exec questions, found {len(SQL_EXEC_QUESTIONS)}"
        )

    def test_every_sql_exec_question_has_required_fields(self) -> None:
        missing: list[str] = []
        for q in SQL_EXEC_QUESTIONS:
            qid = q["id"]
            for field in ("code_es", "code_en", "correct_answer_es", "correct_answer_en", "source"):
                if not q.get(field):
                    missing.append(f"{qid}: missing {field}")
        assert missing == [], "sql_exec questions with missing required fields:\n" + "\n".join(missing)

    def test_every_sql_exec_question_has_a_reference_fill(self) -> None:
        missing = [q["id"] for q in SQL_EXEC_QUESTIONS if q["id"] not in REFERENCE_FILLS]
        assert missing == [], (
            f"sql_exec questions with no reference fill in sql_exec_reference_fills.json: {missing}"
        )

    def test_every_sql_exec_code_runs_and_matches_correct_answer(self) -> None:
        failures: list[str] = []
        for q in SQL_EXEC_QUESTIONS:
            qid = q["id"]
            fill_entry = REFERENCE_FILLS.get(qid)
            if fill_entry is None:
                continue
            fill = fill_entry["fill"]
            for lang in ("es", "en"):
                code_template = q.get(f"code_{lang}") or ""
                if not code_template:
                    failures.append(f"{qid} [{lang}]: missing code_{lang}")
                    continue
                code = code_template.replace("___", fill, 1)
                output, error = _run_sql(code)
                if error:
                    failures.append(f"{qid} [{lang}]: SQL error: {error}")
                    continue
                expected = (q.get(f"correct_answer_{lang}") or "").strip()
                if output.strip() != expected:
                    failures.append(
                        f"{qid} [{lang}]: output {output!r} != correct_answer_{lang} {expected!r}"
                    )
        assert failures == [], (
            f"{len(failures)} sql_exec question(s) failed verification:\n" + "\n".join(failures)
        )
