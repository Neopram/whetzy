#!/usr/bin/env bash
# smoke_post_deploy.sh — Post-deploy smoke tests for backend (31.3).
#
# Run after every merge to master (ADR-45) to verify the deploy is healthy.
#
# Usage:
#   ./scripts/smoke_post_deploy.sh
#   API_BASE=https://custom-url.up.railway.app ./scripts/smoke_post_deploy.sh
#
# QA login (steps 7-8) requires QA_EMAIL and QA_PASSWORD env vars.
# Without them the authenticated steps are skipped, not failed.
#
# Exits 0 if all checks pass, 1 on first failure.
set -euo pipefail

API_BASE="${API_BASE:-https://api-production-9751.up.railway.app}"
PASS=true
TOTAL=0
PASSED=0

step() {
  local name="$1"
  shift
  TOTAL=$((TOTAL + 1))
  if "$@"; then
    echo "  PASS  $name"
    PASSED=$((PASSED + 1))
  else
    echo "  FAIL  $name"
    PASS=false
  fi
}

skip() {
  echo "  SKIP  $1"
}

echo "Post-deploy smoke tests — $API_BASE"
echo

# 1. Health/ready
step "GET /health/ready returns 200" \
  bash -c "curl -sf '$API_BASE/health/ready' | grep -q 'healthy'"

# 2. OpenAPI is served (the app started and routes are mounted)
step "GET /api/v1/openapi.json returns valid JSON" \
  bash -c "curl -sf '$API_BASE/api/v1/openapi.json' | python3 -c 'import json,sys; json.load(sys.stdin)'"

# 3. Quiz start (unauthenticated → 401, not 500)
step "POST /api/v1/quiz/start returns 401 without auth" \
  bash -c "HTTP_CODE=\$(curl -s -o /dev/null -w '%{http_code}' -X POST '$API_BASE/api/v1/quiz/start' -H 'Content-Type: application/json' -d '{}'); [ \"\$HTTP_CODE\" = '401' ]"

# 4. Auth login endpoint exists (returns 422 with empty body, not 404/500)
step "POST /api/v1/auth/login returns 422 with empty body" \
  bash -c "HTTP_CODE=\$(curl -s -o /dev/null -w '%{http_code}' -X POST '$API_BASE/api/v1/auth/login' -H 'Content-Type: application/json' -d '{}'); [ \"\$HTTP_CODE\" = '422' ]"

# 5. Content loaded (tracks endpoint returns data)
step "GET /api/v1/tracks returns 200 with data" \
  bash -c "curl -sf '$API_BASE/api/v1/tracks' | python3 -c 'import json,sys; d=json.load(sys.stdin); assert len(d)>0, \"empty tracks\"'"

# 6. Latency check (health under 2s)
step "GET /health responds within 2 seconds" \
  bash -c "TIME=\$(curl -sf -o /dev/null -w '%{time_total}' '$API_BASE/health'); python3 -c \"assert float('\$TIME')<2, f'took {\$TIME}s'\""

# 7-8. QA login + authenticated quiz start
if [ -n "${QA_EMAIL:-}" ] && [ -n "${QA_PASSWORD:-}" ]; then
  TOKEN=$(curl -sf -X POST "$API_BASE/api/v1/auth/login" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -d "username=$QA_EMAIL&password=$QA_PASSWORD" \
    2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])' 2>/dev/null || echo "")

  if [ -n "$TOKEN" ]; then
    step "POST /api/v1/auth/login with QA account succeeds" true
    step "POST /api/v1/quiz/start with QA auth returns session_id" \
      bash -c "curl -sf -X POST '$API_BASE/api/v1/quiz/start' \
        -H 'Content-Type: application/json' \
        -H 'Authorization: Bearer $TOKEN' \
        -d '{\"mode\":\"study\"}' \
        | python3 -c 'import json,sys; d=json.load(sys.stdin); assert \"session_id\" in d, \"no session_id\"'"
  else
    step "POST /api/v1/auth/login with QA account succeeds" false
    skip "POST /api/v1/quiz/start with QA auth (login failed)"
  fi
else
  skip "QA login (set QA_EMAIL and QA_PASSWORD to enable)"
  skip "Authenticated quiz start (needs QA login)"
fi

echo
echo "$PASSED/$TOTAL steps passed"
if [ "$PASS" = true ]; then
  echo "RESULT: PASS"
  exit 0
else
  echo "RESULT: FAIL"
  exit 1
fi
