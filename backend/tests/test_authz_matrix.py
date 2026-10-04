"""Matriz de autorización: cada ruta declara su política y se cumple (I.6, J.13).

1. La matriz revisada (`tests/authz_matrix.json`) coincide con la que sale del
   código. Una ruta nueva sin fila, o una de admin que pierde su comprobación,
   la ponen en rojo con instrucciones.
2. Un alumno con sesión no pasa ninguna ruta de admin.
3. Sin credenciales no se pasa ninguna ruta `user` ni `admin`.

Regenerar tras un cambio a propósito: `cd backend && python -m app.core.authz --write`.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.authz import load_matrix, route_policies
from app.core.db import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.user import User

MATRIX = load_matrix()
DENIED = {401, 403}
_PARAM = re.compile(r"\{[^}]+\}")


def _url(path: str) -> str:
    # Las comprobaciones de sesión corren antes que la validación de la ruta,
    # así que cualquier valor sirve para el parámetro.
    return _PARAM.sub("1", path)


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def module_client() -> AsyncGenerator[tuple[AsyncClient, dict[str, str]], None]:
    """Una base y un cliente para las ~170 peticiones del módulo, no uno por test.

    Con los del conftest (por función) el módulo tardaba ~40 s; así cabe en el
    nivel 1 del pre-push. Ningún test escribe: todas las peticiones se rechazan.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        student = User(
            id=uuid.uuid4(),
            email=f"authz-{uuid.uuid4().hex[:8]}@whetzy.test",
            username=f"authz{uuid.uuid4().hex[:6]}",
            hashed_password="x",
            display_name="Alumna",
            language="es",
        )
        session.add(student)
        await session.commit()

        async def _override() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_db] = _override
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                yield client, {"Authorization": f"Bearer {create_access_token(student.id)}"}
        finally:
            app.dependency_overrides.pop(get_db, None)
    await engine.dispose()


def _routes_with(policies: set[str]) -> list[tuple[str, str]]:
    return [tuple(key.split(" ", 1)) for key, p in MATRIX.items() if p in policies]  # type: ignore[misc]


def test_la_matriz_revisada_coincide_con_el_codigo() -> None:
    actual = route_policies(app)
    missing = sorted(set(actual) - set(MATRIX))
    stale = sorted(set(MATRIX) - set(actual))
    changed = sorted(f"{k}: {MATRIX[k]} → {actual[k]}" for k in set(actual) & set(MATRIX) if actual[k] != MATRIX[k])
    assert not (missing or stale or changed), (
        "la matriz de autorización no cuadra con el código.\n"
        f"  rutas sin fila: {missing}\n  filas sin ruta: {stale}\n  política cambiada: {changed}\n"
        "Si el cambio es a propósito: cd backend && python -m app.core.authz --write, "
        "y revisa el diff de tests/authz_matrix.json en el PR."
    )


def test_la_matriz_cubre_las_tres_politicas() -> None:
    """Si el clasificador dejara de reconocer las dependencias, todo saldría `public`."""
    assert {"admin", "user", "public"} <= set(MATRIX.values())


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize(("method", "path"), _routes_with({"admin"}))
async def test_un_alumno_no_pasa_una_ruta_de_admin(
    module_client: tuple[AsyncClient, dict[str, str]], method: str, path: str
) -> None:
    client, student_headers = module_client
    res = await client.request(method, _url(path), headers=student_headers, json={})
    assert res.status_code in DENIED, f"{method} {path} → {res.status_code}: {res.text[:200]}"


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize(("method", "path"), _routes_with({"user", "admin"}))
async def test_sin_credenciales_no_se_pasa_una_ruta_protegida(
    module_client: tuple[AsyncClient, dict[str, str]], method: str, path: str
) -> None:
    client, _ = module_client
    res = await client.request(method, _url(path), json={})
    assert res.status_code in DENIED, f"{method} {path} → {res.status_code}: {res.text[:200]}"
