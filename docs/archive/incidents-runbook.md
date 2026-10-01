# Incident Response Runbook (Series 22.7)

Severity levels, response procedures, and escalation paths for Whetzy incidents.

## Severity Levels

### P1 — Complete Outage (SLA: Respond in 15 min)

**Criteria**: Production backend is completely down; users cannot access the app.

- API returns 503 or is unreachable
- Database is unavailable
- Frontend shows error page for all users

**Response**:
1. Declare incident in Slack #incidents channel with message: `P1 INCIDENT: [Brief description]`
2. Page on-call engineer (PagerDuty or direct Slack)
3. Update status page to "Investigating" (Instatus)
4. Check Railway dashboard for deployment errors or resource exhaustion
5. If DB is down: Restart Postgres or failover to backup (see `docs/RUNBOOK.md`)
6. If app is down: Review logs in Railway / Sentry for the last error
7. Revert latest deployment if caused the issue
8. Restore service and verify via `GET /health/ready` returning 200
9. Post-mortem within 4 hours (use template in `postmortem-template.md`)

**Escalation**: If not resolved in 30 min, page secondary on-call or open support ticket with hosting provider.

---

### P2 — Degraded Service (SLA: Respond in 1 hour)

**Criteria**: Service is partially available; some users/features are affected.

- Authentication works but quiz pages are slow (>10s latency)
- Specific endpoints return 500 errors (e.g., `/api/v1/tutor/*` fails, others OK)
- Database performance is degraded (p95 latency >500ms)
- Memory/CPU usage is high but not maxed

**Response**:
1. Declare incident: `P2 INCIDENT: [Endpoint/Feature] degraded`
2. Update status page to "Degraded Performance"
3. Investigate root cause:
   - Check p95/p99 latencies in Prometheus (`/metrics` endpoint)
   - Look for spike in request volume (bot attack?) — compare with baseline
   - Review Sentry for repeated errors
   - Check Cloudflare analytics for rate-limit hits
4. Mitigation options:
   - If rate-limited: Increase rate limit threshold (see `app/core/security_middleware.py`)
   - If slow queries: Check database explain plans, add index if needed
   - If memory leak: Restart the application (graceful shutdown)
   - If bot attack: Enable Cloudflare Bot Fight Mode or Turnstile
5. Once mitigated, monitor for 30 min to ensure stability
6. Post-mortem within 24 hours

**Escalation**: If degradation persists after 2 hours, escalate to database administrator or DevOps team.

---

### P3 — Minor Issue (SLA: Respond in 8 hours)

**Criteria**: Issues that don''t impact core functionality or only affect a small number of users.

- A non-critical API endpoint is misbehaving
- Cosmetic frontend bugs
- Monitoring alert fires but service is still operational
- One user reports an issue that cannot be reproduced

**Response**:
1. Declare incident (optional): `P3 INCIDENT: [Brief description]`
2. Investigate and log issue in GitHub as an incident ticket
3. Triage: Is it a real bug or user error?
4. If real: Create a fix, test locally, merge to master (auto-deploys)
5. Post-mortem (lightweight): Add to incident log if systemic pattern emerges

**Escalation**: None required; handle asynchronously during regular work hours.

---

## Incident Declaration & Communication

### Step 1: Declare in Slack

```
@incidents P[1|2|3] INCIDENT: [Brief Description]
Status: Investigating
ETA: [Time estimate for resolution]
```

### Step 2: Update Status Page

