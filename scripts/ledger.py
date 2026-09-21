#!/usr/bin/env python3
"""ledger.py — indice consultable de `docs/AUTONOMOUS_STATE.md`.

El problema que resuelve, medido el 2026-09-19:

    docs/AUTONOMOUS_STATE.md          115 KB  ~29.000 tokens
    docs/archive/LEDGER_HISTORY.md    258 KB  ~66.000 tokens

ADR-14 manda leer el ledger **por secciones**, no entero. Eso es disciplina, no
diseno: nada lo impide, y una sesion distraida se come 29.000 tokens para
averiguar cual es la siguiente tarea — un dato que cabe en trescientos. A lo
largo de una cadena de sesiones esa es, de largo, la lectura mas repetida del
proyecto.

**Este script no crea una segunda verdad.** Parsea el markdown y responde; no
guarda un indice paralelo que pueda divergir. Esa tentacion —mantener las
cifras en dos sitios— es exactamente el incidente 17.12 (las cifras del
catalogo escritas a mano en la landing mientras el banco crecia) y la razon de
que exista `check_docs.py`. Si el ledger cambia, la respuesta cambia en la
misma corrida. Si el ledger deja de parsearse, `ledger check` falla ruidoso en
vez de contestar algo plausible.

Uso:

    python scripts/ledger.py next            # que toca ahora, por PRI
    python scripts/ledger.py show 22.8       # una fila entera, con criterio
    python scripts/ledger.py series 28       # una serie completa
    python scripts/ledger.py blocked         # la cola HUMAN-BLOCKED
    python scripts/ledger.py inv             # la tabla de invariantes
    python scripts/ledger.py stats           # recuento por estado
    python scripts/ledger.py check           # el ledger parsea y esta bien formado
    python scripts/ledger.py cost            # cuanto ahorra, reproducible

Cualquier subcomando acepta `--json` para consumo por herramientas.

Salida ASCII-safe: la consola de Windows es cp1252 y un glifo unicode la hacia
reventar *justo* en la rama de fallo de `check_docs.py`, con lo que el checker
solo podia terminar bien. Mismo remedio aqui.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "docs" / "AUTONOMOUS_STATE.md"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
except (AttributeError, OSError, ValueError):  # pragma: no cover - depende del entorno
    # Un stream que no se puede reconfigurar (pipes de CI antiguos) sigue
    # sirviendo: `errors="replace"` era una mejora, no un requisito.
    pass

# Estados del ledger, en orden de comprobacion: HUMAN-BLOCKED antes que
# BLOCKED porque el segundo es prefijo del primero por la derecha y un
# `in` ingenuo clasificaria mal toda la cola humana.
STATES = (
    "HUMAN-BLOCKED",
    "BLOCKED",
    "DOING",
    "DONE",
    "PARCIAL",
    "REFUTADA",
    # `REGRESIÓN` no esta en el formato declarado de la cabecera del ledger,
    # pero la fila 24.5 lo usa desde que la serie 24 se llevo por delante el
    # runtime de quiz. Es un estado real del proyecto: omitirlo hacia que la
    # unica tarea PRI 0 abierta no apareciese en `next`.
    "REGRESION",
    # Filas de incidente (`22x`, `24.5x`, `28x`…): la serie 16 las mete en la
    # misma tabla con cuatro celdas en vez de cinco y con estados propios.
    "RESUELTA",
    "CORREGIDA",
    "TODO",
)

# Lo que una sesion puede coger sin esperar a nadie. `PARCIAL`, `REFUTADA` y
# `REGRESION` entran: son trabajo abierto con el criterio a medio cumplir o
# deshecho, que es precisamente lo que la siguiente sesion tiene que terminar.
EXECUTABLE = {"TODO", "DOING", "PARCIAL", "REFUTADA", "REGRESION"}

_ROW = re.compile(r"^\|\s*\**([0-9]+\.[0-9]+[a-z]?|[A-Z]\.[0-9]+|H\.[A-Z0-9]+)\**\s*\|")
_SERIES_HEAD = re.compile(r"^###\s+(\d+)[.\s—-]+(.*)$")
_SECTION = re.compile(r"^##\s+(\d+)\.\s+(.*)$")
_HEADER = re.compile(r"^\|\s*ID\s*\|", re.IGNORECASE)
# Las series 25-29 llevan el estado y la prioridad **de toda la serie** en una
# cita encima de la tabla, no en cada fila.
_SERIES_STATE = re.compile(r"^>\s*\*\*Estado:\*\*\s*`?([A-ZÁÉÍÓÚÑ -]+)`?", re.IGNORECASE)
_SERIES_PRI = re.compile(r"^>\s*\*\*PRI:\*\*\s*(\d+)", re.IGNORECASE)


def _split_row(raw: str) -> list[str]:
    """Parte una fila de tabla por `|`, respetando el codigo en backticks.

    La fila 22.12 documenta un error de FastAPI cuyo texto contiene
    `Request | None` dentro de un span de codigo. Un `split("|")` ingenuo
    parte esa celda en dos, desplaza todas las demas y hace que el estado
    `DONE` se lea como prosa suelta. Paso de verdad, y es el motivo de que
    este parser no sea una linea.
    """
    cells: list[str] = []
    buf: list[str] = []
    in_code = False
    for ch in raw.strip().strip("|"):
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code:
            cells.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    cells.append("".join(buf))
    return cells


def _clean(cell: str) -> str:
    """Quita el enfasis markdown y normaliza espacios de una celda."""
    text = cell.strip()
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _state_of(cell: str) -> str:
    # Las tildes del ledger son parte de la prosa, no del estado: `REGRESIÓN`
    # y `REGRESION` son la misma fila.
    upper = _clean(cell).upper()
    upper = upper.translate(str.maketrans("ÁÉÍÓÚÜÑ", "AEIOUUN"))
    for state in STATES:
        if re.match(rf"^\W*{state}\b", upper):
            return state
    for state in STATES:
        if re.search(rf"\b{state}\b", upper[:40]):
            return state
    return "UNKNOWN"


def _sort_key(task_id: str) -> tuple:
    """`11.10` va despues de `11.9`, no antes. Orden natural, no lexico."""
    parts = re.split(r"[.]", task_id)
    key: list = []
    for part in parts:
        m = re.match(r"^(\d+)([a-z]?)$", part)
        if m:
            key.append((0, int(m.group(1)), m.group(2)))
        else:
            key.append((1, 0, part))
    return tuple(key)


@dataclass
class Task:
    id: str
    pri: int | None
    title: str
    state: str
    state_raw: str
    criterion: str
    series: str
    line: int

    def one_line(self) -> str:
        pri = f"PRI {self.pri}" if self.pri is not None else "PRI -"
        return f"{self.id:<8} {pri:<6} {self.state:<14} {self.title[:70]}"


@dataclass
class Ledger:
    tasks: list[Task] = field(default_factory=list)
    blocked: list[Task] = field(default_factory=list)
    invariants: dict[str, str] = field(default_factory=dict)
    # (numero, titulo, linea) de cada `### N` visto, rindiera filas o no.
    series_heads: list[tuple[str, str, int]] = field(default_factory=list)
    source_bytes: int = 0

    def by_id(self, task_id: str) -> Task | None:
        for task in self.tasks + self.blocked:
            if task.id.lower() == task_id.lower():
                return task
        return None

    def executable(self) -> list[Task]:
        rows = [t for t in self.tasks if t.state in EXECUTABLE]
        return sorted(rows, key=lambda t: (t.pri if t.pri is not None else 99, _sort_key(t.id)))

    def series(self, number: str) -> list[Task]:
        rows = [t for t in self.tasks if t.series.split(" ")[0] == str(number)]
        return sorted(rows, key=lambda t: _sort_key(t.id))


def _columns(header: str) -> dict[str, int]:
    """Indices de columna de una cabecera de tabla del ledger.

    Hubo **dos** formas en el mismo fichero y descubrirlo costo una sesion:

        | ID | PRI | Tarea | Estado | Criterio de aceptación |   todas las series
        | ID | Tarea | Criterio DONE |                           series 25-28 hasta 2026-09-21

    La segunda dejaba el estado y la prioridad en una cita encima de la tabla,
    para la serie entera. Un parser que exija cinco celdas se come esas series
    **sin decir nada** — que es el fallo que este repositorio persigue en todas
    partes menos en sus propias herramientas. Las series 25-28 se normalizaron
    el 2026-09-21 (42 filas, volcados del parser identicos antes y despues); la
    tolerancia se queda por si la forma vuelve, y `check` exige ademas que cada
    serie rinda filas.
    """
    cols: dict[str, int] = {}
    for i, cell in enumerate(_split_row(header)):
        name = _clean(cell).lower()
        if name.startswith("id"):
            cols["id"] = i
        elif name.startswith("pri"):
            cols["pri"] = i
        elif name.startswith("tarea"):
            cols["title"] = i
        elif name.startswith("estado"):
            cols["state"] = i
        elif name.startswith("criterio"):
            cols["criterion"] = i
    return cols


def _cell(cells: list[str], cols: dict[str, int], key: str, default: str = "") -> str:
    """Celda por nombre de columna, tolerante a filas mas cortas de la cuenta.

    Las filas de incidente de la serie 16 (`22x`, `24.5x`) traen cuatro celdas
    en una tabla declarada de cinco. Devolver `default` es correcto ahi: un
    incidente cerrado no tiene criterio de aceptacion que dar.
    """
    idx = cols.get(key)
    if idx is None or idx >= len(cells):
        return default
    return _clean(cells[idx])


def parse(path: Path = LEDGER) -> Ledger:
    text = path.read_text(encoding="utf-8")
    ledger = Ledger(source_bytes=len(text.encode("utf-8")))

    section = ""
    series = "?"
    series_title = ""
    series_state = ""
    series_pri: int | None = None
    cols: dict[str, int] = {}

    for lineno, raw in enumerate(text.splitlines(), start=1):
        m_section = _SECTION.match(raw)
        if m_section:
            section = m_section.group(1)
            cols = {}
            continue

        m_series = _SERIES_HEAD.match(raw)
        if m_series:
            series = m_series.group(1)
            series_title = _clean(m_series.group(2))
            ledger.series_heads.append((series, series_title, lineno))
            series_state = ""
            series_pri = None
            cols = {}
            continue

        if raw.startswith(">"):
            m_state = _SERIES_STATE.match(raw)
            if m_state:
                series_state = _clean(m_state.group(1))
            m_pri = _SERIES_PRI.match(raw)
            if m_pri:
                series_pri = int(m_pri.group(1))
            continue

        if _HEADER.match(raw):
            cols = _columns(raw)
            continue

        # Tabla de invariantes: `| Nombre | Valor |` dentro de `## 0`.
        if section == "0" and raw.startswith("|"):
            cells = _split_row(raw)
            if len(cells) == 2 and not set(_clean(cells[0])) <= set("-: "):
                name = _clean(cells[0])
                if name and name.lower() not in {"invariante", "valor"}:
                    ledger.invariants.setdefault(name, _clean(cells[1]))
            continue

        m_row = _ROW.match(raw)
        if not m_row:
            continue

        cells = _split_row(raw)
        task_id = _clean(cells[0])

        if section == "3":
            # `## 3. Cola HUMAN-BLOCKED` — `| ID | Que falta | Como se desbloquea |`
            ledger.blocked.append(
                Task(
                    id=task_id,
                    pri=None,
                    title=_clean(cells[1]) if len(cells) > 1 else "",
                    state="HUMAN-BLOCKED",
                    state_raw="HUMAN-BLOCKED",
                    criterion=_clean(cells[-1]),
                    series="H",
                    line=lineno,
                )
            )
            continue

        if section != "2" or not cols:
            continue

        pri_cell = _cell(cells, cols, "pri")
        pri = int(pri_cell) if pri_cell.isdigit() else series_pri

        state_raw = _cell(cells, cols, "state") or series_state
        ledger.tasks.append(
            Task(
                id=task_id,
                pri=pri,
                title=_cell(cells, cols, "title"),
                state=_state_of(state_raw) if state_raw else "TODO",
                state_raw=state_raw or "TODO (heredado de la serie)",
                criterion=_cell(cells, cols, "criterion"),
                series=f"{series} {series_title}".strip(),
                line=lineno,
            )
        )

    return ledger


# ---------------------------------------------------------------------------
# Subcomandos
# ---------------------------------------------------------------------------


def cmd_next(ledger: Ledger, args) -> int:
    rows = ledger.executable()[: args.limit]
    if args.json:
        print(json.dumps([asdict(t) for t in rows], ensure_ascii=False, indent=2))
        return 0
    if not rows:
        print("No queda trabajo ejecutable en el ledger. Mira `ledger.py blocked`.")
        return 0
    print(f"Siguientes {len(rows)} (de {len(ledger.executable())} ejecutables), por PRI:\n")
    for task in rows:
        print("  " + task.one_line())
    print("\nDetalle de una: python scripts/ledger.py show <ID>")
    return 0


def cmd_show(ledger: Ledger, args) -> int:
    task = ledger.by_id(args.id)
    if task is None:
        print(f"No hay ninguna fila con id {args.id!r} en {LEDGER.name}.")
        return 1
    if args.json:
        print(json.dumps(asdict(task), ensure_ascii=False, indent=2))
        return 0
    print(f"{task.id} - {task.title}")
    print(f"  Serie    : {task.series}")
    print(f"  PRI      : {task.pri if task.pri is not None else '-'}")
    print(f"  Estado   : {task.state_raw}")
    print(f"  Criterio : {task.criterion}")
    print(f"  Fuente   : docs/AUTONOMOUS_STATE.md:{task.line}")
    return 0


def cmd_series(ledger: Ledger, args) -> int:
    rows = ledger.series(args.number)
    if args.json:
        print(json.dumps([asdict(t) for t in rows], ensure_ascii=False, indent=2))
        return 0
    if not rows:
        print(f"La serie {args.number} no tiene filas en el backlog ejecutable.")
        return 1
    print(f"Serie {args.number} - {rows[0].series}\n")
    for task in rows:
        print("  " + task.one_line())
    done = sum(1 for t in rows if t.state == "DONE")
    print(f"\n  {done}/{len(rows)} DONE")
    return 0


def cmd_blocked(ledger: Ledger, args) -> int:
    if args.json:
        print(json.dumps([asdict(t) for t in ledger.blocked], ensure_ascii=False, indent=2))
        return 0
    print(f"Cola HUMAN-BLOCKED ({len(ledger.blocked)}):\n")
    for task in ledger.blocked:
        print(f"  {task.id:<8} {task.title[:88]}")
    print("\nComo se desbloquea cada una: python scripts/ledger.py show <ID>")
    return 0


def cmd_inv(ledger: Ledger, args) -> int:
    if args.json:
        print(json.dumps(ledger.invariants, ensure_ascii=False, indent=2))
        return 0
    for name, value in ledger.invariants.items():
        print(f"  {name:<22} {value[:100]}")
    return 0


def cmd_stats(ledger: Ledger, args) -> int:
    counts: dict[str, int] = {}
    for task in ledger.tasks:
        counts[task.state] = counts.get(task.state, 0) + 1
    counts["HUMAN-BLOCKED (cola §3)"] = len(ledger.blocked)
    if args.json:
        print(json.dumps(counts, ensure_ascii=False, indent=2))
        return 0
    print(f"Filas en el backlog ejecutable: {len(ledger.tasks)}\n")
    for state, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {state:<26} {n}")
    return 0


def cmd_check(ledger: Ledger, args) -> int:
    """Que el ledger siga siendo parseable es en si mismo un invariante.

    Si alguien reformatea una tabla y este comando deja de encontrar filas, la
    siguiente sesion volveria a leer 29.000 tokens sin enterarse. Preferible
    que falle aqui.
    """
    problems: list[str] = []
    if len(ledger.tasks) < 20:
        problems.append(f"solo {len(ledger.tasks)} filas parseadas: la tabla cambio de forma")
    if not ledger.invariants:
        problems.append("la tabla de invariantes de `## 0` no se ha podido leer")
    # El suelo global de arriba no vigila lo que paso: el parser se comio 48
    # filas de 147 (series 25-29 enteras, otra forma de tabla) y con 99 habria
    # dicho OK. Probado el 2026-09-21 vaciando la serie 22: «OK - 133 filas».
    # Lo que se pierde es una SERIE entera, asi que se mira serie a serie.
    for number, title, line in ledger.series_heads:
        if not ledger.series(number):
            problems.append(
                f"serie {number} ({title}, linea {line}): tiene cabecera y ninguna "
                f"fila parseada - la tabla cambio de forma o se quedo vacia"
            )
    for task in ledger.tasks:
        if task.state == "UNKNOWN":
            problems.append(f"{task.id} (linea {task.line}): estado no reconocido {task.state_raw!r}")
        # El criterio solo se exige a lo que sigue abierto: una tarea sin
        # definicion de «hecho» es la puerta por la que entraron los cuatro
        # hashes inventados. Una fila de incidente ya cerrada no lo necesita.
        if task.state in EXECUTABLE and not task.criterion:
            problems.append(f"{task.id} (linea {task.line}): sin criterio de aceptacion")
    seen: dict[str, int] = {}
    for task in ledger.tasks:
        if task.id in seen:
            problems.append(f"{task.id}: id duplicado (lineas {seen[task.id]} y {task.line})")
        seen[task.id] = task.line

    if args.json:
        print(json.dumps({"ok": not problems, "problems": problems}, ensure_ascii=False, indent=2))
        return 1 if problems else 0
    if problems:
        print(f"FAIL - {len(problems)} problema(s) en el ledger:\n")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"OK - {len(ledger.tasks)} filas, {len(ledger.blocked)} bloqueos humanos, "
          f"{len(ledger.invariants)} invariantes")
    return 0


def cmd_cost(ledger: Ledger, args) -> int:
    """El numero que justifica este script, reproducible por quien no se fie."""
    history = ROOT / "docs" / "archive" / "LEDGER_HISTORY.md"
    history_bytes = history.stat().st_size if history.exists() else 0

    rows = ledger.executable()[:5]
    answer = "\n".join(t.one_line() for t in rows)

    full_tok = ledger.source_bytes // 4
    hist_tok = history_bytes // 4
    ans_tok = max(len(answer) // 4, 1)

    data = {
        "ledger_bytes": ledger.source_bytes,
        "ledger_tokens_aprox": full_tok,
        "history_bytes": history_bytes,
        "history_tokens_aprox": hist_tok,
        "respuesta_next_tokens_aprox": ans_tok,
        "factor": round(full_tok / ans_tok, 1),
    }
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    print("Coste de averiguar 'que toca ahora':\n")
    print(f"  Leer AUTONOMOUS_STATE.md entero   {ledger.source_bytes:>8,} B   ~{full_tok:>6,} tokens")
    print(f"  Leer LEDGER_HISTORY.md entero     {history_bytes:>8,} B   ~{hist_tok:>6,} tokens")
    print(f"  `ledger.py next` (5 filas)        {len(answer):>8,} B   ~{ans_tok:>6,} tokens")
    print(f"\n  Factor sobre el ledger vivo: {data['factor']}x")
    print("\n  Reproducible: `python scripts/ledger.py cost --json`")
    return 0


COMMANDS = {
    "next": cmd_next,
    "show": cmd_show,
    "series": cmd_series,
    "blocked": cmd_blocked,
    "inv": cmd_inv,
    "stats": cmd_stats,
    "check": cmd_check,
    "cost": cmd_cost,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ledger.py",
        description="Indice consultable de docs/AUTONOMOUS_STATE.md (no duplica: parsea).",
    )
    parser.add_argument("--json", action="store_true", help="salida JSON para herramientas")
    parser.add_argument("--file", type=Path, default=LEDGER, help="ledger alternativo (tests)")
    sub = parser.add_subparsers(dest="cmd")

    p_next = sub.add_parser("next", help="siguientes tareas ejecutables por PRI")
    p_next.add_argument("-n", "--limit", type=int, default=5)

    p_show = sub.add_parser("show", help="una fila entera con su criterio")
    p_show.add_argument("id")

    p_series = sub.add_parser("series", help="una serie completa")
    p_series.add_argument("number")

    for name in ("blocked", "inv", "stats", "check", "cost"):
        sub.add_parser(name)

    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_help()
        return 0

    if not args.file.exists():
        print(f"No encuentro el ledger en {args.file}")
        return 1

    return COMMANDS[args.cmd](parse(args.file), args)


if __name__ == "__main__":
    raise SystemExit(main())
