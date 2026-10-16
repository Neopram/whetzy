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
    m = re.search(rf"^\|\s*{re.escape(name)}\s*\|(.+)$", state_text, re.MULTILINE)
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

print("\n[13] Dependabot no propone ningún major (2026-10-02)")
# Dos olas de majors el mismo día con el CI sin runner (H.13): bcrypt 5 tumbó la
# API; typescript 7 dejó a Cloudflare Pages sin publicar; redis 8 tumbó mypy
# --strict. Una lista por nombre no alcanzó: la regla tiene que ser «*» en pip y
# en npm, y los paquetes que ya rompieron tienen que estar bajo ese bloque (si
# un manifiesto cambia de directorio, el bloque deja de cubrirlos sin avisar).
_DEPENDABOT = ROOT / ".github" / "dependabot.yml"
_dep_text = _DEPENDABOT.read_text(encoding="utf-8") if _DEPENDABOT.exists() else ""
_dep_blocks: dict[str, str] = {}
for _blk in re.split(r"\n\s*-\s*package-ecosystem:\s*", _dep_text)[1:]:
    _eco = _blk.split("\n", 1)[0].strip().strip("\"'")
    _dep_blocks[_eco] = _blk
_MUST_COVER = {
    "pip": ("backend/requirements.txt", ("redis", "bcrypt")),
    "npm": ("frontend/package.json", ("typescript", "react-router-dom")),
}
for _eco, (_manifest, _pkgs) in _MUST_COVER.items():
    _blk = _dep_blocks.get(_eco, "")
    _ignores_major = bool(
        re.search(
            r"-\s*dependency-name:\s*[\"']\*[\"']\s*\n\s*update-types:\s*\[[^\]]*version-update:semver-major",
            _blk,
        )
    )
    _dir = re.search(r"directory:\s*[\"']?(/[^\"'\s]*)", _blk)
    _dir_path = ROOT / _dir.group(1).lstrip("/") if _dir else None
    _manifest_path = ROOT / _manifest
    _in_dir = bool(_dir_path) and _manifest_path.parent.resolve() == _dir_path.resolve()
    _manifest_text = _manifest_path.read_text(encoding="utf-8") if _manifest_path.exists() else ""
    _missing = [
        _p for _p in _pkgs if not re.search(rf"(^|[\s\"']){re.escape(_p)}([=\"'\[<>~ ]|$)", _manifest_text, re.MULTILINE)
    ]
    check(
        f"dependabot {_eco}: ignora semver-major de «*» y cubre {', '.join(_pkgs)} ({_manifest})",
        _ignores_major and _in_dir and not _missing,
        f"ignora major de *={_ignores_major} · directorio cubre {_manifest}={_in_dir} · no están en el manifiesto={_missing}",
    )

print("\n[14] Ledger bien formado y `## 1` generada desde las filas (2026-10-02)")
# `ledger.py check` no corria en ninguna puerta: §1 decia «38 = 0/6» con las seis
# filas en DONE. Ahora §1 se genera (`ledger.py fases --write`) y esto exige que cuadre.
try:
    _ledger_check = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "ledger.py"), "check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    _ledger_out = (_ledger_check.stdout + _ledger_check.stderr).strip()
    check("ledger.py check (filas, criterios, §1 generada)", _ledger_check.returncode == 0, _ledger_out[-600:])
except Exception as e:
    check("ledger.py check (filas, criterios, §1 generada)", False, str(e))

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

# ---------------------------------------------------------------------------
# [15]-[23] Oleada 0 del plan ultracode (serie 41, 2026-10-16): una guarda por cada
# contradicción doc ↔ código que el barrido cerró. Cada una se probó mutando el doc.
# ---------------------------------------------------------------------------


def _live_md(skip_files: set[str] = frozenset()) -> list[Path]:
    """Los .md vivos: fuera de archive/, node_modules, corpus y salidas de herramientas."""
    out = []
    for _md in sorted(ROOT.rglob("*.md")):
        _parts = set(_md.relative_to(ROOT).parts)
        if _SKIP_DIRS & _parts or "test-results" in _parts or _md.name in skip_files:
            continue
        out.append(_md)
    return out


def _stale_lines(
    pattern: re.Pattern[str], files: list[Path], allow: re.Pattern[str] = _HISTORY_MARK, around: int = 2
) -> list[str]:
    """Líneas que casan `pattern` sin marca de historia (o de negación) a ±`around` líneas."""
    hits = []
    for _md in files:
        _lines = _md.read_text(encoding="utf-8", errors="replace").splitlines()
        for _i, _ln in enumerate(_lines):
            if pattern.search(_ln) and not allow.search(" ".join(_lines[max(0, _i - around) : _i + around + 1])):
                hits.append(f"{_md.relative_to(ROOT).as_posix()}:{_i + 1}")
    return hits


