#!/usr/bin/env python3
"""instructor_quality_gate.py — puerta de calidad para contenido de instructores (28.2).

Valida un directorio de curso subido por un instructor contra los criterios
automatizables de `docs/MARKETPLACE.md` §3, antes de que el contenido pase a
revision manual (dumps de certificacion e idioma siguen siendo humanos: no hay
forma fiable de detectar "esto es una pregunta copiada literalmente de un
examen" ni "el idioma declarado es el que de verdad se uso" con una regla).

| Criterio                    | Minimo                          | Aqui |
|------------------------------|----------------------------------|------|
| Preguntas por skill           | >= 15                            | si   |
| Preguntas ejecutables         | >= 15% donde el runtime lo permite | si |
| Terminos de glosario          | >= 36 por track                  | si   |
| Lecciones con contenido       | 100% (no esqueleto)              | si   |
| Licencia de la fuente         | reutilizable o "original"        | si   |
| Sin dumps de certificacion    | 0 preguntas copiadas literalmente| manual |
| Idioma                        | consistente con el segmento      | manual |

Estructura de directorio esperada (mismo formato que `content/` en el repo,
para que el mismo loader sirva a ambos):

    <course_dir>/
        questions/**/*.json   # lista, o {"questions": [...]}, mismo shape que
                               # content/questions/. Cada pregunta lleva
                               # "skill_id", "type" y "license".
        lessons/**/*.json     # una leccion por fichero, mismo shape que
                               # content/lessons/. Cada leccion lleva
                               # "body_es", "body_en" y "license".
        glossary/**/*.json    # {"track_id": ..., "terms": [...]}, mismo shape
                               # que content/glossary/.

El campo `license` no existe en el banco interno (ahi la procedencia va en
`source`, texto libre) porque todo el banco interno ya paso por
`check_source_licenses.py` a nivel de indice. El contenido de un instructor no
tiene ese indice, asi que la licencia se declara pregunta a pregunta y leccion
a leccion.

Uso:

    python scripts/instructor_quality_gate.py <course_dir>

Sale con 0 si todo pasa, 1 si algo falla. Sin acceso a red.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

MIN_QUESTIONS_PER_SKILL = 15
EXEC_TARGET = 0.15
MIN_GLOSSARY_TERMS_PER_TRACK = 36

# Mismo conjunto que check_question_bank.py: tipos que el alumno de verdad
# ejecuta, en vez de elegir una opcion.
EXEC_TYPES = {"fill_blank_exec", "fix_bug", "sql_exec", "js_exec"}

VALID_LICENSES = {
    "MIT",
    "Apache-2.0",
    "BSD",
    "CC-BY",
    "CC0",
    "PSF",
    "public-domain",
    "original",
}


def load_json_files(directory: Path) -> list[tuple[Path, Any]]:
    """Carga cada `*.json` bajo `directory`, o [] si no existe."""
    if not directory.is_dir():
        return []
    out = []
    for path in sorted(directory.rglob("*.json")):
        try:
            out.append((path, json.loads(path.read_text(encoding="utf-8"))))
        except json.JSONDecodeError as e:
            out.append((path, e))
    return out


def load_questions(course_dir: Path) -> tuple[list[tuple[Path, dict]], list[str]]:
    """Aplana `questions/**/*.json` a una lista de (fichero, pregunta)."""
    errors: list[str] = []
    items: list[tuple[Path, dict]] = []
    for path, data in load_json_files(course_dir / "questions"):
        if isinstance(data, Exception):
            errors.append(f"{path}: JSON invalido - {data}")
            continue
        # Igual que content/questions/: una lista suelta, o {"questions": [...]}.
        questions = data if isinstance(data, list) else data.get("questions", [])
        for q in questions:
            items.append((path, q))
    return items, errors


def load_lessons(course_dir: Path) -> tuple[list[tuple[Path, dict]], list[str]]:
    errors: list[str] = []
    items: list[tuple[Path, dict]] = []
    for path, data in load_json_files(course_dir / "lessons"):
        if isinstance(data, Exception):
            errors.append(f"{path}: JSON invalido - {data}")
            continue
        # Una leccion por fichero (dict), o varias en una lista.
        lessons = data if isinstance(data, list) else [data]
        for lesson in lessons:
            items.append((path, lesson))
    return items, errors


def load_glossary(course_dir: Path) -> tuple[list[tuple[Path, dict]], list[str]]:
    errors: list[str] = []
    items: list[tuple[Path, dict]] = []
    for path, data in load_json_files(course_dir / "glossary"):
        if isinstance(data, Exception):
            errors.append(f"{path}: JSON invalido - {data}")
            continue
        terms = data.get("terms", []) if isinstance(data, dict) else data
        for term in terms:
            items.append((path, term))
    return items, errors


def check_questions_per_skill(questions: list[tuple[Path, dict]]) -> tuple[list[str], str]:
    errors: list[str] = []
    per_skill: Counter[str] = Counter()
    for _, q in questions:
        skill = q.get("skill_id")
        if not skill:
            continue
        per_skill[skill] += 1

    if not per_skill:
        return (["no se encontro ninguna pregunta con skill_id"], "0 skills")

    for skill in sorted(per_skill):
        n = per_skill[skill]
        if n < MIN_QUESTIONS_PER_SKILL:
            errors.append(
                f"skill {skill}: {n} pregunta(s), el minimo es {MIN_QUESTIONS_PER_SKILL}"
            )
    summary = f"{len(per_skill)} skill(s), {min(per_skill.values())}-{max(per_skill.values())} preguntas/skill"
    return errors, summary


def check_executable_ratio(questions: list[tuple[Path, dict]]) -> tuple[list[str], str]:
    errors: list[str] = []
    total = len(questions)
    if total == 0:
        return (["no hay preguntas que evaluar"], "0 preguntas")

    hits = sum(1 for _, q in questions if q.get("type") in EXEC_TYPES)
    ratio = hits / total
    summary = f"{hits}/{total} = {ratio:.1%}"
    if ratio < EXEC_TARGET:
        errors.append(
            f"solo {ratio:.1%} de las preguntas son ejecutables ({hits}/{total}); "
            f"el minimo es {EXEC_TARGET:.0%} donde el runtime lo permite"
        )
    return errors, summary


def check_glossary(glossary_terms: list[tuple[Path, dict]]) -> tuple[list[str], str]:
    errors: list[str] = []
    per_track: dict[str, int] = defaultdict(int)
    for path, term in glossary_terms:
        # track_id vive en el fichero contenedor si el termino no lo trae.
        track = term.get("track_id") or path.stem
        per_track[track] += 1

    if not per_track:
        return (["no se encontraron terminos de glosario"], "0 tracks")

    for track in sorted(per_track):
        n = per_track[track]
        if n < MIN_GLOSSARY_TERMS_PER_TRACK:
            errors.append(
                f"track {track}: {n} termino(s) de glosario, el minimo es "
                f"{MIN_GLOSSARY_TERMS_PER_TRACK}"
            )
    summary = f"{len(per_track)} track(s), {sum(per_track.values())} termino(s) total"
    return errors, summary


def check_lessons_content(lessons: list[tuple[Path, dict]]) -> tuple[list[str], str]:
    errors: list[str] = []
    if not lessons:
        return (["no se encontro ninguna leccion"], "0 lecciones")

    skeleton = 0
    for path, lesson in lessons:
        lid = lesson.get("id", path.name)
        body_es = (lesson.get("body_es") or "").strip()
        body_en = (lesson.get("body_en") or "").strip()
        if not body_es or not body_en:
            skeleton += 1
            errors.append(f"{path.name} [{lid}]: body_es o body_en vacio - leccion esqueleto")
        elif len(body_es) < 20 or len(body_en) < 20:
            skeleton += 1
            errors.append(
                f"{path.name} [{lid}]: body demasiado corto ({len(body_es)}/{len(body_en)} "
                "caracteres) - probablemente relleno de plantilla"
            )

    summary = f"{len(lessons) - skeleton}/{len(lessons)} con contenido real"
    return errors, summary


def check_licenses(
    questions: list[tuple[Path, dict]], lessons: list[tuple[Path, dict]]
) -> tuple[list[str], str]:
    errors: list[str] = []
    total = 0
    bad = 0
    for label, items in (("pregunta", questions), ("leccion", lessons)):
        for path, item in items:
            total += 1
            item_id = item.get("id", path.name)
            license_ = (item.get("license") or "").strip()
            if not license_:
                bad += 1
                errors.append(f"{path.name} [{item_id}]: falta el campo license")
            elif license_ not in VALID_LICENSES:
                bad += 1
                errors.append(
                    f"{path.name} [{item_id}]: license {license_!r} no reconocida - "
                    f"validas: {sorted(VALID_LICENSES)}"
                )

    if total == 0:
        return (["no hay preguntas ni lecciones que comprobar"], "0 items")
    summary = f"{total - bad}/{total} con licencia valida"
    return errors, summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Puerta de calidad para contenido de instructores (MARKETPLACE.md §3)."
    )
    parser.add_argument("course_dir", type=Path, help="Directorio del curso a validar")
    args = parser.parse_args()

    course_dir: Path = args.course_dir
    if not course_dir.is_dir():
        print(f"[gate] FAIL - {course_dir} no es un directorio")
        return 1

    questions, q_load_errors = load_questions(course_dir)
    lessons, l_load_errors = load_lessons(course_dir)
    glossary_terms, g_load_errors = load_glossary(course_dir)

    load_errors = q_load_errors + l_load_errors + g_load_errors

    checks: list[tuple[str, list[str], str]] = []

    skill_errors, skill_summary = check_questions_per_skill(questions)
    checks.append(("Preguntas por skill (>= 15)", skill_errors, skill_summary))

    exec_errors, exec_summary = check_executable_ratio(questions)
    checks.append(("Preguntas ejecutables (>= 15%)", exec_errors, exec_summary))

    glossary_errors, glossary_summary = check_glossary(glossary_terms)
    checks.append(("Terminos de glosario (>= 36/track)", glossary_errors, glossary_summary))

    lesson_errors, lesson_summary = check_lessons_content(lessons)
    checks.append(("Lecciones con contenido (100%)", lesson_errors, lesson_summary))

    license_errors, license_summary = check_licenses(questions, lessons)
    checks.append(("Licencia de la fuente", license_errors, license_summary))

    print(f"\n[gate] validando {course_dir}\n")

    if load_errors:
        print("  ERROR cargando ficheros:")
        for e in load_errors:
            print(f"    - {e}")
        print()

    all_errors: list[str] = list(load_errors)
    for name, errors, summary in checks:
        mark = "PASS" if not errors else "FAIL"
        print(f"  [{mark}] {name} - {summary}")
        if errors:
            for e in errors[:10]:
                print(f"         - {e}")
            if len(errors) > 10:
                print(f"         ... y {len(errors) - 10} mas")
        all_errors.extend(errors)

    print("\n  Manual (no automatizable aqui):")
    print("  [ - ] Sin dumps de certificacion - revision manual")
    print("  [ - ] Idioma consistente con el segmento declarado - revision manual")

    if all_errors:
        print(f"\n[gate] FAIL - {len(all_errors)} problema(s)\n")
        return 1

    print("\n[gate] PASS - criterios automatizables en verde; queda revision manual "
          "(dumps de certificacion e idioma)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
