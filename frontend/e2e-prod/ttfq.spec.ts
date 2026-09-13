import { expect, test, type Page } from '@playwright/test';

/**
 * 11.6 — "Tiempo hasta la primera pregunta < 60 s desde la landing, registro
 * incluido" and "LCP < 2,5 s en 4G", measured against the *deployed* stack.
 *
 * Both numbers come from one throttled session so they describe the same
 * network, but they assert in separate tests: a failing LCP must not hide a
 * passing time-to-first-question, or the other way round.
 *
 * STATUS: currently BLOCKED by H.11 in docs/AUTONOMOUS_STATE.md. The build deployed
 * at whetzy.com predates the landing page entirely — `/landing` renders the auth
 * screen, so `h1.lnd-hero__h1` does not exist and both tests fail at the first
 * assertion. That failure is a true report about production, not a broken test.
 * Run this again once the frontend is redeployed; it is not part of CI, because CI
 * must not go red on the state of a deploy it does not perform.
 *
 * Run: npm run test:e2e:prod
 */

/**
 * Which "4G" is being measured. They are not the same and the difference is worth
 * a full second of LCP, so the profile is explicit rather than implied:
 *
 *  - `fast4g` (default) — Chrome DevTools' "Fast 4G": 4 Mbps down / 3 Mbps up / 150 ms.
 *  - `slow4g` — the profile Lighthouse's mobile preset uses: 1.6 Mbps down /
 *    750 kbps up / 150 ms. Harsher, and the one behind the 3.5 s figure recorded
 *    in the project log, so quote that number only against this profile.
 *
 * Select with NET_PROFILE=slow4g.
 */
const NET_PROFILES = {
  fast4g: {
    offline: false,
    downloadThroughput: (4 * 1024 * 1024) / 8,
    uploadThroughput: (3 * 1024 * 1024) / 8,
    latency: 150,
  },
  slow4g: {
    offline: false,
    downloadThroughput: (1.6 * 1024 * 1024) / 8,
    uploadThroughput: (750 * 1024) / 8,
    latency: 150,
  },
} as const;

const PROFILE = (process.env.NET_PROFILE as keyof typeof NET_PROFILES) ?? 'fast4g';
const FOUR_G = NET_PROFILES[PROFILE];

const PASSWORD = 'PerfProbe!2026';

/** Installs a buffered LCP observer before any page script runs. */
async function observeLcp(page: Page): Promise<void> {
  await page.addInitScript(() => {
    (window as unknown as { __lcp: number }).__lcp = 0;
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        (window as unknown as { __lcp: number }).__lcp = entry.startTime;
      }
    }).observe({ type: 'largest-contentful-paint', buffered: true });
  });
}

/**
 * CPU slowdown applied on top of the network throttle.
 *
 * Network throttling alone is not "a mid-range phone on 4G": it leaves a fast
 * desktop CPU doing the React mount, which is exactly the work that decides the
 * LCP of this landing (the LCP element is an <h1> React has to render). Measuring
 * without it produces a flattering number that is not comparable to the Lighthouse
 * mobile figure in the project log, so both are applied. 4x is the multiplier
 * Lighthouse's own mobile preset uses.
 */
const CPU_SLOWDOWN = 4;

async function throttleTo4g(page: Page): Promise<void> {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Network.enable');
  await cdp.send('Network.emulateNetworkConditions', FOUR_G);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: CPU_SLOWDOWN });
}

/**
 * Soft-deletes the throttled run's account so a performance probe never shows
 * up as a real signup in the D1/D7 funnel (5.4) it would otherwise pollute.
 */
async function deleteAccount(page: Page, apiBase: string): Promise<string> {
  return page.evaluate(async (base) => {
    const token = localStorage.getItem('whetzy_access_token');
    if (!token) return 'no-token';
    const r = await fetch(`${base}/auth/me/account`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    return `${r.status}`;
  }, apiBase);
}

test.describe('production performance on 4G', () => {
  test('time from landing to first question is under 60 s, registration included', async ({
    page,
  }) => {
    await observeLcp(page);
    await throttleTo4g(page);

    const ts = Date.now();
    const email = `e2e-perf-${ts}@example.com`;
    const username = `perfprobe${ts}`;

    const t0 = Date.now();

    await page.goto('/landing', { waitUntil: 'commit' });
    await expect(page.locator('h1.lnd-hero__h1')).toBeVisible({ timeout: 60_000 });

    const lcpMs = await page.evaluate(() => (window as unknown as { __lcp: number }).__lcp);

    // Hero CTA — the plan cards reuse the same label, so target the hero class.
    await page.locator('button.lnd-hero__cta').click();

    // goToAuth does a full document navigation to '/'.
    await expect(page.getByLabel(/nombre/i)).toBeVisible({ timeout: 60_000 });

    await page.getByLabel(/nombre/i).fill('Perf Probe');
    await page.getByLabel(/usuario/i).fill(username);
    await page.getByLabel(/correo/i).fill(email);
    await page.getByLabel(/contraseña/i).fill(PASSWORD);
    await page.getByRole('button', { name: /empezar a aprender/i }).click();

    // First-run users land on onboarding; its CTA shares the register label, so
    // wait for onboarding's own headline before clicking through.
    const onboardingHeadline = page.getByText(/Aprende Python de 0 a AI Engineer/i);
    if (await onboardingHeadline.isVisible({ timeout: 30_000 }).catch(() => false)) {
      await page.getByRole('button', { name: /empezar a aprender/i }).click();
    }

    await page.getByRole('button', { name: /estudiar ahora/i }).click({ timeout: 60_000 });

    // The question card's <h2> is the first thing a learner can actually read.
    const questionText = page.locator('h2').first();
    await expect(questionText).toBeVisible({ timeout: 60_000 });
    await expect(questionText).not.toBeEmpty();

    const ttfqMs = Date.now() - t0;

    const apiBase = await page.evaluate(
      () => (window as unknown as { __API_BASE?: string }).__API_BASE ?? '',
    );
    const cleanup = await deleteAccount(
      page,
      apiBase || 'https://api-production-9751.up.railway.app/api/v1',
    );

    console.log(
      `[11.6] profile=${PROFILE}+${CPU_SLOWDOWN}x CPU | time-to-first-question=${ttfqMs} ms | ` +
        `landing LCP=${Math.round(lcpMs)} ms | ` +
        `question="${(await questionText.textContent())?.slice(0, 60)}" | cleanup=${cleanup}`,
    );

    expect(ttfqMs, `time to first question on 4G (budget 60000 ms)`).toBeLessThan(60_000);
  });

  test('landing LCP is under 2.5 s', async ({ page }) => {
    await observeLcp(page);
    await throttleTo4g(page);

    await page.goto('/landing', { waitUntil: 'commit' });
    await expect(page.locator('h1.lnd-hero__h1')).toBeVisible({ timeout: 60_000 });
    await page.waitForLoadState('networkidle');

    const lcpMs = await page.evaluate(() => (window as unknown as { __lcp: number }).__lcp);
    console.log(`[11.6] landing LCP on ${PROFILE} + ${CPU_SLOWDOWN}x CPU = ${Math.round(lcpMs)} ms`);

    expect(lcpMs, 'landing LCP on 4G (budget 2500 ms)').toBeLessThan(2_500);
  });
});