_DECISIONS_TEXT = (_DOCS / "DECISIONS.md").read_text(encoding="utf-8")
_LIVE = _live_md({"STATUS.md", "CHANGELOG.md", "DECISIONS.md"})

print("\n[15] Toda ADR citada en un doc vivo existe en DECISIONS.md (ADR-61 se citó 4 veces sin existir)")
_adr_heads = set(re.findall(r"^## ADR-(\d+)\b", _DECISIONS_TEXT, re.M))
_adr_ghost = []
for _md in _LIVE:
    for _i, _ln in enumerate(_md.read_text(encoding="utf-8", errors="replace").splitlines()):
        # «ADR-43 (hoy ADR-47)»: número viejo de antes de la renumeración del 2026-09-25, marcado.
        for _n in re.findall(r"\bADR-(\d+)\b(?!\s*\(hoy ADR-)", _ln):
            if _n not in _adr_heads:
                _adr_ghost.append(f"{_md.relative_to(ROOT).as_posix()}:{_i + 1} ADR-{_n}")
check(
    "Cada «ADR-NN» de un doc vivo tiene su cabecera `## ADR-NN` en DECISIONS.md",
    bool(_adr_heads) and not _adr_ghost,
    ", ".join(_adr_ghost[:20]),
)

print("\n[16] Molde de track vigente = ADR-54 (32 × 10), no el viejo 20 skills · 300 Q")
_old_mould = _stale_lines(
    re.compile(r"20\s*skills\s*[·,/y×x]\s*300|300\s*Q\s*(por|/)\s*track", re.I),
    _LIVE,
    re.compile(r"sustitu[ií]d|hist[oó]ric|antigu", re.I),
)
check("Ningún doc vivo da como vigente «20 skills · 300 Q»", not _old_mould, ", ".join(_old_mould[:20]))

print("\n[17] Precio de la certificación = CERT_EXAM_USD (pago único, ADR-49)")
_prices_py = (BACKEND / "app" / "core" / "prices.py").read_text(encoding="utf-8")
_cert = re.search(r'CERT_EXAM_USD\s*=\s*Decimal\("([\d.]+)"\)', _prices_py)
_cert_es = _cert.group(1).replace(".", ",") if _cert else "?"
# ECONOMIA.md no da precio a la certificación; si algún día lo da, tiene que ser este.
_eco_prices = re.findall(r"certificaci[oó]n[^|\n]{0,60}?(\d+[.,]\d\d)\s*\$", (_DOCS / "ECONOMIA.md").read_text(encoding="utf-8"), re.I)
check(
    f"Si ECONOMIA.md da precio a la certificación, es {_cert_es} $ (prices.py)",
    bool(_cert) and all(p.replace(".", ",") == _cert_es for p in _eco_prices),
    ", ".join(_eco_prices),
)
_cert49 = _stale_lines(
    re.compile(r"\$\s*49\s*/\s*(año|year)|49\s*\$\s*/\s*año|49\s*USD\s*/\s*año|Certs?\b.{0,40}\$\s*49\b", re.I), _LIVE
)
check("Ningún doc vivo vende la certificación a «$49/año»", not _cert49, ", ".join(_cert49[:20]))

print("\n[18] Qué elige la pregunta: skill por 1,1 − dominio y Elo, no un bandit")
_bandit = re.compile(r"bandit\w*.{0,60}\b(decide|elige|escoge|selecciona|selects?|picks?|chooses?)\b|\b(decide|elige)\b.{0,40}bandit", re.I)
_bandit_hits = _stale_lines(_bandit, [ROOT / "README.md", _DOCS / "ORCHESTRATOR.md"])
check("README.md y ORCHESTRATOR.md no dicen que un bandit decide la pregunta", not _bandit_hits, ", ".join(_bandit_hits))
_placement_py = (BACKEND / "app" / "services" / "engine" / "placement.py").read_text(encoding="utf-8")
_thompson_docs = [m.relative_to(ROOT).as_posix() for m in _LIVE if "Thompson" in m.read_text(encoding="utf-8", errors="replace")]
check(
    "Si un doc vivo cita Thompson, existe en engine/placement.py (gammavariate)",
    not _thompson_docs or "gammavariate" in _placement_py,
    "citan Thompson: " + ", ".join(_thompson_docs[:10]),
)

