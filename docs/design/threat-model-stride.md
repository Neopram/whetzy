# Whetzy STRIDE Threat Model & Security Analysis

## Executive Summary

Comprehensive threat analysis of Whetzy (FastAPI backend, React frontend, mobile Capacitor). Identified **6 CRITICAL** and **6 HIGH** priority vulnerabilities. Recommendations focus on progressive auth hardening, secure token handling, and audit logging.

Series 22.2 Status: **Security headers completed**, CORS configuration fixed, tests added.

---

## STRIDE Threats

### S: Spoofing (Authentication & Identity)

#### Threat: Refresh Token Abuse
- **Risk**: CRITICAL
- **Status**: IMPLEMENTED (Series 22.3)
- **Fix**: Validate `jwt_version` in `verify_token()` call on refresh endpoint
- **Code**: `backend/app/core/security.py` → `verify_token()` checks jwt_version

#### Threat: JWT Token Forgery
- **Risk**: MEDIUM
- **Current Gap**: HS256 (symmetric) is still the default; RS256 is used only if `JWT_PRIVATE_KEY` is set (`security.py:73-77`) — if the HS256 key is compromised, attacker forges any token
- **Fix**: Migrate to RS256 (asymmetric); keep private key server-side only
- **Timeline**: Phase 2 (non-breaking, requires key rotation)

---

### T: Tampering (Data Integrity)

#### Threat: OAuth Token in Browser History
- **Risk**: CRITICAL
- **Status**: IMPLEMENTED: the callback sets both tokens in HttpOnly cookies (`set_auth_cookies`), never in the URL
- **Code**: `backend/app/api/v1/endpoints/oauth.py` (module docstring, lines 6-9)

---

### R: Repudiation (Non-Repudiation / Audit Trail)

#### Threat: Audit Logging Missing
- **Risk**: CRITICAL
- **Status**: IMPLEMENTED (Series 22.3)
- **Fix**: Immutable `audit_log` table with all security-relevant actions
- **Code**: Migration `20260908_0700_g7h8i9j0k1l2_asvs_l2_security.py`
- **Verification**: `log_audit_event()` called on login, refresh, logout, account changes

---

### I: Information Disclosure (Confidentiality)

