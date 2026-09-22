#!/usr/bin/env bash
set -e

echo "[start] Whetzy backend starting..."
echo "[start] DATABASE_URL = ${DATABASE_URL:-(NOT SET)}"

# Run migrations only if database is reachable
if [ -n "$DATABASE_URL" ]; then
    echo "[start] Attempting to run migrations..."
    alembic upgrade head || {
        echo "[warning] Alembic failed, but continuing anyway..."
    }
else
    echo "[warning] DATABASE_URL not set - skipping migrations"
fi

echo "[start] Starting Gunicorn..."
exec gunicorn app.main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60
