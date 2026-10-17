# Whetzy Admin Dashboard Specification

## Overview

Admin-only dashboard at `/admin` (owner role, code-split route) with 7 analytics/operations panels.

## Architecture

- **Route**: `/admin` (FastAPI `GET /admin/` SSE + React SPA)
- **Auth**: Owner role only (`role == "owner"`)
- **Code-split**: Lazy-loaded React component
- **Database**: New tables: `audit_log`, `login_attempts`, `user_sessions`, `promo_codes`, `credit_ledger`, `referrals`, `gdpr_requests`
- **API Endpoints**: RESTful, all under `/api/v1/admin/*`

---

## 7 Panels

### 1. **Metrics** (`/admin/metrics`)

DAU/WAU/MAU, Learning Funnel, TTFQ (Time To First Question Attempt)

### 2. **Security** (`/admin/security`)

Auth Events Log, Account Lockouts, IP Reputation

### 3. **Content** (`/admin/content`)

Skill Gaps, Language Parity (ES/EN), Content Health

### 4. **Ops** (`/admin/ops`)

System Health, Error Rate, Database Stats

### 5. **GDPR** (`/admin/gdpr`)

Export Queue, Deletion Queue, Compliance Audit

### 6. **Revenue** (`/admin/revenue`)

MRR, Conversion Funnel, Churn Analysis (test mode until 7.2)

### 7. **Economy** (`/admin/economy`)

Credit Ledger, Referral Attribution, K-Factor

---

## Database Schema

- `audit_log` (immutable, append-only)
- `login_attempts` (lockout tracking)
- `user_sessions` (device/session tracking, 30-day timeout)
- `promo_codes` (referral codes)
- `credit_ledger` (economy tracking)
- `gdpr_requests` (export/deletion queue)
- `referrals` (referral attribution)

---

## API Endpoints

All under `/api/v1/admin/*`. Rate limit: 1 req/sec per endpoint (owner only). CORS: `https://whetzy.pages.dev`.

### Metrics
- `GET /api/v1/admin/metrics/users?range_days=7` (1-365)
- `GET /api/v1/admin/metrics/funnel?segment=es|en`
- `GET /api/v1/admin/metrics/ttfq?segment=es|en`

### Security
- `GET /api/v1/admin/security/auth-events?limit=100&offset=0&action=login_failed`
- `GET /api/v1/admin/security/lockouts?active_only=true`
- `GET /api/v1/admin/security/ip-analysis?ip=1.2.3.4`

### Content
- `GET /api/v1/admin/content/gaps?language=es|en`
- `GET /api/v1/admin/content/parity?segment=questions|lessons`

### Ops
- `GET /api/v1/admin/ops/health`
- `GET /api/v1/admin/ops/errors?window=1h|24h`
- `GET /api/v1/admin/ops/database`

### GDPR
- `GET /api/v1/admin/gdpr/exports?status=pending`
- `GET /api/v1/admin/gdpr/deletions?status=pending`
- `POST /api/v1/admin/gdpr/deletions/{user_id}/cancel`

### Revenue
- `GET /api/v1/admin/revenue/mrr?month=2026-09`
- `GET /api/v1/admin/revenue/conversions?range_days=7`
- `GET /api/v1/admin/revenue/churn?window=30d`

### Economy
- `GET /api/v1/admin/economy/credits?user_id=X`
- `GET /api/v1/admin/economy/referrals`
- `GET /api/v1/admin/economy/k-factor`

---

## Migration & Rollout

Phase 1: Create audit_log, login_attempts, user_sessions tables
Phase 2: Deploy API endpoints with sample data
Phase 3: Route guard + React UI; owner role check
Phase 4: Enable revenue tracking (Stripe integration)
