#!/usr/bin/env bash
set -e

echo "[start] Running Alembic migrations..."
if ! alembic upgrade head; then
  echo "[ERROR] Alembic migration failed. Exiting."
  exit 1
fi
echo "[start] Alembic migration completed successfully"

echo "[start] Starting Gunicorn with Uvicorn workers..."
echo "[start] Binding to 0.0.0.0:8000 with 2 workers, timeout=60s"
exec gunicorn app.main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
