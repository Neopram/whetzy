# Series 22.4–22.7 Implementation Summary

Four comprehensive series for supply chain security, Cloudflare optimization, scaling, and incident management.

**Date**: 2026-09-19  
**Status**: Ready for implementation  
**Priority**: Non-blocking (can be implemented independently or in sequence)

---

## Series Overview

### 22.4 — Supply Chain at €0 (Free OSS Tools)

**Objective**: Secure the software supply chain with dependency scanning and secret detection.

**What''s Included**:
- `.pre-commit-config.yaml`: Hooks for gitleaks, bandit, semgrep, ruff, yamllint
- `docs/supply-chain.md`: Dependency pinning strategy, SBOM generation, Dependabot setup

**Checklist**:
```
- [ ] Install pre-commit hooks locally: pip install pre-commit && pre-commit install
- [ ] Verify gitleaks is blocking commits with secrets
- [ ] Enable Dependabot in GitHub (Settings → Code Security → Dependabot)
- [ ] Run pre-commit on all files: pre-commit run --all-files
- [ ] Generate SBOM before release: pip install cyclonedx-python && cyclonedx-python -o requirements.txt --output-file sbom.json
```

**Files**:
- `.pre-commit-config.yaml` (created)
- `docs/supply-chain.md` (created)

**Cost**: €0

---

### 22.5 — Cloudflare Free Tier (WAF + Cache)

**Objective**: DDoS protection, WAF, rate limiting, and CDN caching at zero cost.

**What''s Included**:
- WAF managed rulesets (OWASP Top 10)
- Rate limiting rules (/auth: 12 req/min, /tutor: 12 req/min, /api: 300 req/min)
- Bot Fight Mode (automatic CAPTCHA challenges)
- Cache rules (5-min cache for public data, no-cache for private)
- Turnstile CAPTCHA widget (optional, abuse-triggered)

**Checklist**:
```
- [ ] Verify Cloudflare DNS is configured for whetzy.com
- [ ] Enable Cloudflare Managed Ruleset (WAF)
- [ ] Create 4 rate-limiting rules (see cloudflare-config.md)
- [ ] Enable Bot Fight Mode
- [ ] Create 4 cache rules
- [ ] Backend: Add Cache-Control headers (see app/core/cache.py)
- [ ] Optional: Set up Turnstile CAPTCHA widget
```

**Files**:
- `docs/cloudflare-config.md` (created)

**Cost**: €0

---

### 22.6 — Scaling Without Cost (ADR-19)

**Objective**: Horizontal scaling and capacity planning for 500k+ users.

**What''s Included**:

1. **Rate Limiter Interface**: `app/core/rate_limiter.py`
   - In-memory by default (existing middleware)
   - Redis backend if REDIS_URL is set
   
2. **Pagination**: `app/core/pagination.py`
   - `PaginationParams`: limit (1–100, default 50) + offset
   - `PaginatedResponse`: items + total + has_more flag
   - Use in all list endpoints

3. **Cache Headers**: `app/core/cache.py`
   - `public_cache_response()`: 5-min cache for glossary, tracks
   - `private_cache_response()`: 1-min cache for user-specific data
   - `no_cache_response()`: no-store for auth, payments

4. **Background Jobs**: 
   - `app/models/job.py`: Job model (user_id, job_type, payload, status, result)
   - `app/services/job_worker.py`: Job executor + handlers
   - `alembic/versions/20260919_1400_*.py`: Migration for jobs table
   - Lifespan worker: Processes queued jobs every 5 seconds

5. **Documentation & Testing**:
   - `docs/capacity.md`: Database sizing, connection pool tuning, cache strategy, load testing
   - `backend/tests/load/baseline.js`: k6 load test (1,000 VUs, 60s)
   - `backend/IMPLEMENTATION_GUIDE_22_6.md`: Integration guide
   - `backend/tests/test_rate_limiter.py`: Unit tests
   - `backend/tests/test_pagination.py`: Unit tests

**Checklist**:
```
- [ ] Run alembic upgrade head (creates jobs table)
- [ ] Add job worker to app/main.py lifespan
- [ ] Register job handlers (email, export, DKT retrain, etc.)
- [ ] Update endpoints to use PaginationParams
- [ ] Add cache headers to GET endpoints
- [ ] Run pytest backend/tests/ (verify tests pass)
- [ ] Run k6 load test: k6 run baseline.js --vus 1000 --duration 60s
- [ ] Verify p95 latency <500ms, error rate <1%
- [ ] Optional: Configure Redis for horizontal scaling
```

