#!/usr/bin/env python3
"""check_legal_facts.py — 21.0: verifica hechos legales en documentos legales.

Comprueba que los 14 documentos legales (7 ficheros x 2 idiomas) no contienen
afirmaciones falsas, defectos de codificación o inconsistencias que violarían
los ADRs o resolverían issues abiertas de revisión.

Variable de entorno: WHETZY_LEGAL_DIR (default: docs/legal)
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
LEGAL_DIR = Path(os.environ.get("WHETZY_LEGAL_DIR", "docs/legal"))
if not LEGAL_DIR.is_absolute():
    LEGAL_DIR = ROOT / LEGAL_DIR

# Windows: reconfigurar stdout a UTF-8 para que los fallos se impriman bien
_UNICODE_OK = True
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
except Exception:
    _UNICODE_OK = False

_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _mark(ok: bool) -> str:
    glyph = ("OK", "FAIL") if not _UNICODE_OK else ("OK", "X")
    text = glyph[0] if ok else glyph[1]
    if not _COLOR:
        return text
    return f"\033[92m{text}\033[0m" if ok else f"\033[91m{text}\033[0m"


errors: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {_mark(ok)} {label}" + (f" - {detail}" if detail and not ok else ""))
    if not ok:
        errors.append(f"{label}: {detail}" if detail else label)


# Ficheros esperados: 7 documentos x 2 idiomas
EXPECTED_DOCS = [
    "ai-notice",
    "cookie-policy",
    "dpa",
    "ip-disclaimers",
    "privacy-policy",
    "refund-policy",
    "terms-of-service",
]

LANGS = ["es", "en"]

# Afirmaciones prohibidas (case-insensitive) con sus motivos
PROHIBITED = {
    "whetzy inc": "sociedad inexistente",
    "marca registrada": "marcado falso de marca",
    "registered trademark": "marcado falso de marca",
    "google analytics": "rastreador prohibido por linea roja 5",
    "lemon squeezy": "procesador que no existe en el codigo",
    "paddle": "procesador que no existe en el codigo",
    "revenuecat": "procesador que no existe en el codigo",
}

print()
print("[1] Afirmaciones prohibidas")
prohibited_ok = True
for doc_name in EXPECTED_DOCS:
    for lang in LANGS:
        fpath = LEGAL_DIR / f"{doc_name}.{lang}.md"
        if not fpath.exists():
            continue
        try:
            content = fpath.read_text(encoding="utf-8")
            content_lower = content.lower()
            for phrase, reason in PROHIBITED.items():
                if phrase in content_lower:
                    check(
                        f"{doc_name}.{lang}.md contiene {phrase!r}",
                        False,
                        reason,
                    )
                    prohibited_ok = False
        except Exception as e:
            check(f"{doc_name}.{lang}.md lectura", False, str(e))
            prohibited_ok = False

if prohibited_ok:
    check("Afirmaciones prohibidas", True)

print()
print("[2] Cabecera de borrador/draft")
draft_ok = True
for doc_name in EXPECTED_DOCS:
    for lang in LANGS:
        fpath = LEGAL_DIR / f"{doc_name}.{lang}.md"
        if not fpath.exists():
            continue
        try:
            content = fpath.read_text(encoding="utf-8")
            if lang == "es":
                has_draft = "BORRADOR" in content
                detail = "falta BORRADOR" if not has_draft else ""
            else:  # en
                has_draft = "DRAFT" in content
                detail = "falta DRAFT" if not has_draft else ""

            if not has_draft:
                check(f"{doc_name}.{lang}.md cabecera", False, detail)
                draft_ok = False
        except Exception as e:
            check(f"{doc_name}.{lang}.md lectura", False, str(e))
            draft_ok = False

if draft_ok:
    check("Cabecera de borrador/draft", True)

print()
print("[3] Doble codificacion (UTF-8 leido como latin-1)")
encoding_ok = True
for doc_name in EXPECTED_DOCS:
    for lang in LANGS:
        fpath = LEGAL_DIR / f"{doc_name}.{lang}.md"
        if not fpath.exists():
            continue
        try:
            content = fpath.read_text(encoding="utf-8")
            if "Ã" in content or "Â" in content:
                check(
                    f"{doc_name}.{lang}.md codificacion",
                    False,
                    "contiene Ã o Â (UTF-8 leido como latin-1)",
                )
                encoding_ok = False
        except Exception as e:
            check(f"{doc_name}.{lang}.md lectura", False, str(e))
            encoding_ok = False

if encoding_ok:
    check("Doble codificacion", True)

print()
print("[4] Idioma del frontmatter")
frontmatter_ok = True
for doc_name in EXPECTED_DOCS:
    for lang in LANGS:
        fpath = LEGAL_DIR / f"{doc_name}.{lang}.md"
        if not fpath.exists():
            continue
        try:
            content = fpath.read_text(encoding="utf-8")
            # Extraer frontmatter (entre --- ... ---)
            fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if not fm_match:
                continue
            frontmatter = fm_match.group(1)
            # Buscar la línea status:
            status_match = re.search(r"^\s*status:\s*(.+)$", frontmatter, re.MULTILINE)
            if not status_match:
                continue
            status_value = status_match.group(1).strip()

            if lang == "es":
                # .es.md: status NO puede estar en inglés
                if (
                    "Requires" in status_value
                    or "Requires legal review" in status_value
                    or status_value.startswith("DRAFT")
                ):
                    check(
                        f"{doc_name}.es.md frontmatter",
                        False,
                        f"status en ingles: {status_value!r}",
                    )
                    frontmatter_ok = False
            else:  # en
                # .en.md: status NO puede estar en español (BORRADOR, etc.)
                if "BORRADOR" in status_value or "borrador" in status_value.lower():
                    check(
                        f"{doc_name}.en.md frontmatter",
                        False,
                        f"status en espanol: {status_value!r}",
                    )
                    frontmatter_ok = False
        except Exception as e:
            check(f"{doc_name}.{lang}.md lectura", False, str(e))
            frontmatter_ok = False

if frontmatter_ok:
    check("Idioma del frontmatter", True)

print()
print("[5] Paridad (14 ficheros: 7 docs x 2 idiomas)")
expected_files = {f"{doc}.{lang}.md" for doc in EXPECTED_DOCS for lang in LANGS}
actual_files = {f.name for f in LEGAL_DIR.glob("*.md")}

missing = sorted(expected_files - actual_files)
extra = sorted(actual_files - expected_files)

# Los "extra" NO son un fallo: docs/legal/ guarda tambien investigacion
# (README.md, privacy-matrix.md, ai-act-dsa-eaa.md, trademark-search.md,
# h21-decision.md). Solo faltar un documento de cara al usuario es fallo.
for fname in missing:
    check("Paridad", False, f"falta {fname}")
if not missing:
    check("Paridad (14 ficheros: 7 docs x 2 idiomas)", True)
if extra:
    print(f"  --   {len(extra)} fichero(s) adicional(es), no son de cara al usuario: "
          + ", ".join(extra))

print()
print("[6] Ninguna decision del dueno firmada por un agente (21.0)")
# El commit 5f7bd7b escribio "H.21 RESOLVED ... Authorized by autonomous agent"
# y "FINAL & BINDING" en docs/legal/h21-decision.md. Un agente no cierra un
# HUMAN-BLOCKED: si vuelve a aparecer, esta guardia lo para. Se aplica a TODO
# docs/legal, no solo a los 14 de cara al usuario.
SELF_AUTHORIZED = {
    "authorized by autonomous agent": "un agente no puede autorizar una decision del dueno",
    "autorizado por el agente autonomo": "un agente no puede autorizar una decision del dueno",
    "final & binding": "ninguna decision de entidad o rail de pagos es vinculante sin el dueno (H.19/H.29)",
    "h.20 resolved": "H.20 (revision profesional) solo lo cierra el dueno",
    "h.21 resolved": "H.21 solo lo cierra el dueno",
    "h.19 resolved": "H.19 solo lo cierra el dueno",
}
self_auth_ok = True
for path in sorted(LEGAL_DIR.glob("*.md")):
    try:
        low = path.read_text(encoding="utf-8").lower()
    except Exception as e:  # noqa: BLE001
        check(f"{path.name} lectura", False, str(e))
        self_auth_ok = False
        continue
    # Un documento marcado ANULADO puede citar la frase para explicar por que
    # se anula; eso es historia, no una decision vigente.
    if "anulado" in low or "annulled" in low:
        continue
    for needle, reason in SELF_AUTHORIZED.items():
        if needle in low:
            check(f"{path.name} contiene '{needle}'", False, reason)
            self_auth_ok = False
if self_auth_ok:
    check("Ninguna decision del dueno firmada por un agente", True)

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
    sys.exit(0)
