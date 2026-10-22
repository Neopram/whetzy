"""Esquema de las cuatro tablas del marketplace (28.0): modelo SQLAlchemy y migración
`u2v3w4x5y6z7` dicen lo mismo en columnas, claves foráneas (con su `ondelete`),
claves únicas y clave primaria.

Hasta ahora su único test era `test_modelos_registrados.py` (que el módulo esté
importado). La migración se lee ejecutando su `upgrade()` contra un registrador de
`op`, así que se comparan los objetos `sa.Column` tal cual los declara — sin pasar por
la reflexión de SQLite, que renombra `UUID` a `NUMERIC`.

Hallazgo (28.0): la migración crea siete índices que el modelo no declara
(`MIGRACION_INDICES_EXTRA`). No rompe nada en Postgres (la migración manda), pero
`alembic check` los vería como «a borrar» si el modelo es la referencia; quedan fijados
aquí para que cualquier cambio —en un sentido u otro— sea una decisión y no un descuido.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa

import app.models  # noqa: F401 — registra las clases mapeadas
from app.core.db import Base

MIGRACION = (
    Path(__file__).resolve().parents[1]
    / "alembic" / "versions" / "20260919_1500_u2v3w4x5y6z7_instructor_marketplace.py"
)
TABLAS = ("instructors", "instructor_courses", "instructor_enrollments", "instructor_payouts")

# Lo que el producto necesita, escrito a mano: borrar un instructor se lleva sus
# cursos, inscripciones y liquidaciones; borrar un alumno, sus inscripciones.
FKS_ESPERADAS: dict[str, set[tuple[str, str, str | None]]] = {
    "instructors": {("user_id", "users.id", "CASCADE")},
    "instructor_courses": {("instructor_id", "instructors.id", "CASCADE")},
    "instructor_enrollments": {
        ("course_id", "instructor_courses.id", "CASCADE"),
        ("user_id", "users.id", "CASCADE"),
    },
    "instructor_payouts": {("instructor_id", "instructors.id", "CASCADE")},
}

UNICAS_ESPERADAS: dict[str, set[tuple[str, tuple[str, ...]]]] = {
    "instructors": {("uq_instructor_user", ("user_id",))},
    "instructor_courses": set(),
    "instructor_enrollments": {("uq_instructor_course_user", ("course_id", "user_id"))},
    "instructor_payouts": set(),
}

# Índices de la migración que el modelo no declara (hallazgo, ver docstring).
MIGRACION_INDICES_EXTRA = {
    ("ix_instructors_verified_at", "instructors", ("verified_at",)),
    ("ix_instructor_courses_status", "instructor_courses", ("status",)),
    ("ix_instructor_courses_created_at", "instructor_courses", ("created_at",)),
    ("ix_instructor_enrollments_enrolled_at", "instructor_enrollments", ("enrolled_at",)),
    ("ix_instructor_payouts_status", "instructor_payouts", ("status",)),
    ("ix_instructor_payouts_period_start", "instructor_payouts", ("period_start",)),
    ("ix_instructor_payouts_created_at", "instructor_payouts", ("created_at",)),
}


class _RegistradorOp:
    """Sustituye a `alembic.op`: guarda lo que la migración pide en vez de ejecutarlo."""

    def __init__(self) -> None:
        self.tablas: dict[str, tuple[Any, ...]] = {}
        self.indices: list[tuple[str, str, tuple[str, ...], bool]] = []

    def create_table(self, nombre: str, *elementos: Any, **_: Any) -> None:
        self.tablas[nombre] = elementos

    def create_index(self, nombre: str, tabla: str, columnas: list[str], unique: bool = False) -> None:
        self.indices.append((nombre, tabla, tuple(columnas), unique))


def _tipo(t: sa.types.TypeEngine[Any]) -> str:
    """Familia del tipo, con longitud o zona horaria cuando cambian el DDL."""
    if isinstance(t, sa.Uuid):  # incluye sa.UUID
        return "uuid"
    if isinstance(t, sa.String) and not isinstance(t, sa.Text):
        return f"string({t.length})"
    if isinstance(t, sa.Text):
        return "text"
    if isinstance(t, sa.BigInteger):
        return "bigint"
    if isinstance(t, sa.Integer):
        return "integer"
    if isinstance(t, sa.DateTime):
        return f"datetime(tz={t.timezone})"
    raise AssertionError(f"tipo sin clasificar: {t!r}")


def _columnas(cols: list[sa.Column[Any]], pk: set[str]) -> dict[str, tuple[str, bool, bool, bool]]:
    """nombre -> (tipo, nullable, tiene server_default, es PK)."""
    return {
        c.name: (_tipo(c.type), bool(c.nullable) and c.name not in pk, c.server_default is not None, c.name in pk)
        for c in cols
    }


@pytest.fixture(scope="module")
def migracion() -> dict[str, dict[str, Any]]:
    spec = importlib.util.spec_from_file_location("mig_instructor", MIGRACION)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rec = _RegistradorOp()
    mod.op = rec
    mod.upgrade()

    out: dict[str, dict[str, Any]] = {}
    for nombre, elementos in rec.tablas.items():
        cols = [e for e in elementos if isinstance(e, sa.Column)]
        # Los constraints aún no están pegados a una tabla: sus columnas son los nombres
        # (`_pending_colargs`) tal como se escribieron en la migración.
        pk: set[str] = set()
        for e in elementos:
            if isinstance(e, sa.PrimaryKeyConstraint):
                pk = set(e._pending_colargs)  # type: ignore[attr-defined]
        out[nombre] = {
            "cols": _columnas(cols, pk),
            "pk": pk,
            "fks": {
                (e.column_keys[0], e.elements[0]._colspec, e.ondelete)
                for e in elementos if isinstance(e, sa.ForeignKeyConstraint)
            },
            "unicas": {
                (e.name, tuple(e._pending_colargs))  # type: ignore[attr-defined]
                for e in elementos if isinstance(e, sa.UniqueConstraint)
            },
            "indices": {(n, t, c) for n, t, c, _u in rec.indices if t == nombre},
        }
    return out


def _modelo(nombre: str) -> dict[str, Any]:
    t = Base.metadata.tables[nombre]
    pk = {c.name for c in t.primary_key.columns}
    return {
        "cols": _columnas(list(t.columns), pk),
        "pk": pk,
        "fks": {
            (fk.parent.name, fk.target_fullname, fk.ondelete) for fk in t.foreign_keys
        },
        "unicas": {
            (c.name, tuple(col.name for col in c.columns))
            for c in t.constraints if isinstance(c, sa.UniqueConstraint)
        },
        "indices": {(i.name, nombre, tuple(c.name for c in i.columns)) for i in t.indexes},
    }


def test_la_migracion_crea_las_cuatro_tablas(migracion: dict[str, dict[str, Any]]) -> None:
    assert set(migracion) == set(TABLAS)


@pytest.mark.parametrize("tabla", TABLAS)
def test_columnas_del_modelo_y_la_migracion_coinciden(tabla: str, migracion: dict[str, dict[str, Any]]) -> None:
    assert _modelo(tabla)["cols"] == migracion[tabla]["cols"]


@pytest.mark.parametrize("tabla", TABLAS)
def test_clave_primaria_es_id(tabla: str, migracion: dict[str, dict[str, Any]]) -> None:
    assert _modelo(tabla)["pk"] == migracion[tabla]["pk"] == {"id"}


@pytest.mark.parametrize("tabla", TABLAS)
def test_claves_foraneas_y_ondelete(tabla: str, migracion: dict[str, dict[str, Any]]) -> None:
    esperado = FKS_ESPERADAS[tabla]
    assert _modelo(tabla)["fks"] == esperado, "modelo"
    assert migracion[tabla]["fks"] == esperado, "migración"


@pytest.mark.parametrize("tabla", TABLAS)
def test_claves_unicas(tabla: str, migracion: dict[str, dict[str, Any]]) -> None:
    esperado = UNICAS_ESPERADAS[tabla]
    assert _modelo(tabla)["unicas"] == esperado, "modelo"
    assert migracion[tabla]["unicas"] == esperado, "migración"


def test_indices_del_modelo_estan_en_la_migracion_y_los_extra_son_los_conocidos(
    migracion: dict[str, dict[str, Any]],
) -> None:
    en_modelo = set().union(*(_modelo(t)["indices"] for t in TABLAS))
    en_migracion = set().union(*(migracion[t]["indices"] for t in TABLAS))
    assert en_modelo <= en_migracion, f"el modelo declara índices que la migración no crea: {en_modelo - en_migracion}"
    assert en_migracion - en_modelo == MIGRACION_INDICES_EXTRA
