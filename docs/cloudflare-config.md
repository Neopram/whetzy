# Cloudflare Free Tier Security (Series 22.5)

Zero-cost DDoS, WAF, rate limiting, and performance caching via Cloudflare.

## Overview

Whetzy uses Cloudflare's free tier as the DNS and WAF layer in front of the frontend (Cloudflare Pages). The backend (Railway) is NOT behind Cloudflare: the API is served directly from `api-production-9751.up.railway.app` (`docs/RUNBOOK.md`, 22.5 section C, checked 2026-10-02).

**Domains**:
- `whetzy.com` (apex): Cloudflare Pages → frontend (SPA)
- `api-production-9751.up.railway.app`: backend (FastAPI), direct to Railway, not proxied by Cloudflare

## Managed WAF Rule Sets

Enable in **Cloudflare Dashboard** → **whetzy.com** → **Security** → **WAF**:

1. **Cloudflare Managed Ruleset** (free) — default OWASP Top 10 rules
   - Protects against: SQL injection, XSS, RFI, LFI, code injection
   - Action: Block with HTTP 403

2. **Rate Limiting Rules** (Free plan: one rule, 10 s period; see `docs/RUNBOOK.md` 22.5 section C)
   - See section below

3. **Zone Lockdown** (free) — restrict access by IP/country
   - Disabled by default (open to all)
   - Enable only if targeted abuse detected

**JSON Config** (exported via Cloudflare API):

```json
{
  "rules": [
    {
      "id": "waf_default_ruleset",
      "name": "Cloudflare Managed Ruleset",
      "description": "Default OWASP protection",
      "enabled": true,
      "mode": "block"
    }
  ]
}
```

## Rate Limiting Rules

Create rules in **Cloudflare Dashboard** → **Security** → **Rate limiting**:

### Rule 1: Authentication Endpoints (12 req/min per IP)

```
Threshold: 12 requests
Period: 1 minute
Scope: Per IP
Paths: /api/v1/auth/*
Action: Challenge (JavaScript challenge, then block)
```

**Reason**: Protect against credential stuffing and brute-force login attempts.

### Rule 2: Tutor Endpoint (12 req/min per IP)

```
Threshold: 12 requests
Period: 1 minute
Scope: Per IP
Paths: /api/v1/tutor/*
Action: Challenge
```

**Reason**: LLM calls are expensive; limit to prevent abuse.

### Rule 3: Question Bank (100 req/min per IP)

```
Threshold: 100 requests
Period: 1 minute
Scope: Per IP
Paths: /api/v1/questions/* /api/v1/quiz/*
Action: Log (no block; monitor for spikes)
```

**Reason**: Quiz sessions may generate many requests; log to detect bots.

### Rule 4: General API (300 req/min per IP)

```
Threshold: 300 requests
Period: 1 minute
Scope: Per IP
Paths: /api/v1/*
Action: Challenge
```

**Reason**: Blanket catch-all for API abuse.

**Note**: Cloudflare rate limiting complements the backend''s `RateLimitMiddleware`. Backend checks fire first (stricter), then Cloudflare (coarser-grained, geographic redundancy).

## Bot Fight Mode

Enable in **Cloudflare Dashboard** → **Security** → **Bots**:

```
Super Bot Fight Mode: On
- Block known bots: Yes
- Block verified bots: No (allow Google, Bing, etc.)
- Heuristic-based bot detection: On (sensitivity: medium)
```

**Action**: Cloudflare CAPTCHA challenge for suspected bots.

**Logs**: Visible in **Analytics** → **Bot Analytics** tab.

## Cache Rules (Performance)

Create rules in **Cloudflare Dashboard** → **Caching** → **Cache Rules**:

### Rule 1: Glossary Endpoint (5-minute cache, public)

```
Path: /api/v1/glossary*
TTL: 300 seconds (5 minutes)
Cache Key: Include query string
Audience: Public (cache in all edge locations)
```

**Headers set by backend** (see `backend/app/api/v1/endpoints/glossary.py:28`):
```
Cache-Control: public, max-age=7200, stale-while-revalidate=86400
```

### Rule 2: Track Listing (5-minute cache)

```
Path: /api/v1/tracks
TTL: 300 seconds
Cache Key: Include authorization header? No
Audience: Public
```

### Rule 3: Landing Page / SPA (1-hour cache)

```
Path: /
TTL: 3600 seconds (1 hour)
Cache Key: Default
Audience: Public
Bypass for: Cookies (always serve fresh if session cookie present)
```

