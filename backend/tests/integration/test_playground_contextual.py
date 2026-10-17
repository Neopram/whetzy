"""43.7 (ADR-65 D9): la lección sabe en qué runtime se puede probar su ejemplo.

El playground ejecuta Python, SQL y JS. El JSON de las lecciones trae
`language` en 512 de 730 y el loader no lo guardaba; las 218 sin etiqueta son
Python (las 218 pasan `ast.parse`, medido el 2026-10-17). Shell, YAML, HTTP,
Dockerfile y texto no se pueden ejecutar aquí: sin runtime, sin botón.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.models.content import Lesson, Module, Skill, Track
from app.services.content_loader import _upsert_lesson, lesson_code_runtime

LESSONS = Path(__file__).resolve().parents[3] / "content" / "lessons"


@pytest.mark.parametrize(
    ("language", "code", "runtime"),
    [
        ("python", "print(1)", "python"),
        ("sql", "SELECT 1;", "sql"),
        ("javascript", "console.log(1)", "js"),
        ("shell", "ls -la", None),
        ("yaml", "a: 1", None),
        (None, "x = 1\nprint(x)", "python"),
        (None, "SELECT * FROM t WHERE", None),  # sin etiqueta y no es Python
        ("python", None, None),  # sin ejemplo
    ],
)
def test_runtime_del_ejemplo(language, code, runtime):
    data = {"example_code": code}
    if language is not None:
        data["language"] = language
    assert lesson_code_runtime(data) == runtime


def test_el_catalogo_real_tiene_runtime_en_las_de_python_sql_y_js():
    counts: dict[str | None, int] = {}
    for f in LESSONS.rglob("*.json"):
        raw = json.loads(f.read_text(encoding="utf-8"))
        items = raw if isinstance(raw, list) else raw.get("lessons", [raw])
        for lesson in items:
            if isinstance(lesson, dict) and "example_code" in lesson:
                rt = lesson_code_runtime(lesson)
                counts[rt] = counts.get(rt, 0) + 1
    assert sum(counts.values()) == 730
    # 330 + 218 Python, 32 SQL, 28 JS; el resto (122) no se ejecuta en el navegador.
    assert counts == {"python": 548, "sql": 32, "js": 28, None: 122}


async def test_el_loader_guarda_el_runtime_y_la_api_lo_devuelve(client, db_session):
    db_session.add(
        Track(id="t_pg", name_es="T", name_en="T", order=98, icon="x", color="#000", total_questions=0)
    )
    db_session.add(
        Module(id="t_pg_m1", track_id="t_pg", name_es="M", name_en="M", order=1,
               description_es="", description_en="")
    )
    db_session.add(Skill(id="t_pg_s1", module_id="t_pg_m1", name_es="S", name_en="S", order=1))
    await db_session.flush()
    base = {"skill_id": "t_pg_s1", "title_es": "L", "title_en": "L", "body_es": "b",
            "body_en": "b", "source": "test"}
    await _upsert_lesson(db_session, {**base, "id": "l_sql", "example_code": "SELECT 1;",
                                      "language": "sql", "order": 1})
    await _upsert_lesson(db_session, {**base, "id": "l_sh", "example_code": "ls",
                                      "language": "shell", "order": 2})
    await db_session.commit()
    assert (await db_session.get(Lesson, "l_sql")).code_runtime == "sql"

    r = await client.get("/api/v1/lessons/t_pg_s1")
    assert r.status_code == 200, r.text
    by_id = {lesson["id"]: lesson["code_runtime"] for lesson in r.json()}
    assert by_id == {"l_sql": "sql", "l_sh": None}
