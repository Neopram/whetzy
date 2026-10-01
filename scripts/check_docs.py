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
    # RUNBOOK también da la cifra («Current Alembic HEAD: `x` (N migrations»), y
    # sin guarda se quedó en `t0u1v2w3x4y5` / 20 desde el 2026-09-18 hasta el
    # 2026-10-01 con 46 reales.
    runbook_text = (DOCS_STATE.parent / "RUNBOOK.md").read_text(encoding="utf-8")
    m = re.search(r"Current Alembic HEAD:\s*`([0-9a-z_]+)`\s*\((\d+)\s*migrations", runbook_text)
    rb_head, rb_n = (m.group(1), int(m.group(2))) if m else ("not_found", -1)
    check(
        f"RUNBOOK Alembic HEAD ({rb_head}, {rb_n} migraciones)",
        real_head == rb_head and rb_n == real_migrations,
        f"real={real_head!r}/{real_migrations} RUNBOOK={rb_head!r}/{rb_n}",
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


print("\n[5a] ARCHITECTURE.md figures (31.0)")
ARCH_MD = ROOT / "docs" / "ARCHITECTURE.md"
if ARCH_MD.exists():
    arch_text = ARCH_MD.read_text(encoding="utf-8")
    arch_pairs = [
        (r"(\d[\d.,]*)\s*questions", "ARCHITECTURE questions", real_questions),
        (r"(\d[\d.,]*)\s*tracks", "ARCHITECTURE tracks", real_tracks),
        (r"(\d[\d.,]*)\s*skills", "ARCHITECTURE skills", real_skills),
        (r"(\d[\d.,]*)\s*lessons", "ARCHITECTURE lessons", real_lessons),
        (r"(\d[\d.,]*)\s*glossary terms", "ARCHITECTURE glossary", real_terms),
    ]
    for pattern, label, real in arch_pairs:
        m = re.search(pattern, arch_text)
        if m:
            doc_val = _num(m.group(1))
            check(f"{label}: code={real} doc={doc_val}", doc_val == real, f"off by {real - doc_val}")
        else:
            check(label, False, "not found in ARCHITECTURE.md")
else:
    check("ARCHITECTURE.md exists", False, "file not found")


print("\n[5b] CATALOGO_MAESTRO.md figures (31.0)")
CATALOG_MD = ROOT / "docs" / "CATALOGO_MAESTRO.md"
if CATALOG_MD.exists():
    cat_text = CATALOG_MD.read_text(encoding="utf-8")
    cat_pairs = [
        (r"Tracks\s*\|\s*\*\*(\d[\d.,]*)\*\*", "CATALOGO tracks", real_tracks),
        (r"Skills\s*\|\s*\*\*(\d[\d.,]*)\*\*", "CATALOGO skills", real_skills),
        (r"Preguntas\s*\|\s*\*\*(\d[\d.,]*)\*\*", "CATALOGO questions", real_questions),
        (r"Glosario\s*\|\s*\*\*(\d[\d.,]*)\*\*", "CATALOGO glossary", real_terms),
    ]
    for pattern, label, real in cat_pairs:
        m = re.search(pattern, cat_text)
        if m:
            doc_val = _num(m.group(1))
            check(f"{label}: code={real} doc={doc_val}", doc_val == real, f"off by {real - doc_val}")
        else:
            check(label, False, "not found in CATALOGO_MAESTRO.md §1")
else:
    check("CATALOGO_MAESTRO.md exists", False, "file not found")


print("\n[5c] API docs vs OpenAPI spec — check_api_docs.py (20.3)")
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
_MAX_LEDGER = 61440  # 60 KB — enforced by 20.10 diet
check(
    f"AUTONOMOUS_STATE.md size: {_ledger_size:,} bytes <= {_MAX_LEDGER:,}",
    _ledger_size <= _MAX_LEDGER,
    f"{_ledger_size:,} bytes ({_ledger_size / 1024:.1f} KB)",
)

print("\n[9] ECONOMIA <> credits.json (29.2)")
import json as _json

_credits_path = ROOT / "content" / "economy" / "credits.json"
_economia_path = ROOT / "docs" / "ECONOMIA.md"
if _credits_path.exists() and _economia_path.exists():
    _cj = _json.loads(_credits_path.read_text(encoding="utf-8"))
    _eco_text = _economia_path.read_text(encoding="utf-8")
    _cj_val = _cj.get("credit_value_usd")
    _cj_cap = _cj.get("monthly_cap_learning")
    _cj_exp = _cj.get("expiration_days")
    _cj_ref = _cj.get("monthly_cap_referrals")

    _eco_val_m = re.search(r"1\s*cr[eé]dito\s*[≈~]\s*\$?([\d.,]+)", _eco_text)
    _eco_val = float(_eco_val_m.group(1).replace(",", ".")) if _eco_val_m else None
    check(
        f"credit_value_usd: credits.json={_cj_val} == ECONOMIA.md={_eco_val}",
        _eco_val is not None and float(_cj_val) == _eco_val,
        f"credits.json={_cj_val}, ECONOMIA.md={_eco_val}",
    )

    _eco_cap_m = re.search(r"([\d.]+)\s*cr[eé]ditos?/mes", _eco_text)
    _eco_cap = int(_eco_cap_m.group(1).replace(".", "")) if _eco_cap_m else None
    check(
        f"monthly_cap_learning: credits.json={_cj_cap} == ECONOMIA.md={_eco_cap}",
        _eco_cap is not None and int(_cj_cap) == _eco_cap,
        f"credits.json={_cj_cap}, ECONOMIA.md={_eco_cap}",
    )

    _eco_exp_m = re.search(r"(\d+)\s*d[ií]as", _eco_text[_eco_text.find("Caducidad"):] if "Caducidad" in _eco_text else "")
    _eco_exp = int(_eco_exp_m.group(1)) if _eco_exp_m else None
    check(
        f"expiration_days: credits.json={_cj_exp} == ECONOMIA.md={_eco_exp}",
        _eco_exp is not None and int(_cj_exp) == _eco_exp,
        f"credits.json={_cj_exp}, ECONOMIA.md={_eco_exp}",
    )

    _eco_ref_m = re.search(r"(\d+)\s*activaciones?/mes", _eco_text)
    _eco_ref = int(_eco_ref_m.group(1)) if _eco_ref_m else None
    check(
        f"monthly_cap_referrals: credits.json={_cj_ref} == ECONOMIA.md={_eco_ref}",
        _eco_ref is not None and int(_cj_ref) == _eco_ref,
        f"credits.json={_cj_ref}, ECONOMIA.md={_eco_ref}",
    )
else:
    check("ECONOMIA.md or credits.json exists", False, "file(s) missing")

print("\n[10] Plan vigente del catálogo = ADR-54 (2026-10-01)")
# ADR-54 sustituyó el suelo y el ideal de ADR-53 (50 skills · 800 preguntas por track,
# «ideal por temario», banco reservado de 6 × el examen), que a su vez había sustituido
# la meta de volumen de ADR-46 («≥ 50 cursos por track», 200 skills y 3.000 preguntas
# por track, 126.000 en total, 42 tracks fijos). Un documento vivo puede nombrar esas
# cifras solo para decir que son historia: la línea, o sus dos vecinas por cada lado,
# tienen que decir «sustituid…» o «históric…». Nombrar ADR-53 ya no basta: hasta el
# 2026-10-01 la marca aceptaba cualquier línea con «ADR-53» y blanqueaba cifras vigentes.
# DECISIONS.md (las ADR no se reescriben), STATUS.md y CHANGELOG.md (registros por fecha)
# y archive/ (no manda) quedan fuera.
_STALE_PLAN = re.compile(
    r"≥\s*50\s*cursos|50\s*cursos\s*(por|/)\s*track|126[.,]000|200\s*skills|"
    r"3[.,]000\s*(Q\b|preguntas)|2[.,]7\d\d\s*cursos|42\s*tracks|≥\s*400\s*términos|400\s*términos\s*por|"
    r"50\s*skills\s*[·,/y]\s*800|800\s*(Q|preguntas)\s*(por|/)\s*track|ideal\s+por\s+temario|"
    r"6\s*[×x]\s*(la\s+longitud|el\s+examen|examen|la\s+duración)",
    re.IGNORECASE,
)
_HISTORY_MARK = re.compile(r"sustitu[ií]d|hist[oó]ric", re.IGNORECASE)
_SKIP_DIRS = {"node_modules", ".git", "archive", "corpus", "dist", ".ci-local"}
_SKIP_FILES = {"STATUS.md", "CHANGELOG.md", "DECISIONS.md"}
_stale: list[str] = []
for _md in sorted(ROOT.rglob("*.md")):
    if _SKIP_DIRS & set(_md.relative_to(ROOT).parts) or _md.name in _SKIP_FILES:
        continue
    _lines = _md.read_text(encoding="utf-8", errors="replace").splitlines()
    for _i, _ln in enumerate(_lines):
        if not _STALE_PLAN.search(_ln):
            continue
        _window = " ".join(_lines[max(0, _i - 2) : _i + 3])
        if not _HISTORY_MARK.search(_window):
            _stale.append(f"{_md.relative_to(ROOT).as_posix()}:{_i + 1}")
check(
    "Ningún doc vivo da como vigente el suelo/ideal de ADR-53 ni la meta de ADR-46",
    not _stale,
    f"{len(_stale)} línea(s) sin «sustituid…»/«históric…» cerca: " + ", ".join(_stale[:40]),
)

print("\n[11] Pausa de sesiones autónomas (31.7, 2026-09-30; levantada el 2026-10-01, ADR-56)")
_CIERRE_MD = ROOT / "docs" / "CIERRE_2026-09-30.md"
_CIERRE_TEXT = _CIERRE_MD.read_text(encoding="utf-8") if _CIERRE_MD.exists() else ""
if "Estado: pausa levantada" in _CIERRE_TEXT:
    # Levantada la pausa, ningún doc que lee una sesión al arrancar puede seguir
    # mandándola parar: era justo lo que hacía CLAUDE.md con sesiones activas.
    for _doc_path, _doc_label in (
        (CLAUDE_MD, "CLAUDE.md"),
        (ROOT / "docs" / "ORCHESTRATOR.md", "docs/ORCHESTRATOR.md"),
        (ROOT / "docs" / "README.md", "docs/README.md"),
    ):
        _doc_text = _doc_path.read_text(encoding="utf-8") if _doc_path.exists() else ""
        _stale = [m for m in ("PAUSA desde", "Proyecto en PAUSA", "informa del estado y para") if m in _doc_text]
        check(
            f"{_doc_label} ya no manda parar (pausa levantada, ADR-56)",
            not _stale,
            "sigue diciendo: " + ", ".join(_stale),
        )
elif "Estado: PAUSA" in _CIERRE_TEXT:
    for _doc_path, _doc_label in (
        (CLAUDE_MD, "CLAUDE.md"),
        (ROOT / "docs" / "ORCHESTRATOR.md", "docs/ORCHESTRATOR.md"),
    ):
        _doc_text = _doc_path.read_text(encoding="utf-8") if _doc_path.exists() else ""
        _has_pausa = "PAUSA" in _doc_text
        _cites_cierre = "CIERRE_2026-09-30.md" in _doc_text
        check(
            f"{_doc_label} avisa de la PAUSA y cita CIERRE_2026-09-30.md",
            _has_pausa and _cites_cierre,
            f"PAUSA={_has_pausa} cita={_cites_cierre}",
        )

print("\n[12] Índice de documentos completo y sin enlaces rotos (paso 6, 2026-10-01)")
# Todo .md de docs/ fuera de archive/ está en docs/README.md o en docs/INVENTARIO_DOCS.md
# (que lista cada documento con su clase): un doc que nadie indexa acaba diciendo cosas
# viejas sin que nadie lo vea. Y ningún enlace markdown relativo de un .md fuera de
# archive/ apunta a un fichero que no existe.
_DOCS = ROOT / "docs"
_index_text = (_DOCS / "README.md").read_text(encoding="utf-8") if (_DOCS / "README.md").exists() else ""
_inv_text = (
    (_DOCS / "INVENTARIO_DOCS.md").read_text(encoding="utf-8") if (_DOCS / "INVENTARIO_DOCS.md").exists() else ""
)
_unindexed = []
for _md in sorted(_DOCS.rglob("*.md")):
    _rel = _md.relative_to(_DOCS).as_posix()
    if _rel.startswith("archive/") or _rel in {"README.md", "INVENTARIO_DOCS.md"}:
        continue
    if _rel not in _index_text and f"docs/{_rel}" not in _inv_text:
        _unindexed.append(f"docs/{_rel}")
check(
    "Todo .md de docs/ (fuera de archive/) está en docs/README.md o en docs/INVENTARIO_DOCS.md",
    not _unindexed,
    "sin indexar: " + ", ".join(_unindexed[:20]),
)
_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
_broken_links = []
for _md in sorted(ROOT.rglob("*.md")):
    if _SKIP_DIRS & set(_md.relative_to(ROOT).parts):
        continue
    for _m in _LINK.finditer(_md.read_text(encoding="utf-8", errors="replace")):
        _target = _m.group(1).split("#")[0]
        if not _target or re.match(r"^[a-z][a-z0-9+.-]*:", _target) or _target.startswith("/"):
            continue
        if not (_md.parent / _target).exists():
            _broken_links.append(f"{_md.relative_to(ROOT).as_posix()} → {_m.group(1)}")
check(
    "Ningún enlace markdown relativo roto fuera de archive/",
    not _broken_links,
    ", ".join(_broken_links[:20]),
)

# ---------------------------------------------------------------------------
# docs/MAPA_PRODUCTO.md nombra todo lo que existe (2026-10-01): hasta entonces
# ningún documento enumeraba todas las pantallas, y cada una nueva entraba sin
# que nadie escribiera dónde se especifica.
# ---------------------------------------------------------------------------

_MAPA = _DOCS / "MAPA_PRODUCTO.md"
_mapa_text = _MAPA.read_text(encoding="utf-8") if _MAPA.exists() else ""
_FRONT = ROOT / "frontend" / "src"
_app_tsx = (_FRONT / "App.tsx").read_text(encoding="utf-8")
_store_tsx = (_FRONT / "stores" / "useAppStore.ts").read_text(encoding="utf-8")

_pages = sorted(p.stem for p in (_FRONT / "pages").glob("*.tsx"))
_routes = sorted(
    set(re.findall(r"path(?: === |\.startsWith\()'(/[^']*)'", _app_tsx))
    | set(re.findall(r"_PATH = '(/[^']*)'", _app_tsx))
)
_screen_union = re.search(r"type Screen = ([^;]+);", _store_tsx)
_screens = re.findall(r"'([a-z]+)'", _screen_union.group(1)) if _screen_union else []

_missing_map = (
    [p for p in _pages if p not in _mapa_text]
    + [r for r in _routes if f"`{r}" not in _mapa_text]
    + [f"Screen '{s}'" for s in _screens if f"`{s}`" not in _mapa_text]
)
check(
    "docs/MAPA_PRODUCTO.md nombra cada pantalla de frontend/src/pages, cada ruta de App.tsx y cada Screen",
    bool(_mapa_text) and bool(_pages) and bool(_routes) and bool(_screens) and not _missing_map,
    "sin mapear: " + ", ".join(_missing_map[:20]) if _missing_map else "no se pudo leer el mapa o el código",
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

