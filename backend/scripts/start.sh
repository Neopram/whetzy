#!/usr/bin/env bash

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"

echo "[start] Starting Whetzy backend (PID: $$)"
echo "[start] Environment: ${ENVIRONMENT:-development}"

# If migrations are enabled, run them in the background (don't block server startup)
if [ "${SKIP_MIGRATIONS:-false}" != "true" ]; then
    echo "[start] Scheduling database migrations in background..."
    # Run migrations in background with timeout protection
    (
        set +e  # Don't exit on error in this subshell
        echo "[migrations] Starting Alembic upgrade..."
        timeout 300 alembic upgrade head 2>&1 | while IFS= read -r line; do
            echo "[migrations] $line"
        done
        RESULT=$?
        if [ $RESULT -eq 0 ]; then
            echo "[migrations] Completed successfully"
        elif [ $RESULT -eq 124 ]; then
            echo "[migrations] TIMEOUT: Migration took longer than 300 seconds"
        else
            echo "[migrations] Exited with code $RESULT"
        fi
    ) &
    MIGRATION_PID=$!
    echo "[start] Migration process PID: $MIGRATION_PID"
else
    echo "[start] SKIP_MIGRATIONS=true; not running migrations"
fi

echo "[start] Starting Gunicorn server..."
echo "[start] Listening on 0.0.0.0:8000 with 2 workers"
echo "[start] Server starting..."

exec gunicorn app.main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --worker-tmp-dir /dev/shm
