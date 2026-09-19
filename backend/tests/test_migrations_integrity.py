"""Guardias estáticas sobre la cadena de migraciones de Alembic (24.0).

Nacen del incidente del 2026-09-19: `alembic upgrade head` murió en producción
con `DuplicateTable: relation "ix_login_attempts_email" already exists` porque la
migración 22.1 declaraba `index=True` en una columna *y además* creaba el índice
con el mismo nombre, y porque 22.1 y 23.1 creaban las mismas tres tablas. El
backend se quedó en 502 hasta que se arreglaron las tres migraciones.

Son estáticas a propósito: corren sin Postgres, así que valen en CI y en local.
"""

from __future__ import annotations

import ast
from pathlib import Path

VERSIONS_DIR = Path(__file__).resolve().parents[1] / "alembic" / "versions"


def _module_asts() -> dict[str, ast.Module]:
    return {
        path.name: ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for path in sorted(VERSIONS_DIR.glob("*.py"))
    }


def _string_arg(node: ast.Call, index: int) -> str | None:
    if len(node.args) <= index:
        return None
    arg = node.args[index]
    return arg.value if isinstance(arg, ast.Constant) and isinstance(arg.value, str) else None


def _revision_ids(tree: ast.Module) -> tuple[str | None, str | None]:
    revision = down_revision = None
    for node in tree.body:
        # Las migraciones usan tanto `revision = "x"` como `revision: str = "x"`.
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            target = node.targets[0]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target = node.target
        else:
            continue
        name = target.id
        value = node.value.value if isinstance(node.value, ast.Constant) else None
        if name == "revision":
            revision = value
        elif name == "down_revision":
            down_revision = value
    return revision, down_revision


def _ordered_chain(modules: dict[str, ast.Module]) -> list[tuple[str, ast.Module]]:
    """Devuelve (fichero, AST) en orden de aplicación, de la base a la head."""
    by_down: dict[str | None, tuple[str, ast.Module]] = {}
    for filename, tree in modules.items():
        revision, down_revision = _revision_ids(tree)
        assert revision, f"{filename}: sin `revision`"
        assert down_revision not in by_down, (
            f"cadena bifurcada: {filename} y {by_down[down_revision][0]} "
            f"parten de {down_revision}"
        )
        by_down[down_revision] = (filename, tree)

    chain: list[tuple[str, ast.Module]] = []
    cursor: str | None = None
    while cursor in by_down:
        filename, tree = by_down.pop(cursor)
        chain.append((filename, tree))
        cursor = _revision_ids(tree)[0]
    assert not by_down, f"migraciones huérfanas fuera de la cadena: {sorted(by_down.values())}"
    return chain


def _upgrade_calls(tree: ast.Module) -> list[ast.Call]:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "upgrade":
            return [n for n in ast.walk(node) if isinstance(n, ast.Call)]
    return []


def _op_name(call: ast.Call) -> str | None:
    func = call.func
    return func.attr if isinstance(func, ast.Attribute) else None


def _implicit_indexes(create_table: ast.Call, table: str) -> list[str]:
    """Índices que Alembic crea solo por `index=True` en una columna."""
    names: list[str] = []
    for arg in create_table.args[1:]:
        if not isinstance(arg, ast.Call) or _op_name(arg) != "Column":
            continue
        column = _string_arg(arg, 0)
        indexed = any(
            kw.arg == "index" and isinstance(kw.value, ast.Constant) and kw.value.value is True
            for kw in arg.keywords
        )
        if column and indexed:
            names.append(f"ix_{table}_{column}")
    return names


def test_single_head() -> None:
    """Una sola head: `alembic upgrade head` es ambiguo con dos."""
    modules = _module_asts()
    revisions = {_revision_ids(t)[0] for t in modules.values()}
    down_revisions = {_revision_ids(t)[1] for t in modules.values()}
    heads = revisions - down_revisions
    assert len(heads) == 1, f"se esperaba una sola head, hay {sorted(heads)}"


def test_no_table_created_twice() -> None:
    """Ninguna migración crea una tabla que otra anterior ya creó y no borró."""
    live: dict[str, str] = {}
    duplicates: list[str] = []
    for filename, tree in _ordered_chain(_module_asts()):
        for call in _upgrade_calls(tree):
            op = _op_name(call)
            name = _string_arg(call, 0)
            if not name:
                continue
            if op == "create_table":
                if name in live:
                    duplicates.append(f"{name}: {live[name]} y {filename}")
                live[name] = filename
            elif op == "drop_table":
                live.pop(name, None)
    assert not duplicates, "tablas creadas dos veces sin drop intermedio: " + "; ".join(duplicates)


def test_no_index_name_created_twice() -> None:
    """Ningún nombre de índice se crea dos veces, ni explícito ni por `index=True`.

    El fallo de producción del 2026-09-19 fue exactamente esto dentro de una
    sola migración: `sa.Column("email", ..., index=True)` + `op.create_index(
    "ix_login_attempts_email", ...)`.
    """
    live: dict[str, str] = {}
    duplicates: list[str] = []

    def add(index_name: str, where: str) -> None:
        if index_name in live:
            duplicates.append(f"{index_name}: {live[index_name]} y {where}")
        live[index_name] = where

    for filename, tree in _ordered_chain(_module_asts()):
        for call in _upgrade_calls(tree):
            op = _op_name(call)
            name = _string_arg(call, 0)
            if not name:
                continue
            if op == "create_table":
                for implicit in _implicit_indexes(call, name):
                    add(implicit, f"{filename} (index=True)")
            elif op == "create_index":
                add(name, filename)
            elif op == "drop_index":
                live.pop(name, None)
            elif op == "drop_table":
                for index_name in [i for i, src in live.items() if i.startswith(f"ix_{name}_")]:
                    live.pop(index_name, None)
    assert not duplicates, "nombres de índice repetidos: " + "; ".join(duplicates)
