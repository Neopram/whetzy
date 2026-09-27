"""Las herramientas de QA de contenido detectan lo que tienen que detectar (26-09).

Cada una existe por un fallo real de esa noche; ver scripts/content_qa/README.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "content_qa"))

import check_key_drift
import check_only_fields
import validate_lessons

Q = {
    "id": "q1",
    "type": "multiple_choice",
    "question_es": "¿Qué hace git fetch?",
    "question_en": "What does git fetch do?",
    "options_es": [
        "Descarga objetos del remoto sin fusionar",
        "Fusiona la rama remota",
        "Borra ramas locales",
        "Crea un commit",
    ],
    "options_en": [
        "Downloads objects from the remote without merging",
        "Merges the remote branch",
        "Deletes local branches",
        "Creates a commit",
    ],
    "correct_index": 0,
    "explanation_es": "fetch descarga sin fusionar.",
    "explanation_en": "fetch downloads without merging.",
}


def _write(folder: Path, questions: list[dict]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "mod.json").write_text(
        json.dumps({"questions": questions}), encoding="utf-8"
    )


def test_key_drift_sees_a_correct_option_moved_to_another_slot(tmp_path: Path) -> None:
    _write(tmp_path / "base", [Q])
    moved = dict(
        Q, correct_index=1
    )  # el texto correcto sigue en 0, la clave apunta a 1
    _write(tmp_path / "new", [moved])
    assert check_key_drift.drift(tmp_path / "base", tmp_path / "new")
    _write(tmp_path / "same", [Q])
    assert not check_key_drift.drift(tmp_path / "base", tmp_path / "same")


def test_only_fields_flags_a_change_outside_the_allowed_fields(tmp_path: Path) -> None:
    _write(tmp_path / "a", [Q])
    _write(
        tmp_path / "b", [dict(Q, explanation_es="Otra explicación distinta y real.")]
    )
    assert not check_only_fields.problems(
        tmp_path / "a", tmp_path / "b", {"explanation_es", "explanation_en"}
    )
    _write(tmp_path / "c", [dict(Q, correct_index=2)])
    assert check_only_fields.problems(
        tmp_path / "a", tmp_path / "c", {"explanation_es", "explanation_en"}
    )


def test_validate_lessons_accepts_a_real_lesson_and_counts_only_stdout(
    tmp_path: Path,
) -> None:
    real = ROOT / "content" / "lessons" / "track28" / "l280304.json"
    assert validate_lessons.problems(real, None) == []
    lesson = json.loads(real.read_text(encoding="utf-8"))
    lesson["example_code"] = lesson["example_code"].replace(", stream=sys.stdout", "")
    broken = tmp_path / "l280304.json"
    broken.write_text(json.dumps(lesson), encoding="utf-8")
    assert any("salida distinta" in p for p in validate_lessons.problems(broken, None))
