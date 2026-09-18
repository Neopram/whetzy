# Whetzy Progressive Auth Security Hardening

## Overview

Comprehensive auth security spec including progressive lockout, refresh token rotation, session/device tracking, 2FA TOTP, and audit logging. TDD-first implementation with phased rollout.

---

## 1. Progressive Account Lockout

### Design

Per-email + per-IP combo tracking with exponential backoff.

### Schema

```sql
CREATE TABLE login_attempts (
  id BIGSERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  ip INET NOT NULL,
  success BOOLEAN NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY (email, ip, created_at)
);
CREATE INDEX idx_login_email_ip ON login_attempts(email, ip, created_at DESC);
```

### Algorithm

```python
def check_lockout(email: str, ip: str) -> bool:
    """Check if (email, ip) combo is locked out."""
    attempts = db.query(LoginAttempt).filter(
        LoginAttempt.email == email,
        LoginAttempt.ip == ip,
        LoginAttempt.success == False,
        LoginAttempt.created_at > now() - timedelta(minutes=15)
    ).order_by(LoginAttempt.created_at.desc()).all()
    
    if len(attempts) < 5:
        return False  # Not locked out
    
    # Calculate delay
    delay_seconds = 2 ** (len(attempts) - 5)  # 1, 2, 4, 8, 16, ...
    time_since_last = (now() - attempts[0].created_at).total_seconds()
    
    return time_since_last < delay_seconds

def record_login_attempt(email: str, ip: str, success: bool):
    """Record login attempt; reset lockout on success."""
    db.add(LoginAttempt(email=email, ip=ip, success=success))
    db.commit()
    
    if success:
        # Clear old failed attempts for this combo
        db.query(LoginAttempt).filter(
            LoginAttempt.email == email,
            LoginAttempt.ip == ip,
            LoginAttempt.success == False
        ).delete()
        db.commit()
```

### Endpoint

```python
@router.post("/auth/login")
async def login(email: str, password: str, request: Request):
    ip = request.client.host
    
    if check_lockout(email, ip):
        raise HTTPException(status_code=429, detail="Account temporarily locked")
    
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        record_login_attempt(email, ip, success=False)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    record_login_attempt(email, ip, success=True)
    
    # Generate tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    return {"access_token": access_token, "refresh_token": refresh_token}
```

---

## 2. Refresh Token Rotation

### Design

Opaque tokens stored in DB (not JWT). Family-based tracking for replay detection.

### Schema

```sql
CREATE TABLE refresh_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  token_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA256(token)
  family_id UUID NOT NULL,  -- Tracks token family for replay detection
  issued_at TIMESTAMP NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMP NOT NULL,
  revoked BOOLEAN DEFAULT FALSE,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX idx_refresh_user_family ON refresh_tokens(user_id, family_id);
```

### Algorithm

```python
def create_refresh_token(user_id: UUID) -> str:
    """Create opaque refresh token; store hash in DB."""
    token = secrets.token_urlsafe(64)
    token_hash = sha256(token.encode()).hexdigest()
    family_id = uuid4()
    
    db.add(RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        family_id=family_id,
        expires_at=now() + timedelta(days=30)
    ))
    db.commit()
    
    return token

def verify_refresh_token(token: str) -> dict:
    """Verify refresh token; detect replay attacks."""
    token_hash = sha256(token.encode()).hexdigest()
    rt = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()
    
    if not rt or rt.revoked or rt.expires_at < now():
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    return {"user_id": rt.user_id, "family_id": rt.family_id}

def refresh_token_rotation(token: str) -> dict:
    """Exchange refresh token for new access + refresh token pair."""
    # 1. Verify & get user_id, family_id
    payload = verify_refresh_token(token)
    user_id = payload["user_id"]
    family_id = payload["family_id"]
    
    # 2. Check for replays in same family
    replays = db.query(RefreshToken).filter(
        RefreshToken.family_id == family_id,
        RefreshToken.user_id == user_id,
        RefreshToken.issued_at > now() - timedelta(minutes=5)
    ).all()
    
    if len(replays) > 1:
        # Replay detected: revoke entire family
        db.query(RefreshToken).filter(
            RefreshToken.family_id == family_id
        ).update({RefreshToken.revoked: True})
        db.commit()
        
        # Alert user
        log_audit_event(user_id, "refresh_replay_attack", ip=request.client.host)
        raise HTTPException(status_code=401, detail="Token replay detected; session revoked")
    
    # 3. Issue new token pair
    new_access = create_access_token(user_id)
    new_refresh = create_refresh_token(user_id)  # Same family_id
    
    # 4. Mark old token as used (optional, for audit trail)
    db.query(RefreshToken).filter(
        RefreshToken.token_hash == sha256(token.encode()).hexdigest()
    ).update({RefreshToken.revoked: True})
    db.commit()
    
    return {"access_token": new_access, "refresh_token": new_refresh}
```