print("\n[19] Los créditos no compran cursos, simulacros ni bootcamps (ADR-58)")
_credit_buys = re.compile(r"cr[eé]ditos?\b.{0,60}\b(cursos?|simulacros?|bootcamps?)\b|\b(cursos?|simulacros?|bootcamps?)\b.{0,40}\bcon\s+cr[eé]ditos", re.I)
_credit_ok = re.compile(r"\bno\b|\bnunca\b|\bni\b|ADR-58|sustitu[ií]d|hist[oó]ric", re.I)
_credit_hits = _stale_lines(_credit_buys, [_DOCS / "MARKETPLACE.md", _DOCS / "DISTRIBUCION.md"], _credit_ok, around=0)
check("MARKETPLACE.md y DISTRIBUCION.md no dicen que los créditos pagan cursos/simulacros/bootcamps", not _credit_hits, ", ".join(_credit_hits))

print("\n[20] Duelos: asíncronos, estados pending | in_progress | completed (models/duel.py)")
_duel_py = (BACKEND / "app" / "models" / "duel.py").read_text(encoding="utf-8")
check("models/duel.py sigue con pending | in_progress | completed", '"pending" | "in_progress" | "completed"' in _duel_py)
_duel_live = _stale_lines(re.compile(r"duel(?:o|os|s)?\s+en\s+(vivo|directo|tiempo\s+real)|\blive\s+duels?\b|pending\s*[/|,]\s*active", re.I), _LIVE)
check("Ningún doc vivo dice «duelos en vivo» ni el estado `active`", not _duel_live, ", ".join(_duel_live[:20]))

print("\n[21] STATUS.md y CHANGELOG.md llegan, al menos, a la última ADR")
_adr_dates = re.findall(r"^## ADR-\d+\b.*?(20\d\d-\d\d-\d\d)", _DECISIONS_TEXT, re.M)
_last_adr = max(_adr_dates) if _adr_dates else ""
_status_dates = re.findall(r"^## (20\d\d-\d\d-\d\d)", (_DOCS / "STATUS.md").read_text(encoding="utf-8"), re.M)
_changelog_dates = re.findall(r"^## \[[^\]]+\] — (20\d\d-\d\d-\d\d)", (_DOCS / "CHANGELOG.md").read_text(encoding="utf-8"), re.M)
check(
    f"Última entrada de STATUS.md ≥ última ADR ({_last_adr})",
    bool(_status_dates) and max(_status_dates) >= _last_adr,
    f"STATUS {max(_status_dates) if _status_dates else '?'}",
)
check(
    f"Última entrada de CHANGELOG.md ≥ última ADR ({_last_adr})",
    bool(_changelog_dates) and max(_changelog_dates) >= _last_adr,
    f"CHANGELOG {max(_changelog_dates) if _changelog_dates else '?'}",
)

print("\n[22] INVENTARIO_DOCS.md: el resumen cuadra con sus filas y todo .md vivo tiene fila")
_inv_rows = re.findall(r"^\| `([^`]+)` \| ([a-záéíóú\-]+) \|", _inv_text, re.M)
_inv_counts: dict[str, int] = {}
for _path, _cls in _inv_rows:
    _inv_counts[_cls] = _inv_counts.get(_cls, 0) + 1
_summary = dict(re.findall(r"^\| ([a-záéíóú\-]+) \| (\d+) \|", _inv_text, re.M))
_mismatch = [f"{c}: resumen {_summary.get(c)} ≠ filas {n}" for c, n in sorted(_inv_counts.items()) if str(n) != _summary.get(c)]
_total = re.search(r"^\| \*\*Total\*\* \| \*\*(\d+)\*\* \|", _inv_text, re.M)
if not _total or int(_total.group(1)) != len(_inv_rows):
    _mismatch.append(f"Total: resumen {_total.group(1) if _total else '?'} ≠ filas {len(_inv_rows)}")
check("El resumen de INVENTARIO_DOCS.md cuadra con sus filas", not _mismatch, "; ".join(_mismatch))
_inv_paths = {p for p, _ in _inv_rows}
_tracked = subprocess.run(["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True, text=True).stdout.split()
_no_row = [
    f for f in _tracked
    if not f.startswith("docs/archive/") and "node_modules" not in f and "test-results" not in f and not f.startswith("corpus/")
    and f not in _inv_paths
]
check("Todo .md vivo del repo tiene fila en INVENTARIO_DOCS.md", bool(_tracked) and not _no_row, "sin fila: " + ", ".join(_no_row[:20]))

print("\n[23] Toda fila DONE del ledger dice dónde está su evidencia")
sys.path.insert(0, str(Path(__file__).parent))
import ledger as _ledger_mod  # noqa: E402

_done_bare = [
    t.id
    for t in _ledger_mod.parse().tasks
    if t.state == "DONE" and not re.search(r"`[0-9a-f]{7,40}`|→\s*(§|STATUS)|#\d+|DONE\s+—", t.criterion + " " + t.state_raw)
]
check("Cada fila DONE cita un hash, un PR o un puntero «→ §»", not _done_bare, f"{len(_done_bare)} sin evidencia: " + ", ".join(_done_bare[:30]))

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

