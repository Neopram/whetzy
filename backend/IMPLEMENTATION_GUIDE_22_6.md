# Series 22.6 Implementation Guide

This document explains how to integrate the new scaling components (rate limiting, pagination, caching, background jobs) into existing endpoints.

## Components Added

### 1. Rate Limiter (`app/core/rate_limiter.py`)

**Abstraction**: Supports both in-memory (default) and Redis backends.

**Usage**:

```python
from app.core.rate_limiter import get_rate_limiter
from app.core.config import settings

# In lifespan or app initialization:
rate_limiter = get_rate_limiter(settings.REDIS_URL)

# In an endpoint:
is_allowed = await rate_limiter.is_allowed(
    key=f"{client_ip}:auth",  # e.g. "192.168.1.1:auth"
    limit=12,  # 12 requests
    window_seconds=60  # per 60 seconds
)

if not is_allowed:
    return JSONResponse(
        {"detail": "Rate limited"},
        status_code=429
    )
```

**Note**: The existing `RateLimitMiddleware` in `app/core/security_middleware.py` already implements rate limiting for the entire app. The `rate_limiter.py` module provides a lower-level abstraction for custom per-endpoint rate limiting if needed.

### 2. Pagination (`app/core/pagination.py`)

**Usage** in endpoints:

```python
from fastapi import Depends
from sqlalchemy import select, func
from app.core.pagination import PaginationParams, PaginatedResponse
from app.models.content import GlossaryTerm

@router.get("/glossary")
async def list_glossary(
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    # Get total count
    total = await db.scalar(select(func.count()).select_from(GlossaryTerm))
    
    # Get paginated items
    items = await db.scalars(
        select(GlossaryTerm)
        .limit(params.limit)
        .offset(params.offset)
    )
    
    return PaginatedResponse(
        items=[item.to_dict() for item in items],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )
```

**Frontend usage**:

```typescript
// First page
const response = await fetch("/api/v1/glossary?limit=50&offset=0");
const { items, total, has_more } = await response.json();

// Next page
const response = await fetch(`/api/v1/glossary?limit=50&offset=${offset + 50}`);
```

### 3. Cache Headers (`app/core/cache.py`)

**Usage** in endpoints:

```python
from app.core.cache import public_cache_response, private_cache_response

@router.get("/glossary")
async def list_glossary(db: AsyncSession = Depends(get_db)):
    items = ...
    # Cache publicly for 5 minutes (default)
    return public_cache_response({"items": items})

@router.get("/user/progress")
async def get_progress(user: User = Depends(get_current_user)):
    progress = ...
    # Cache privately (browser only) for 1 minute
    return private_cache_response({"progress": progress}, max_age=60)
```

Or manually set headers:

```python
from fastapi.responses import JSONResponse
from app.core.cache import set_cache_header

response = JSONResponse({"data": items})
set_cache_header(response, max_age=300, is_private=False)
return response
```

### 4. Background Jobs (`app/models/job.py`, `app/services/job_worker.py`)

**Create a job**:

```python
from app.models.job import Job
from sqlalchemy import insert

# In an endpoint
new_job = Job(
    user_id=user.id,
    job_type="send_email",
    payload={
        "email": user.email,
        "subject": "Password Reset",
        "body": "Click here to reset..."
    },
    status="queued"
)
db.add(new_job)
await db.commit()

# Return immediately
return {"message": "Email will be sent shortly", "job_id": new_job.id}
```

**Register a job handler**:

```python
from app.services.job_worker import register_job_handler

@register_job_handler("send_email")
async def send_email_job(job: Job, db: AsyncSession) -> dict:
    payload = job.payload
    email = payload["email"]
    subject = payload["subject"]
    body = payload["body"]
    
    # Send email
    # await email_service.send(email, subject, body)
    
    return {"email": email, "sent": True}
```

**Enable job worker in lifespan** (`app/main.py`):

```python
import asyncio
from app.services.job_worker import job_worker_loop
from app.core.db import AsyncSessionLocal

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # ... existing setup ...
    
    # Start background job worker
    job_worker_task = asyncio.create_task(job_worker_loop(AsyncSessionLocal))
    logger.info("Job worker started")
    
    yield  # App is running
    
    # Shutdown
    job_worker_task.cancel()
    logger.info("Job worker stopped")
    await close_db()
```

## Migration & Database

After adding the new components, run the Alembic migration:

```bash
cd backend
alembic upgrade head
```

This creates the `jobs` table.

## Configuration

### Redis (Optional)

To use Redis-backed rate limiting for horizontal scaling:

```bash
# Set environment variable
export REDIS_URL="redis://localhost:6379/0"

# Or in .env
REDIS_URL=redis://localhost:6379/0
```

Free Redis providers:
- **Upstash** (https://upstash.com): Free tier, serverless
- **Redis Cloud** (https://redis.com): Free tier, managed
- **Railway Redis** (https://railway.app): Free add-on for Railway projects

### Database Pool

Tuning for better connection pooling (already configured in `app/core/config.py`):

```python
DATABASE_POOL_SIZE = 10  # Min connections to maintain
DATABASE_MAX_OVERFLOW = 20  # Additional connections under spike
```

For Railway, these defaults are safe up to 500k users.

## Testing

Run the included tests:

```bash
pytest tests/test_rate_limiter.py -v
pytest tests/test_pagination.py -v
```

Run load test:

```bash
k6 run backend/tests/load/baseline.js --vus 1000 --duration 60s
```

## Migration Checklist

- [ ] Add `.pre-commit-config.yaml` (supply chain)
- [ ] Create `docs/supply-chain.md` (supply chain)
- [ ] Create `docs/cloudflare-config.md` (Cloudflare)
- [ ] Create `docs/incidents/runbook.md` (incidents)
- [ ] Create `docs/incidents/postmortem-template.md` (incidents)
- [ ] Create `docs/capacity.md` (scaling)
- [ ] Create `backend/tests/load/baseline.js` (load testing)
- [ ] Run `alembic upgrade head` to create jobs table
- [ ] Add job worker to `app/main.py` lifespan (see above)
- [ ] Update endpoints to use `PaginationParams` and `public_cache_response` / `private_cache_response`
- [ ] Register job handlers in `app/services/job_worker.py`
- [ ] Test locally: `pytest`, `k6 run baseline.js`
- [ ] Run `python scripts/check_question_bank.py` and `pytest tests/content` before pushing

## Performance Targets

After implementing these changes:

| Metric | Target | Current |
|--------|--------|---------|
| p95 latency | <500ms | ~50ms (on baseline) |
| Error rate | <1% | ~0% |
| Cache hit ratio | >60% | TBD |
| Concurrent users | 1,000+ | TBD |
| DB connections | <30 | <10 |

Run load test to verify targets are met.
