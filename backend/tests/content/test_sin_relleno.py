"""Ninguna pregunta del banco es relleno de generador (ledger 37.14).

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
    return cqb.is_placeholder(q)


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("question_es", "Pregunta de sk130102"),
        ("question_en", "Question for sk130102"),
        ("options_es", ["A", "B", "C", "D"]),
        ("explanation_es", "Explicacion correcta"),
        ("explanation_en", "Correct explanation"),
        # Segunda forma (39.37): track20 mod2003-2005.
        ("options_es", ["Opción C 1", "Opción D 1", "Opción B 1", "Opción A 1"]),
        ("options_es", ["Snowflake A 6", "Snowflake D 6", "Snowflake C 6", "Snowflake B 6"]),
        ("explanation_es", "Respuesta para pregunta 1"),
        ("explanation_en", "Snowflake answer 6"),
    ],
)
def test_cada_senal_de_relleno_se_detecta_sola(campo: str, valor: object) -> None:
    q = {
        "question_es": "¿Qué garantiza la integridad?",
        "question_en": "What does integrity ensure?",
        "options_es": [
            "Que nadie altere los datos",
            "Otra cosa",
            "Nada",
            "Todo lo anterior",
        ],
        "explanation_es": "Porque sí.",
        "explanation_en": "Because.",
    }
    assert not _es_relleno(q)
    q[campo] = valor
    assert _es_relleno(q)


def test_opciones_numericas_no_son_relleno() -> None:
    # track01 pregunta «¿Qué imprime?» con opciones 1-4: legítimo.
    assert not _es_relleno(
        {
            "question_es": "¿Qué imprime el siguiente código?",
            "options_es": ["2", "3", "1", "4"],
        }
    )


def _preguntas(p: Path) -> list[dict]:
    data = json.loads(p.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data.get("questions", [])


def _relleno_del_banco() -> list[str]:
    return [
        str(q.get("id"))
        for p in sorted((ROOT / "content" / "questions").rglob("*.json"))
        for q in _preguntas(p)
        if _es_relleno(q)
    ]


def test_el_banco_no_tiene_relleno_nuevo() -> None:
    """El relleno conocido (39.37) espera su reescritura; uno nuevo no entra."""
    conocido = set(json.loads(cqb.PLACEHOLDER_KNOWN.read_text(encoding="utf-8")))
    nuevo = sorted(set(_relleno_del_banco()) - conocido)
    assert nuevo == [], f"{len(nuevo)} preguntas de relleno nuevas: {nuevo[:5]}"


def test_la_lista_de_relleno_conocido_solo_encoge() -> None:
    """Una pregunta reescrita sale de la lista en el mismo commit: si no, la lista tapa relleno futuro."""
    conocido = set(json.loads(cqb.PLACEHOLDER_KNOWN.read_text(encoding="utf-8")))
    arreglado = sorted(conocido - set(_relleno_del_banco()))
    assert arreglado == [], f"ya no son relleno, quítalos de {cqb.PLACEHOLDER_KNOWN.name}: {arreglado[:5]}"


def test_la_muestra_de_track13_es_relleno() -> None:
    assert _es_relleno(RELLENO)