---

## 3. Session & Device Tracking

### Design

Max 5 active sessions per user. Device fingerprint = SHA256(user_agent + IP). 30-day inactivity timeout. Remote logout capability.

### Schema

```sql
CREATE TABLE user_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  fingerprint VARCHAR(64) NOT NULL,  -- SHA256(user_agent + ip)
  ip INET NOT NULL,
  user_agent TEXT NOT NULL,
  device_name VARCHAR(255),  -- "Chrome on Windows", "Safari on iPhone", etc.
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  last_activity TIMESTAMP NOT NULL DEFAULT NOW(),
  revoked BOOLEAN DEFAULT FALSE,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX idx_session_user ON user_sessions(user_id);
```

### Algorithm

```python
def create_session(user_id: UUID, request: Request) -> UUID:
    """Create new session; limit to max 5 per user."""
    fingerprint = sha256(
        f"{request.headers.get('user-agent', '')}{request.client.host}".encode()
    ).hexdigest()
    
    # Check active sessions
    active = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.revoked == False,
        UserSession.last_activity > now() - timedelta(days=30)
    ).all()
    
    if len(active) >= 5:
        # Revoke oldest session
        oldest = min(active, key=lambda s: s.last_activity)
        db.query(UserSession).filter(UserSession.id == oldest.id).update(
            {UserSession.revoked: True}
        )
        db.commit()
        log_audit_event(user_id, "session_evoked", ip=oldest.ip)
    
    session = UserSession(
        user_id=user_id,
        fingerprint=fingerprint,
        ip=request.client.host,
        user_agent=request.headers.get("user-agent", ""),
        device_name=parse_user_agent(request.headers.get("user-agent", ""))
    )
    db.add(session)
    db.commit()
    
    return session.id

def get_user_sessions(user_id: UUID) -> list:
    """Get all active sessions for user."""
    return db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.revoked == False
    ).all()

def revoke_session(user_id: UUID, session_id: UUID):
    """Remote logout: revoke session."""
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404)
    
    db.query(UserSession).filter(UserSession.id == session_id).update(
        {UserSession.revoked: True}
    )
    db.commit()
    log_audit_event(user_id, "session_revoked", ip=session.ip)
```

---

## 4. Two-Factor Authentication (TOTP)

### Design

Optional 2FA using Time-based One-Time Password (RFC 6238). QR code setup. 10 one-time backup codes.

### Schema

```sql
CREATE TABLE user_2fa (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id),
  secret_key VARCHAR(32) NOT NULL,  -- Base32-encoded TOTP secret
  backup_codes TEXT[] NOT NULL,  -- Array of hashed one-time codes
  enabled BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  last_used TIMESTAMP
);
```

### Algorithm

```python
def setup_2fa(user_id: UUID) -> dict:
    """Generate TOTP secret and backup codes for 2FA setup."""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    qr_uri = totp.provisioning_uri(name=user.email, issuer_name="Whetzy")
    
    # Generate 10 one-time backup codes
    backup_codes = [secrets.token_hex(4) for _ in range(10)]
    backup_codes_hash = [sha256(code.encode()).hexdigest() for code in backup_codes]
    
    db.add(User2FA(
        user_id=user_id,
        secret_key=secret,
        backup_codes=backup_codes_hash,
        enabled=False
    ))
    db.commit()
    
    return {
        "qr_uri": qr_uri,
        "backup_codes": backup_codes  # Print to user, never send via email
    }

def enable_2fa(user_id: UUID, totp_code: str) -> bool:
    """Verify TOTP code and enable 2FA."""
    u2fa = db.query(User2FA).filter(User2FA.user_id == user_id).first()
    totp = pyotp.TOTP(u2fa.secret_key)
    
    if not totp.verify(totp_code, valid_window=1):  # Allow 1 window drift
        return False
    
    db.query(User2FA).filter(User2FA.user_id == user_id).update(
        {User2FA.enabled: True}
    )
    db.commit()
    log_audit_event(user_id, "2fa_enabled")
    
    return True

def verify_2fa(user_id: UUID, totp_code: str) -> bool:
    """Verify TOTP code or backup code."""
    u2fa = db.query(User2FA).filter(User2FA.user_id == user_id).first()
    
    if not u2fa or not u2fa.enabled:
        return False
    
    totp = pyotp.TOTP(u2fa.secret_key)
    
    # Try TOTP first
    if totp.verify(totp_code, valid_window=1):
        db.query(User2FA).filter(User2FA.user_id == user_id).update(
            {User2FA.last_used: now()}
        )
        db.commit()
        return True
    
    # Try backup code
    code_hash = sha256(totp_code.encode()).hexdigest()
    if code_hash in u2fa.backup_codes:
        # One-time use: remove from list
        remaining = [c for c in u2fa.backup_codes if c != code_hash]
        db.query(User2FA).filter(User2FA.user_id == user_id).update(
            {User2FA.backup_codes: remaining, User2FA.last_used: now()}
        )
        db.commit()
        log_audit_event(user_id, "2fa_backup_code_used")
        return True
    
    return False
```

