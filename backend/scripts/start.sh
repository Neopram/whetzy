#!/usr/bin/env bash
set -e
echo "[start] alembic upgrade..."
alembic upgrade head
echo "[start] gunicorn..."
exec gunicorn app.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 60 -
