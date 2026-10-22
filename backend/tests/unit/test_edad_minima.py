"""Edad mínima: 16 años (ADR-70; el dueño corrige así ADR-61 el 2026-10-22).

La casilla del alta, su error, los Términos y la Privacidad dicen la misma edad en ES y
EN, y el backend rechaza el alta con el mismo número. Antes decían 13: si un texto se
queda atrás, el alumno ve una edad y los Términos publican otra.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
EDAD = "16"
ANTERIOR = "13"
CLAVES = ("ageLabel", "errAge", "termsP2", "privacyCoppaDesc")


def _buscar(doc: Any, clave: str) -> list[str]:
    if isinstance(doc, dict):
        out = [v for k, v in doc.items() if k == clave and isinstance(v, str)]
        for v in doc.values():
            out += _buscar(v, clave)
        return out
    if isinstance(doc, list):
        return [x for v in doc for x in _buscar(v, clave)]
    return []


def test_los_textos_del_alta_y_los_legales_dicen_16_en_es_y_en() -> None:
    for lang in ("es", "en"):
        doc = json.loads(
            (ROOT / "frontend" / "src" / "i18n" / lang / "common.json").read_text(
                encoding="utf-8"
            )
        )
        for clave in CLAVES:
            textos = _buscar(doc, clave)
            assert textos, f"{lang}: falta la clave {clave}"
            for t in textos:
                assert EDAD in t, f"{lang}.{clave} no dice {EDAD}: {t!r}"
                assert ANTERIOR not in t, (
                    f"{lang}.{clave} sigue diciendo {ANTERIOR}: {t!r}"
                )


def test_el_backend_rechaza_el_alta_con_la_misma_edad() -> None:
    src = (ROOT / "backend" / "app" / "api" / "v1" / "endpoints" / "auth.py").read_text(
        encoding="utf-8"
    )
    assert f"must be {EDAD} or older" in src
    assert f"must be {ANTERIOR} or older" not in src
