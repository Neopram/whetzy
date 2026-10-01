#!/usr/bin/env python3
"""check_legal_facts.py — 21.0: verifica hechos legales en documentos legales.

Comprueba que los 14 documentos legales (7 ficheros x 2 idiomas) no contienen
afirmaciones falsas, defectos de codificación o inconsistencias que violarían
los ADRs o resolverían issues abiertas de revisión.

Variable de entorno: WHETZY_LEGAL_DIR (default: docs/legal)
"""

from __future__ import annotations

import json
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

# Afirmaciones prohibidas, como expresiones regulares sobre el texto en
# minusculas. Son regex y no subcadenas porque un verificador adversario colo
# "Whetzy, Inc." (con coma) por delante de la version literal: los separadores
# de una razon social se escriben de diez formas y todas dicen lo mismo.
PROHIBITED = {
    r"whetzy[\s,\.\-]*inc": "sociedad inexistente",
    r"whetzy[\s,\.\-]*(llc|ltd|limited|gmbh|corp|s\.?a\.?r\.?l|s\.?l\.?|o[uü])": "sociedad inexistente",
    r"marcas?[\s\-]+registradas?": "marcado falso de marca",
    r"registered[\s\-]+trade[\s\-]*marks?": "marcado falso de marca",
    r"google[\s\-_]*analytics": "rastreador prohibido por linea roja 5",
    r"lemon[\s\-_]*squeezy": "procesador que no existe en el codigo",
    r"revenue[\s\-_]*cat": "procesador que no existe en el codigo",
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
            for pattern, reason in PROHIBITED.items():
                hit = re.search(pattern, content_lower)
                if hit:
                    check(
                        f"{doc_name}.{lang}.md contiene {hit.group(0)!r}",
                        False,
                        reason,
                    )
                    prohibited_ok = False
        except Exception as e:
            check(f"{doc_name}.{lang}.md lectura", False, str(e))
            prohibited_ok = False

if prohibited_ok:
    check("Afirmaciones prohibidas", True)

# Procesadores que el código ya integra: la política de privacidad —la de
# docs/legal y la que se publica en /privacy (claves i18n `legal.privacy*` que
# pinta LegalScreen.tsx)— tiene que nombrarlos, y si el código deja de tenerlos
# ya no puede nombrarlos. Paddle estaba en PROHIBITED («no existe en el
# código») hasta que el #58 (H.29) lo integró: a partir de ahí la regla
# vieja exigía callar un procesador que cobra.
PROCESSORS_IN_CODE = {
    "paddle": ROOT / "backend" / "app" / "services" / "paddle_billing.py",
}
I18N_DIR = ROOT / "frontend" / "src" / "i18n"

print()
print("[1b] Procesadores del código nombrados en la política de privacidad")
processors_ok = True
for name, marker in PROCESSORS_IN_CODE.items():
    in_code = marker.exists()
    for lang in LANGS:
        sources: dict[str, str] = {}
        md = LEGAL_DIR / f"privacy-policy.{lang}.md"
        if md.exists():
            sources[md.name] = md.read_text(encoding="utf-8")
        i18n = I18N_DIR / lang / "common.json"
        if i18n.exists():
            legal = json.loads(i18n.read_text(encoding="utf-8")).get("legal", {})
            sources[f"i18n {lang} legal.privacy*"] = " ".join(
                v for k, v in legal.items() if k.startswith("privacy")
            )
        for label, text in sources.items():
            named = name in text.lower()
            if in_code and not named:
                check(f"{label} no nombra a {name}", False, f"{marker.name} existe en el código")
                processors_ok = False
            elif not in_code and named:
                check(f"{label} nombra a {name}", False, "procesador que no existe en el código")
                processors_ok = False
if processors_ok:
    check("Procesadores del código nombrados en la política de privacidad", True)

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
print("[7] Landing sin testimonios ni cifras inventados (30.1)")
# El 2026-09-24 la landing de produccion publicaba testimonios con nombre de
# otro producto, «1.2M learners» y ventajas que no existen. Se reescribio; esto
# impide que vuelvan por el codigo o por las traducciones.
_FRONT = ROOT / "frontend"
LANDING_FILES = [
    _FRONT / "index.html",
    _FRONT / "src" / "pages" / "LandingScreen.tsx",
    _FRONT / "src" / "i18n" / "es" / "common.json",
    _FRONT / "src" / "i18n" / "en" / "common.json",
]
INVENTED = {
    "marina petrescu": "testimonio inventado",
    "diego alvarenga": "testimonio inventado",
    "1.2m learners": "cifra de usuarios inventada (hay cero usuarios reales)",
    "14-day streak club": "afirmacion sin datos",
    "240+ tracks": "cifra de catalogo inventada (sale de lib/catalog.ts)",
    "mock interviews": "funcion que no existe (descartada en ADR-47)",
}
landing_ok = True
for path in LANDING_FILES:
    if not path.exists():
        check(f"{path.name} existe", False, "falta un fichero de la landing")
        landing_ok = False
        continue
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".tsx":
        # Los comentarios cuentan la historia (qué se quitó y por qué); el
        # usuario no los ve. Se mira solo el código.
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        text = "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith("//"))
    # Se compara sin espacios ni puntuación: «1.2 M learners», «1,2M-learners»
    # o «Marina  Petrescu» no pueden colarse por el formato (hallazgo del
    # verificador adversario, 2026-09-25).
    squashed = re.sub(r"[\W_]+", "", text.lower())
    for needle, reason in INVENTED.items():
        if re.sub(r"[\W_]+", "", needle) in squashed:
            check(f"{path.name} contiene '{needle}'", False, reason)
            landing_ok = False
if landing_ok:
    check("Landing sin testimonios ni cifras inventados", True)

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
