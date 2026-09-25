"""Ninguna pregunta del banco es relleno de generador (ledger 35.14).

61 preguntas de track13 llegaron a producción como «Pregunta de sk130102» con
opciones A/B/C/D y «Explicacion correcta». Pasaban el resto de la puerta: ids
únicos, ES y EN presentes, fuente y posiciones repartidas.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

import check_question_bank as cqb

RELLENO = {
    "id": "q130102068",
    "question_es": "Pregunta de sk130102",
    "question_en": "Question for sk130102",
    "options_es": ["A", "B", "C", "D"],
    "explanation_es": "Explicacion correcta",
    "explanation_en": "Correct explanation",
}


def _es_relleno(q: dict) -> bool:
    return bool(
        cqb.PLACEHOLDER_STEM.match(q.get("question_es") or "")
        or cqb.PLACEHOLDER_STEM.match(q.get("question_en") or "")
        or [str(o).strip() for o in (q.get("options_es") or [])] in cqb.PLACEHOLDER_OPTIONS
        or (q.get("explanation_es") or "").strip().lower() in cqb.PLACEHOLDER_EXPLANATIONS
        or (q.get("explanation_en") or "").strip().lower() in cqb.PLACEHOLDER_EXPLANATIONS
    )


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("question_es", "Pregunta de sk130102"),
        ("question_en", "Question for sk130102"),
        ("options_es", ["A", "B", "C", "D"]),
        ("explanation_es", "Explicacion correcta"),
        ("explanation_en", "Correct explanation"),
    ],
)
def test_cada_senal_de_relleno_se_detecta_sola(campo: str, valor: object) -> None:
    q = {"question_es": "¿Qué garantiza la integridad?", "question_en": "What does integrity ensure?",
         "options_es": ["Que nadie altere los datos", "Otra cosa", "Nada", "Todo lo anterior"],
         "explanation_es": "Porque sí.", "explanation_en": "Because."}
    assert not _es_relleno(q)
    q[campo] = valor
    assert _es_relleno(q)


def test_opciones_numericas_no_son_relleno() -> None:
    # track01 pregunta «¿Qué imprime?» con opciones 1-4: legítimo.
    assert not _es_relleno({"question_es": "¿Qué imprime el siguiente código?", "options_es": ["2", "3", "1", "4"]})


def test_el_banco_no_tiene_relleno() -> None:
    relleno = [
        f"{p.relative_to(ROOT).as_posix()} {q.get('id')}"
        for p in sorted((ROOT / "content" / "questions").rglob("*.json"))
        for q in (lambda d: d if isinstance(d, list) else d.get("questions", []))(json.loads(p.read_text(encoding="utf-8")))
        if _es_relleno(q)
    ]
    assert relleno == [], f"{len(relleno)} preguntas de relleno: {relleno[:5]}"


def test_la_muestra_de_track13_es_relleno() -> None:
    assert _es_relleno(RELLENO)
