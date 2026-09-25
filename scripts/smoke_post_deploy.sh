#!/usr/bin/env bash
# smoke_post_deploy.sh — Post-deploy smoke tests for backend (31.3).
#
# Run after every merge to master (ADR-45) to verify the deploy is healthy.
#
# Usage:
#   ./scripts/smoke_post_deploy.sh
#   API_BASE=https://custom-url.up.railway.app ./scripts/smoke_post_deploy.sh
#
# Exits 0 if all checks pass, 1 on first failure.
set -euo pipefail

API_BASE="${API_BASE:-https://api-production-9751.up.railway.app}"
PASS=true

step() {
  local name="$1"
  shift
  if "$@"; then
    echo "  ✅ $name"
  else
    echo "  ❌ $name"
    PASS=false
    return 1
  fi
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
step "GET /api/v1/tracks returns 200" \
  bash -c "curl -sf '$API_BASE/api/v1/tracks' | python3 -c 'import json,sys; d=json.load(sys.stdin); assert len(d)>0, \"empty tracks\"'"

# 6. Latency check (health under 2s)
step "GET /health responds within 2 seconds" \
  bash -c "TIME=\$(curl -sf -o /dev/null -w '%{time_total}' '$API_BASE/health'); python3 -c \"assert float('$TIME')<2, f'took {$TIME}s'\""

echo
if [ "$PASS" = true ]; then
  echo "✅ All smoke tests PASSED"
  exit 0
else
  echo "❌ Some smoke tests FAILED"
  exit 1
fi