**Reason**: Static SPA assets change infrequently; cache aggressively to reduce latency.

### Rule 4: Auth/Private Endpoints (No cache)

```
Path: /api/v1/auth/* /api/v1/user/*
TTL: 0 (no cache)
```

**Reason**: Private data must never be cached.

## Turnstile CAPTCHA (Optional, Trigger-Based)

Enable only if automated abuse is detected (e.g., spike in failed login attempts).

### Setup

1. **Cloudflare Dashboard** → **Turnstile** → Create a new site
   - Domain: `whetzy.com`
   - Subdomain: None
   - Mode: Managed (Cloudflare decides when to challenge)

2. **Backend code** (see `backend/app/core/security.py`):
   ```python
   if abuse_detected:  # e.g., spike in 401 responses
       return {"error": "Please complete Turnstile", "turnstile_required": True}
   ```

3. **Frontend code** (see `frontend/src/components/Turnstile.tsx`):
   ```typescript
   import Turnstile from 'react-turnstile';
   <Turnstile sitekey={process.env.REACT_APP_TURNSTILE_SITEKEY} />
   ```

4. **Environment variables**:
   - Backend: `TURNSTILE_SECRET_KEY` (server-side verification)
   - Frontend: `REACT_APP_TURNSTILE_SITEKEY` (public key for widget)

5. **Verification** (backend):
   ```python
   response = requests.post(
       "https://challenges.cloudflare.com/turnstile/v0/siteverify",
       json={"secret": settings.TURNSTILE_SECRET_KEY, "response": token}
   )
   is_valid = response.json().get("success")
   ```

**Deployment**: Turnstile is disabled by default. Activate only if abuse threshold is crossed (ver `docs/RUNBOOK.md` § Incident Management).

## DDoS Protection (Always-On)

Cloudflare free tier includes automatic DDoS protection:
- **HTTP Flood**: Automatic rate limiting per IP
- **UDP Flood**: ISP-level filtering
- **DNS Amplification**: Mitigated by Cloudflare''s network

No configuration required. Visible in **Analytics** → **DDoS** tab if large attacks occur.

## Monitoring & Alerts

### Cloudflare Dashboard Tabs

- **Analytics** → **Traffic**: Request volume, cache hit ratio, geographic distribution
- **Analytics** → **Security**: Rate limit hits, WAF blocks, bot challenge successes
- **Analytics** → **DDoS**: Large attack events (if any)
- **Logs** → **Logpush** (Enterprise only; free tier: manual download)

### Email Alerts

Enable in **Notifications** → **Email Notifications**:
- [ ] DDoS Attack Detected
- [ ] High Attack Rate
- [ ] SSL/TLS Certificate Expiring Soon

## Checklist

- [ ] Whetzy domain configured as Cloudflare nameserver (CNAME or NS records)
- [ ] Cloudflare Managed Ruleset enabled (WAF)
- [ ] 4 rate-limiting rules created (/auth, /tutor, /questions, /api/v1/*)
- [ ] Bot Fight Mode enabled (Free plan)
- [ ] Cache rules configured for /glossary, /tracks, landing page, no cache for /auth
- [ ] Backend sends appropriate Cache-Control headers (set per endpoint, e.g. `app/api/v1/endpoints/glossary.py`)
- [ ] Turnstile integration (not implemented: no Turnstile code in backend or frontend; add only if abuse is detected)
- [ ] Email alerts enabled for DDoS and attacks
- [ ] GitHub issue #22.5 closed upon verification

## Cost Breakdown

| Feature | Free Tier | Cost |
|---------|-----------|------|
| Managed WAF | ✓ (basic rules) | €0 |
| Rate Limiting | ✓ (20 rules) | €0 |
| Bot Fight Mode | ✓ | €0 |
| Cache Rules | ✓ (unlimited) | €0 |
| Turnstile CAPTCHA | ✓ | €0 (100k challenges/month free) |
| DDoS Protection | ✓ | €0 |
| SSL/TLS Certificate | ✓ (auto-renewal) | €0 |
| **Total** | | **€0** |

## References

- [Cloudflare WAF Documentation](https://developers.cloudflare.com/waf/)
- [Cloudflare Rate Limiting](https://developers.cloudflare.com/waf/rate-limiting-rules/)
- [Cloudflare Bot Management](https://developers.cloudflare.com/bots/)
- [Turnstile Documentation](https://developers.cloudflare.com/turnstile/)
