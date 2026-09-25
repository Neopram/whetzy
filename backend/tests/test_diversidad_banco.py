"""Guarda de diversidad del banco (ledger 35.0, ADR-42): `scripts/question_diversity.py`.

Criterio de la fila: la guarda pone en rojo track24/25 de la cuarentena (14
enunciados distintos de 400) y deja en verde track12. Además, cada una de las
cuatro métricas se rompe a propósito sobre track12 y tiene que ponerse roja.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import question_diversity as qd

ROOT = SCRIPTS.parent
QUARANTINE = ROOT / "content" / "_quarantine"


@pytest.fixture(scope="module")
def urls() -> list[str]:
    return qd.indexed_urls()


@pytest.fixture(scope="module")
def live() -> dict[str, list[dict]]:
    return qd.load()


@pytest.fixture(scope="module")
def baseline() -> dict[str, dict]:
    return qd.load_baseline()


def test_el_banco_vivo_no_empeora(live, baseline, urls) -> None:
    assert qd.check(live, baseline, urls) == []


@pytest.mark.parametrize("track", ["track24", "track25"])
def test_la_cuarentena_de_la_serie_25_queda_en_rojo(track, urls) -> None:
    quarantine = qd.load(QUARANTINE)
    problems = qd.check({track: quarantine[track]}, {}, urls)
    texto = "\n".join(problems)
    assert "enunciados distintos" in texto
    assert "opciones de una palabra" in texto
    assert "*_exec sin código" in texto


def test_track12_en_verde(live, baseline, urls) -> None:
    assert qd.check({"track12": live["track12"]}, baseline, urls) == []


def _track12(live: dict[str, list[dict]]) -> list[dict]:
    return copy.deepcopy(live["track12"])


def test_mutacion_enunciados_repetidos(live, baseline, urls) -> None:
    qs = _track12(live)
    clon = qs[0]
    qs += [copy.deepcopy(clon) for _ in range(60)]
    assert any(
        "enunciados distintos" in p for p in qd.check({"track12": qs}, baseline, urls)
    )


def test_mutacion_opciones_de_una_palabra(live, baseline, urls) -> None:
    qs = _track12(live)
    for i in range(120):
        q = copy.deepcopy(qs[0])
        q["question_es"] = f"Pregunta sintética {i}"
        q["options_es"] = ["a", "b", "c", "d"]
        q["source"] = "https://github.com/heroku/12factor"
        qs.append(q)
    assert any("una palabra" in p for p in qd.check({"track12": qs}, baseline, urls))


def test_mutacion_exec_sin_codigo(live, baseline, urls) -> None:
    qs = _track12(live)
    q = copy.deepcopy(qs[0])
    q.update(
        type="fill_blank_exec",
        question_es="Completa el hueco",
        code_es=None,
        code_en=None,
    )
    qs.append(q)
    assert any(
        "*_exec sin código" in p for p in qd.check({"track12": qs}, baseline, urls)
    )


def test_mutacion_fuente_sin_indexar(live, baseline, urls) -> None:
    qs = _track12(live)
    q = copy.deepcopy(qs[0])
    q.update(
        question_es="Pregunta nueva y distinta",
        source="https://example.com/no-indexada",
    )
    qs.append(q)
    assert any(
        "fuente indexada" in p for p in qd.check({"track12": qs}, baseline, urls)
    )


def test_una_pregunta_nueva_bien_hecha_pasa(live, baseline, urls) -> None:
    qs = _track12(live)
    q = copy.deepcopy(qs[0])
    q.update(
        question_es="¿Qué cláusula agrupa filas con el mismo valor antes de agregarlas?",
        options_es=[
            "La cláusula GROUP BY",
            "La cláusula ORDER BY",
            "La cláusula WHERE",
            "Una subconsulta",
        ],
        source="Twelve-Factor App: https://github.com/heroku/12factor",
    )
    qs.append(q)
    assert qd.check({"track12": qs}, baseline, urls) == []


def test_un_track_nuevo_cumple_adr42_sin_trinquete(live, urls) -> None:
    # Sin línea base, track12 tal cual quedaría en rojo: 300 preguntas sin
    # fuente indexada. Es la razón del trinquete, y lo que un track nuevo no
    # puede arrastrar.
    problems = qd.check({"track99": live["track12"]}, {}, urls)
    assert any("sin fuente en content/sources/index.json" in p for p in problems)


def test_los_alias_del_indice_cuentan_como_fuente(tmp_path, live) -> None:
    idx = tmp_path / "index.json"
    idx.write_text(
        '[{"url": "https://github.com/python/cpython", "aliases": ["https://docs.python.org/3"]}]',
        encoding="utf-8",
    )
    urls = qd.indexed_urls(idx)
    q = {"source": "PSF: https://docs.python.org/3/tutorial/controlflow.html"}
    assert qd._source_indexed(q, urls)
    assert not qd._source_indexed({"source": "https://docs.python.org/es/3/"}, urls)


def test_mutacion_la_correcta_es_la_mas_larga(live, baseline, urls) -> None:
    # 35.16: una tanda que siempre alarga la correcta tiene que ponerse roja.
    qs = _track12(live)
    for i in range(200):
        q = copy.deepcopy(qs[0])
        q.update(
            question_es=f"Pregunta sintética distinta número {i}",
            options_es=[
                "Una opción corta",
                "Otra opción corta",
                "La correcta, bastante más larga que las demás",
                "Opción breve",
            ],
            correct_index=2,
            source="https://github.com/heroku/12factor",
        )
        qs.append(q)
    assert any(
        "opción más larga" in p for p in qd.check({"track12": qs}, baseline, urls)
    )


def test_la_mas_larga_empatada_no_cuenta() -> None:
    q = {"options_es": ["abcd", "abcd", "ab", "a"], "correct_index": 0}
    assert not qd._correct_is_longest(q)
    q["options_es"] = ["abcde", "abcd", "ab", "a"]
    assert qd._correct_is_longest(q)


def test_track_nuevo_sesgado_en_rojo(live, urls) -> None:
    # Sintético a propósito: el ejemplo real (track11, 98 %) se arregló en 35.16.
    sesgadas = []
    for i, q in enumerate(_track12(live)):
        q = dict(q, question_es=f"Enunciado sintético {i}", correct_index=0)
        q["options_es"] = [
            "La correcta, claramente más larga que el resto",
            "Corta",
            "Breve",
            "Otra",
        ]
        sesgadas.append(q)
    assert any(
        "opción más larga" in p for p in qd.check({"track99": sesgadas}, {}, urls)
    )
