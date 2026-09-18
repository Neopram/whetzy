# Whetzy STRIDE Threat Model & Security Analysis

## Executive Summary

Comprehensive threat analysis of Whetzy (FastAPI backend, React frontend, mobile Capacitor). Identified **6 CRITICAL** and **6 HIGH** priority vulnerabilities. Recommendations focus on progressive auth hardening, secure token handling, and audit logging.

---

## STRIDE Threats

### S: Spoofing (Authentication & Identity)

#### Threat: Refresh Token Abuse
- **Risk**: CRITICAL
- **Current Gap**: `jwt_version` not validated in `/auth/refresh` endpoint
- **Attack**: Attacker captures old refresh token, uses it if JWT version incremented but validation missing
- **Fix**: Validate `jwt_version` in `verify_token()` call on refresh endpoint
- **Code**: `backend/app/core/security.py` → add `assert token.jwt_version == current_jwt_version`

#### Threat: JWT Token Forgery
- **Risk**: MEDIUM
- **Current Gap**: HS256 (symmetric) — if signing key compromised, attacker forges any token
- **Fix**: Migrate to RS256 (asymmetric); keep private key server-side only
- **Timeline**: Phase 2 (non-breaking, requires key rotation)

---

### T: Tampering (Data Integrity)

#### Threat: OAuth Token in Browser History
- **Risk**: CRITICAL
- **Current Gap**: Redirect uses `?oauth_token=XXX` in query string (logged by browser, proxy, CDN)
- **Attack**: Attacker reads browser history or proxy logs → steals OAuth token
- **Fix**: Use `#oauth_token=XXX` (fragment, never sent to server); process client-side only
- **Code**: `backend/app/api/v1/endpoints/auth.py` → redirect response

---

### R: Repudiation (Non-Repudiation / Audit Trail)

#### Threat: Audit Logging Missing
- **Risk**: CRITICAL
- **Current Gap**: No trail for password changes, account deletions, admin edits, failed logins
- **Attack**: Attacker modifies account, no forensic trail; admin abuse undetected
- **Fix**: Add immutable `audit_log` table; log all security-relevant actions
- **Schema**:
  ```sql
  CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID,
    action VARCHAR(64),  -- login_success, login_failed, password_change, 2fa_enable, etc.
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    ip INET,
    user_agent TEXT,
    result VARCHAR(16),  -- success, failed, blocked
    error_message TEXT,
    metadata JSONB
  );
  ```

---

### I: Information Disclosure (Confidentiality)

#### Threat: Tokens in localStorage (XSS Vulnerable)
- **Risk**: CRITICAL
- **Current Gap**: Access token + refresh token stored in `localStorage` (accessible to any XSS)
- **Attack**: Script injection steals all tokens; attacker impersonates user indefinitely
- **Fix**: Move to `HttpOnly Secure SameSite=Strict` cookies; never store in localStorage
- **Code**: `frontend/src/services/api.ts` → replace localStorage with cookie-based auth
- **Timeline**: Phase 3 (requires frontend rewrite, CSRF token for POST)

#### Threat: Admin Key in Plaintext Header
- **Risk**: CRITICAL
- **Current Gap**: `X-Admin-Key: secret-key-here` passed in plaintext headers
- **Attack**: Network sniffer, CDN logs, or Cloudflare expose admin key
- **Fix**: Use HMAC-SHA256 signed requests; include timestamp + nonce to prevent replay
- **Code**: Middleware to validate `Authorization: HMAC-SHA256 Signature=...`

---

### D: Denial of Service (Availability)

#### Threat: Account Lockout Missing
- **Risk**: HIGH
- **Current Gap**: No progressive lockout after N failed attempts
- **Attack**: Brute-force password attacks succeed easily; rate limiting only at IP level (proxies bypass)
- **Fix**: Implement exponential backoff per email + IP combo:
  - Attempt 1-4: no delay
  - Attempt 5: 1s delay
  - Attempt 6: 2s delay
  - Attempt 7: 4s delay
  - Attempt 8: 8s delay
  - Attempt 9: 16s delay
  - Reset after 15 min inactivity or successful login
