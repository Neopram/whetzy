"""Cobertura del catálogo frente al plan ADR-53 (2026-09-30).

Por qué existe: ADR-46 medía el catálogo contra una cifra fija (≥ 50 cursos por
track = 200 skills · 3.000 preguntas) que ningún temario ni competidor respalda.
ADR-53 la sustituye por dos metas medibles por track, con los denominadores en
`scripts/metas_adr53.json` (cada cifra externa con URL y fecha):

* **Suelo** (competitivo): 50 skills · 800 preguntas (≥ 16 por skill) · 1 lección
  y 1 término por skill.
* **Ideal** (cobertura): tantas skills como nodos del temario de referencia
  asignados al track (roadmap.sh), nunca menos que el suelo; 20 preguntas por skill.

Las certificaciones se miden aparte: skills frente a objetivos oficiales,
práctica por skill y **banco de simulacro reservado** de 6 × la longitud del
examen (preguntas con `"pool": "simulacro"`, que no salen en práctica ni repaso).

Uso::

    python scripts/catalog_coverage.py            # tabla por track y totales
    python scripts/catalog_coverage.py --json     # lo mismo, en JSON
    python scripts/catalog_coverage.py --check    # solo valida metas ↔ catálogo (exit 1 si falla)

Nada de aquí escribe ficheros del proyecto.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
METAS = Path(__file__).resolve().parent / "metas_adr53.json"
MOCK_POOL = "simulacro"


def load_metas(path: Path = METAS) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_catalog(content: Path = CONTENT) -> dict[str, dict[str, Any]]:
    """Recuento real por track: skills, preguntas, lecciones, términos, reservadas."""
    data = json.loads((content / "curriculum" / "tracks.json").read_text(encoding="utf-8"))
    tracks = next(iter(data.values()))
    out: dict[str, dict[str, Any]] = {}
    for t in tracks:
        skills = [s["id"] for m in t["modules"] for s in m["skills"]]
        out[t["id"]] = {
            "nombre": t["name_es"],
            "certificacion": bool(t.get("certification")),
            "skills": len(skills),
            "skill_ids": set(skills),
            "preguntas": 0,
            "reservadas": 0,
            "lecciones": 0,
            "terminos": 0,
        }
    q = Counter()
    reserved = Counter()
    for qdir in sorted((content / "questions").iterdir()):
        m = re.match(r"(track\d+)", qdir.name)
        if not m or not qdir.is_dir():
            continue
        for f in sorted(qdir.rglob("*.json")):
            doc = json.loads(f.read_text(encoding="utf-8"))
            items = doc if isinstance(doc, list) else doc.get("questions", [])
            q[m.group(1)] += len(items)
            reserved[m.group(1)] += sum(1 for it in items if it.get("pool") == MOCK_POOL)
    for tid, row in out.items():
        row["preguntas"] = q[tid]
        row["reservadas"] = reserved[tid]
        ldir = content / "lessons" / tid
        if ldir.is_dir():
            covered = set()
            for f in ldir.rglob("*.json"):
                sk = json.loads(f.read_text(encoding="utf-8")).get("skill_id")
                if sk in row["skill_ids"]:
                    covered.add(sk)
            row["lecciones"] = len(covered)
        gfile = content / "glossary" / f"{tid}.json"
        if gfile.is_file():
            # Misma forma doble que cuenta project_snapshot.py: lista suelta o {"terms": [...]}.
            payload = json.loads(gfile.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                row["terminos"] = len(payload)
            else:
                row["terminos"] = len(payload.get("terms", payload.get("entries", [])))
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


def ideal_skills(entry: dict[str, Any], metas: dict[str, Any]) -> tuple[int, bool]:
    """(skills ideales, tiene_referencia). Sin referencia, el ideal es el suelo."""
    floor = metas["ideal"]["minimo_skills"]
    nodes = metas["roadmap"]["nodos"]
    if not entry.get("referencia"):
        return floor, False
    total = sum(nodes[r["roadmap"]] * r["parte"] for r in entry["referencia"])
    return max(floor, round(total)), True


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
    s = metas["suelo"]
    i = metas["ideal"]
    rows = []
    for t in metas["tracks"]:
        real = catalog.get(t["id"], {"skills": 0, "preguntas": 0, "lecciones": 0, "terminos": 0})
        isk, has_ref = ideal_skills(t, metas)
        iq = isk * i["preguntas_por_skill"]
        rows.append({
            "id": t["id"],
            "nombre": t["nombre"],
            "estado": t["estado"],
            "nivel": tier(t, metas),
            "skills": real["skills"],
            "preguntas": real["preguntas"],
            "q_por_skill": round(real["preguntas"] / real["skills"], 1) if real["skills"] else 0.0,
            "lecciones": real["lecciones"],
            "terminos": real["terminos"],
            "suelo_ok": real["skills"] >= s["skills"] and real["preguntas"] >= s["preguntas"],
            "ideal_skills": isk,
            "ideal_preguntas": iq,
            "ideal_con_referencia": has_ref,
            "suelo_skills_pct": min(real["skills"], s["skills"]) / s["skills"],
            "suelo_preguntas_pct": min(real["preguntas"], s["preguntas"]) / s["preguntas"],
            "ideal_skills_pct": min(real["skills"], isk) / isk,
            "ideal_preguntas_pct": min(real["preguntas"], iq) / iq,
        })
    n = len(rows)
    totals = {
        "tracks_plan": n,
        "tracks_construidos": sum(1 for r in rows if r["estado"] == "construido"),
        "tracks_en_suelo": sum(1 for r in rows if r["suelo_ok"]),
        "suelo_skills": (sum(min(r["skills"], s["skills"]) for r in rows), n * s["skills"]),
        "suelo_preguntas": (sum(min(r["preguntas"], s["preguntas"]) for r in rows), n * s["preguntas"]),
        "ideal_skills": (sum(min(r["skills"], r["ideal_skills"]) for r in rows), sum(r["ideal_skills"] for r in rows)),
        "ideal_preguntas": (sum(min(r["preguntas"], r["ideal_preguntas"]) for r in rows), sum(r["ideal_preguntas"] for r in rows)),
        "ideal_sin_referencia": [r["id"] for r in rows if not r["ideal_con_referencia"]],
    }
    c = metas["certificacion"]
    certs = []
    for e in metas["certificaciones"]:
        real = catalog.get(e["id"], {"skills": 0, "preguntas": 0, "reservadas": 0})
        obj = e.get("objetivos")
        L = e.get("preguntas_examen")
        certs.append({
            "id": e["id"],
            "codigo": e["codigo"],
            "objetivos": obj,
            "skills": real["skills"],
            "preguntas": real["preguntas"],
            "q_por_skill": round(real["preguntas"] / real["skills"], 1) if real["skills"] else 0.0,
            "suelo_skills": obj * c["suelo_skills_por_objetivo"] if obj else None,
            "ideal_skills": obj * c["ideal_skills_por_objetivo"] if obj else None,
            "preguntas_examen": L,
            "reservadas_meta": L * c["formas_de_simulacro_reservadas"] if L else None,
            "reservadas": real.get("reservadas", 0),
        })
    known = [x for x in certs if x["suelo_skills"]]
    totals["cert_practica_suelo"] = (
        sum(min(x["preguntas"], x["suelo_skills"] * c["suelo_preguntas_por_skill"]) for x in known),
        sum(x["suelo_skills"] * c["suelo_preguntas_por_skill"] for x in known),
    )
    totals["cert_practica_ideal"] = (
        sum(min(x["preguntas"], x["ideal_skills"] * c["ideal_preguntas_por_skill"]) for x in known),
        sum(x["ideal_skills"] * c["ideal_preguntas_por_skill"] for x in known),
    )
    with_len = [x for x in certs if x["reservadas_meta"]]
    totals["cert_reservadas"] = (
        sum(min(x["reservadas"], x["reservadas_meta"]) for x in with_len),
        sum(x["reservadas_meta"] for x in with_len),
    )
    totals["cert_sin_objetivos"] = [x["id"] for x in certs if not x["objetivos"]]
    totals["cert_sin_longitud"] = [x["id"] for x in certs if not x["preguntas_examen"]]
    return {"tracks": rows, "totales": totals, "certificaciones": certs}


def _pct(pair: tuple[int, int]) -> str:
    a, b = pair
    return f"{a:,}/{b:,} ({a / b:.1%})".replace(",", ".")


def render(result: dict[str, Any]) -> str:
    out = ["Tracks de aprendizaje (ADR-53)", ""]
    out.append(f"{'id':8} {'nivel':5} {'estado':11} {'skills':>6} {'Q':>6} {'Q/sk':>5} {'lecc':>5} {'suelo':>5} {'ideal sk':>8} {'ideal Q':>7}")
    for r in result["tracks"]:
        ref = "" if r["ideal_con_referencia"] else "*"
        out.append(
            f"{r['id']:8} {r['nivel']:5} {r['estado']:11} {r['skills']:6} {r['preguntas']:6} {r['q_por_skill']:5} "
            f"{r['lecciones']:5} {'sí' if r['suelo_ok'] else 'no':>5} {str(r['ideal_skills']) + ref:>8} {r['ideal_preguntas']:7}"
        )
    t = result["totales"]
    out += [
        "",
        "* sin temario de referencia todavía: el ideal es el suelo (fila 37.1)",
        "",
        f"Tracks del plan: {t['tracks_plan']} · construidos: {t['tracks_construidos']} · en el suelo: {t['tracks_en_suelo']}",
        f"Suelo, skills:     {_pct(t['suelo_skills'])}",
        f"Suelo, preguntas:  {_pct(t['suelo_preguntas'])}",
        f"Ideal, skills:     {_pct(t['ideal_skills'])}",
        f"Ideal, preguntas:  {_pct(t['ideal_preguntas'])}",
        "",
        "Certificaciones",
        "",
        f"{'id':8} {'código':11} {'obj':>4} {'skills':>6} {'Q':>5} {'Q/sk':>5} {'suelo sk':>8} {'ideal sk':>8} {'reserva meta':>12} {'reservadas':>10}",
    ]
    for c in result["certificaciones"]:
        out.append(
            f"{c['id']:8} {c['codigo']:11} {c['objetivos'] or '—'!s:>4} {c['skills']:6} {c['preguntas']:5} {c['q_por_skill']:5} "
            f"{c['suelo_skills'] or '—'!s:>8} {c['ideal_skills'] or '—'!s:>8} {c['reservadas_meta'] or '—'!s:>12} {c['reservadas']:10}"
        )
    out += [
        "",
        f"Práctica, suelo (15 Q × objetivo):  {_pct(t['cert_practica_suelo'])}",
        f"Práctica, ideal (20 Q × 2 skills/objetivo): {_pct(t['cert_practica_ideal'])}",
        f"Banco de simulacro reservado (6 × examen): {_pct(t['cert_reservadas'])}",
        (
            f"Sin objetivos contados: {', '.join(t['cert_sin_objetivos']) or '—'} · "
            f"sin longitud de examen publicada: {', '.join(t['cert_sin_longitud']) or '—'}"
        ),
    ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    metas = load_metas()
    catalog = load_catalog()
    problems = validate(metas, catalog)
    if problems:
        print("[catalog_coverage] FAIL — metas_adr53.json no describe el catálogo real:")
        for p in problems:
            print(f"  - {p}")
        return 1
    if args.check:
        print(f"[catalog_coverage] PASS — {len(metas['tracks'])} tracks y {len(metas['certificaciones'])} certificaciones en metas ↔ tracks.json")
        return 0
    result = measure(metas, catalog)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