**Files** (Created):
- `app/core/rate_limiter.py`
- `app/core/pagination.py`
- `app/core/cache.py`
- `app/models/job.py`
- `app/services/job_worker.py`
- `alembic/versions/20260919_1400_x5y6z7a8b9c0_background_jobs.py`
- `backend/tests/test_rate_limiter.py`
- `backend/tests/test_pagination.py`
- `backend/tests/load/baseline.js`
- `docs/capacity.md`
- `backend/IMPLEMENTATION_GUIDE_22_6.md`

**Cost**: €0 (optional Redis: €0–7/mo depending on provider)

---

### 22.7 — Incidents & Status Page

**Objective**: Structured incident response, post-mortem process, and status transparency.

**What''s Included**:

1. **Runbook** (`docs/incidents/runbook.md`):
   - P1 (Complete Outage): Respond in 15 min, post-mortem in 4 hrs
   - P2 (Degraded): Respond in 1 hr, post-mortem in 24 hrs
   - P3 (Minor): Respond in 8 hrs, post-mortem in 1 week
   - Quick diagnostics: Backend health, deployments, DB status, memory/CPU, rate limits, Cloudflare analytics

2. **Post-Mortem Template** (`docs/incidents/postmortem-template.md`):
   - Executive summary
   - Timeline
   - Impact (scope, business loss, data)
   - Root cause analysis
   - Resolution
   - Preventive measures (short/medium/long-term)
   - Action items + owners + due dates

3. **Monitoring & Status**:
   - **UptimeRobot** (free): HTTP ping every 5 min, email/Slack alerts
   - **Instatus** (free): Public status page + incident templates + subscriber notifications
   - **Cloudflare Analytics**: Traffic, cache, security, DDoS events

**Checklist**:
```
- [ ] Set up UptimeRobot account and add monitor for /health/ready
- [ ] Create Instatus account and configure status page
- [ ] Share public status page URL in app footer (https://whetzy.instatus.com)
- [ ] Enable UptimeRobot → Slack webhook for alerts
- [ ] Enable Instatus → Email notifications for subscribers
- [ ] Schedule P1/P2 post-mortems within SLAs
- [ ] Archive completed post-mortems in docs/incidents/
```

**Files**:
- `docs/incidents/runbook.md` (created)
- `docs/incidents/postmortem-template.md` (created)

**Cost**: €0 (UptimeRobot free, Instatus free tier)

---

## Implementation Order

**Recommended sequence** (non-blocking; can be done in parallel):

1. **Week 1: Supply Chain (22.4) + Cloudflare (22.5)**
   - Install pre-commit hooks
   - Enable Dependabot
   - Configure Cloudflare WAF, rate limiting, cache rules
   - Review `docs/supply-chain.md` and `docs/cloudflare-config.md`

2. **Week 2–3: Scaling (22.6) Core**
   - Run `alembic upgrade head`
   - Add rate limiter, pagination, cache modules to backend
   - Update 2–3 endpoints as examples (e.g., /glossary, /tracks)
   - Run unit tests: `pytest backend/tests/test_*.py`
   - Run k6 load test locally

3. **Week 3–4: Scaling (22.6) Endpoints**
   - Gradually update all list endpoints with pagination
   - Add cache headers to GET endpoints
   - Register job handlers (email, export, DKT retrain)
   - Test end-to-end with k6 against production-like DB

4. **Week 4: Incidents (22.7) + Monitoring**
   - Set up UptimeRobot + Instatus
   - Write runbook and post-mortem template
   - Run a mock incident drill (internal test)
   - Update docs/RUNBOOK.md with new incident flow

---

## Verification Checklist

Before marking series as done:

### 22.4 Supply Chain
- [ ] Pre-commit hooks run locally and block secrets
- [ ] Dependabot enabled and posting PRs for updates
- [ ] CI pipeline runs pip-audit successfully
- [ ] SBOM can be generated: `cyclonedx-python -o requirements.txt --output-file sbom.json`

### 22.5 Cloudflare
- [ ] WAF Managed Ruleset enabled (blocks XSS, SQL injection, etc.)
- [ ] 4 rate-limiting rules created and visible in Cloudflare dashboard
- [ ] Bot Fight Mode: On
- [ ] Cache rules: /glossary (5 min), /tracks (5 min), landing page (1 hr), /auth (no-cache)
- [ ] Backend sends Cache-Control headers: `curl -I https://api-production-9751.up.railway.app/api/v1/glossary | grep Cache-Control`

