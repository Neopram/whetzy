#!/usr/bin/env python3
"""Valida lecciones con las MISMAS funciones que backend/tests/content/test_lessons.py.

Uso: python scripts/content_qa/validate_lessons.py DIR [ORIG_DIR]
Además del test: Python ejecutable solo con la biblioteca estándar (el alumno lo
ejecuta en Pyodide) e id/skill_id iguales al original. Solo cuenta stdout.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

sys.path[:0] = [
    str(Path(__file__).resolve().parents[2] / "backend" / "tests" / "content"),
    str(Path(__file__).resolve().parents[2] / "backend"),
]
import test_lessons as T


def problems(path: Path, orig: Path | None) -> list[str]:
    lesson = json.loads(path.read_text(encoding="utf-8"))
    out: list[str] = []
    if orig and (orig / path.name).exists():
        before = json.loads((orig / path.name).read_text(encoding="utf-8"))
        out += [
            f"{k} cambió" for k in ("id", "skill_id") if lesson.get(k) != before.get(k)
        ]
    out += [
        f"{k} vacío"
        for k in ("title_es", "title_en", "body_es", "body_en")
        if not str(lesson.get(k, "")).strip()
    ]
    for k in ("body_es", "body_en"):
        n = T._word_count(str(lesson.get(k, "")))
        if not T.MIN_BODY_WORDS <= n <= T.MAX_BODY_WORDS:
            out.append(f"{k}: {n} palabras")
    if lesson.get("body_es") == lesson.get("body_en"):
        out.append("ES y EN idénticos")
    if not T.URL_RE.search(str(lesson.get("source", ""))):
        out.append("source sin URL")
    lang = T._language(lesson)
    if lang not in T.EXECUTABLE_LANGUAGES | T.ILLUSTRATIVE_LANGUAGES:
        return [*out, f"language {lang!r} desconocido"]
    runnable = T._is_executable(lesson)
    if runnable and lesson.get("executable", True) is False:
        out.append("ejecutable marcado executable: false")
    if not runnable and lesson.get("executable") is not False:
        out.append('ilustrativo sin "executable": false')
    code = str(lesson.get("example_code", "")).strip()
    expected = str(lesson.get("example_output", "")).rstrip("\n")
    if not code or not expected:
        return [*out, "falta example_code o example_output"]
    if not runnable:
        return out
    if lang == "sql":
        actual = T._run_sql(code).rstrip("\n")
    else:
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            return [*out, f"sintaxis: {exc}"]
        mods = {
            n.name.split(".")[0]
            for x in ast.walk(tree)
            if isinstance(x, ast.Import)
            for n in x.names
        }
        mods |= {
            x.module.split(".")[0]
            for x in ast.walk(tree)
            if isinstance(x, ast.ImportFrom) and x.module
        }
        extra = sorted(m for m in mods if m not in sys.stdlib_module_names)
        if extra:
            out.append(f"importa fuera de la stdlib: {extra}")
        proc = T._run_in_cpython(code)
        if proc.returncode:
            return [
                *out,
                "el ejemplo lanza: " + (proc.stderr.strip().splitlines() or ["?"])[-1],
            ]
        actual = (proc.stdout or "").rstrip("\n")
    if actual != expected:
        out.append(
            f"salida distinta (solo cuenta stdout)\n--- esperada ---\n{expected}\n--- real ---\n{actual}"
        )
    return out


def main(argv: list[str]) -> int:
    folder = Path(argv[0])
    orig = Path(argv[1]) if len(argv) > 1 else None
    fails = 0
    for path in sorted(folder.glob("*.json")):
        for p in problems(path, orig):
            fails += 1
            print(f"FALLO {path.stem}: {p}")
    print("OK" if not fails else f"FALLOS: {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