#### Threat: Tokens in localStorage (XSS Vulnerable)
- **Risk**: CRITICAL
- **Status**: IMPLEMENTED (22.15): tokens in HttpOnly cookies, never in localStorage. Amended 2026-10-23: when the
  browser blocks the cookie (Safari/iPhone, 43.1, PR #226), `bridgeIfCookiesBlocked` keeps both tokens in
  `sessionStorage` for the tab and sends them as `Authorization: Bearer`. Accepted cost (owner): an XSS could read
  them while that tab is open
- **Code**: `backend/app/core/cookies.py` (`set_auth_cookies`); `frontend/src/services/api.ts` only removes the legacy keys

#### Threat: Admin Key in Plaintext Header
- **Risk**: CRITICAL
- **Current Gap**: `X-Admin-Key: secret-key-here` passed in plaintext headers
- **Attack**: Network sniffer, CDN logs, or Cloudflare expose admin key
- **Fix**: Use HMAC-SHA256 signed requests; include timestamp + nonce to prevent replay
- **Code**: Middleware to validate `Authorization: HMAC-SHA256 Signature=...`
- **Timeline**: Phase 2

---

### D: Denial of Service (Availability)

#### Threat: Account Lockout Missing
- **Risk**: HIGH
- **Status**: IMPLEMENTED (Series 22.3)
- **Fix**: Exponential backoff per email + IP combo after N failed attempts
- **Code**: `backend/app/core/security.py` → `check_lockout()` and `record_login_attempt()`
- **Schema**: `login_attempts(email, ip, success, created_at)` table

#### Threat: Brute-Force on Email Verification
- **Risk**: HIGH
- **Status**: IMPLEMENTED (Series 22.3)
- **Fix**: Rate limit: 3 attempts/hour per email + IP in `RateLimitMiddleware`
- **Code**: `backend/app/core/security_middleware.py` → auth and tutor endpoints

#### Threat: Brute-Force on Password Reset
- **Risk**: HIGH
- **Status**: IMPLEMENTED (Series 22.3)
- **Fix**: Rate limit: 3 requests/hour per email, 10 requests/min global
- **Code**: `backend/app/core/security_middleware.py` → stricter auth_limit for /auth/*

---

## Security Headers Analysis

### Current (Verified in Code) — Series 22.2 COMPLETE

✓ **HSTS** (Strict-Transport-Security: max-age=63072000; includeSubDomains; preload)
✓ **X-Frame-Options**: DENY
✓ **X-Content-Type-Options**: nosniff
✓ **X-XSS-Protection**: 1; mode=block (NEW in Series 22.2)
✓ **X-Permitted-Cross-Domain-Policies**: none
✓ **Referrer-Policy**: strict-origin-when-cross-origin
✓ **Permissions-Policy**: geolocation=(), microphone=(), camera=(), payment=()
✓ **CSP** (default-src 'none'; frame-ancestors 'none'; base-uri 'none')
✓ **Cross-Origin-Opener-Policy**: same-origin
✓ **Cross-Origin-Resource-Policy**: same-origin
✓ **Cache-Control**: no-store

### CORS Configuration Issue — Series 22.2 FIXED

- **Previous**: `https://*.pages.dev` (wildcard subdomain — too broad)
- **Current**: `https://whetzy.pages.dev` (explicit only)
- **Code**: `backend/app/core/config.py` → BACKEND_CORS_ORIGINS

---

## Testing — Series 22.2

### Security Headers Tests
- **File**: `backend/tests/unit/test_security_headers.py` (6 tests)
- **Coverage**: Verify all security headers present, CSP validation, HSTS check, cache-control, no server header leakage

### CORS Tests
- **File**: `backend/tests/integration/test_cors_security.py` (10 tests)
- **Coverage**: Allowed origins (whetzy.com, whetzy.pages.dev, localhost), rejection of unauthorized origins, no wildcard subdomains, credentials handling, preflight

---

## Severity Summary

| Priority | Count | Threats | Status |
|----------|-------|---------|--------|
| **CRITICAL** | 6 | Refresh token abuse, OAuth in history, Audit logging, Tokens in localStorage, Admin key plaintext, Account lockout | 5 implemented, 1 in roadmap |
| **HIGH** | 6 | Email verification brute-force, Password reset brute-force, HS256 vs RS256, Session hijacking, CORS too broad, Weak password policy | 3 implemented, 1 fixed (CORS), 2 in roadmap |
| **MEDIUM** | 3 | Error message leakage, Timing attacks on token validation, SQL injection (unlikely with ORM) | Deferred |

---

## Implementation Roadmap

### Phase 1: Non-Breaking (COMPLETE)
- ✓ Create `audit_log` table (append-only)
- ✓ Create `login_attempts` table
- ✓ Deploy audit logging middleware (logs all actions)
- ✓ Add missing security headers (X-XSS-Protection)
- ✓ Fix CORS to explicit `https://whetzy.pages.dev`
- ✓ Add security header tests
- ✓ Add CORS tests

### Phase 2: Gradual Rollout (COMPLETE)
- ✓ Deploy account lockout with loose thresholds
- ✓ Deploy refresh token validation
- ✓ Add rate limiting to `/auth/verify-email` and `/auth/reset-password`
- ( ) Enable HMAC signing for admin requests (optional header validation, no errors yet)

### Phase 3: Full Enforcement (DEFERRED)
- ( ) Tighten lockout thresholds (5 attempts → exponential)
- ( ) Enforce HMAC signing (reject unsigned requests)
- ( ) Migrate JWT to RS256 (gradual key rotation)
- ✓ Move tokens to HttpOnly cookies (done, 22.15)

---

## References

- OWASP Top 10 2021: A01:2021 - Broken Access Control, A02:2021 - Cryptographic Failures
- OWASP STRIDE Threat Modeling
- CWE-384: Session Fixation
- CWE-613: Insufficient Session Expiration
- OWASP ASVS 5.0 (Level 2)
