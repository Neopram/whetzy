# Scaling Without Cost (Series 22.6) — Capacity & Architecture

Zero-cost scaling strategies and capacity planning for the learning engine.

## Architecture Overview

### Request Flow

```
User → Cloudflare (Cache, Rate Limiting, WAF)
     → Railway Backend (FastAPI + Uvicorn workers)
     → PostgreSQL Database (connection pool)
     → Redis (optional, rate limiting + caching)
```

### Horizontal vs. Vertical Scaling

| Dimension | Free Tier | Strategy |
|-----------|-----------|----------|
| API Servers | 1 process | Multi-threaded (Uvicorn workers) + Railway auto-scaling |
| Database | Shared Postgres (512MB–5GB) | Read replicas (Railway: $7/mo per replica) or query optimization |
| Cache | In-memory (Python dict) | Redis (free tier at [upstash.com](https://upstash.com)) or skip |
| CDN | Cloudflare | Free forever (100k HTTP requests/month, unlimited HTTPS) |

---

## Database Capacity Planning

### Planning scenario (not a baseline)

> **Correction 2026-09-25:** this table was titled «Current Baseline (2026-09-19)» and said
> «~50k users — estimate from sign-ups». Whetzy has **zero real users**
> (`AUDITORIA_EXTERNA_2026-09-19.md`), and the bank count lives in `CATALOGO_MAESTRO.md` §1
> (guarded by `check_docs.py`). Read the rows below as a **sizing scenario**, not measurements.

| Metric | Value | Notes |
|--------|-------|-------|
| Users | ~50k (scenario) | Hypothetical load for sizing; real users today: 0 |
| Questions in bank | ~5,000 | See `docs/CATALOGO_MAESTRO.md` |
| Quiz attempts per user/year | ~100 | 2–3 per week |
| Database size | ~500MB | Users + questions + progress + analytics |
| Concurrent connections | ~50 (avg), ~200 (spike) | Pool size: 10, max overflow: 20 |
| p95 query latency | ~50ms | Baseline; >500ms is degraded |

### Scaling Calculation

**Formula**: Database size grows with:
- Users × (avg row size per user)
- Quiz attempts × (avg row size per attempt)
- Analytics events × (event size)

**Estimate**:
```
1 user = ~2KB (profile + progress)
1 quiz attempt = ~1KB (answers, timing, metadata)
1 analytics event = ~500B

50k users × 2KB = 100MB (user data)
50k users × 100 attempts/year × 1KB = 5GB (quiz data, annual)
Bulk analytics = ~1GB

Total ~6GB after 1 year (manageable on Railway Postgres Starter)
```

### Scaling Thresholds

| Users | Approx DB Size | Recommended Action |
|-------|---|---|
| 0–10k | <500MB | Single Postgres (Railway free: 5GB) |
| 10k–50k | 500MB–2GB | Single Postgres with tuning (indexes, query optimization) |
| 50k–100k | 2GB–5GB | Upgrade to Railway Postgres Starter ($7/mo) |
| 100k–500k | 5GB–20GB | Add read replica ($7/mo) + query optimization + caching |
| 500k+ | 20GB+ | PostgreSQL Pro tier + sharding (out of scope for free tier) |

**Current status** (Sep 2026): ~50k users, 500MB DB → can add 50k more users before hitting Railway limit.

---

## API Server Capacity

### Uvicorn Worker Configuration

Backend runs Uvicorn with the following defaults (see `backend/app/main.py`):

```python
# Number of worker processes (set via UVICORN_WORKERS env var)
UVICORN_WORKERS = 4  # Railway default; can increase to 8

# Each worker handles concurrent requests:
# - Default: 1000 max concurrent connections per worker
# - Tunable via UVICORN_LOOP_SETUP_KWARGS
```

**Throughput estimate**:
```
4 workers × 1000 connections/worker = 4,000 concurrent requests capacity
Avg response time: 50ms → ~80 requests/sec per worker = 320 req/sec total

If spikes exceed this: Cloudflare queues requests, returns 429 to excess
```

### Connection Pool Tuning

Configure in `backend/app/core/config.py` (via environment variables):

```python
DATABASE_POOL_SIZE = 10       # Min connections (Railway: default 10)
DATABASE_MAX_OVERFLOW = 20    # Max additional connections under spike
```

**Calculation**:
```
10 workers × 1 DB connection per request = 10 concurrent DB connections
If spike: 10 + 20 = 30 total connections allowed
Railway Postgres: Supports 100+ connections (free tier), so we''re safe
```

**If you see "QueuePool timeout"**:
- Either: Too many requests for pool size (increase POOL_SIZE or add Redis cache)
- Or: Long-running queries blocking connections (optimize queries or add read replica)

---

## Rate Limiting (Backend)

### In-Memory Limiter (Current)

Implemented in `backend/app/core/security_middleware.py`:

```python
class RateLimitMiddleware:
    def __init__(self, default_limit=120, auth_limit=12):
        self._default_limit = default_limit  # 120 req/min for API
        self._auth_limit = auth_limit        # 12 req/min for /auth
```

**Behavior**:
- Per-IP, fixed-window (60 seconds)
- In-process memory (Python dict)
- No persistence (resets on restart)

**Limits to Know**:
```
/auth/login, /auth/register:  12 req/min per IP (12 attempts per minute)
/tutor:                        12 req/min per IP (expensive LLM calls)
/api/v1/*:                     120 req/min per IP (general API)
/health:                       Unlimited (health checks exempt)
```

### Redis-Backed Limiter (Optional)

To scale across multiple instances or persist across restarts:

```python
# Set environment variable
export REDIS_URL="redis://localhost:6379/0"

# Backend auto-detects and uses Redis if available
# (See backend/app/core/rate_limiter.py for implementation)
```

Free Redis options:
- **Upstash**: [upstash.com](https://upstash.com) — free tier: 10,000 commands/day
- **Redis Cloud**: [redis.com](https://redis.com) — free tier: 30MB
- **Railway Redis add-on**: $0/mo (included in free tier, but limited)

---

## Pagination (List Endpoints)

### Implementation

All list endpoints support `limit` and `offset` query parameters:

```
GET /api/v1/glossary?limit=50&offset=0
GET /api/v1/tracks?limit=20&offset=40
```

**Defaults**:
- `limit`: 50 (max: 100)
- `offset`: 0

**Schema** (FastAPI):

```python
from pydantic import BaseModel, Field

class PaginationParams(BaseModel):
    limit: int = Field(50, ge=1, le=100, description="Items per page")
    offset: int = Field(0, ge=0, description="Number of items to skip")

# Endpoint:
@router.get("/glossary")
async def list_glossary(
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    query = select(Glossary).limit(params.limit).offset(params.offset)
    items = await db.scalars(query)
    return {"items": items, "total": len(items), "limit": params.limit, "offset": params.offset}
```

**Why**:
- Prevents loading all 5k questions into memory on a single request
- Reduces bandwidth: Users only fetch what they see
- Improves frontend responsiveness: Lazy-load as user scrolls

---

## Caching Strategy

### HTTP Cache Headers

Backend sends `Cache-Control` headers (see `backend/app/core/cache.py`):

```python
# GET /api/v1/glossary (static reference data)
response.headers["Cache-Control"] = "public, max-age=300"  # 5 min cache

# GET /api/v1/tracks (occasional updates)
response.headers["Cache-Control"] = "public, max-age=300"

# GET /api/v1/user/progress (private, personalized)
response.headers["Cache-Control"] = "private, max-age=60"  # Only cached by browser

# POST, DELETE, etc. (must not cache)
response.headers["Cache-Control"] = "no-store"
```

**Layered Caching**:
1. **Cloudflare edge cache** (5 min): Shared across all users, reduces backend load
2. **Browser cache** (60 sec–5 min): Reduces network round-trips for user
3. **Redis (optional)**: Session caching, rate limit state (if REDIS_URL set)

**Cache hit ratio goal**: >60% for static assets (glossary, tracks, landing page)

### Invalidation

On content updates:

```python
# When a glossary term is updated (PATCH /api/v1/glossary/{id}):
1. Update database
2. Purge Cloudflare cache for /api/v1/glossary*
   (Cloudflare API: POST /cache/purge)
3. Clear Redis cache (if Redis is used)

# Code:
import httpx
async def purge_cloudflare(url_pattern: str):
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache",
            json={"files": [url_pattern]},
            headers={"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"}
        )
```

---

## Background Jobs (Async Tasks)

### Architecture

Add a `jobs` table to the database for asynchronous work (email, exports, etc.):

```sql
CREATE TABLE jobs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL,  -- ''email'', ''export'', ''dkt_train''
    status VARCHAR(20) DEFAULT ''queued'',  -- ''queued'', ''running'', ''done'', ''failed''
    payload JSONB NOT NULL,  -- e.g., {"format": "csv", "track_id": 123}
    result JSONB,  -- e.g., {"file_url": "s3://..."}
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_jobs_user_status ON jobs(user_id, status);
```

### Lifespan Worker

In `backend/app/main.py` lifespan, spawn a background worker:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    import asyncio
    
    # Start job worker
    job_worker_task = asyncio.create_task(job_worker_loop())
    
    yield  # App is running
    
    # Shut down job worker
    job_worker_task.cancel()

async def job_worker_loop():
    """Poll jobs table and process queued jobs."""
    while True:
        try:
            await process_pending_jobs()
            await asyncio.sleep(5)  # Poll every 5 seconds
        except Exception as e:
            logger.error(f"Job worker error: {e}")
            await asyncio.sleep(10)

async def process_pending_jobs():
    """Fetch and execute pending jobs."""
    from app.core.db import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        jobs = await db.scalars(
            select(Job)
            .where(Job.status == "queued")
            .limit(10)  # Process max 10 per poll
        )
        
        for job in jobs:
            job.status = "running"
            job.started_at = datetime.utcnow()
            await db.commit()
            
            try:
                result = await execute_job(job)
                job.status = "done"
                job.result = result
            except Exception as e:
                job.status = "failed"
                job.error = str(e)
            
            job.completed_at = datetime.utcnow()
            await db.commit()
```

### Use Cases

- **Email sending**: Send password reset, quiz result emails asynchronously
- **Exports**: Generate CSV/PDF reports without blocking the API
- **Cron tasks**: DKT model retraining, analytics aggregation
- **Notifications**: Push notifications, streak reminders

---

## Load Testing (k6)

### Baseline Test

Create `backend/tests/load/baseline.js`:

```javascript
import http from 'http';
import { check, group, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },    // Ramp-up to 100 VUs over 2 min
    { duration: '5m', target: 1000 },   // Climb to 1,000 VUs
    { duration: '2m', target: 0 },      // Ramp-down to 0
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],  // 95th percentile <500ms
    http_req_failed: ['rate<0.1'],  // Error rate <10%
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  group('Health check', () => {
    let res = http.get(`${BASE_URL}/health`);
    check(res, { 'health is 200': (r) => r.status === 200 });
  });

  group('Get glossary (paginated)', () => {
    let res = http.get(`${BASE_URL}/api/v1/glossary?limit=50`);
    check(res, { 'glossary is 200': (r) => r.status === 200 });
  });

  group('Get tracks', () => {
    let res = http.get(`${BASE_URL}/api/v1/tracks`);
    check(res, { 'tracks is 200': (r) => r.status === 200 });
  });

  sleep(1);
}
```

### Run Locally

```bash
# Install k6
brew install k6  # macOS
# or: https://k6.io/docs/getting-started/installation/

# Run test
k6 run backend/tests/load/baseline.js --vus 100 --duration 60s

# Or with a specific base URL
BASE_URL=https://api-production-9751.up.railway.app k6 run baseline.js
```

### Metrics to Monitor

- **http_req_duration**: Response time (p50, p95, p99)
- **http_req_failed**: Percentage of failed requests
- **http_reqs**: Total requests per second (throughput)
- **vus**: Virtual users active at each stage

**Expected results** (baseline, 1,000 VUs):
- p95 latency: <500ms (API is responsive)
- Error rate: <1% (requests succeeding)
- Throughput: ~320 req/sec (with 50ms avg response time)

---

## Backup & Disaster Recovery

### Database Backups (Railway Managed)

Railway Postgres automatically backs up daily:

1. **Access backups**: Railway Dashboard → Postgres service → Backups
2. **Restore procedure**:
   ```bash
   # Option A: Via Railway UI
   # Click "Restore from backup" → select date → confirm

   # Option B: Via CLI
   railway backup restore --select
   ```

3. **Verify restore**:
   ```bash
   # SSH into new instance
   railway connect --service postgres
   SELECT COUNT(*) FROM users;  -- Should match old count
   ```

### Manual Backup (Recommended Before Major Changes)

```bash
# Export to local SQL dump
pg_dump postgresql://user:pass@host:5432/db > backup_$(date +%Y%m%d).sql

# Or export to CSV (for data analytics)
COPY (SELECT * FROM users) TO STDOUT CSV HEADER > users_backup.csv;
```

### Restore from Manual Backup

```bash
# Restore from SQL dump
psql postgresql://user:pass@host:5432/db < backup_20260919.sql

# Or from CSV
COPY users FROM ''/tmp/users_backup.csv'' CSV HEADER;
```

---

## Capacity Checklist

- [ ] Database pool size tuned: `DATABASE_POOL_SIZE=10, MAX_OVERFLOW=20`
- [ ] Pagination implemented on all list endpoints (limit, offset)
- [ ] Cache headers set on static content (/glossary, /tracks: 5 min TTL)
- [ ] Private content has no-store headers (/user/progress, /auth)
- [ ] Cloudflare cache rules configured (5 min for public, 0 for private)
- [ ] k6 load test baseline run: target p95 <500ms with 1,000 VUs
- [ ] Rate limiting thresholds tuned: /auth=12, /tutor=12, /api=120 req/min
- [ ] Monitoring in place: Prometheus metrics, Sentry errors, UptimeRobot
- [ ] Backup strategy documented and tested (Railway: restore from backup)
- [ ] Database indexes optimized (no N+1 queries; see EXPLAIN ANALYZE)
- [ ] Redis (optional) configured if horizontal scaling needed
