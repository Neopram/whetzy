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

import os
import re
import subprocess
import sys
from pathlib import Path

# project_snapshot.py is the single source of truth for project figures (31.0)
from project_snapshot import snapshot

ROOT = Path(__file__).parent.parent
BACKEND = ROOT / "backend"
DOCS_STATE = ROOT / "docs" / "AUTONOMOUS_STATE.md"
CLAUDE_MD = ROOT / "CLAUDE.md"
EVIDENCE_TSX = ROOT / "frontend" / "src" / "lib" / "catalog.ts"

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
# Verdad canónica — single source via project_snapshot (31.0)
# ---------------------------------------------------------------------------

_snap = snapshot()
real_tracks = _snap["tracks"]
real_skills = _snap["skills"]
real_courses = _snap["courses"]
real_questions = _snap["questions"]
real_lessons = _snap["lessons"]
real_terms = _snap["glossary_terms"]
real_migrations = _snap["migrations"]

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
    real_head = _snap["alembic_head"]

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
print("[4] Cifras del catalogo en la web (lib/catalog.ts)")
if not EVIDENCE_TSX.exists():
    check("lib/catalog.ts existe", False, f"no esta en {EVIDENCE_TSX}")
else:
    evidence_text = EVIDENCE_TSX.read_text(encoding="utf-8")
    for const_name, label, real_value in (
        ("CATALOG_TRACKS", "Tracks en la web", real_tracks),
        ("CATALOG_COURSES", "Cursos en la web", real_courses),
        ("CATALOG_QUESTIONS", "Preguntas en la web", real_questions),
    ):
        m = re.search(r"^export const " + const_name + r"\s*=\s*(\d+);", evidence_text, re.MULTILINE)
        if not m:
            check(label, False, "no se encuentra `const " + const_name + " = ...`")
            continue
        shown = int(m.group(1))
        check(
            f"{label}: code={real_value} page={shown}",
            shown == real_value,
            f"off by {real_value - shown}",
        )


print("\n[5] API docs vs OpenAPI spec — check_api_docs.py (20.3)")
try:
    api_check = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "check_api_docs.py")],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        timeout=60,
    )
    for line in api_check.stdout.strip().splitlines():
        print(f"  {line}")
    if api_check.returncode != 0:
        check("API.md ↔ OpenAPI bidirectional check", False, "see lines above")
    else:
        check("API.md ↔ OpenAPI bidirectional check", True, "")
except Exception as e:
    check("API.md ↔ OpenAPI bidirectional check", False, str(e))


print("\n[6] Source licenses (content/sources/index.json + CATALOGO_MAESTRO.md §2.2 — 20.5)")
try:
    src_check = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "check_source_licenses.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    for line in src_check.stdout.strip().splitlines():
        print(f"  {line}")
    if src_check.returncode != 0:
        check("Source licenses (index.json + §2.2 verificar)", False, "see lines above")
    else:
        check("Source licenses (index.json + §2.2 verificar)", True, "")
except Exception as e:
    check("Source licenses (index.json + §2.2 verificar)", False, str(e))

print("\n[7] Legal facts (hechos legales docs/legal/ — 21.0)")
try:
    legal_check = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "check_legal_facts.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    for line in legal_check.stdout.strip().splitlines():
        print(f"  {line}")
    if legal_check.returncode != 0:
        check("Legal facts (afirmaciones + borrador + codificacion + frontmatter + paridad)", False, "see lines above")
    else:
        check("Legal facts (afirmaciones + borrador + codificacion + frontmatter + paridad)", True, "")
except Exception as e:
    check("Legal facts (afirmaciones + borrador + codificacion + frontmatter + paridad)", False, str(e))

print("\n[8] Ledger size guard (20.10)")
_ledger_size = DOCS_STATE.stat().st_size
_MAX_LEDGER = 262144  # 256 KB — diet pending (20.10)
check(
    f"AUTONOMOUS_STATE.md size: {_ledger_size:,} bytes <= {_MAX_LEDGER:,}",
    _ledger_size <= _MAX_LEDGER,
    f"{_ledger_size:,} bytes ({_ledger_size / 1024:.1f} KB)",
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

