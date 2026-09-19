# -*- coding: utf-8 -*-
"""Guardia de paridad ES/EN (tarea 23.5; la cita `PROTOCOLO_VERIFICACION.md` §10).

Comprueba las tres superficies donde un texto puede salir en un solo idioma:

1. **Frontend** — `frontend/src/i18n/{es,en}/common.json`: el conjunto de claves
   tiene que ser idéntico. Con paridad total, el `fallbackLng: 'es'` de
   `src/i18n.ts` no se dispara nunca, que es lo que pide la línea roja 3.
2. **Emails** — `_TEMPLATES` de `backend/app/services/email.py`: cada plantilla
   debe existir en `es` y en `en`, y con los mismos campos (`subject`, `html`).
3. **Documentos legales de cara al usuario** — `docs/legal/<nombre>.<es|en>.md`:
   cada uno con sus dos versiones. Los documentos **internos** de investigación
   (`docs/legal/*.md` sin sufijo de idioma: README, h21-decision, privacy-matrix,
   trademark-search, ai-act-dsa-eaa) NO entran: no los ve un usuario, y contarlos
   era lo que hacía que `check-i18n.mjs` informara de un falso 58,33 %.

Sale con 0 si todo tiene pareja, y con 1 pegando exactamente lo que falta.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGS = ("es", "en")


def _flatten(node: object, prefix: str = "") -> list[str]:
    """Aplana el JSON a rutas de hoja. Las listas se indexan (`items.0`) para que
    una traduccion con menos elementos que la otra tambien salte."""
    if isinstance(node, dict):
        return [k for key, value in node.items() for k in _flatten(value, prefix + key + ".")]
    if isinstance(node, list):
        return [k for i, value in enumerate(node) for k in _flatten(value, prefix + str(i) + ".")]
    return [prefix.rstrip(".")]


def check_frontend() -> list[str]:
    keys: dict[str, set[str]] = {}
    for lang in LANGS:
        path = ROOT / "frontend" / "src" / "i18n" / lang / "common.json"
        if not path.exists():
            return ["frontend: falta %s" % path.relative_to(ROOT)]
        keys[lang] = set(_flatten(json.loads(path.read_text(encoding="utf-8"))))
    problems = []
    for lang, other in (("es", "en"), ("en", "es")):
        for key in sorted(keys[lang] - keys[other]):
            problems.append("frontend: la clave '%s' está en %s pero no en %s" % (key, lang, other))
    print("  frontend: %d claves en es, %d en en" % (len(keys["es"]), len(keys["en"])))
    return problems


def _email_templates() -> dict[str, dict[str, dict[str, str]]]:
    source = (ROOT / "backend" / "app" / "services" / "email.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        target = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target = node.target.id
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            target = node.targets[0].id
        if target == "_TEMPLATES" and node.value is not None:
            return ast.literal_eval(node.value)
    raise SystemExit("no se encontró _TEMPLATES en backend/app/services/email.py")


def check_emails() -> list[str]:
    templates = _email_templates()
    problems = []
    for name, by_lang in sorted(templates.items()):
        for lang in LANGS:
            if lang not in by_lang:
                problems.append("emails: la plantilla '%s' no tiene versión %s" % (name, lang))
        if all(lang in by_lang for lang in LANGS):
            fields_es, fields_en = set(by_lang["es"]), set(by_lang["en"])
            for field in sorted(fields_es ^ fields_en):
                problems.append("emails: '%s' tiene el campo '%s' en un solo idioma" % (name, field))
    print("  emails: %d plantillas" % len(templates))
    return problems


def check_legal() -> list[str]:
    legal = ROOT / "docs" / "legal"
    by_name: dict[str, set[str]] = {}
    for path in sorted(legal.glob("*.md")):
        parts = path.name.split(".")
        if len(parts) != 3 or parts[1] not in LANGS:
            continue  # doc interno de investigación, no lo ve un usuario
        by_name.setdefault(parts[0], set()).add(parts[1])
    problems = []
    for name, langs in sorted(by_name.items()):
        for lang in LANGS:
            if lang not in langs:
                problems.append("legal: '%s' no tiene versión %s (docs/legal/%s.%s.md)" % (name, lang, name, lang))
    print("  legal: %d documentos de cara al usuario" % len(by_name))
    return problems


def main() -> int:
    print("[i18n-parity] comprobando paridad ES/EN")
    problems = check_frontend() + check_emails() + check_legal()
    if problems:
        print("\n%d problema(s) de paridad:" % len(problems))
        for problem in problems:
            print("  - %s" % problem)
        return 1
    print("\n[i18n-parity] PASS - frontend, emails y legal tienen ES y EN completos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
