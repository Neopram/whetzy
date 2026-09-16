#!/usr/bin/env python3
"""check_docs.py — 17.8: verifica que los documentos coinciden con git HEAD.

Extrae los valores canónicos del código y el contenido, y los compara contra lo
que dicen los docs. Sale con 1 si algún doc miente.

Dos reglas que la primera versión rompía y por las que nunca pudo pasar:

1. **La verdad sale de la fuente canónica, no de los nombres de carpeta.**
   `content/questions/` tiene DOCE directorios pero el producto tiene ONCE
   tracks: `track08_aws_clf_c02` y `track08_aws_cloud_practitioner` son el
   mismo track08 (mismos `skill_id`, `sk0801xx`) repartido en dos carpetas.
   Contar carpetas daba 12 y el checker acusaba al doc de mentir. Los tracks y
   las skills salen de `content/curriculum/tracks.json`, que es lo que carga
   la app.

2. **El lado del doc se lee anclado, no con el primer match del fichero.**
   `AUTONOMOUS_STATE.md` es una narrativa de 60 KB: un `re.search(r"(\\d+)\\s*tracks")`
   suelto encuentra «los 3 tracks nuevos» de una bitácora y lo compara contra
   el banco entero. Los números se leen de la fila `Contenido` de la tabla de
   invariantes (`## 0`), que es donde el ledger promete que están.

Además la salida es ASCII-safe: la consola de Windows es cp1252 y un `✗` la
hacía reventar con UnicodeEncodeError *justo* en la rama de fallo, así que el
checker solo podía terminar bien — cualquier fallo real moría en el print.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
BACKEND = ROOT / "backend"
CONTENT = ROOT / "content"
DOCS_STATE = ROOT / "docs" / "AUTONOMOUS_STATE.md"
CLAUDE_MD = ROOT / "CLAUDE.md"
EVIDENCE_TSX = ROOT / "frontend" / "src" / "pages" / "EvidenceScreen.tsx"

# La consola de Windows no es UTF-8. Reconfigurar es lo que evita que el
# checker muera al imprimir su propio fallo; el fallback ASCII cubre el caso
# de un stream que no se puede reconfigurar (pipes de CI antiguos).
_UNICODE_OK = True
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
except Exception:  # pragma: no cover - depende del entorno
    _UNICODE_OK = False

_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _mark(ok: bool) -> str:
    glyph = ("OK", "FAIL") if not _UNICODE_OK else ("✓", "✗")
    text = glyph[0] if ok else glyph[1]
    if not _COLOR:
        return text
    return f"\033[92m{text}\033[0m" if ok else f"\033[91m{text}\033[0m"


errors: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {_mark(ok)} {label}" + (f" - {detail}" if detail and not ok else ""))
    if not ok:
        errors.append(f"{label}: {detail}" if detail else label)


# ---------------------------------------------------------------------------
# Verdad canónica
# ---------------------------------------------------------------------------

curriculum = json.loads((CONTENT / "curriculum" / "tracks.json").read_text(encoding="utf-8"))
_tracks = curriculum["tracks"] if isinstance(curriculum, dict) else curriculum

real_tracks = len(_tracks)
real_skill_ids: set[str] = set()
for _t in _tracks:
    for _m in _t.get("modules", []):
        for _s in _m.get("skills", []):
            real_skill_ids.add(_s["id"] if isinstance(_s, dict) else _s)
real_skills = len(real_skill_ids)

# Un "curso" es un track x nivel (17.4): `tracks.json` da un `level` por
# modulo, y el catalogo que ve el usuario agrupa por (track, level).
real_courses = sum(
    len({m.get("level") for m in t.get("modules", []) if m.get("level") is not None})
    for t in _tracks
)

real_questions = 0
for qfile in sorted((CONTENT / "questions").rglob("*.json")):
    payload = json.loads(qfile.read_text(encoding="utf-8"))
    items = payload if isinstance(payload, list) else payload.get("questions", [])
    real_questions += len(items)

lesson_skill_ids: set[str] = set()
for lfile in sorted((CONTENT / "lessons").rglob("*.json")):
    lesson = json.loads(lfile.read_text(encoding="utf-8"))
    if lesson.get("skill_id"):
        lesson_skill_ids.add(lesson["skill_id"])
real_lessons = len(lesson_skill_ids)

real_terms = 0
for gfile in sorted((CONTENT / "glossary").rglob("*.json")):
    payload = json.loads(gfile.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        real_terms += len(payload)
    else:
        real_terms += len(payload.get("terms", payload.get("entries", [])))

real_migrations = len(
    [
        p
        for p in (BACKEND / "alembic" / "versions").glob("*.py")
        if re.search(r"^revision(?::\s*str)?\s*=", p.read_text(encoding="utf-8"), re.M)
    ]
)

# ---------------------------------------------------------------------------
# Lado del doc: fila `Contenido` de la tabla de invariantes
# ---------------------------------------------------------------------------

state_text = DOCS_STATE.read_text(encoding="utf-8")
claude_text = CLAUDE_MD.read_text(encoding="utf-8")


def _num(text: str) -> int:
    """`4.512` y `4,512` son el mismo numero escrito en dos idiomas."""
    return int(re.sub(r"[.,\s]", "", text))


def _invariant_row(name: str) -> str:
    m = re.search(rf"^\|\s*{re.escape(name)}\s*\|(.+)$", state_text, re.M)
    return m.group(1) if m else ""


content_row = _invariant_row("Contenido")
alembic_row = _invariant_row("Alembic HEAD")


def _from_row(row: str, pattern: str, label: str) -> int | None:
    m = re.search(pattern, row)
    if not m:
        errors.append(f"{label}: no se encuentra en la fila de invariantes")
        print(f"  {_mark(False)} {label} - ausente de la tabla de invariantes")
        return None
    return _num(m.group(1))


print("\n[1] Alembic")
try:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "heads"],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        timeout=60,
    )
    # Los revision ids de este repo no son hex (`q7r8s9t0u1v2`): el regex
    # `[0-9a-f]{12}` de la version anterior no podia casar ni uno.
    heads = re.findall(r"^([0-9a-z_]{6,})\s*\(head\)", result.stdout, re.M)
    real_head = heads[-1] if heads else "unknown"

    m = re.search(r"HEAD actual:\s*`([0-9a-z_]+)`", claude_text)
    claude_head = m.group(1) if m else "not_found"
    check(
        f"CLAUDE.md Alembic HEAD ({claude_head})",
        real_head != "unknown" and real_head == claude_head,
        f"real={real_head!r} CLAUDE.md={claude_head!r}",
    )

    m = re.search(r"`([0-9a-z_]+)`", alembic_row)
    ledger_head = m.group(1) if m else "not_found"
    check(
        f"Ledger Alembic HEAD ({ledger_head})",
        real_head != "unknown" and real_head == ledger_head,
        f"real={real_head!r} ledger={ledger_head!r}",
    )

    for label, text in (("CLAUDE.md", claude_text), ("Ledger", alembic_row)):
        m = re.search(r"\((\d+)\s*migraciones", text)
        doc_migrations = int(m.group(1)) if m else -1
        check(
            f"{label} migraciones ({doc_migrations})",
            doc_migrations == real_migrations,
            f"real={real_migrations} doc={doc_migrations}",
        )
except Exception as e:  # pragma: no cover - fallo de entorno
    check("Alembic", False, str(e))


print("\n[2] Banco de contenido (fila `Contenido` de los invariantes)")
if not content_row:
    check("Fila `Contenido` en la tabla de invariantes", False, "no encontrada")
else:
    pairs = [
        (r"([\d.,]+)\s*preguntas", "Preguntas", real_questions),
        (r"([\d.,]+)\s*tracks", "Tracks", real_tracks),
        (r"([\d.,]+)\s*skills", "Skills", real_skills),
        (r"([\d.,]+)\s*lecciones", "Lecciones", real_lessons),
        (r"([\d.,]+)\s*t\w+rminos glosario", "Glosario", real_terms),
    ]
    for pattern, label, real in pairs:
        doc = _from_row(content_row, pattern, label)
        if doc is None:
            continue
        check(f"{label}: code={real} doc={doc}", doc == real, f"off by {real - doc}")


print("\n[3] Cobertura de lecciones")
check(
    f"Lecciones cubren las skills: {real_lessons}/{real_skills}",
    real_lessons == real_skills,
    f"faltan {real_skills - real_lessons}",
)


# ---------------------------------------------------------------------------
# [4] La pagina publica de evidencia
#
# `/evidence` existe para publicar numeros reproducibles, y publicaba dos que
# eran falsos: «8 tracks 3 419 Q» cuando el banco ya iba por 11 tracks y 4.724
# preguntas. Nadie lo noto porque estaban escritos a mano dentro de dos
# cadenas y ningun check miraba el frontend. Una pagina de evidencia con
# cifras caducas no es un despiste de marketing: es la linea roja 1 aplicada
# justo en el sitio donde mas se nota.
# ---------------------------------------------------------------------------
print()
print("[4] Pagina publica de evidencia (EvidenceScreen.tsx)")
if not EVIDENCE_TSX.exists():
    check("EvidenceScreen.tsx existe", False, f"no esta en {EVIDENCE_TSX}")
else:
    evidence_text = EVIDENCE_TSX.read_text(encoding="utf-8")
    for const_name, label, real_value in (
        ("CATALOG_TRACKS", "Tracks en /evidence", real_tracks),
        ("CATALOG_COURSES", "Cursos en /evidence", real_courses),
        ("CATALOG_QUESTIONS", "Preguntas en /evidence", real_questions),
    ):
        m = re.search(r"^const " + const_name + r"\s*=\s*(\d+);", evidence_text, re.MULTILINE)
        if not m:
            check(label, False, "no se encuentra `const " + const_name + " = ...`")
            continue
        shown = int(m.group(1))
        check(
            f"{label}: code={real_value} page={shown}",
            shown == real_value,
            f"off by {real_value - shown}",
        )


print()
if errors:
    head = f"{len(errors)} check(s) FAILED:"
    print(f"\033[91m{head}\033[0m" if _COLOR else head)
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    msg = "All checks PASSED"
    print(f"\033[92m{msg}\033[0m" if _COLOR else msg)
