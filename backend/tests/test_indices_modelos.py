"""Ningun indice se declara dos veces, ni con dos nombres iguales.

`CampaignClick` declaraba `Index("ix_campaign_clicks_user_id", "user_id")` en
`__table_args__` **y** `index=True` en la propia columna. SQLAlchemy nombra el
segundo igual, asi que `Base.metadata.create_all` reventaba con «index
ix_campaign_clicks_user_id already exists» — 450 errores en cuanto el modulo
entro en `app/models/__init__.py` el 2026-09-20.

No se habia visto porque `campaign` no estaba importado: un modelo que nadie
registra nunca se crea, y sus defectos esperan.

Es el mismo patron que ya tumbo produccion una vez (ver el ledger: `sa.Column(
"email", ..., index=True)` junto a `op.create_index("ix_login_attempts_email")`
en la misma migracion).
"""

from __future__ import annotations

from collections import Counter

import app.models  # noqa: F401 — registra las clases mapeadas
from app.core.db import Base


def test_hay_tablas_que_comprobar() -> None:
    assert len(Base.metadata.tables) >= 30


def test_ningun_nombre_de_indice_se_repite_en_una_tabla() -> None:
    """Dos indices con el mismo nombre = `create_all` reventado."""
    problemas = []
    for nombre, tabla in Base.metadata.tables.items():
        cuenta = Counter(i.name for i in tabla.indexes)
        repetidos = [n for n, c in cuenta.items() if c > 1]
        if repetidos:
            problemas.append(f"{nombre}: {repetidos}")
    assert not problemas, "indices declarados dos veces: " + "; ".join(problemas)


def test_ningun_nombre_de_indice_se_repite_entre_tablas() -> None:
    """En Postgres los nombres de indice son globales al esquema."""
    vistos: Counter[str] = Counter()
    donde: dict[str, list[str]] = {}
    for nombre, tabla in Base.metadata.tables.items():
        for idx in tabla.indexes:
            if idx.name:
                vistos[idx.name] += 1
                donde.setdefault(idx.name, []).append(nombre)
    repetidos = {n: donde[n] for n, c in vistos.items() if c > 1}
    assert not repetidos, f"el mismo nombre de indice en varias tablas: {repetidos}"


def test_una_columna_indexada_no_lleva_ademas_un_index_explicito() -> None:
    """El caso exacto de CampaignClick, expresado como propiedad.

    `index=True` crea `ix_<tabla>_<columna>`. Si `__table_args__` declara un
    `Index` con ese mismo nombre, hay dos. Se mira por nombre porque es lo que
    colisiona al crear.
    """
    problemas = []
    for nombre, tabla in Base.metadata.tables.items():
        for col in tabla.columns:
            implicito = f"ix_{nombre}_{col.name}"
            coincidencias = [i for i in tabla.indexes if i.name == implicito]
            if col.index and len(coincidencias) > 1:
                problemas.append(f"{nombre}.{col.name} -> {implicito}")
    assert not problemas, (
        "columnas con `index=True` y ademas un Index del mismo nombre: "
        + "; ".join(problemas)
    )
