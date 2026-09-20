"""Toda clave foranea tiene el mismo tipo que la columna a la que apunta, y el
loader de contenido no crea el esquema en produccion.

El 2026-09-20 el backend de produccion estuvo caido devolviendo 502. La cadena
fue esta, y las dos guardas de este fichero cortan un eslabon cada una:

1. `app/models/__init__.py` empezo a registrar siete modulos que nadie importaba
   (commit `6aee4fe`). Entre ellos `payment`, con cuatro tablas que **ninguna
   migracion crea a proposito** — esperan la decision de H.19.
2. `scripts/start.sh` corre `python -m app.services.content_loader`, cuyo `main()`
   llamaba a `init_db()` -> `Base.metadata.create_all` **sin mirar el entorno**.
   En produccion el esquema es de Alembic: la linea anterior de `start.sh` ya
   corrio `alembic upgrade head`.
3. `create_all` intento crear `stripe_customers`, cuyo `user_id` era
   `String(36)` contra `users.id`, que es `Uuid`. Postgres rechaza la FK:
   «foreign key constraint "stripe_customers_user_id_fkey" cannot be
   implemented ... are of incompatible types: character varying and uuid».
4. `set -euo pipefail` mato el contenedor. Railway: `status: Crashed`.

No se vio en la suite porque los tests corren sobre SQLite, que acepta una FK
con tipos distintos sin rechistar. Por eso la primera guarda compara **tipos en
el metadata**, no el resultado de un `CREATE TABLE`: asi falla en cualquier
motor, tambien en SQLite.
"""

from __future__ import annotations

import inspect

import app.models  # noqa: F401 — registra las clases mapeadas
from app.core.db import Base
from app.services import content_loader


def test_hay_claves_foraneas_que_comprobar() -> None:
    total = sum(len(col.foreign_keys) for t in Base.metadata.tables.values() for col in t.columns)
    assert total >= 20, f"solo {total} FKs registradas; el metadata parece incompleto"


def test_cada_fk_tiene_el_tipo_de_la_columna_a_la_que_apunta() -> None:
    """El caso exacto de `stripe_customers.user_id`, como propiedad.

    Se comparan las clases del tipo (`Uuid` vs `String`), no la instancia: dos
    `String` de longitud distinta los acepta Postgres en una FK; un `String`
    contra un `Uuid`, no.
    """
    problemas = []
    for nombre, tabla in Base.metadata.tables.items():
        for col in tabla.columns:
            for fk in col.foreign_keys:
                destino = fk.column
                aqui = type(col.type).__name__
                alli = type(destino.type).__name__
                if aqui != alli:
                    problemas.append(
                        f"{nombre}.{col.name} es {aqui} "
                        f"pero {destino.table.name}.{destino.name} es {alli}"
                    )
    assert not problemas, (
        "claves foraneas con tipos incompatibles (Postgres rechaza la tabla entera): "
        + "; ".join(problemas)
    )


def test_el_loader_de_contenido_no_crea_el_esquema_fuera_de_development() -> None:
    """En produccion el esquema es de Alembic; `create_all` ahi solo puede romper.

    Se lee el codigo en vez de ejecutarlo porque `main()` necesita una base de
    datos viva. Lo que se exige es que la llamada a `init_db()` este dentro de
    una guarda por entorno, como ya la tiene `app/main.py`.
    """
    fuente = inspect.getsource(content_loader.main)
    assert "init_db()" in fuente, "cambio la forma de main(); revisa esta guarda"
    lineas = [ln.strip() for ln in fuente.splitlines()]
    i = next(i for i, ln in enumerate(lineas) if ln == "await init_db()")
    anteriores = " ".join(lineas[:i])
    assert 'settings.ENVIRONMENT == "development"' in anteriores, (
        "content_loader.main() llama a init_db() sin comprobar el entorno: "
        "eso corre create_all en produccion y tumbo el backend el 2026-09-20"
    )
