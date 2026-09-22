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

echo "[start] Seeding database with gamification data..."
python -c "
import asyncio
from app.services.seed import seed_gamification
from app.core.db import AsyncSessionLocal

async def seed():
    try:
        async with AsyncSessionLocal() as session:
            await seed_gamification(session)
        print('[seed] ✓ Gamification data loaded')
    except Exception as e:
        print(f'[seed] Warning: {e}')

asyncio.run(seed())
" 2>/dev/null || true

echo "[start] Starting Gunicorn..."
exec gunicorn app.main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60

