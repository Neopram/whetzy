"""24.8: la migración `20261022_perfil_publico` deja a todos en privado y se deshace.

Corre las funciones `upgrade`/`downgrade` de la migración con datos reales en una
tabla `users` mínima (SQLite en memoria); la prueba contra Postgres está en el
PR (`alembic upgrade/downgrade` con un usuario insertado).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import sqlalchemy as sa
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext

VERSIONS = Path(__file__).resolve().parents[1] / "alembic" / "versions"


def _migracion():
    path = VERSIONS / "20261022_perfil_publico.py"
    spec = importlib.util.spec_from_file_location("perfil_publico_mig", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _correr(conn: sa.Connection, fn) -> None:
    ctx = MigrationContext.configure(conn)
    with Operations.context(ctx):
        fn()


def test_la_cadena_de_revisiones() -> None:
    mod = _migracion()
    assert mod.revision == "20261022_perfil_publico"
    assert mod.down_revision == "20261022_track_blueprint"


def test_upgrade_deja_a_los_existentes_en_privado_y_downgrade_no_pierde_filas() -> None:
    mod = _migracion()
    eng = sa.create_engine("sqlite://")
    with eng.begin() as conn:
        conn.execute(sa.text("CREATE TABLE users (id INTEGER PRIMARY KEY, username VARCHAR(30) NOT NULL)"))
        conn.execute(sa.text("INSERT INTO users (id, username) VALUES (1, 'ana'), (2, 'bea')"))

        _correr(conn, mod.upgrade)
        rows = conn.execute(sa.text("SELECT username, public_profile_opt_in FROM users ORDER BY id")).all()
        assert [(r[0], bool(r[1])) for r in rows] == [("ana", False), ("bea", False)]

        conn.execute(sa.text("UPDATE users SET public_profile_opt_in = 1 WHERE id = 1"))
        _correr(conn, mod.downgrade)
        cols = [c["name"] for c in sa.inspect(conn).get_columns("users")]
        assert "public_profile_opt_in" not in cols
        assert conn.execute(sa.text("SELECT count(*) FROM users")).scalar_one() == 2
