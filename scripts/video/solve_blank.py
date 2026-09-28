"""Encuentra el texto del hueco de una pregunta fill_blank_exec probando candidatos.

Uso: python solve_blank.py <question_id>  -> imprime la respuesta o nada.
Solo ejecuta código del banco de preguntas propio, en local, con timeout.
"""

import os
import re
import subprocess
import sys

DB = os.environ.get(
    "WHETZY_DB_URL", "postgresql://neurium:neurium_dev@localhost:5433/neurium"
)
BLANKS = ("[tu respuesta]", "____", "___")


def row(qid: str) -> tuple[str, str, str]:
    sql = f"select coalesce(code_es,''), question_es, coalesce(correct_answer_es,'') from questions where id='{qid}'"
    out = subprocess.run(
        ["psql", DB, "-At", "-F", "\x01", "-c", sql],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    code, question, expected = (out.rstrip("\n").split("\x01") + ["", "", ""])[:3]
    return code, question, expected


def main() -> None:
    qid = sys.argv[1]
    if not re.fullmatch(r"[A-Za-z0-9_]+", qid):
        sys.exit(f"id de pregunta no valido: {qid!r}")
    code, question, expected = row(qid)
    if not code:
        m = re.search(r"```python\n(.*?)```", question, re.DOTALL)
        code = m.group(1) if m else ""
    blank = next((b for b in BLANKS if b in code), None)
    if not blank or not expected:
        return
    idents = re.findall(r"[A-Za-z_][A-Za-z_0-9]*", code.replace(blank, " "))
    extra: list[str] = []
    m = re.search(r"([A-Za-z_][A-Za-z_0-9]*)\." + re.escape(blank), code)
    if m:
        try:
            extra = [a for a in dir(__import__(m.group(1))) if not a.startswith("_")]
        except ImportError:
            pass
    import builtins

    # Una salida correcta no basta: `eval` imprime lo mismo que `int` y enseña lo contrario.
    unsafe = {
        "eval",
        "exec",
        "compile",
        "input",
        "open",
        "breakpoint",
        "exit",
        "quit",
        "help",
        "globals",
        "vars",
    }
    common = [
        "int",
        "str",
        "float",
        "bool",
        "list",
        "dict",
        "set",
        "tuple",
        "len",
        "type",
        "isinstance",
        "sum",
        "sorted",
    ]
    builtin_names = common + [
        b for b in dir(builtins) if not b.startswith("_") and b not in unsafe
    ]
    ops = [
        "==",
        "is",
        "!=",
        "in",
        "not in",
        "is not",
        "and",
        "or",
        "+",
        "-",
        "*",
        "/",
        "//",
        "%",
        "**",
        "<",
        ">",
        "<=",
        ">=",
    ]
    cands = list(dict.fromkeys([*ops, *idents, *extra, *builtin_names]))
    stems = {w[:5].lower() for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúñ]{5,}", question)}
    cands.sort(key=lambda c: not any(s in c.lower() for s in stems))
    for c in cands:
        src = code.replace(blank, c)
        try:
            r = subprocess.run(
                [sys.executable, "-c", src],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except subprocess.TimeoutExpired:
            continue
        if r.returncode == 0 and r.stdout.strip() == expected.strip().replace(
            "\\n", "\n"
        ):
            print(c)
            return
        lines = [ln.strip() for ln in r.stdout.strip().splitlines()]
        if r.returncode == 0 and lines and all(ln == expected.strip() for ln in lines):
            print(c)
            return


if __name__ == "__main__":
    main()
