"""Cada ruta que llama el frontend existe en el router de FastAPI.

El 2026-09-20 se encontro que `placement.result()` pedia
`GET /placement/{session_id}/result` mientras el backend expone
`GET /placement/result?session_id=...`: **404 en produccion**. Habia un test que
lo cubria (`services.api.extra.test.ts`), pero moquea `fetch`, asi que pasa con
cualquier URL. Diecinueve tests del frontend tienen esa forma; ninguno puede
detectar una ruta equivocada.

Esta guarda vive en el backend a proposito: lee las rutas reales del router
—no una copia ni un snapshot de OpenAPI, que envejecen— y las compara con las
que el cliente escribe. Si alguien renombra un endpoint y no toca el cliente,
o al reves, este test se pone rojo antes del despliegue.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.main import app

RAIZ = Path(__file__).resolve().parents[2]
CLIENTE = RAIZ / "frontend" / "src" / "services" / "api.ts"

#: `${...}` de una plantilla JS -> parametro de ruta de FastAPI.
_INTERPOLACION = re.compile(r"\$\{[^}]+\}")

#: Rutas que el cliente construye y que no pasan por el backend propio.
_EXENTAS = (
    "/auth/oauth/",  # redireccion de pagina completa, no fetch
)


def _rutas_del_router() -> set[str]:
    """Plantillas de ruta del router, con los parametros normalizados."""
    rutas = set()
    for r in app.routes:
        camino = getattr(r, "path", None)
        if not camino or not camino.startswith("/api/v1"):
            continue
        rutas.add(re.sub(r"\{[^}]+\}", "{}", camino))
    return rutas


def _rutas_del_cliente() -> set[str]:
    """Rutas literales que `services/api.ts` pide, normalizadas igual.

    Solo se miran las que salen de `request(...)`, que es el unico punto por
    donde el cliente habla con la API.
    """
    texto = CLIENTE.read_text(encoding="utf-8")
    crudas: set[str] = set()
    for m in re.finditer(r"request(?:<[^>]*>)?\(\s*[`'\"]([^`'\"]+)", texto):
        crudas.add(m.group(1))

    rutas = set()
    for cruda in crudas:
        camino = cruda.split("?")[0].rstrip("/")
        if any(camino.startswith(e) for e in _EXENTAS):
            continue
        # Una interpolacion que NO empieza segmento (`/skills${suffix}`) es una
        # query construida aparte, no un parametro de ruta: la ruta termina ahi.
        # Una que si lo empieza (`/duels/${id}/join`) si lo es.
        camino = re.sub(r"(?<!/)\$\{[^}]+\}.*$", "", camino)
        camino = _INTERPOLACION.sub("{}", camino).rstrip("/")
        if not camino.startswith("/api/v1"):
            camino = "/api/v1" + camino
        rutas.add(camino)
    return rutas


def test_el_cliente_encuentra_rutas_que_leer() -> None:
    """Si el regex deja de casar, el test de abajo pasaria sin comprobar nada."""
    assert CLIENTE.exists(), f"no encuentro {CLIENTE}"
    assert len(_rutas_del_cliente()) >= 25


def test_el_router_expone_rutas() -> None:
    assert len(_rutas_del_router()) >= 80


def test_toda_ruta_que_llama_el_frontend_existe_en_el_backend() -> None:
    """La comprobacion que habria cazado el 404 de `placement.result`."""
    del_router = _rutas_del_router()
    huerfanas = sorted(r for r in _rutas_del_cliente() if r not in del_router)

    assert not huerfanas, (
        "el cliente llama a rutas que el backend no expone:\n  "
        + "\n  ".join(huerfanas)
        + "\n\nO se renombro el endpoint sin tocar `frontend/src/services/api.ts`, "
        "o la ruta del cliente esta mal escrita. Los tests de `src/test/services.api.*` "
        "no lo detectan porque moquean `fetch`."
    )


@pytest.mark.parametrize(
    ("ruta", "por_que"),
    [
        ("/api/v1/placement/result", "devolvia 404: el cliente pedia /placement/{id}/result"),
        ("/api/v1/auth/oauth/providers", "decide si se pintan los botones de OAuth"),
        ("/api/v1/admin/email/status", "unica forma de saber si el correo sale (H.30)"),
        ("/api/v1/quiz/start", "el bucle principal del producto"),
    ],
)
def test_rutas_que_ya_se_rompieron_una_vez(ruta: str, por_que: str) -> None:
    assert ruta in _rutas_del_router(), f"{ruta} — {por_que}"
