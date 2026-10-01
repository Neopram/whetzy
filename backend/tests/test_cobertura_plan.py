"""Guarda del plan de catálogo ADR-54: `scripts/catalog_coverage.py` + `scripts/metas_catalogo.json`.

Dos cosas: (1) el fichero de metas describe exactamente el catálogo real (cada
track de `tracks.json` tiene su fila, ninguna fila «construido» falta, ningún
roadmap se reparte dos veces) y (2) cada regla de ADR-54 —32 skills, 10 preguntas
por skill, nada se borra, práctica máx(300, 3L), reservadas 2L, «pendiente» sin L,
sin ideal por temario— tiene su test, mutado a rojo antes de darlo por bueno.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import catalog_coverage as cov

FORMA = {
    "skills": 32,
    "preguntas_por_skill": 10,
    "ejecutables_min_por_skill": 3,
    "lecciones_por_skill": 1,
    "terminos_por_skill": 1,
}
CERT = {"practica_min": 300, "practica_factor_examen": 3, "reservadas_factor_examen": 2}


def _track(n_skills: int, q_per_skill: int, ejec: int = 0, lecciones: int | None = None, terminos: int = 0) -> dict:
    skills = [f"sk{i:03d}" for i in range(n_skills)]
    return {
        "practica_por_skill": dict.fromkeys(skills, q_per_skill),
        "ejecutables_por_skill": dict.fromkeys(skills, ejec),
        "lecciones": set(skills[: n_skills if lecciones is None else lecciones]),
        "terminos": terminos,
    }


@pytest.fixture(scope="module")
def metas() -> dict:
    return cov.load_metas()


@pytest.fixture(scope="module")
def catalog(metas) -> dict:
    return cov.load_catalog(exec_types=frozenset(metas["tipos_ejecutables"]["tipos"]))


# ── las metas son las de ADR-54 ──────────────────────────────────────────────


def test_las_metas_son_las_de_adr54(metas) -> None:
    assert metas["adr"] == "ADR-54"
    assert {k: metas["forma_track"][k] for k in FORMA} == FORMA
    assert {k: metas["certificacion"][k] for k in CERT} == CERT


def test_no_queda_ideal_por_temario(metas, catalog) -> None:
    assert "ideal" not in metas and "suelo" not in metas
    assert not hasattr(cov, "ideal_skills")
    result = cov.measure(metas, catalog)
    claves = set(result["totales"]) | {k for r in result["tracks"] for k in r} | {
        k for c in result["certificaciones"] for k in c
    }
    assert not any("ideal" in k for k in claves), sorted(k for k in claves if "ideal" in k)


# ── forma del track: 32 skills × 10 preguntas ────────────────────────────────


def test_un_track_corto_de_skills_pide_hasta_32() -> None:
    gap = cov.track_gap(_track(30, 10, terminos=30), FORMA)
    assert gap["skills_pendientes"] == 2
    assert gap["preguntas_pendientes"] == 20  # 10 por cada skill nueva
    assert gap["lecciones_pendientes"] == 2
    assert gap["terminos_pendientes"] == 2


def test_cada_skill_necesita_10_preguntas() -> None:
    gap = cov.track_gap(_track(32, 7, terminos=32), FORMA)
    assert gap["skills_pendientes"] == 0
    assert gap["preguntas_pendientes"] == 32 * 3


def test_nada_se_borra_por_encima_de_la_forma() -> None:
    gap = cov.track_gap(_track(52, 16, ejec=3, terminos=60), FORMA)
    assert gap == {
        "skills": 52,
        "skills_pendientes": 0,
        "preguntas_pendientes": 0,
        "lecciones_pendientes": 0,
        "terminos_pendientes": 0,
        "skills_con_ejecutables": "52/52",
    }


def test_ejecutables_sin_preguntas_ejecutables_es_sin_medir_salvo_exencion() -> None:
    assert cov.track_gap(_track(32, 10), FORMA)["skills_con_ejecutables"] == "sin medir"
    assert cov.track_gap(_track(32, 10), FORMA, exenta="el navegador no ejecuta AWS")["skills_con_ejecutables"] == "exento"
    assert cov.track_gap(_track(32, 10, ejec=2), FORMA)["skills_con_ejecutables"] == "0/32"


# ── certificaciones ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(("exam_len", "practica"), [(30, 300), (65, 300), (100, 300), (120, 360)])
def test_practica_es_el_maximo_de_300_y_3_veces_el_examen(exam_len, practica) -> None:
    assert cov.cert_targets(exam_len, CERT)["practica"] == practica


def test_reservadas_son_2_veces_el_examen() -> None:
    assert cov.cert_targets(65, CERT)["reservadas"] == 130
    assert cov.cert_targets(90, CERT)["reservadas"] == 180


def test_sin_longitud_publicada_las_reservadas_quedan_pendientes(metas, catalog) -> None:
    assert cov.cert_targets(None, CERT) == {"practica": 300, "reservadas": "pendiente"}
    result = cov.measure(metas, catalog)
    az900 = next(c for c in result["certificaciones"] if c["id"] == "track44")
    assert az900["reservadas_meta"] == "pendiente"
    assert "track44" in result["totales"]["cert_sin_longitud"]
    con_l = [c for c in result["certificaciones"] if c["preguntas_examen"]]
    assert result["totales"]["cert_reservadas_pendientes"] == sum(c["reservadas_pendientes"] for c in con_l)


# ── metas ↔ catálogo (--check) ───────────────────────────────────────────────


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


def test_exencion_sin_razon_se_pone_roja(metas, catalog) -> None:
    m = copy.deepcopy(metas)
    next(t for t in m["tracks"] if t["id"] == "track22")["ejecucion_exenta"] = " "
    assert any("track22" in p and "ejecucion_exenta" in p for p in cov.validate(m, catalog))


def test_los_niveles_salen_de_la_demanda_medida(metas) -> None:
    by_id = {t["id"]: t for t in metas["tracks"]}
    assert cov.tier(by_id["track38"], metas) == "A"  # TypeScript 43,6 %
    assert cov.tier(by_id["track35"], metas) == "B"  # Go 16,4 %
    assert cov.tier(by_id["track49"], metas) == "C"  # Ruby 6,4 %
    assert cov.tier(by_id["track52"], metas) == "C"  # sin medida


def test_las_reservadas_no_cuentan_como_practica(metas, catalog) -> None:
    result = cov.measure(metas, catalog)
    for c in result["certificaciones"]:
        real = catalog[c["id"]]
        assert c["practica"] == sum(real["practica_por_skill"].values())
        assert c["reservadas"] == real["reservadas"]