### 22.6 Scaling
- [ ] `alembic upgrade head` succeeds; jobs table exists
- [ ] Job worker starts in app lifespan (check Railway logs for "Job worker started")
- [ ] `pytest backend/tests/ --cov=app --cov-report=term-missing -q` passes with >80% coverage
- [ ] k6 load test runs: `k6 run baseline.js --vus 1000 --duration 60s`
- [ ] k6 SLAs pass: p95 latency <500ms, error rate <1%, throughput >100 req/sec
- [ ] Endpoints support pagination: `curl "https://api-production-9751.up.railway.app/api/v1/glossary?limit=20&offset=20"`
- [ ] At least 2–3 endpoints return paginated responses with `has_more` flag
- [ ] Private endpoints return `Cache-Control: no-store`
- [ ] Public endpoints return `Cache-Control: public, max-age=300`

### 22.7 Incidents
- [ ] UptimeRobot monitor created and healthy: `https://stats.uptimerobot.com`
- [ ] Instatus status page accessible and public
- [ ] Runbook covers P1/P2/P3 escalation paths
- [ ] Post-mortem template has all required sections
- [ ] Mock incident drill completed (team walked through runbook)
- [ ] Slack `#incidents` channel created for incident declarations

---

## Cost Summary

| Series | Component | Free Tier | Cost |
|--------|-----------|-----------|------|
| 22.4 | gitleaks, bandit, semgrep | ✓ | €0 |
| 22.4 | Dependabot | ✓ (GitHub) | €0 |
| 22.5 | Cloudflare WAF | ✓ | €0 |
| 22.5 | Cloudflare Rate Limiting | ✓ (20 rules) | €0 |
| 22.5 | Cloudflare Bot Fight Mode | ✓ | €0 |
| 22.5 | Cloudflare Cache | ✓ | €0 |
| 22.5 | Turnstile CAPTCHA | ✓ (100k/mo) | €0 |
| 22.6 | Database (Railway Postgres) | ✓ (5GB) | €0–7 |
| 22.6 | Redis (optional) | ✓ (Upstash free) | €0–7 |
| 22.6 | k6 load testing | ✓ (local) | €0 |
| 22.7 | UptimeRobot | ✓ | €0 |
| 22.7 | Instatus | ✓ | €0 |
| **TOTAL** | | | **€0** |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Pre-commit hooks too strict | Developer friction | Tune linting rules in `.pre-commit-config.yaml`; allow skipping with `--no-verify` in CI |
| Pagination breaks existing clients | API breaks | Gradual rollout; add pagination to 1–2 endpoints first; test with load tests |
| Cache stale data | Users see outdated info | Set reasonable TTLs (5 min); invalidate on updates (Cloudflare purge) |
| Job worker drops tasks on restart | Lost emails, exports | Persist jobs in DB; mark `done` only after confirmation; retry failed jobs |
| Incident SLAs too strict | Unrealistic expectations | Base SLAs on team capacity; adjust in post-mortems |

---

## References

- [docs/supply-chain.md](./supply-chain.md): Full supply chain security guide
- [docs/cloudflare-config.md](./cloudflare-config.md): Cloudflare free tier setup
- [docs/capacity.md](./capacity.md): Database sizing, connection pools, caching, load testing
- [docs/incidents/runbook.md](./incidents/runbook.md): Incident response SLAs and procedures
- [docs/incidents/postmortem-template.md](./incidents/postmortem-template.md): Post-mortem structure
- [backend/IMPLEMENTATION_GUIDE_22_6.md](../backend/IMPLEMENTATION_GUIDE_22_6.md): Integration guide for scaling components
- [.pre-commit-config.yaml](./.pre-commit-config.yaml): Security hooks
- [backend/tests/load/baseline.js](../backend/tests/load/baseline.js): k6 load test script

---

## Next Steps

1. Review all documentation (this document + the four series docs)
2. Prioritize by team capacity: 22.4 (easiest) → 22.5 → 22.6 → 22.7
3. For each series:
   - Read the docs thoroughly
   - Check off the checklist
   - Test (unit tests, integration tests, load tests)
   - Merge to master (auto-deploys to production)
   - Verify in production (monitoring, metrics, status page)
4. Post-mortems: Document learnings, adjust SLAs/thresholds based on production experience

**Questions?** See individual series docs or open GitHub issues tagged `22.4`, `22.5`, `22.6`, `22.7`.
