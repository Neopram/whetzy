"""Cobertura del catálogo frente al plan ADR-54 (2026-10-01).

ADR-54 sustituye el suelo (50 skills · 800 preguntas) y el «ideal por temario» de
ADR-53 por una forma única, con las metas en `scripts/metas_catalogo.json`:

* **Track de aprendizaje**: 32 skills (8 módulos × 4) · 10 preguntas por skill
  (320 por track), ≥ 3 de ellas ejecutables donde el navegador ejecute · 1 lección
  y 1 término por skill. Nada se borra: lo que pase de esa forma se conserva.
* **Certificación**: 100 % de objetivos oficiales · práctica ≥ máx(300, 3 × L) ·
  banco reservado de simulacro (`"pool": "simulacro"`) = 2 × L, con L = preguntas
  del examen. Sin L publicada, las reservadas quedan «pendiente».

Solo cuentan para lo pendiente los tracks ya construidos: los nuevos entran por la
demanda medida (niveles A/B/C de ADR-53), con la misma forma.

Uso::

    python scripts/catalog_coverage.py            # tabla por track y totales
    python scripts/catalog_coverage.py --json     # lo mismo, en JSON
    python scripts/catalog_coverage.py --check    # solo valida metas ↔ catálogo (exit 1 si falla)

Nada de aquí escribe ficheros del proyecto.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
METAS = Path(__file__).resolve().parent / "metas_catalogo.json"
MOCK_POOL = "simulacro"


def load_metas(path: Path = METAS) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_catalog(content: Path = CONTENT, exec_types: frozenset[str] | None = None) -> dict[str, dict[str, Any]]:
    """Recuento real por track y por skill: práctica, ejecutables, reservadas, lecciones, términos."""
    if exec_types is None:
        exec_types = frozenset(load_metas()["tipos_ejecutables"]["tipos"])
    data = json.loads((content / "curriculum" / "tracks.json").read_text(encoding="utf-8"))
    tracks = next(iter(data.values()))
    out: dict[str, dict[str, Any]] = {}
    owner: dict[str, str] = {}
    for t in tracks:
        skills = [s["id"] for m in t["modules"] for s in m["skills"]]
        for sk in skills:
            owner[sk] = t["id"]
        out[t["id"]] = {
            "nombre": t["name_es"],
            "certificacion": bool(t.get("certification")),
            "skill_ids": skills,
            "practica_por_skill": dict.fromkeys(skills, 0),
            "ejecutables_por_skill": dict.fromkeys(skills, 0),
            "reservadas": 0,
            "lecciones": set(),
            "terminos": 0,
        }
    for qdir in sorted((content / "questions").iterdir()):
        m = re.match(r"(track\d+)", qdir.name)
        if not m or not qdir.is_dir():
            continue
        for f in sorted(qdir.rglob("*.json")):
            doc = json.loads(f.read_text(encoding="utf-8"))
            for it in doc if isinstance(doc, list) else doc.get("questions", []):
                tid = owner.get(it.get("skill_id", ""), m.group(1))
                row = out.get(tid)
                if row is None:
                    continue
                if it.get("pool") == MOCK_POOL:
                    row["reservadas"] += 1
                    continue
                sk = it.get("skill_id")
                if sk in row["practica_por_skill"]:
                    row["practica_por_skill"][sk] += 1
                    if it.get("type") in exec_types:
                        row["ejecutables_por_skill"][sk] += 1
    for tid, row in out.items():
        ldir = content / "lessons" / tid
        if ldir.is_dir():
            for f in ldir.rglob("*.json"):
                sk = json.loads(f.read_text(encoding="utf-8")).get("skill_id")
                if sk in row["practica_por_skill"]:
                    row["lecciones"].add(sk)
        gfile = content / "glossary" / f"{tid}.json"
        if gfile.is_file():
            # Misma forma doble que cuenta project_snapshot.py: lista suelta o {"terms": [...]}.
            payload = json.loads(gfile.read_text(encoding="utf-8"))
            terms = payload if isinstance(payload, list) else payload.get("terms", payload.get("entries", []))
            row["terminos"] = len(terms)
    return out


def tier(entry: dict[str, Any], metas: dict[str, Any]) -> str:
    if entry.get("prioridad"):
        return str(entry["prioridad"])
    d = entry.get("demanda")
    if not d:
        return "C"
    if d["pct"] >= metas["demanda"]["nivel_A_min_pct"]:
        return "A"
    if d["pct"] >= metas["demanda"]["nivel_B_min_pct"]:
        return "B"
    return "C"


def track_gap(real: dict[str, Any], forma: dict[str, Any], exenta: str | None = None) -> dict[str, Any]:
    """Lo que le falta a un track para la forma 32 × 10. Nunca negativo: nada se borra."""
    practica = real["practica_por_skill"]
    ejecutables = real["ejecutables_por_skill"]
    n = len(practica)
    nuevas = max(0, forma["skills"] - n)
    q_skill = forma["preguntas_por_skill"]
    sin_leccion = sum(1 for sk in practica if sk not in real["lecciones"])
    total_skills = max(n, forma["skills"])
    if exenta:
        ejec = "exento"
    elif not any(ejecutables.values()):
        ejec = "sin medir"
    else:
        ok = sum(1 for sk in practica if ejecutables[sk] >= forma["ejecutables_min_por_skill"])
        ejec = f"{ok}/{n}"
    return {
        "skills": n,
        "skills_pendientes": nuevas,
        "preguntas_pendientes": sum(max(0, q_skill - q) for q in practica.values()) + nuevas * q_skill,
        "lecciones_pendientes": sin_leccion + nuevas * forma["lecciones_por_skill"],
        "terminos_pendientes": max(0, total_skills * forma["terminos_por_skill"] - real["terminos"]),
        "skills_con_ejecutables": ejec,
    }


def cert_targets(exam_len: int | None, cfg: dict[str, Any]) -> dict[str, Any]:
    """Práctica ≥ máx(300, 3L); reservadas = 2L, o «pendiente» sin L publicada."""
    if exam_len is None:
        return {"practica": cfg["practica_min"], "reservadas": "pendiente"}
    return {
        "practica": max(cfg["practica_min"], cfg["practica_factor_examen"] * exam_len),
        "reservadas": cfg["reservadas_factor_examen"] * exam_len,
    }


def validate(metas: dict[str, Any], catalog: dict[str, dict[str, Any]]) -> list[str]:
    """Metas y catálogo tienen que describir el mismo mundo."""
    problems: list[str] = []
    ids = [t["id"] for t in metas["tracks"]]
    cert_ids = [c["id"] for c in metas["certificaciones"]]
    for dup in {i for i in ids + cert_ids if (ids + cert_ids).count(i) > 1}:
        problems.append(f"{dup}: aparece dos veces en metas")
    nodes = metas["roadmap"]["nodos"]
    for t in metas["tracks"]:
        for r in t.get("referencia", []):
            if r["roadmap"] not in nodes:
                problems.append(f"{t['id']}: roadmap '{r['roadmap']}' sin recuento en metas.roadmap.nodos")
        if not t.get("referencia") and not t.get("pendiente"):
            problems.append(f"{t['id']}: sin referencia y sin nota 'pendiente'")
        if "ejecucion_exenta" in t and not str(t["ejecucion_exenta"]).strip():
            problems.append(f"{t['id']}: 'ejecucion_exenta' sin razón escrita")
        built = t["estado"] == "construido"
        if built and t["id"] not in catalog:
            problems.append(f"{t['id']}: marcado 'construido' y no está en tracks.json")
        if not built and t["id"] in catalog:
            problems.append(f"{t['id']}: marcado '{t['estado']}' pero ya está en tracks.json")
        if t["id"] in catalog and catalog[t["id"]]["certificacion"]:
            problems.append(f"{t['id']}: es certificación en tracks.json y está en metas.tracks")
    shares: Counter[str] = Counter()
    for t in metas["tracks"]:
        for r in t.get("referencia", []):
            shares[r["roadmap"]] += r["parte"]
    for slug, share in shares.items():
        if share > 1.0001:
            problems.append(f"roadmap '{slug}': repartido más de una vez ({share:.4f})")
    for tid, row in catalog.items():
        if row["certificacion"] and tid not in cert_ids:
            problems.append(f"{tid}: certificación de tracks.json sin fila en metas.certificaciones")
        if not row["certificacion"] and tid not in ids:
            problems.append(f"{tid}: track de tracks.json sin fila en metas.tracks")
    for c in metas["certificaciones"]:
        if c["id"] not in catalog:
            problems.append(f"{c['id']}: certificación en metas y no en tracks.json")
        if not c.get("fuente") or not c.get("leido"):
            problems.append(f"{c['id']}: sin fuente o fecha de lectura")
    return problems


def measure(metas: dict[str, Any], catalog: dict[str, dict[str, Any]]) -> dict[str, Any]:
    forma = metas["forma_track"]
    rows = []
    for t in metas["tracks"]:
        built = t["estado"] == "construido"
        row = {"id": t["id"], "nombre": t["nombre"], "estado": t["estado"], "nivel": tier(t, metas)}
        if built:
            real = catalog[t["id"]]
            row.update(track_gap(real, forma, t.get("ejecucion_exenta")))
            row["preguntas"] = sum(real["practica_por_skill"].values())
        rows.append(row)
    built_rows = [r for r in rows if r["estado"] == "construido"]
    totals: dict[str, Any] = {
        "tracks_plan": len(rows),
        "tracks_construidos": len(built_rows),
        "tracks_en_forma": sum(
            1 for r in built_rows
            if not (r["skills_pendientes"] or r["preguntas_pendientes"] or r["lecciones_pendientes"] or r["terminos_pendientes"])
        ),
    }
    for k in ("skills_pendientes", "preguntas_pendientes", "lecciones_pendientes", "terminos_pendientes"):
        totals[k] = sum(r[k] for r in built_rows)
    totals["ejecutables_sin_medir"] = [r["id"] for r in built_rows if r["skills_con_ejecutables"] == "sin medir"]

    cfg = metas["certificacion"]
    certs = []
    for e in metas["certificaciones"]:
        real = catalog[e["id"]]
        practica = sum(real["practica_por_skill"].values())
        meta = cert_targets(e.get("preguntas_examen"), cfg)
        reservadas_pend = (
            max(0, meta["reservadas"] - real["reservadas"]) if isinstance(meta["reservadas"], int) else "pendiente"
        )
        obj = e.get("objetivos")
        certs.append({
            "id": e["id"],
            "codigo": e["codigo"],
            "objetivos": obj,
            "skills": len(real["practica_por_skill"]),
            # Proxy: una skill por objetivo. El mapa objetivo → skill no existe todavía.
            "objetivos_cubiertos_proxy": (min(len(real["practica_por_skill"]), obj), obj) if obj else None,
            "preguntas_examen": e.get("preguntas_examen"),
            "practica": practica,
            "practica_meta": meta["practica"],
            "practica_pendiente": max(0, meta["practica"] - practica),
            "reservadas": real["reservadas"],
            "reservadas_meta": meta["reservadas"],
            "reservadas_pendientes": reservadas_pend,
        })
    totals["cert_practica_pendiente"] = sum(c["practica_pendiente"] for c in certs)
    totals["cert_reservadas_pendientes"] = sum(
        c["reservadas_pendientes"] for c in certs if isinstance(c["reservadas_pendientes"], int)
    )
    totals["cert_sin_longitud"] = [c["id"] for c in certs if c["preguntas_examen"] is None]
    totals["cert_sin_objetivos"] = [c["id"] for c in certs if not c["objetivos"]]
    total_q = totals["preguntas_pendientes"] + totals["cert_practica_pendiente"] + totals["cert_reservadas_pendientes"]
    totals["preguntas_pendientes_total"] = total_q
    ritmo = metas["sesion"]["preguntas_por_sesion"]
    totals["sesiones_estimadas"] = math.ceil(total_q / ritmo) if total_q else 0
    return {"tracks": rows, "totales": totals, "certificaciones": certs}


def _n(v: int) -> str:
    return f"{v:,}".replace(",", ".")


def render(result: dict[str, Any], ritmo: int) -> str:
    out = ["Tracks de aprendizaje (ADR-54: 32 skills × 10 preguntas, 1 lección y 1 término por skill)", ""]
    out.append(f"{'id':8} {'nivel':5} {'estado':11} {'skills':>6} {'Q':>6} {'+skills':>7} {'+Q':>5} {'+lecc':>5} {'+térm':>5} {'skills ≥3 ejec':>14}")
    for r in result["tracks"]:
        if r["estado"] != "construido":
            out.append(f"{r['id']:8} {r['nivel']:5} {r['estado']:11} {'—':>6}")
            continue
        out.append(
            f"{r['id']:8} {r['nivel']:5} {r['estado']:11} {r['skills']:6} {r['preguntas']:6} {r['skills_pendientes']:7} "
            f"{r['preguntas_pendientes']:5} {r['lecciones_pendientes']:5} {r['terminos_pendientes']:5} {r['skills_con_ejecutables']:>14}"
        )
    t = result["totales"]
    out += [
        "",
        f"Tracks del plan: {t['tracks_plan']} · construidos: {t['tracks_construidos']} · ya en la forma: {t['tracks_en_forma']}",
        "Pendiente en tracks construidos (los planificados entran por demanda, no cuentan aquí):",
        (
            f"  skills {_n(t['skills_pendientes'])} · lecciones {_n(t['lecciones_pendientes'])} · "
            f"términos {_n(t['terminos_pendientes'])} · preguntas {_n(t['preguntas_pendientes'])}"
        ),
        f"  ejecutables sin medir (sin preguntas ejecutables ni exención escrita): {', '.join(t['ejecutables_sin_medir']) or '—'}",
        "",
        "Certificaciones (práctica ≥ máx(300, 3 × L) · reservadas = 2 × L)",
        "",
        f"{'id':8} {'código':11} {'obj':>4} {'skills':>6} {'L':>4} {'práctica':>8} {'meta':>5} {'+práct':>6} {'reserv':>6} {'meta':>9} {'+reserv':>9}",
    ]
    for c in result["certificaciones"]:
        out.append(
            f"{c['id']:8} {c['codigo']:11} {c['objetivos'] or '—'!s:>4} {c['skills']:6} {c['preguntas_examen'] or '—'!s:>4} "
            f"{c['practica']:8} {c['practica_meta']:5} {c['practica_pendiente']:6} {c['reservadas']:6} "
            f"{c['reservadas_meta']!s:>9} {c['reservadas_pendientes']!s:>9}"
        )
    out += [
        "",
        f"Práctica de certificación pendiente: {_n(t['cert_practica_pendiente'])}",
        (
            f"Reservadas pendientes: {_n(t['cert_reservadas_pendientes'])} "
            f"(sin contar {', '.join(t['cert_sin_longitud']) or '—'}: examen sin número de preguntas publicado)"
        ),
        (
            f"Objetivos sin contar: {', '.join(t['cert_sin_objetivos']) or '—'} · cobertura de objetivos medida con el proxy "
            "«una skill por objetivo» (no hay mapa objetivo → skill)"
        ),
        "",
        (
            f"Total de preguntas pendientes: {_n(t['preguntas_pendientes_total'])} "
            f"≈ {t['sesiones_estimadas']} sesiones a {ritmo} preguntas/sesión (estimación)"
        ),
    ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    metas = load_metas()
    catalog = load_catalog(exec_types=frozenset(metas["tipos_ejecutables"]["tipos"]))
    problems = validate(metas, catalog)
    if problems:
        print("[catalog_coverage] FAIL — metas_catalogo.json no describe el catálogo real:")
        for p in problems:
            print(f"  - {p}")
        return 1
    if args.check:
        print(f"[catalog_coverage] PASS — {len(metas['tracks'])} tracks y {len(metas['certificaciones'])} certificaciones en metas ↔ tracks.json")
        return 0
    result = measure(metas, catalog)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=sorted))
    else:
        print(render(result, metas["sesion"]["preguntas_por_sesion"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
