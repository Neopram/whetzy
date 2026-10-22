"""Auditoría determinista de los tracks frente a la forma del catálogo (ADR-54).

Fase 1 de la auditoría «a la altura de un curso de referencia». Solo lee
`content/` y `scripts/metas_catalogo.json`, y escribe en
`docs/auditoria-tracks/<fecha>/`: `resumen.md` (una fila por track del plan),
`tracks/<tid>.md` (ficha de cada track construido) e `inventario.json` (lo mismo
en máquina, para la fase 2). No usa modelos: cada recomendación sale de una
regla explícita y constante de este fichero, nunca de una valoración.

Qué cuenta, y por qué así:

* **Preguntas** de `content/questions/`, asignadas al track que posee su skill en
  `content/curriculum/tracks.json`. Los ficheros sueltos de `content/_quarantine/`
  no cuentan (track13 tiene uno con 15 preguntas que no son del track construido);
  los directorios de cuarentena (track24, track25) se listan aparte.
* **Ejecutable estricto** = el navegador lo corre (Pyodide, sql.js, worker JS):
  `fill_blank_exec`, `fix_bug`, `sql_exec`, `js_exec`, `interactive`.
  **Con código** = eso más `code_output`. `js_exec` cuenta: sin él, JavaScript
  (track14) saldría con 0 ejecutables cuando tiene 16.
* **Lecciones** = ficheros de `content/lessons/<track>/`; **términos** = entradas
  de `content/glossary/<track>.json`.

Uso::

    python scripts/audit_tracks.py                      # docs/auditoria-tracks/<hoy>/
    python scripts/audit_tracks.py --fecha 2026-10-22   # carpeta con esa fecha
    python scripts/audit_tracks.py --out DIR            # otra carpeta (pruebas)

Las guardas existentes (banco, D5) se ejecutan como proceso y se guarda su veredicto
global; ninguna de ellas da un veredicto por track, y así consta en el informe.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
METAS = Path(__file__).resolve().parent / "metas_catalogo.json"
SALIDA = ROOT / "docs" / "auditoria-tracks"

MOCK_POOL = "simulacro"
SKILLS_FORMA = 32  # ADR-54: 8 módulos × 4 skills
PREGUNTAS_FORMA = 10  # ADR-54: 10 preguntas por skill
CON_CODIGO_MIN = (
    3  # ADR-54: ≥ 3 preguntas «con código» por skill (metas: ejecutables_min_por_skill)
)
UMBRAL_EJECUTABLE = 0.15  # por debajo, «D3»

# Ejecutable estricto: lo que el navegador ejecuta. Ver el docstring.
EJECUTABLES = frozenset(
    {"fill_blank_exec", "fix_bug", "sql_exec", "js_exec", "interactive"}
)
CON_CODIGO = EJECUTABLES | {"code_output"}

# Materia de código: track cuya enseñanza es programar, consultar o script. Lista
# explícita y editable; cada entrada cuenta para «D3 crítico» y «Proyectos (43.6)».
MATERIA_DE_CODIGO = frozenset(
    {
        "track01",
        "track02",
        "track03",
        "track04",
        "track09",
        "track12",
        "track14",
        "track15",
        "track16",
        "track20",
        "track21",
        "track27",
        "track28",
        "track41",
    }
)

GUARDAS = ("scripts/check_question_bank.py",)

FILA_TRACK = re.compile(r"(track\d+)")


def cargar_tracks(content: Path) -> list[dict[str, Any]]:
    data = json.loads(
        (content / "curriculum" / "tracks.json").read_text(encoding="utf-8")
    )
    return next(iter(data.values()))


def cargar_plan(metas: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    m = json.loads(metas.read_text(encoding="utf-8"))
    return m["tracks"], m["certificaciones"]


def _items(doc: Any) -> list[dict[str, Any]]:
    return doc if isinstance(doc, list) else doc.get("questions", [])


def contar_cuarentena(content: Path) -> dict[str, dict[str, Any]]:
    """Directorios `track*` de `_quarantine/`. Los ficheros sueltos quedan fuera."""
    out: dict[str, dict[str, Any]] = {}
    for d in sorted((content / "_quarantine").iterdir()):
        m = FILA_TRACK.match(d.name)
        if not d.is_dir() or not m:
            continue
        items = [
            it
            for f in sorted(d.rglob("*.json"))
            for it in _items(json.loads(f.read_text(encoding="utf-8")))
        ]
        out[m.group(1)] = {
            "preguntas": len(items),
            "ejecutables": sum(1 for it in items if it.get("type") in EJECUTABLES),
            "skills": len({it.get("skill_id") for it in items}),
        }
    return out


def contar_fichero_suelto(content: Path) -> list[str]:
    return sorted(p.name for p in (content / "_quarantine").glob("*.json"))


def inventariar(content: Path, tracks: list[dict[str, Any]]) -> dict[str, Any]:
    """Recuento por track construido y por skill, a partir de los ficheros."""
    owner: dict[str, str] = {}
    skills_de: dict[str, list[str]] = {}
    for t in tracks:
        skills_de[t["id"]] = [s["id"] for m in t["modules"] for s in m["skills"]]
        for sk in skills_de[t["id"]]:
            owner[sk] = t["id"]

    pregunta_skill: dict[str, Counter] = {t: Counter() for t in skills_de}
    ejec_skill: dict[str, Counter] = {t: Counter() for t in skills_de}
    codigo_skill: dict[str, Counter] = {t: Counter() for t in skills_de}
    reservadas: Counter = Counter()
    huerfanas = 0
    for qdir in sorted((content / "questions").iterdir()):
        if not qdir.is_dir():
            continue
        for f in sorted(qdir.rglob("*.json")):
            for it in _items(json.loads(f.read_text(encoding="utf-8"))):
                sk = it.get("skill_id", "")
                tid = owner.get(sk)
                if tid is None:
                    huerfanas += 1
                    continue
                pregunta_skill[tid][sk] += 1
                if it.get("type") in EJECUTABLES:
                    ejec_skill[tid][sk] += 1
                if it.get("type") in CON_CODIGO:
                    codigo_skill[tid][sk] += 1
                if it.get("pool") == MOCK_POOL:
                    reservadas[tid] += 1

    lecciones: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for tdir in sorted((content / "lessons").iterdir()):
        m = FILA_TRACK.match(tdir.name)
        if not tdir.is_dir() or not m:
            continue
        for f in sorted(tdir.glob("*.json")):
            lecciones[m.group(1)].append(json.loads(f.read_text(encoding="utf-8")))

    terminos: Counter = Counter()
    for f in sorted((content / "glossary").glob("track*.json")):
        m = FILA_TRACK.match(f.stem)
        if m:
            doc = json.loads(f.read_text(encoding="utf-8"))
            # Dos formas en el repo: {"track_id", "terms": [...]} y una lista plana.
            terminos[m.group(1)] = len(doc if isinstance(doc, list) else doc["terms"])

    leccion_por_skill: dict[str, dict[str, Any]] = {}
    for tid, ls in lecciones.items():
        for le in ls:
            leccion_por_skill[le["skill_id"]] = le

    return {
        "skills_de": skills_de,
        "pregunta_skill": pregunta_skill,
        "ejec_skill": ejec_skill,
        "codigo_skill": codigo_skill,
        "reservadas": reservadas,
        "huerfanas": huerfanas,
        "lecciones": lecciones,
        "terminos": terminos,
        "leccion_por_skill": leccion_por_skill,
    }


def _palabras(texto: str) -> int:
    return len(texto.split())


def fila_track(t: dict[str, Any], inv: dict[str, Any]) -> dict[str, Any]:
    tid = t["id"]
    skills = inv["skills_de"][tid]
    preg = inv["pregunta_skill"][tid]
    ejec = inv["ejec_skill"][tid]
    cod = inv["codigo_skill"][tid]
    ls = inv["lecciones"].get(tid, [])
    palabras = [_palabras(le.get("body_es", "")) for le in ls]
    detalle = []
    for sk in skills:
        le = inv["leccion_por_skill"].get(sk)
        detalle.append(
            {
                "skill": sk,
                "preguntas": preg[sk],
                "faltan_para_10": max(0, PREGUNTAS_FORMA - preg[sk]),
                "ejecutables": ejec[sk],
                "con_codigo": cod[sk],
                "leccion": le is not None,
                "palabras_leccion": _palabras(le.get("body_es", "")) if le else 0,
                "fuente": bool(le and le.get("source")),
            }
        )
    return {
        "id": tid,
        "nombre": t["name_es"],
        "estado": "construido",
        "certificacion": bool(t.get("certification")),
        "skills": len(skills),
        "preguntas": sum(preg.values()),
        "ejecutables": sum(ejec.values()),
        "con_codigo": sum(cod.values()),
        "reservadas": inv["reservadas"][tid],
        "lecciones": len(ls),
        "mediana_palabras": int(statistics.median(palabras)) if palabras else 0,
        "terminos": inv["terminos"][tid],
        "detalle": detalle,
    }


def recomendaciones(
    fila: dict[str, Any], cert_meta: dict[str, Any] | None
) -> list[str]:
    """Reglas explícitas. Cada texto dice qué regla lo ha disparado."""
    out: list[str] = []
    tid = fila["id"]
    if not fila["certificacion"] and fila["skills"] < SKILLS_FORMA:
        out.append(
            f"Forma ADR-54: faltan {SKILLS_FORMA - fila['skills']} skills para {SKILLS_FORMA}"
        )
    bajas = [d for d in fila["detalle"] if d["preguntas"] < PREGUNTAS_FORMA]
    if bajas:
        out.append(
            f"Skills con menos de {PREGUNTAS_FORMA} preguntas: {len(bajas)} (faltan {sum(d['faltan_para_10'] for d in bajas)})"
        )
    if tid in MATERIA_DE_CODIGO:
        if fila["ejecutables"] == 0:
            out.append("D3 crítico: materia de código con 0 ejecutables estrictos")
        out.append("Proyectos (43.6): 0 en el catálogo")
    if (
        fila["preguntas"]
        and fila["ejecutables"] / fila["preguntas"] < UMBRAL_EJECUTABLE
    ):
        out.append(
            f"D3: ejecutables {fila['ejecutables'] / fila['preguntas']:.1%} (< {UMBRAL_EJECUTABLE:.0%})"
        )
    if fila["terminos"] < fila["skills"]:
        out.append(
            f"Glosario: {fila['terminos']} términos para {fila['skills']} skills"
        )
    if fila["certificacion"] and cert_meta is not None:
        lx = cert_meta.get("preguntas_examen")
        if lx is None:
            out.append(
                "D6: examen sin número de preguntas publicado; reservado pendiente"
            )
        else:
            out.append(
                f"D6: mapa objetivo→skill pendiente; reservado {fila['reservadas']} de {2 * lx} (2 × {lx})"
            )
    return out


def en_forma(f: dict[str, Any]) -> bool:
    """ADR-54 por skill: 10 preguntas, ≥ 3 con código y 1 lección. Solo tracks de aprendizaje.

    Los términos no llevan `skill_id` en el repo, así que el término por skill no se
    comprueba aquí; el resumen lo dice.
    """
    if f["certificacion"] or f["skills"] < SKILLS_FORMA:
        return False
    return all(
        d["preguntas"] >= PREGUNTAS_FORMA
        and d["con_codigo"] >= CON_CODIGO_MIN
        and d["leccion"]
        for d in f["detalle"]
    )


def fila_plan(entrada: dict[str, Any], estado: str) -> dict[str, Any]:
    return {
        "id": entrada["id"],
        "nombre": entrada.get("nombre", entrada.get("codigo", entrada["id"])),
        "estado": estado,
        "certificacion": False,
        "skills": 0,
        "preguntas": 0,
        "ejecutables": 0,
        "con_codigo": 0,
        "reservadas": 0,
        "lecciones": 0,
        "mediana_palabras": 0,
        "terminos": 0,
        "detalle": [],
    }


def construir(content: Path, metas: Path) -> dict[str, Any]:
    tracks = cargar_tracks(content)
    plan_tracks, plan_certs = cargar_plan(metas)
    cert_meta = {c["id"]: c for c in plan_certs}
    inv = inventariar(content, tracks)
    cuarentena = contar_cuarentena(content)
    construidos = {t["id"] for t in tracks}

    filas: dict[str, dict[str, Any]] = {}
    for t in tracks:
        filas[t["id"]] = fila_track(t, inv)
    for tid, q in cuarentena.items():
        f = fila_plan({"id": tid, "nombre": "en cuarentena"}, "cuarentena")
        f.update(
            preguntas=q["preguntas"],
            ejecutables=q["ejecutables"],
            con_codigo=q["ejecutables"],
            skills=q["skills"],
        )
        filas[tid] = f
    for entrada in plan_tracks + plan_certs:
        if entrada["id"] not in filas:
            filas[entrada["id"]] = fila_plan(entrada, "planificado")

    orden = sorted(filas)
    plan_completo = [filas[k] for k in orden]
    for f in plan_completo:
        f["recomendaciones"] = (
            recomendaciones(f, cert_meta.get(f["id"]))
            if f["estado"] == "construido"
            else []
        )

    construidas = [f for f in plan_completo if f["estado"] == "construido"]
    return {
        "filas": plan_completo,
        "totales": {
            "plan": len(plan_completo),
            "construidos": len(construidas),
            "cuarentena": len(cuarentena),
            "planificados": sum(
                1 for f in plan_completo if f["estado"] == "planificado"
            ),
            "preguntas": sum(f["preguntas"] for f in construidas),
            "lecciones": sum(f["lecciones"] for f in construidas),
            "terminos": sum(f["terminos"] for f in construidas),
            "sin_ejecutable": sum(1 for f in construidas if f["ejecutables"] == 0),
            "en_forma_adr54": sum(1 for f in construidas if en_forma(f)),
            "aprendizaje_construidos": sum(
                1 for f in construidas if not f["certificacion"]
            ),
            "huerfanas": inv["huerfanas"],
            "sueltos_cuarentena": contar_fichero_suelto(content),
        },
        "construidos": sorted(construidos),
    }


def ejecutar_guardas() -> list[dict[str, Any]]:
    out = []
    for g in GUARDAS:
        p = subprocess.run(
            [sys.executable, str(ROOT / g)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        ultima = (p.stdout.strip().splitlines() or [""])[-1]
        out.append({"guarda": g, "rc": p.returncode, "ultima_linea": ultima})
    return out


def _md_tabla(filas: list[dict[str, Any]]) -> str:
    cab = "| Track | Nombre | Estado | Skills | Preguntas | Ejecutables | Con código | Lecciones | Mediana palabras/lección | Términos | Reservadas |"
    sep = "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"
    cuerpo = [
        f"| {f['id']} | {f['nombre']} | {f['estado']} | {f['skills']} | {f['preguntas']} | {f['ejecutables']} | {f['con_codigo']} | {f['lecciones']} | {f['mediana_palabras']} | {f['terminos']} | {f['reservadas']} |"
        for f in filas
    ]
    return "\n".join([cab, sep, *cuerpo])


def escribir(
    res: dict[str, Any], out: Path, fecha: str, guardas: list[dict[str, Any]]
) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "tracks").mkdir(exist_ok=True)
    t = res["totales"]
    lineas = [
        f"# Resumen de la auditoría de tracks ({fecha})",
        "",
        "Generado por `scripts/audit_tracks.py` desde `content/` y `scripts/metas_catalogo.json`.",
        "Sin modelos: cada recomendación de las fichas sale de una regla de ese script.",
        "",
        f"Plan: {t['plan']} tracks · construidos: {t['construidos']} · cuarentena: {t['cuarentena']} · planificados: {t['planificados']}.",
        f"Construidos: {t['preguntas']} preguntas · {t['lecciones']} lecciones · {t['terminos']} términos.",
        f"Construidos sin ningún ejecutable estricto: {t['sin_ejecutable']} de {t['construidos']}.",
        f"En la forma ADR-54 de aprendizaje (≥ 32 skills; por skill ≥ 10 preguntas, ≥ 3 con código y 1 lección): {t['en_forma_adr54']} de {t['aprendizaje_construidos']} construidos de aprendizaje (los términos no llevan skill_id y no se comprueban por skill).",
        f"Preguntas huérfanas (skill que no pertenece a ningún track): {t['huerfanas']}.",
        f"Ficheros sueltos en `_quarantine/` (no cuentan): {', '.join(t['sueltos_cuarentena']) or 'ninguno'}.",
        "",
        "«Ejecutable» = `fill_blank_exec`, `fix_bug`, `sql_exec`, `js_exec`, `interactive`.",
        "«Con código» = eso más `code_output`.",
        "",
        "## Tabla",
        "",
        _md_tabla(res["filas"]),
        "",
        "## Guardas existentes",
        "",
    ]
    for g in guardas:
        lineas.append(f"- `{g['guarda']}`: rc={g['rc']} · {g['ultima_linea']}")
    lineas += ["", "Ninguna guarda da veredicto por track; su resultado es global.", ""]
    (out / "resumen.md").write_text("\n".join(lineas), encoding="utf-8")

    for f in res["filas"]:
        if f["estado"] != "construido":
            continue
        ficha = [
            f"# {f['id']} — {f['nombre']}",
            "",
            f"Estado: {f['estado']} · skills {f['skills']} · preguntas {f['preguntas']} · ejecutables {f['ejecutables']} · con código {f['con_codigo']} · lecciones {f['lecciones']} · términos {f['terminos']}",
            "",
            "## Recomendaciones (regla disparada)",
            "",
        ]
        ficha += [f"- {r}" for r in f["recomendaciones"]] or [
            "- Ninguna regla se dispara."
        ]
        ficha += [
            "",
            "## Skills",
            "",
            "| Skill | Preguntas | Faltan para 10 | Ejecutables | Con código | Lección | Palabras | Fuente |",
            "|---|---:|---:|---:|---:|:---:|---:|:---:|",
        ]
        ficha += [
            f"| {d['skill']} | {d['preguntas']} | {d['faltan_para_10']} | {d['ejecutables']} | {d['con_codigo']} | {'sí' if d['leccion'] else 'no'} | {d['palabras_leccion']} | {'sí' if d['fuente'] else 'no'} |"
            for d in f["detalle"]
        ]
        (out / "tracks" / f"{f['id']}.md").write_text(
            "\n".join(ficha) + "\n", encoding="utf-8"
        )

    (out / "inventario.json").write_text(
        json.dumps(
            {"fecha": fecha, "totales": t, "filas": res["filas"], "guardas": guardas},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fecha", default=datetime.now(tz=UTC).date().isoformat())
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--content", type=Path, default=CONTENT)
    ap.add_argument("--metas", type=Path, default=METAS)
    args = ap.parse_args(argv)
    out = args.out or (SALIDA / args.fecha)
    res = construir(args.content, args.metas)
    guardas = ejecutar_guardas() if args.content == CONTENT else []
    escribir(res, out, args.fecha, guardas)
    t = res["totales"]
    print(
        f"preguntas {t['preguntas']} · lecciones {t['lecciones']} · términos {t['terminos']} · sin ejecutable {t['sin_ejecutable']}/{t['construidos']}"
    )
    print(f"escrito en {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
