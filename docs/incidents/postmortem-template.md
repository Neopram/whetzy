# Post-Mortem Template (Series 22.7)

Use this template within 4 hours (P1), 24 hours (P2), or 1 week (P3) of incident closure.

---

## Incident Post-Mortem: [INCIDENT TITLE]

**Date**: [Date incident occurred]  
**Severity**: [P1 | P2 | P3]  
**Duration**: [Start time UTC] – [End time UTC] (Total: [X hours/mins])  
**Authors**: [Who attended the post-mortem]  

---

## 1. Executive Summary

[1–2 sentence summary of what happened and impact]

**Example**: On 2026-09-19 at 02:15 UTC, the backend database exceeded memory limits, causing 100% of users to see "Service Unavailable" for 45 minutes. We served 50k requests during the outage, of which ~30k failed.

---

## 2. Timeline

| Time (UTC) | Event |
|------------|-------|
| 02:15 | Uptime robot detects /health/ready returning 503 |
| 02:18 | Engineer paged; opens Railway dashboard |
| 02:22 | Identified: Postgres memory at 512MB (limit), queries stuck in queue |
| 02:30 | Postgres service restarted |
| 02:35 | API returned to normal, /health/ready returning 200 |
| 02:45 | Status page updated to "Resolved" |
| 03:15 | Investigation: Found N+1 query in `/api/v1/progress` endpoint |

---

## 3. Impact

**Scope**:
- Who was affected? All users | Specific feature | Specific geographic region
- How many users? [Estimate or exact from analytics]
- How many requests failed? [From logs/metrics]

**Business Impact**:
- Revenue lost? (if applicable; e.g., missed quiz attempts, subscription charges pending)
- Reputation damage? (check social media, support tickets)
- Data loss? (any data corrupted or permanently lost?)

**Example**:
```
- ~50k active users affected
- ~30k requests failed (60% error rate)
- ~$120 in missed subscriptions (estimate, based on 400 users unable to subscribe during outage)
- No data loss; all requests queued and retried successfully after restart
```

---

## 4. Root Cause Analysis

### What was the root cause?

[Describe the technical reason the incident occurred. Be specific: exact code, configuration, or operational mistake.]

**Example**: `The /api/v1/progress endpoint had an N+1 query problem: for each of 1,000 users, it was fetching their modules separately instead of using a JOIN. A single request was spawning 1,000 database queries. A spike in traffic (end-of-day quiz submissions) saturated the connection pool.`

### Why did we not catch this earlier?

[Identify the monitoring / testing gaps that let this slip through.]

**Example**:
- No query-count alerting (only latency alerts)
- Load tests used 100 VUs; production spike hit 500 concurrent users
- Pre-commit linting doesn't catch N+1 patterns

### Contributing factors

[List any secondary causes or conditions that made it worse.]

**Example**:
- No database query logging in production (couldn''t see the N+1 until after the fact)
- Connection pool was tuned for 50 concurrent users, but spike hit 200
- No automatic failover to read replica

---

## 5. Resolution

### What fixed it?

[Describe the immediate action taken to restore service.]

**Example**: Restarted the Postgres service, which cleared the query queue. Latency returned to normal within 2 minutes.

### Why did that fix it?

[Explain the mechanism.]

**Example**: The hanging queries were released, connection pool was flushed, and new queries started processing normally.

---

## 6. Preventive Measures

### Short-term (do this week)

- [ ] **[Measure 1]**: [What we''re doing] (Owner: [Name], ETA: [Date])
  - **Example**: Fix N+1 query in progress endpoint by using SQLAlchemy joinedload()
  - **PR**: [Link to GitHub PR]
  - **Verification**: Run load test with 500 VUs; confirm /progress latency <200ms

- [ ] **[Measure 2]**: [What we''re doing] (Owner: [Name], ETA: [Date])
  - **Example**: Add database query-count alerting (Prometheus histogram)
  - **Alert threshold**: Queries per request >10 → page on-call

### Medium-term (this month)

- [ ] Add query logging to staging environment (QueryLogger middleware)
- [ ] Increase load test VU count to 1,000 (more realistic production load)
- [ ] Document connection pool tuning guide (DATABASE_POOL_SIZE, DATABASE_MAX_OVERFLOW)

### Long-term (this quarter)

- [ ] Implement database read replicas + failover (Railway managed Postgres)
- [ ] Auto-scaling rules: If p95 latency >500ms or memory >400MB, scale up
- [ ] Query optimization pass: Audit all endpoints for N+1, missing indexes

---

## 7. Action Items

| Action | Owner | Due | Status |
|--------|-------|-----|--------|
| Fix progress endpoint N+1 query | @alice | 2026-09-20 | In Progress |
| Add query-count alerting | @bob | 2026-09-21 | Open |
| Increase load test to 1K VUs | @charlie | 2026-09-22 | Open |
| Post results in #incidents | @alice | 2026-09-20 | Open |

---

## 8. Lessons Learned

### What did we do well?

- Uptime robot caught the outage in 3 minutes
- Engineer responded quickly and had access to all necessary dashboards
- Communication was clear in Slack (updates every 15 min)

### What could we improve?

- We need query-level observability in production (not just latency)
- Load testing should use realistic spike patterns (not uniform load)
- Post-incident tooling (this template) ensures we don''t repeat mistakes

---

## 9. Sign-Off

- **Post-mortem facilitator**: [Name]
- **Date reviewed**: [Date]
- **Approved by**: [Tech lead or manager]

---

## Appendix: Supporting Evidence

### Relevant Logs

```
# Postgres logs showing connection pool exhaustion:
[2026-09-19 02:15:30] FATAL: remaining connection slots are reserved for non-replication superuser connections
```

### Metrics Snapshot

```
# Prometheus query at time of incident:
pg_stat_activity_total{state="active"} = 512  # Max connections
rate(http_requests_total{status="500"}[1m]) = 100  # 100 errors/sec
```

### GitHub Issues Created

- Issue #[N]: N+1 query in progress endpoint (needs fix)
- Issue #[M]: Add query-count alerting (feature request)

---

## Distribution

- [ ] Post in Slack #incidents
- [ ] Share with engineering team (via GitHub issue link)
- [ ] File in docs/incidents/[INCIDENT_TITLE]_postmortem.md (archive)
- [ ] Send summary email to stakeholders (if P1 or public impact)
