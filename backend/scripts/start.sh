#!/usr/bin/env bash
# Arranque de produccion: esquema -> contenido -> cuenta de dueno -> seed -> servidor.
#
# Los tres primeros pasos son FATALES a proposito. Entre el 2026-09-22
# (`12ff838`, «Temporarily disable content_loader») y el 2026-09-24 este script
# siguio adelante pese a todo: `alembic` fallaba con «continuing anyway» y
# `content_loader` ni se ejecutaba, asi que produccion arranco con las tablas
# vacias — los 18 tracks respondian «Track not found» y nadie lo vio, porque
# `/health` decia 200. Un contenedor que muere aqui no pasa el healthcheck de
# Railway y ese deploy no sustituye al anterior; uno que arranca vacio si.
set -euo pipefail

echo "[start] Whetzy backend starting..."
if [ -z "${DATABASE_URL:-}" ]; then
    echo "[start] DATABASE_URL no esta definida; abortando" >&2
    exit 1
fi
# Sin ENVIRONMENT, config.py cae en «development» y se salta la guarda de
# SECRET_KEY: los JWT se firmarian con la clave de desarrollo, que es publica.
if [ -z "${ENVIRONMENT:-}" ]; then
    echo "[start] ENVIRONMENT no esta definida; abortando" >&2
    exit 1
fi

# D-4: con el pre-deploy de Railway activado (`bash scripts/boot_tasks.sh`) y
# BOOT_TASKS_IN_PREDEPLOY=1, las tareas ya corrieron antes del cambio de
# version y aqui solo se comprueba el esquema. Si aun asi no esta en la cabeza
# (variable puesta sin el pre-deploy), se corren aqui: nunca se arranca un
# servidor sobre un esquema viejo.
if [ "${BOOT_TASKS_IN_PREDEPLOY:-}" = "1" ] && alembic current 2>/dev/null | grep -q "(head)"; then
    echo "[start] tareas de arranque hechas en el pre-deploy; esquema en la cabeza"
else
    bash "$(dirname "$0")/boot_tasks.sh"
fi

# Railway (and most PaaS) proxy to $PORT. Listening on 8000 while the
# platform probes another port is the 502 'Application failed to respond'.
PORT="${PORT:-8000}"
echo "[start] Starting Gunicorn on 0.0.0.0:${PORT}..."
# --no-control-socket: gunicorn 25.1+ abre un socket de control en
# $XDG_RUNTIME_DIR o, sin el, en $HOME/.gunicorn/gunicorn.ctl. El usuario
# `app` del Dockerfile es de sistema (`adduser --system`) y su HOME es
# /nonexistent, asi que cada arranque en Railway escribia «Control server
# error: [Errno 13] Permission denied: '/nonexistent'». Nadie usa `gunicornc`
# en el contenedor: se apaga en vez de reubicarlo.
exec gunicorn app.main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind "0.0.0.0:${PORT}" \
  --timeout 60 \
  --no-control-socket
