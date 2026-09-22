#!/usr/bin/env bash
set -o pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"

echo "[start] Starting Whetzy backend..."
echo "[start] Python version: $(python --version)"
echo "[start] Working directory: $(pwd)"
echo "[start] Environment: ${ENVIRONMENT:-not set}"

# Step 1: Verify database connectivity
echo "[start] Checking database connectivity..."
python -c "
import asyncio
import sys
from app.core.db import AsyncSessionLocal

async def check_db():
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(__import__('sqlalchemy').text('SELECT 1'))
            print(f'[start] Database connection successful')
            return True
    except Exception as e:
        print(f'[ERROR] Database connection failed: {type(e).__name__}: {e}')
        return False

success = asyncio.run(check_db())
sys.exit(0 if success else 1)
" || {
    echo "[ERROR] Database check failed. Cannot proceed."
    exit 1
}

# Step 2: Run Alembic migrations
echo "[start] Running Alembic migrations..."
alembic upgrade head || {
    echo "[ERROR] Alembic migration failed. Cannot proceed."
    exit 1
}
echo "[start] Migrations completed successfully"

# Step 3: Verify app loads
echo "[start] Verifying FastAPI app loads..."
python -c "from app.main import app; print('[start] FastAPI app loaded successfully')" || {
    echo "[ERROR] FastAPI app failed to load."
    exit 1
}

# Step 4: Start Gunicorn
echo "[start] Starting Gunicorn with 2 Uvicorn workers"
echo "[start] Listening on 0.0.0.0:8000"
exec gunicorn app.main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --graceful-timeout 30 \
  --max-requests 1000 \
  --max-requests-jitter 100
