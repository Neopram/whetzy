#!/usr/bin/env bash

# Exit on any error EXCEPT when continuing with caution
# set -e is too aggressive; we'll handle errors explicitly

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"

echo "[start] Environment: ${ENVIRONMENT:-development}"
echo "[start] DEBUG: $(python -c 'import sys; print(sys.version)')"
echo "[start] Working directory: $(pwd)"

# Run migrations if not explicitly disabled
if [ "${SKIP_MIGRATIONS:-false}" != "true" ]; then
    echo "[start] Running database migrations..."
    timeout 120 alembic upgrade head
    ALEMBIC_EXIT=$?
    
    if [ $ALEMBIC_EXIT -eq 124 ]; then
        echo "[WARNING] Alembic timed out after 120 seconds. This may indicate a stuck migration or database connection issue."
        echo "[WARNING] Continuing anyway to start the server..."
    elif [ $ALEMBIC_EXIT -ne 0 ]; then
        echo "[WARNING] Alembic exited with code $ALEMBIC_EXIT"
        echo "[WARNING] Continuing anyway to start the server..."
    else
        echo "[start] Migrations completed successfully"
    fi
else
    echo "[start] SKIP_MIGRATIONS=true; skipping database migrations"
fi

echo "[start] Starting Gunicorn..."
echo "[start] Listening on 0.0.0.0:8000 with 2 workers"
exec gunicorn app.main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
