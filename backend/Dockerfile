# syntax=docker/dockerfile:1
# Build context: repo root (not backend/).
# docker-compose: context: .  dockerfile: backend/Dockerfile
# Railway:        railway.toml sets rootDirectory / dockerfilePath

# ---- Builder stage: compile wheels for all dependencies ----------------
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt


# ---- Runtime stage: slim image with only the built wheels ---------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    CONTENT_DIR=/app/content

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system app && adduser --system --ingroup app app

COPY --from=builder /build/wheels /wheels
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/scripts ./scripts
COPY backend/alembic.ini ./alembic.ini

# Content bank baked into the image (no volume mounts in Railway)
COPY content ./content

RUN chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["bash", "scripts/start.sh"]
