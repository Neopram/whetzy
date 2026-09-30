"""Guarda del plan de catálogo ADR-53: `scripts/catalog_coverage.py` + `scripts/metas_adr53.json`.

Criterio: el fichero de metas describe exactamente el catálogo real (cada track
de `tracks.json` tiene su fila, ninguna fila «construido» falta en el catálogo,
ningún roadmap se reparte más de una vez) y cada una de esas reglas se rompe a
propósito y se pone roja. Sin esto, el plan y el catálogo divergen en silencio,
que es lo que pasó con los ids track41–46 hasta el 2026-09-29.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import catalog_coverage as cov


@pytest.fixture(scope="module")
def metas() -> dict:
    return cov.load_metas()


@pytest.fixture(scope="module")
def catalog() -> dict:
    return cov.load_catalog()


def test_metas_describen_el_catalogo_real(metas, catalog) -> None:
    assert cov.validate(metas, catalog) == []


def test_un_track_del_catalogo_sin_fila_se_pone_rojo(metas, catalog) -> None:
    m = copy.deepcopy(metas)
    m["tracks"] = [t for t in m["tracks"] if t["id"] != "track12"]
    assert any("track12" in p and "sin fila" in p for p in cov.validate(m, catalog))


def test_una_certificacion_sin_fila_se_pone_roja(metas, catalog) -> None:
    m = copy.deepcopy(metas)
    m["certificaciones"] = [c for c in m["certificaciones"] if c["id"] != "track42"]
    assert any("track42" in p for p in cov.validate(m, catalog))


def test_planificado_que_ya_existe_se_pone_rojo(metas, catalog) -> None:
    m = copy.deepcopy(metas)
    next(t for t in m["tracks"] if t["id"] == "track12")["estado"] = "planificado"
    assert any("track12" in p and "ya está en tracks.json" in p for p in cov.validate(m, catalog))


def test_construido_que_no_existe_se_pone_rojo(metas, catalog) -> None:
    m = copy.deepcopy(metas)
    next(t for t in m["tracks"] if t["id"] == "track33")["estado"] = "construido"
    assert any("track33" in p for p in cov.validate(m, catalog))


def test_roadmap_repartido_dos_veces_se_pone_rojo(metas, catalog) -> None:
    m = copy.deepcopy(metas)
    next(t for t in m["tracks"] if t["id"] == "track13")["referencia"][0]["parte"] = 1
    assert any("cyber-security" in p for p in cov.validate(m, catalog))


def test_roadmap_sin_recuento_se_pone_rojo(metas, catalog) -> None:
    m = copy.deepcopy(metas)
    del m["roadmap"]["nodos"]["sql"]
    assert any("'sql'" in p for p in cov.validate(m, catalog))


def test_sin_referencia_exige_nota_pendiente(metas, catalog) -> None:
    m = copy.deepcopy(metas)
    t = next(t for t in m["tracks"] if t["id"] == "track22")
    del t["pendiente"]
    assert any("track22" in p and "pendiente" in p for p in cov.validate(m, catalog))


def test_el_ideal_nunca_baja_del_suelo(metas) -> None:
    for t in metas["tracks"]:
        skills, _ = cov.ideal_skills(t, metas)
        assert skills >= metas["suelo"]["skills"], t["id"]


def test_los_niveles_salen_de_la_demanda_medida(metas) -> None:
    by_id = {t["id"]: t for t in metas["tracks"]}
    assert cov.tier(by_id["track38"], metas) == "A"  # TypeScript 43,6 %
    assert cov.tier(by_id["track35"], metas) == "B"  # Go 16,4 %
    assert cov.tier(by_id["track49"], metas) == "C"  # Ruby 6,4 %
    assert cov.tier(by_id["track52"], metas) == "C"  # sin medida


def test_el_simulacro_reservado_se_cuenta_aparte(metas, catalog) -> None:
    result = cov.measure(metas, catalog)
    clf = next(c for c in result["certificaciones"] if c["id"] == "track08")
    assert clf["reservadas_meta"] == 6 * 65
    assert clf["reservadas"] <= clf["preguntas"]