1. Navigate to [Instatus Dashboard](https://whetzy.instatus.com) (or configured provider)
2. Click "Create Incident"
3. Select affected component: "API", "Frontend", or "All Services"
4. Set status: "Investigating" (P1/P2), "Monitoring" (P3)
5. Post initial message: `[Timestamp UTC] We are investigating a [P1|P2|P3] incident affecting [Component]. More updates to follow.`
6. Subscribe stakeholders (automatic email to customers)

### Step 3: Investigation & Updates

- Every 15 min (P1) or hourly (P2): Post status update in Slack + status page
- Be transparent: "We found X, working on fix Y, expect resolution in Z minutes"
- If unsure: "Still investigating, will provide update in 15 min"

### Step 4: Resolution & Closure

1. Post root cause to Slack: `RESOLVED: [Root cause]. [Preventive measure taken].`
2. Update status page: "Resolved" + timestamp
3. Schedule post-mortem meeting (P1 within 4 hrs, P2 within 24 hrs, P3 within 1 week)

---

## Quick Diagnostics

### Is the Backend Down?

```bash
# From anywhere:
curl -s https://api-production-9751.up.railway.app/health
# Should return {"status": "healthy"} and HTTP 200

# Check readiness (includes DB):
curl -s https://api-production-9751.up.railway.app/health/ready
# Should return {"status": "ready"} and HTTP 200
```

### Check Recent Deployments

1. Open [Railway Dashboard](https://railway.app) → Whetzy project
2. Look at recent deploys in the "Deployments" tab
3. If a deploy happened in the last 15 min and it''s showing "Failed", that''s the cause
4. Click "Revert" to roll back the previous good deployment

### Check Database

```bash
# SSH into Railway Postgres service:
railway connect --service postgres

# Once connected:
SELECT version();  -- Should return (usually fast)
SELECT COUNT(*) FROM users;  -- Rough health check

# Check if any queries are stuck:
SELECT * FROM pg_stat_activity WHERE state != ''idle'';
```

### Check Memory/CPU

1. [Railway Dashboard](https://railway.app) → Whetzy Backend service → "Monitoring" tab
2. Look at CPU and Memory graphs
3. If Memory is near 512MB limit (or configured max):
   - Possible memory leak
   - Possible spike in concurrent connections
   - Solution: Restart the service (Railway: click "Redeploy")

### Check Rate Limiting

1. Look at middleware logs in Railway: `docker logs` or "View Logs" in dashboard
2. Search for `RateLimitMiddleware` entries
3. If many IPs are hitting 429 limits, either:
   - Users are hammering the API (expected under load)
   - A bot is attacking (see Cloudflare Bot Analytics)
   - A frontend bug is creating loop requests

### Cloudflare Analytics

1. Navigate to [Cloudflare Dashboard](https://dash.cloudflare.com) → whetzy.com → Analytics
2. Check for spikes in:
   - **Request volume** (indicates bot attack or viral moment)
   - **Error rate** (4xx, 5xx)
   - **Cache hit ratio** (should be >50% for static assets)
   - **Rate limit hits** (see "Security" → "Rate Limiting")

### Sentry Error Tracking

1. Open [Sentry Project](https://sentry.io) → whetzy-backend
2. Look at "Issues" tab, sorted by "Frequency"
3. Recent issues may indicate the problem
4. Click on an issue to see stack trace and affected users

---

## Common Incidents & Solutions

### "API returns 503 Service Unavailable"

**Cause**: Usually database is down or overloaded.

**Fix**:
```bash
# 1. SSH into Railway and check DB
railway connect --service postgres
SELECT 1;  # If this hangs, DB is overloaded

# 2. If DB is hung, restart it:
# (From Railway dashboard: Postgres service → Click three-dots → Restart)

# 3. Check connection pool:
# (Backend should have at most DATABASE_POOL_SIZE + DATABASE_MAX_OVERFLOW connections)
SELECT COUNT(*) FROM pg_stat_activity;
```

### "Frontend can''t reach API (CORS error)"

**Cause**: Either backend is down, or CORS origins are misconfigured.

**Fix**:
```bash
# 1. Check if backend is responding
curl -s https://api-production-9751.up.railway.app/health

# 2. If yes, check CORS in config
# (backend/app/core/config.py, BACKEND_CORS_ORIGINS)
# Add frontend URL if missing and redeploy

# 3. Verify frontend is using correct API URL
# (frontend/.env.production should have REACT_APP_API_URL=https://api-...)
```

### "Users report slow login / 10+ second latency"

**Cause**: Rate limiter is throttling requests, or tutor endpoint is overloaded.

**Fix**:
```bash
# 1. Check rate limiting in middleware logs
railway logs --service backend | grep RateLimitMiddleware

# 2. If many 429 responses, either:
#    a) Users are legitimately using the app heavily (add more replicas)
#    b) A bot is attacking (enable Cloudflare Turnstile or Bot Fight Mode)

# 3. Check Prometheus metrics
curl -s https://api-production-9751.up.railway.app/metrics | grep auth_request_duration

# 4. If latency is high, check database query performance
# (See "Check Database" section above)
```

### "Out of Memory or 'OOM Killed' errors"

**Cause**: Application has exceeded Railway''s memory limit (512MB free tier, configurable).

**Fix**:
```bash
# 1. Identify the leak
# Check Sentry for memory-related errors
# Look for patterns in what happens before OOM

# 2. Short-term: Restart the service
# (Railway: Click "Redeploy")

# 3. Long-term:
# a) Upgrade to a higher memory tier (Railway: Edit plan)
# b) Fix the memory leak (e.g., unbounded list growth, unclosed connections)
```

---

## Monitoring Tools Setup

### UptimeRobot (Free, HTTP pings)

1. Create account at [uptimerobot.com](https://uptimerobot.com)
2. Add monitor:
   - URL: `https://api-production-9751.up.railway.app/health/ready`
   - Type: HTTP(S)
   - Interval: 5 minutes
   - Timeout: 30 seconds
3. Set alert: Email to ops team + Slack webhook
4. Done — UptimeRobot will ping every 5 min and alert if down

### Instatus (Free, Status Page)

1. Create account at [instatus.com](https://instatus.com)
2. Add components:
   - "API Backend"
   - "Frontend (SPA)"
   - "Database"
3. Set up incident templates (see `postmortem-template.md`)
4. Share public status page URL (whetzy.instatus.com) on main site footer
5. Subscribers can opt-in to email/SMS notifications

### Cloudflare Analytics

- Already included with free Cloudflare plan
- No setup needed
- Check dashboard for traffic, cache hit ratio, security events

---

## Post-Incident Checklist

After every incident:

- [ ] Post-mortem scheduled within SLA (P1: 4 hrs, P2: 24 hrs)
- [ ] Root cause identified
- [ ] Preventive measures documented (see `postmortem-template.md`)
- [ ] GitHub issue created for any code fixes needed
- [ ] Status page closed (if open)
- [ ] Slack summary posted in #incidents
- [ ] Stakeholders notified (via status page, if needed)
- [ ] Monitoring thresholds tuned (if false positive)
