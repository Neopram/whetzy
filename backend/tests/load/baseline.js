import http from ''k6/http'';
import { check, group, sleep } from ''k6'';

export const options = {
  // Stages: ramp-up to 1,000 VUs, sustain, then ramp-down
  stages: [
    { duration: ''2m'', target: 100 },     // Ramp-up to 100 VUs
    { duration: ''5m'', target: 1000 },    // Climb to 1,000 VUs (1 sec each)
    { duration: ''5m'', target: 1000 },    // Sustain at 1,000 VUs
    { duration: ''2m'', target: 0 },       // Ramp-down to 0
  ],
  // SLA thresholds — test fails if these aren''t met
  thresholds: {
    ''http_req_duration'': [''p(95)<500'', ''p(99)<1000''],  // 95th percentile latency
    ''http_req_failed'': [''rate<0.1''],  // Error rate <10%
    ''http_reqs'': [''rate>100''],  // At least 100 req/sec sustained
  },
};

const BASE_URL = __ENV.BASE_URL || ''http://localhost:8000'';
const TIMEOUT = ''10s'';

// Track auth token for authenticated requests (optional)
let authToken = null;

export default function () {
  // Group 1: Health check (unthrottled)
  group(''Health & Readiness'', () => {
    let res = http.get(`${BASE_URL}/health`, { timeout: TIMEOUT });
    check(res, {
      ''health returns 200'': (r) => r.status === 200,
      ''response time <100ms'': (r) => r.timings.duration < 100,
    });

    // Readiness includes DB check — higher latency OK
    res = http.get(`${BASE_URL}/health/ready`, { timeout: TIMEOUT });
    check(res, {
      ''readiness returns 200'': (r) => r.status === 200,
    });
  });

  // Group 2: Public API endpoints (cached)
  group(''Public Content (Cached)'', () => {
    // Glossary: paginated, should be cached by Cloudflare/browser
    let res = http.get(`${BASE_URL}/api/v1/glossary?limit=50&offset=0`, {
      timeout: TIMEOUT,
    });
    check(res, {
      ''glossary returns 200'': (r) => r.status === 200,
      ''glossary includes terms'': (r) => r.body.includes(''term'') || r.status !== 200,
    });

    // Tracks: list of learning tracks
    res = http.get(`${BASE_URL}/api/v1/tracks`, { timeout: TIMEOUT });
    check(res, {
      ''tracks returns 200'': (r) => r.status === 200,
      ''tracks has data'': (r) => r.body.length > 0,
    });

    // Pagination test
    res = http.get(`${BASE_URL}/api/v1/glossary?limit=20&offset=20`, {
      timeout: TIMEOUT,
    });
    check(res, {
      ''pagination works (offset=20)'': (r) => r.status === 200,
    });
  });

  // Group 3: Rate-limited endpoints (auth)
  group(''Auth Endpoints (Rate-Limited)'', () => {
    // These are rate-limited (12 req/min per IP in production)
    // In load test, may hit 429 if we exceed limit — that''s OK, just track it

    let res = http.post(
      `${BASE_URL}/api/v1/auth/health`,
      JSON.stringify({ message: ''test'' }),
      {
        headers: { ''Content-Type'': ''application/json'' },
        timeout: TIMEOUT,
      }
    );
    check(res, {
      ''auth endpoint responds'': (r) => r.status < 500,  // 200, 401, 429 all OK
      ''no server errors'': (r) => r.status < 500,
    });
  });

  // Group 4: Tutor endpoint (expensive, rate-limited)
  group(''Tutor (LLM) Endpoint'', () => {
    // Tutor is expensive, rate-limited to 12 req/min per IP
    // We''ll hit this limit quickly in a load test — expected

    let res = http.post(
      `${BASE_URL}/api/v1/tutor/ask`,
      JSON.stringify({
        question_id: 1,
        user_answer: ''test answer'',
      }),
      {
        headers: { ''Content-Type'': ''application/json'' },
        timeout: TIMEOUT,
      }
    );
    check(res, {
      ''tutor responds (may be 429)'': (r) => r.status > 0,  // Any response is OK
      ''tutor not 500'': (r) => r.status !== 500,
    });
  });

  // Small sleep to avoid hammering the server
  sleep(0.5);  // 500ms between iterations per VU
}

/**
 * Setup: runs once at test start
 * Can initialize auth, load test data, etc.
 */
export function setup() {
  // Optional: register test user or get auth token
  console.log(`Starting load test against ${BASE_URL}`);
  return { testStartTime: Date.now() };
}

/**
 * Teardown: runs once after test completes
 */
export function teardown(data) {
  const duration = Date.now() - data.testStartTime;
  console.log(`Load test completed in ${duration}ms`);
}
