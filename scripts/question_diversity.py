"""Guarda de diversidad del banco de preguntas (ledger 35.0, ADR-42).

Por qué existe: el primer intento de la serie 25 (2026-09-19) generó 800
preguntas para track24/25 con **14 enunciados distintos por track** (3,5 %),
opciones de una sola palabra en el 94 % de los casos y 131 `*_exec` sin código.
Pasaron `check_question_bank.py` porque este solo miraba forma, no contenido.
ADR-42 exige esta guarda antes de escribir una sola pregunta nueva.

Métricas por track (ADR-42):

* ``distinct_ratio``      enunciados distintos (ES, normalizados) / total   ≥ 0,90
* ``one_word_ratio``      opciones de una sola palabra / opciones           ≤ 0,40
* ``exec_without_code``   `*_exec` sin código en el enunciado ni en `code_*`  = 0
* ``source_not_indexed``  preguntas cuya URL de `source` no está en
                          `content/sources/index.json`                       = 0

**Trinquete**, como la guarda `.tsx`↔`.module.css`: medido el 2026-09-25, el banco
vivo no cumple todo ADR-42. Seis tracks superan el 40 % de opciones de una
palabra, track13 tiene un 87,9 % de enunciados distintos, y `index.json` tiene 10
entradas frente a 6.305 preguntas: el 62 % no lleva ninguna URL. Aplicar los
umbrales tal cual pondría en rojo todo el banco, y una puerta siempre roja se
acaba saltando. Por eso:

* un track **sin línea base** (uno nuevo, o track24/25 si salen de la
  cuarentena) cumple ADR-42 **al pie de la letra**;
* un track **con línea base** no puede empeorar ninguna métrica respecto a su
  base. En la práctica, cada pregunta nueva tiene que ser distinta, traer código
  si es `*_exec` y citar una fuente indexada.

La línea base la escribe este script (``--write-baseline``), nunca una persona:
`scripts/question_diversity_baseline.json`. Solo debe regenerarse cuando un track
**mejora** y se quiere fijar la mejora. Regenerarla para tapar un empeoramiento
es justo lo que la guarda impide, y el diff lo delata.

Uso::

    python scripts/question_diversity.py                  # banco vivo
    python scripts/question_diversity.py --root content/_quarantine
    python scripts/question_diversity.py --write-baseline
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content" / "questions"
INDEX = ROOT / "content" / "sources" / "index.json"
BASELINE = Path(__file__).resolve().parent / "question_diversity_baseline.json"

MIN_DISTINCT = 0.90
MAX_ONE_WORD = 0.40
_EPS = 1e-9
_URL = re.compile(r"https?://[^\s)\]>\"']+")


def _norm(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _has_code(q: dict[str, Any]) -> bool:
    return bool(q.get("code_es") or q.get("code_en")) or "```" in (q.get("question_es") or "")


def indexed_urls(index_path: Path = INDEX) -> list[str]:
    data = json.loads(index_path.read_text(encoding="utf-8"))
    # `aliases`: la URL donde se publica la misma fuente verificada (35.4).
    return [str(u).rstrip("/") for s in data for u in [s["url"], *s.get("aliases", [])]]


def _source_indexed(q: dict[str, Any], urls: list[str]) -> bool:
    for found in _URL.findall(q.get("source") or ""):
        u = found.rstrip("/.,;")
        if any(u == x or u.startswith(x + "/") for x in urls):
            return True
    return False


def track_of(path: Path) -> str:
    """`track08_aws_clf_c02` y `track08_aws_cloud_practitioner` son el mismo track."""
    name = path.parent.name
    return name[:7] if name.startswith("track") and name[5:7].isdigit() else name


def load(root: Path = CONTENT) -> dict[str, list[dict[str, Any]]]:
    by_track: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in sorted(root.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        questions = data if isinstance(data, list) else data.get("questions", [])
        if questions:
            by_track[track_of(path)].extend(questions)
    return dict(by_track)


def metrics(questions: list[dict[str, Any]], urls: list[str]) -> dict[str, float | int]:
    n = len(questions)
    stems = {_norm(q.get("question_es")) for q in questions}
    options = [o for q in questions for o in (q.get("options_es") or [])]
    one_word = sum(1 for o in options if len(str(o).split()) <= 1)
    execs = [q for q in questions if str(q.get("type", "")).endswith("_exec")]
    return {
        "n": n,
        "distinct_ratio": round(len(stems) / n, 4) if n else 1.0,
        "one_word_ratio": round(one_word / len(options), 4) if options else 0.0,
        "exec_without_code": sum(1 for q in execs if not _has_code(q)),
        "source_not_indexed": sum(1 for q in questions if not _source_indexed(q, urls)),
    }


def check(
    by_track: dict[str, list[dict[str, Any]]],
    baseline: dict[str, dict[str, float | int]],
    urls: list[str],
) -> list[str]:
    problems: list[str] = []
    for track, qs in sorted(by_track.items()):
        m = metrics(qs, urls)
        base = baseline.get(track)
        if base is None:
            if m["distinct_ratio"] < MIN_DISTINCT:
                problems.append(f"{track}: enunciados distintos {m['distinct_ratio']:.1%} < {MIN_DISTINCT:.0%} (ADR-42)")
            if m["one_word_ratio"] > MAX_ONE_WORD:
                problems.append(f"{track}: opciones de una palabra {m['one_word_ratio']:.1%} > {MAX_ONE_WORD:.0%} (ADR-42)")
            if m["exec_without_code"]:
                problems.append(f"{track}: {m['exec_without_code']} preguntas *_exec sin código")
            if m["source_not_indexed"]:
                problems.append(f"{track}: {m['source_not_indexed']} preguntas sin fuente en content/sources/index.json")
            continue
        floor = min(MIN_DISTINCT, float(base["distinct_ratio"]))
        if m["distinct_ratio"] < floor - _EPS:
            problems.append(f"{track}: enunciados distintos {m['distinct_ratio']:.1%} empeora (base {floor:.1%})")
        ceiling = max(MAX_ONE_WORD, float(base["one_word_ratio"]))
        if m["one_word_ratio"] > ceiling + _EPS:
            problems.append(f"{track}: opciones de una palabra {m['one_word_ratio']:.1%} empeora (base {ceiling:.1%})")
        if m["exec_without_code"] > int(base["exec_without_code"]):
            problems.append(f"{track}: *_exec sin código {m['exec_without_code']} > base {base['exec_without_code']}")
        if m["source_not_indexed"] > int(base["source_not_indexed"]):
            problems.append(
                f"{track}: preguntas sin fuente indexada {m['source_not_indexed']} > base {base['source_not_indexed']} "
                "(las preguntas nuevas citan una fuente de content/sources/index.json)"
            )
    return problems


def load_baseline(path: Path = BASELINE) -> dict[str, dict[str, float | int]]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=CONTENT)
    ap.add_argument("--write-baseline", action="store_true")
    args = ap.parse_args(argv)
    urls = indexed_urls()
    by_track = load(args.root)
    if args.write_baseline:
        data = {t: {k: v for k, v in metrics(q, urls).items() if k != "n"} for t, q in sorted(by_track.items())}
        BASELINE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[diversidad] línea base escrita para {len(data)} tracks en {BASELINE.name}")
        return 0
    baseline = load_baseline() if args.root.resolve() == CONTENT.resolve() else {}
    problems = check(by_track, baseline, urls)
    if problems:
        print(f"[diversidad] FAIL - {len(problems)} problema(s):")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"[diversidad] PASS - {len(by_track)} tracks sin empeorar (ADR-42, 35.0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
