#!/usr/bin/env bash
# Tareas de arranque: esquema -> contenido -> cuenta de dueno -> seed.
#
# D-4 (dueno, 2026-10-12): este script es el «pre-deploy command» de Railway.
# Alli corre ANTES de cambiar de version: si una migracion o el contenido
# fallan, el deploy se para y la version anterior sigue sirviendo, en vez de
# morir el contenedor nuevo con el viejo ya apagado. Mientras el pre-deploy no
# este activado, `start.sh` lo sigue llamando (ver alli).
#
# Los tres primeros pasos son FATALES a proposito. Entre el 2026-09-22
# (`12ff838`, «Temporarily disable content_loader») y el 2026-09-24 el
# arranque siguio adelante pese a todo y produccion arranco con las tablas
# vacias mientras `/health` decia 200.
set -euo pipefail

if [ -z "${DATABASE_URL:-}" ]; then
    echo "[boot] DATABASE_URL no esta definida; abortando" >&2
    exit 1
fi
if [ -z "${ENVIRONMENT:-}" ]; then
    echo "[boot] ENVIRONMENT no esta definida; abortando" >&2
    exit 1
fi

echo "[boot] alembic upgrade head..."
alembic upgrade head

echo "[boot] cargando contenido (content_loader)..."
python -m app.services.content_loader

echo "[boot] cuenta de dueno (OWNER_EMAIL / OWNER_PASSWORD)..."
python -m app.services.bootstrap_owner

echo "[boot] seed de gamificacion..."
python -m app.services.seed || echo "[boot] seed fallido; se continua (no bloquea el arranque)" >&2

