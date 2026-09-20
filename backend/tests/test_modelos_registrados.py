"""Todo modulo de `app/models/` esta registrado en `Base.metadata`.

Importar el modulo es lo unico que registra una clase mapeada. Siete no lo
estaban —`admin`, `campaign`, `economy`, `experiment`, `instructor`, `oauth` y
`payment`— y eso tiene dientes: `alembic revision --autogenerate` compara la
base contra el metadata, asi que con modulos fuera proponia **borrar**
`instructor_courses`, `experiments`, `credit_ledger`, `oauth_accounts` y las
demas. Quien generara una migracion y la aplicara se llevaba tablas con datos.

Detectado el 2026-09-20 al intentar usar `alembic check` como puerta.
"""

from __future__ import annotations

import importlib
import pkgutil

import pytest

import app.models
from app.core.db import Base


def _modulos_de_modelos() -> list[str]:
    return sorted(
        m.name
        for m in pkgutil.iter_modules(app.models.__path__)
        if not m.name.startswith("_")
    )


def test_hay_modulos_que_comprobar() -> None:
    """Si el descubrimiento se rompe, el test de abajo pasaria sin mirar nada."""
    assert len(_modulos_de_modelos()) >= 15


@pytest.mark.parametrize("modulo", _modulos_de_modelos())
def test_cada_modulo_esta_importado_en_el_paquete(modulo: str) -> None:
    """`import app.models` tiene que arrastrar a todos."""
    fuente = (app.models.__file__ or "")
    assert fuente, "no encuentro app/models/__init__.py"
    with open(fuente, encoding="utf-8") as fh:
        texto = fh.read()

    assert f"from app.models.{modulo} import" in texto, (
        f"`{modulo}` no se importa en app/models/__init__.py, asi que sus tablas "
        f"no estan en Base.metadata. Consecuencia: `alembic --autogenerate` las "
        f"propone BORRAR, y `Base.metadata.create_all` no las crea en los tests"
    )


def test_todas_las_tablas_mapeadas_estan_en_el_metadata() -> None:
    """La comprobacion de verdad: cada modelo aporta su tabla.

    No basta con que el import este escrito; tiene que registrar algo. Un
    modulo que solo declare enums o dataclasses no aporta tabla y aqui se ve.
    """
    for modulo in _modulos_de_modelos():
        mod = importlib.import_module(f"app.models.{modulo}")
        mapeadas = {
            getattr(obj, "__tablename__", None)
            for obj in vars(mod).values()
            if isinstance(obj, type) and hasattr(obj, "__tablename__")
        }
        mapeadas.discard(None)
        faltan = mapeadas - set(Base.metadata.tables)
        assert not faltan, (
            f"`{modulo}` define {sorted(faltan)} y no estan en Base.metadata"
        )
