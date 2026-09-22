#!/usr/bin/env bash
# Production entrypoint: migrate schema, load content, serve.
set -euo pipefail

echo "[start] checking alembic stamp for existing schema..."
# If the users table exists but alembic_version does not, this is a pre-Alembic
# deployment. Stamp the baseline revision so alembic upgrade head only runs the
# new migrations (not the empty baseline that would try to recreate all tables).
python -c "
import asyncio, os, sys

BASELINE_REV = 'a1b2c3d4e5f6'  # initial_schema — all tables except duels

async def maybe_stamp():
    url = os.environ.get('DATABASE_URL', '')
    if not url.startswith('postgresql'):
        print('[stamp] non-postgres DB, skipping stamp check')
        return
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            r1 = await conn.execute(text(\"SELECT to_regclass('alembic_version')\"))
            alembic_exists = r1.scalar() is not None
            if alembic_exists:
                print('[stamp] alembic_version already exists, nothing to do')
                return
            r2 = await conn.execute(text(\"SELECT to_regclass('users')\"))
            users_exist = r2.scalar() is not None
            if users_exist:
                print(f'[stamp] pre-Alembic schema detected — stamping baseline {BASELINE_REV}')
                await conn.execute(text(
                    'CREATE TABLE alembic_version ('
                    '  version_num VARCHAR(32) NOT NULL, '
                    '  CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)'
                    ')'
                ))
                await conn.execute(text(
                    f\"INSERT INTO alembic_version (version_num) VALUES ('{BASELINE_REV}')\"
                ))
            else:
                print('[stamp] fresh DB — alembic upgrade will create everything')
    finally:
        await engine.dispose()

asyncio.run(maybe_stamp())
"

echo "[start] running alembic upgrade head..."
alembic upgrade head

#echo "[start] loading content..."
#if ! python -m app.services.content_loader; then
#  echo "[start] content_loader failed — check JSON syntax and skill IDs; aborting" >&2
#  exit 1
#fi

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