- **Schema**: `login_attempts(email, ip, success, created_at)` table

#### Threat: Brute-Force on Email Verification
- **Risk**: HIGH
- **Current Gap**: No rate limit on `/auth/verify-email` endpoint
- **Attack**: Attacker tries all 6-digit codes rapidly
- **Fix**: Rate limit: 3 attempts/hour per email + IP
- **Code**: Middleware decorator `@rate_limit(limit=3, window=3600)`

#### Threat: Brute-Force on Password Reset
- **Risk**: HIGH
- **Current Gap**: No rate limit on `/auth/reset-password` endpoint
- **Attack**: Attacker tries many reset tokens
- **Fix**: Rate limit: 3 requests/hour per email, 10 requests/min global
- **Code**: Separate buckets for per-email and global rate limiting

---

## Security Headers Analysis

### Current (Verified in Code)

✓ **HSTS** (Strict-Transport-Security: max-age=31536000; includeSubDomains)
✓ **X-Frame-Options: DENY**
✓ **CSP** (script-src 'self'; style-src 'self' fonts.googleapis.com; img-src 'self' data: https:)
✓ **X-Content-Type-Options: nosniff**

### Missing (Add to FastAPI middleware)

- **X-XSS-Protection**: `1; mode=block`
- **X-Permitted-Cross-Domain-Policies**: `none`
- **Referrer-Policy**: `strict-origin-when-cross-origin`
- **Permissions-Policy**: `geolocation=(), microphone=(), camera=(), payment=()`

### CORS Configuration Issue

- **Current**: `https://*.pages.dev` (wildcard subdomain — too broad)
- **Fix**: `https://whetzy.pages.dev` (explicit only)

---

## Severity Summary

| Priority | Count | Threats |
|----------|-------|---------|
| **CRITICAL** | 6 | Refresh token abuse, OAuth in history, Audit logging missing, Tokens in localStorage, Admin key plaintext, Account lockout missing |
| **HIGH** | 6 | Email verification brute-force, Password reset brute-force, HS256 vs RS256, Session hijacking, CORS too broad, Weak password policy |
| **MEDIUM** | 3 | Error message leakage, Timing attacks on token validation, SQL injection (unlikely with ORM) |

---

## Implementation Roadmap

### Phase 1: Non-Breaking (Week 1)
- Create `audit_log` table (append-only)
- Create `login_attempts` table
- Deploy audit logging middleware (logs all actions)
- Add missing security headers

### Phase 2: Gradual Rollout (Week 2-3)
- Deploy account lockout with loose thresholds (20 attempts → 1s delay)
- Deploy refresh token validation
- Add rate limiting to `/auth/verify-email` and `/auth/reset-password`
- Enable HMAC signing for admin requests (optional header validation, no errors yet)

### Phase 3: Full Enforcement (Week 4)
- Tighten lockout thresholds (5 attempts → exponential)
- Enforce HMAC signing (reject unsigned requests)
- Migrate JWT to RS256 (gradual key rotation)
- Move tokens to HttpOnly cookies (requires frontend rewrite)
- Fix CORS to explicit `https://whetzy.pages.dev`

---

## Testing Strategy

- **Unit**: Lockout math (exponential delay), token validation
- **Integration**: End-to-end lockout flow, refresh token rotation
- **Security**: Simulated brute-force attacks; verify rate limits work
- **Regression**: Existing login/logout flows still work

---

## References

- OWASP Top 10 2021: A01:2021 - Broken Access Control, A02:2021 - Cryptographic Failures
- OWASP STRIDE Threat Modeling
- CWE-384: Session Fixation
- CWE-613: Insufficient Session Expiration
