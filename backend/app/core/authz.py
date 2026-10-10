"""Matriz de autorización: la política de cada ruta, sacada de sus dependencias (I.6, J.13).

Cada ruta de la API queda en una de tres políticas, según lo que cuelga de
su árbol de dependencias de FastAPI:

- ``admin``: pasa por una comprobación de administrador o de dueño
  (``require_admin``, ``require_owner``, ``X-Admin-Key``);
- ``user``: exige sesión (``get_current_user`` o algo que dependa de él);
- ``public``: ninguna de las dos. Los webhooks verifican su firma dentro del
  endpoint, así que salen aquí y es correcto.

La matriz revisada vive en ``backend/tests/authz_matrix.json`` y
``tests/test_authz_matrix.py`` la compara con lo que sale del código: una ruta
nueva sin fila, o una ruta de admin que pierde su comprobación, ponen la
suite en rojo. Tras añadir o cambiar una ruta a propósito:

    cd backend && python -m app.core.authz --write

y la diferencia en el JSON se revisa en el PR como cualquier otro cambio.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute

MATRIX_PATH = Path(__file__).resolve().parents[2] / "tests" / "authz_matrix.json"

ADMIN_DEPENDENCIES = frozenset(
    {
        "app.api.v1.endpoints.admin.require_admin",
        "app.api.v1.endpoints.admin.require_owner",
        "app.core.admin_auth.require_admin",
        "app.api.v1.endpoints.content._require_admin_key",
        "app.api.v1.endpoints.push._require_admin",
    }
)
USER_DEPENDENCIES = frozenset(
    {
        "app.core.security.get_current_user",
        "app.core.security.get_current_active_premium_user",
    }
)


def _qualname(call: Any) -> str:
    return f"{getattr(call, '__module__', '?')}.{getattr(call, '__qualname__', repr(call))}"


def _dependency_names(dependant: Dependant) -> set[str]:
    names: set[str] = set()
    for sub in dependant.dependencies:
        if sub.call is not None:
            names.add(_qualname(sub.call))
        names |= _dependency_names(sub)
    return names


def _routes(app: FastAPI) -> Iterator[Any]:
    """Las rutas efectivas, incluidas las de routers montados con `include_router`.

    Desde FastAPI 0.142 `app.routes` guarda un `_IncludedRouter` por cada
    `include_router` y las rutas reales salen de `effective_route_contexts()`.
    """
    for route in app.routes:
        if isinstance(route, APIRoute):
            yield route
        elif hasattr(route, "effective_route_contexts"):
            yield from route.effective_route_contexts()


def policy_of(dependant: Dependant) -> str:
    names = _dependency_names(dependant)
    if names & ADMIN_DEPENDENCIES:
        return "admin"
    if names & USER_DEPENDENCIES:
        return "user"
    return "public"


def route_policies(app: FastAPI) -> dict[str, str]:
    """`"MÉTODO /ruta"` → política, ordenado."""
    out: dict[str, str] = {}
    for route in _routes(app):
        if route.dependant is None:
            continue
        policy = policy_of(route.dependant)
        for method in route.methods:
            if method in {"HEAD", "OPTIONS"}:
                continue
            out[f"{method} {route.path}"] = policy
    return dict(sorted(out.items()))


def load_matrix() -> dict[str, str]:
    data: dict[str, str] = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    return data


def write_matrix(app: FastAPI) -> None:
    MATRIX_PATH.write_text(
        json.dumps(route_policies(app), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    from app.main import app as _app

    if sys.argv[1:] == ["--write"]:
        write_matrix(_app)
        print(f"matriz escrita en {MATRIX_PATH}")
    else:
        print(json.dumps(route_policies(_app), indent=2, ensure_ascii=False))
