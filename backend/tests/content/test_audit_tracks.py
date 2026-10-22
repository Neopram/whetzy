"""La auditoría de tracks cuenta lo que dice contar (fase 1, auditoría de tracks).

Cada regla de `scripts/audit_tracks.py` tiene aquí un caso que la rompe si cambia:
qué cuenta como ejecutable (`js_exec` sí, `code_output` no), qué se deja fuera de
los totales (el fichero suelto de `_quarantine/`), y las dos formas del glosario.
Los totales del repo se comparan con un recuento independiente hecho aquí, no con
cifras fijas: el contenido cambia y el script tiene que seguir cuadrando.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_tracks as at

# Los tests que siguen construyen un árbol mínimo de `content/` en tmp_path.


def _escribir(path: Path, doc: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")


def _pregunta(skill: str, tipo: str, pool: str | None = None) -> dict:
    q = {"id": f"{skill}-{tipo}-{pool or 'p'}", "skill_id": skill, "type": tipo}
    if pool:
        q["pool"] = pool
    return q


def _arbol(tmp_path: Path) -> tuple[Path, Path]:
    """Dos tracks de aprendizaje (01 y 14), una certificación (08), cuarentena y un suelto."""
    c = tmp_path / "content"
    _escribir(
        c / "curriculum" / "tracks.json",
        {
            "tracks": [
                {
                    "id": "track01",
                    "name_es": "Python",
                    "modules": [{"skills": [{"id": "sk01"}, {"id": "sk02"}]}],
                },
                {
                    "id": "track14",
                    "name_es": "JS",
                    "modules": [{"skills": [{"id": "sk14"}]}],
                },
                {
                    "id": "track08",
                    "name_es": "CLF",
                    "certification": True,
                    "modules": [{"skills": [{"id": "sk08"}]}],
                },
            ]
        },
    )
    _escribir(
        c / "questions" / "track01_python" / "a.json",
        [
            _pregunta("sk01", "multiple_choice"),
            _pregunta("sk01", "fill_blank_exec"),
            _pregunta("sk02", "code_output"),
            _pregunta("sk02", "multiple_choice", pool="simulacro"),
        ],
    )
    _escribir(
        c / "questions" / "track14_js" / "a.json",
        {
            "questions": [
                _pregunta("sk14", "js_exec"),
                _pregunta("sk14", "code_output"),
            ]
            + [_pregunta("sk14", "true_false")] * 7
        },
    )
    _escribir(
        c / "questions" / "track08_clf" / "a.json",
        [_pregunta("sk08", "mcq", pool="simulacro")],
    )
    _escribir(
        c / "_quarantine" / "track24_pentest" / "mod.json",
        [_pregunta("sk24", "sql_exec")] * 4,
    )
    # El suelto de track13 tiene 15 preguntas de otro track: no entra en ningún total.
    _escribir(
        c / "_quarantine" / "track13_suelto.json", [_pregunta("sk01", "fix_bug")] * 15
    )
    _escribir(
        c / "lessons" / "track01" / "l1.json",
        {
            "id": "l1",
            "skill_id": "sk01",
            "body_es": "uno dos tres",
            "source": "https://example.org",
        },
    )
    _escribir(
        c / "lessons" / "track01" / "l2.json",
        {"id": "l2", "skill_id": "sk02", "body_es": "uno dos", "source": ""},
    )
    _escribir(
        c / "glossary" / "track01.json",
        {"track_id": "track01", "terms": [{"id": "g1"}, {"id": "g2"}]},
    )
    _escribir(c / "glossary" / "track08.json", [{"id": "g3"}])
    metas = tmp_path / "metas.json"
    _escribir(
        metas,
        {
            "tracks": [
                {"id": "track01", "nombre": "Python", "estado": "construido"},
                {"id": "track14", "nombre": "JS", "estado": "construido"},
                {"id": "track24", "nombre": "Pentest", "estado": "cuarentena"},
                {"id": "track31", "nombre": "Móvil", "estado": "planificado"},
            ],
            "certificaciones": [
                {"id": "track08", "codigo": "CLF-C02", "preguntas_examen": 65}
            ],
        },
    )
    return c, metas


def _fila(filas: list[dict], tid: str) -> dict:
    return next(f for f in filas if f["id"] == tid)


def test_cuenta_preguntas_por_track_y_no_cuenta_el_fichero_suelto(
    tmp_path: Path,
) -> None:
    c, metas = _arbol(tmp_path)
    res = at.construir(c, metas)
    assert _fila(res["filas"], "track01")["preguntas"] == 4
    assert res["totales"]["sueltos_cuarentena"] == ["track13_suelto.json"]
    # 4 + 9 + 1 construidos; el suelto (15) y la cuarentena (4) quedan fuera.
    assert res["totales"]["preguntas"] == 14


def test_js_exec_es_ejecutable_y_code_output_solo_cuenta_como_con_codigo(
    tmp_path: Path,
) -> None:
    c, metas = _arbol(tmp_path)
    fila = _fila(at.construir(c, metas)["filas"], "track14")
    assert fila["ejecutables"] == 1  # js_exec, sin él saldría 0
    assert fila["con_codigo"] == 2  # js_exec + code_output
    assert fila["preguntas"] == 9


def test_cuarentena_directorio_se_lista_aparte_y_no_suma_a_construidos(
    tmp_path: Path,
) -> None:
    c, metas = _arbol(tmp_path)
    res = at.construir(c, metas)
    cuar = _fila(res["filas"], "track24")
    assert cuar["estado"] == "cuarentena"
    assert cuar["preguntas"] == 4
    assert res["totales"]["cuarentena"] == 1
    assert res["totales"]["construidos"] == 3


def test_reservadas_se_cuentan_por_pool_simulacro(tmp_path: Path) -> None:
    c, metas = _arbol(tmp_path)
    res = at.construir(c, metas)
    assert _fila(res["filas"], "track01")["reservadas"] == 1
    assert _fila(res["filas"], "track08")["reservadas"] == 1


def test_glosario_acepta_objeto_con_terms_y_lista_plana(tmp_path: Path) -> None:
    c, metas = _arbol(tmp_path)
    res = at.construir(c, metas)
    assert _fila(res["filas"], "track01")["terminos"] == 2
    assert _fila(res["filas"], "track08")["terminos"] == 1


def test_lecciones_medianas_y_fuente_por_skill(tmp_path: Path) -> None:
    c, metas = _arbol(tmp_path)
    res = at.construir(c, metas)
    fila = _fila(res["filas"], "track01")
    assert fila["lecciones"] == 2
    assert fila["mediana_palabras"] == 2  # mediana de [3, 2]
    sk1 = next(d for d in fila["detalle"] if d["skill"] == "sk01")
    sk2 = next(d for d in fila["detalle"] if d["skill"] == "sk02")
    assert sk1["fuente"] is True
    assert sk2["fuente"] is False


def test_recomendaciones_disparan_las_reglas_explicitas(tmp_path: Path) -> None:
    c, metas = _arbol(tmp_path)
    res = at.construir(c, metas)
    rec = _fila(res["filas"], "track01")["recomendaciones"]
    # track01 es materia de código y tiene 1 ejecutable de 4 (25 %, no dispara D3).
    assert any("faltan 30 skills" in r for r in rec)
    assert any("Proyectos (43.6)" in r for r in rec)
    assert not any("D3" in r for r in rec)
    rec14 = _fila(res["filas"], "track14")["recomendaciones"]
    assert any(r.startswith("D3: ejecutables 11.1%") for r in rec14)  # 1 de 9 < 15 %
    rec08 = _fila(res["filas"], "track08")["recomendaciones"]
    assert any("reservado 1 de 130" in r for r in rec08)


def test_plan_completo_sin_contar_cuarentena_ni_planificados_como_construidos(
    tmp_path: Path,
) -> None:
    c, metas = _arbol(tmp_path)
    t = at.construir(c, metas)["totales"]
    assert t["plan"] == 5  # 4 de tracks (01, 14, 24, 31) + 1 certificación (08)
    assert t["construidos"] == 3
    assert t["planificados"] == 1
    assert t["sin_ejecutable"] == 1  # track08 no tiene ejecutables


def test_totales_del_repo_coinciden_con_recuento_de_ficheros() -> None:
    """Independiente del script: recuenta los ficheros del repo y compara."""
    content = at.CONTENT
    tracks = at.cargar_tracks(content)
    owner = {
        s["id"]: t["id"] for t in tracks for m in t["modules"] for s in m["skills"]
    }
    preguntas = 0
    for qdir in (content / "questions").iterdir():
        if not qdir.is_dir():
            continue
        for f in qdir.rglob("*.json"):
            doc = json.loads(f.read_text(encoding="utf-8"))
            for it in doc if isinstance(doc, list) else doc.get("questions", []):
                assert it["skill_id"] in owner, f"pregunta huérfana en {f}"
                preguntas += 1
    lecciones = sum(1 for _ in (content / "lessons").rglob("*.json"))
    terminos = 0
    for f in (content / "glossary").glob("track*.json"):
        doc = json.loads(f.read_text(encoding="utf-8"))
        terminos += len(doc if isinstance(doc, list) else doc["terms"])

    t = at.construir(content, at.METAS)["totales"]
    assert t["construidos"] == len(tracks)
    assert t["preguntas"] == preguntas
    assert t["lecciones"] == lecciones
    assert t["terminos"] == terminos
    assert t["huerfanas"] == 0


def test_escribe_resumen_fichas_e_inventario(tmp_path: Path) -> None:
    c, metas = _arbol(tmp_path)
    res = at.construir(c, metas)
    out = tmp_path / "salida"
    at.escribir(res, out, "2026-10-22", [])
    assert (
        (out / "resumen.md")
        .read_text(encoding="utf-8")
        .startswith("# Resumen de la auditoría de tracks (2026-10-22)")
    )
    assert (out / "tracks" / "track01.md").exists()
    assert not (out / "tracks" / "track24.md").exists()  # cuarentena: sin ficha
    inv = json.loads((out / "inventario.json").read_text(encoding="utf-8"))
    assert inv["totales"]["preguntas"] == 14
