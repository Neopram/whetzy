#!/usr/bin/env bash
# Production entrypoint: ensure schema + content, then serve.
# For a mature deployment replace init_db (invoked by the loaders) with
# `alembic upgrade head`; kept simple here so the stack boots out of the box.
set -euo pipefail

echo "[start] loading content..."
python -m app.services.content_loader || echo "[start] content load skipped (no content dir mounted)"

echo "[start] seeding gamification..."
python -m app.services.seed || echo "[start] seed skipped"

echo "[start] launching gunicorn..."
exec gunicorn app.main:app \
  --workers "${WEB_CONCURRENCY:-4}" \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind "0.0.0.0:${PORT:-8000}" \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