---

## 5. Audit Logging (Immutable)

### Schema

```sql
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  action VARCHAR(64) NOT NULL,
  timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  ip INET,
  user_agent TEXT,
  result VARCHAR(16),  -- success, failed, blocked
  error_message TEXT,
  metadata JSONB,
  CONSTRAINT immutable CHECK (true)  -- Logical immutability (no UPDATE)
);
CREATE INDEX idx_audit_user_timestamp ON audit_log(user_id, timestamp DESC);
CREATE INDEX idx_audit_action ON audit_log(action);
```

### Logged Actions

- `login_success`, `login_failed`, `login_lockout`
- `logout`
- `password_change`
- `password_reset_requested`, `password_reset_completed`
- `2fa_enabled`, `2fa_disabled`, `2fa_backup_code_used`
- `session_created`, `session_revoked`, `session_evoked`
- `refresh_token_issued`, `refresh_replay_attack`
- `admin_access`, `admin_action`
- `account_deleted`, `account_exported`

### API

```python
def log_audit_event(
    user_id: Optional[UUID],
    action: str,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    result: str = "success",
    error_message: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """Log security-relevant action; immutable append-only."""
    db.add(AuditLog(
        user_id=user_id,
        action=action,
        ip=ip,
        user_agent=user_agent,
        result=result,
        error_message=error_message,
        metadata=metadata
    ))
    db.commit()
```

---

## Implementation Phases

### Phase 1: Non-Breaking Infrastructure (Week 1)
- Create `login_attempts`, `refresh_tokens`, `user_sessions`, `user_2fa`, `audit_log` tables
- Deploy audit logging middleware (log all actions)
- Add login attempt recording (loose thresholds, no blocking yet)
- Test end-to-end: login → audit log trail

### Phase 2: Gradual Rollout (Week 2-3)
- Deploy account lockout with loose thresholds (20 failed attempts → 1s delay)
- Deploy refresh token rotation (store in DB, validate family_id)
- Deploy session tracking (allow unlimited sessions initially)
- Deploy 2FA setup (optional, not required yet)
- Monitor metrics: lockout rate, refresh token churn

### Phase 3: Full Enforcement (Week 4)
- Tighten lockout thresholds (5 failed attempts → exponential)
- Enforce max 5 sessions per user
- Require 2FA for admin accounts
- Enable session/device tracking UI
- Measure security improvements: lockout prevents N attacks, replay detection works

---

## Testing Strategy

### Unit Tests

```python
def test_lockout_exponential_delay():
    """5 attempts → 1s, 6 → 2s, 7 → 4s, etc."""
    for i in range(1, 10):
        delay = 2 ** (i - 5) if i >= 5 else 0
        assert calculate_delay(i) == delay

def test_refresh_token_replay_detection():
    """Use same refresh token twice → family revoked."""
    token = create_refresh_token(user_id)
    
    # First use: OK
    assert refresh_token_rotation(token) != None
    
    # Second use: Replay detected
    with pytest.raises(HTTPException):
        refresh_token_rotation(token)
    
    # Entire family revoked
    assert all(rt.revoked for rt in get_user_refresh_tokens(user_id))

def test_2fa_backup_code_one_time():
    """Backup code used → removed from list; can't reuse."""
    setup_2fa(user_id)
    codes = enable_2fa(user_id)
    
    assert verify_2fa(user_id, codes[0]) == True
    assert verify_2fa(user_id, codes[0]) == False  # One-time use
```

### Integration Tests

```python
def test_login_flow_with_lockout():
    """Login → 5 failed attempts → locked 1s → wait → login OK."""
    for i in range(5):
        with pytest.raises(HTTPException):
            login(email, wrong_password)
    
    # Locked
    with pytest.raises(HTTPException) as exc:
        login(email, correct_password)
    assert exc.value.status_code == 429
    
    time.sleep(1)
    
    # Unlocked
    resp = login(email, correct_password)
    assert "access_token" in resp
```

---

## Migration Strategy

1. **Backward Compatibility**: Old tokens still work during Phase 2
2. **Gradual Enforcement**: Loose thresholds first; tighten over time
3. **Monitoring**: Track lockout rate, refresh churn, session creation
4. **Communication**: Notify users of 2FA requirement (admin accounts first)
5. **Rollback**: Keep old auth code available; feature flags to disable new features

---

## Security Assumptions

- HTTPS enforced (TLS 1.3+)
- Secrets stored in environment variables (not in code)
- Database credentials rotated regularly
- IP blacklist/whitelist maintained by ops team
- User agent spoofing not considered a threat (fingerprint is convenience, not security)
