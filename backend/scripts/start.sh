#!/usr/bin/env bash
set -e

echo "[start] Minimal startup - skipping migrations for now"
echo "[start] Starting gunicorn..."

exec gunicorn app.main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60
