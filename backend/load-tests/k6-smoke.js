/**
 * k6 smoke load test (8.2)
 *
 * Scenario: 100 virtual users (VUs) for 30 s, simulating the core
 * authenticated request loop.
 *
 * Usage (local, against dev backend on :8000 with 4 uvicorn workers):
 *   TRUST_PROXY_HEADERS=True DEFAULT_RATE_LIMIT=10000 \
 *     uvicorn app.main:app --workers 4 --port 8000
 *   k6 run backend/load-tests/k6-smoke.js
 *
 * Against production:
 *   k6 run --env BASE_URL=https://api-production-9751.up.railway.app \
 *           --env P95_BUDGET_MS=500 \
 *           backend/load-tests/k6-smoke.js
 *
 * Success criteria (production Railway target):
 *   - p95 latency < 500 ms  (local dev: ~3000 ms on a single-machine Docker PG)
 *   - 0 HTTP 5xx responses
 *   - error rate < 1%
 *
 * P95_BUDGET_MS env var overrides the latency threshold (default 3000 for local,
 * set to 500 when running against production).
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const BASE = __ENV.BASE_URL || 'http://127.0.0.1:8000';
// Local dev: ~3 s (4-worker uvicorn + local Docker PG, 100 VUs measured 2.58 s p95)
// Production Railway target: 500 ms
const P95_MS = parseInt(__ENV.P95_BUDGET_MS || '3000', 10);

export const errorRate = new Rate('error_rate');
export const reqDuration = new Trend('req_duration', true);

export const options = {
  stages: [
    { duration: '5s',  target: 20  },  // ramp up
    { duration: '20s', target: 100 },  // hold at 100 VUs
    { duration: '5s',  target: 0   },  // ramp down
  ],
  thresholds: {
    [`http_req_duration`]: [`p(95)<${P95_MS}`],  // 3000 ms local / 500 ms prod
    http_req_failed: ['rate<0.01'],               // 0 5xx (enforced locally too)
    error_rate:      ['rate<0.01'],
  },
};

// ---------------------------------------------------------------------------
// setup(): run once, register a user and return the auth token
// ---------------------------------------------------------------------------

export function setup() {
  const ts = Date.now();
  const reg = http.post(
    `${BASE}/api/v1/auth/register`,
    JSON.stringify({
      username: `k6user_${ts}`,
      email: `k6_${ts}@loadtest.whetzy.io`,
      password: 'K6pass!23',
      display_name: 'k6',
    }),
    { headers: { 'Content-Type': 'application/json' } },
  );
  if (reg.status !== 201) {
    console.error(`setup() register failed: ${reg.status} — ${reg.body}`);
    return { token: null };
  }
  const token = reg.json('access_token');
  return { token };
}

// ---------------------------------------------------------------------------
// default(): per-VU request loop
// ---------------------------------------------------------------------------

export default function (data) {
  const { token } = data;
  // Unique per-VU source IP so each VU gets its own rate-limit bucket
  // (simulates requests coming through a load balancer with TRUST_PROXY_HEADERS=true).
  const vuIp = `10.${Math.floor(__VU / 255)}.${__VU % 255}.1`;
  const authHeaders = token
    ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json', 'X-Forwarded-For': vuIp }
    : { 'Content-Type': 'application/json', 'X-Forwarded-For': vuIp };

  // 1. health check (unauthenticated)
  const health = http.get(`${BASE}/health`);
  const healthOk = check(health, {
    'health 200': (r) => r.status === 200,
  });
  errorRate.add(!healthOk);
  reqDuration.add(health.timings.duration);

  // 2. authenticated: progress dashboard
  if (token) {
    const dash = http.get(`${BASE}/api/v1/progress/dashboard`, { headers: authHeaders });
    const dashOk = check(dash, {
      'dashboard 200': (r) => r.status === 200,
      'dashboard no 5xx': (r) => r.status < 500,
    });
    errorRate.add(!dashOk);
    reqDuration.add(dash.timings.duration);
  }

  // 3. authenticated: start a quiz (returns question or null)
  if (token) {
    const quiz = http.post(
      `${BASE}/api/v1/quiz/start`,
      JSON.stringify({}),
      { headers: authHeaders },
    );
    const quizOk = check(quiz, {
      'quiz/start 200': (r) => r.status === 200,
      'quiz/start no 5xx': (r) => r.status < 500,
    });
    errorRate.add(!quizOk);
    reqDuration.add(quiz.timings.duration);
  }

  sleep(0.5);
}
