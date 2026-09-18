/**
 * 11.6 — Time-To-First-Question (TTFQ) against production (whetzy.com).
 *
 * Run with:
 *   E2E_BASE_URL=https://whetzy.com AUTH_RATE_LIMIT=200 npx playwright test ttfq-prod
 *
 * The test is skipped when E2E_BASE_URL is not set (local dev suite) so it
 * never runs against the local dev server by accident.
 */
import { test, expect, CDPSession } from '@playwright/test';
import { registerUser, uniqueUsername } from './helpers';

const PROD_URL = process.env.E2E_BASE_URL ?? '';

test.describe('11.6 — TTFQ production (4G simulation)', () => {
  test.skip(!PROD_URL.includes('whetzy'), 'Only runs when E2E_BASE_URL=https://whetzy.com');

  test('registration → first question < 60 s on 4G', async ({ page, context }) => {
    // Emulate 4G: 4 Mbps down / 2 Mbps up / 150 ms latency (typical LTE)
    const cdp: CDPSession = await context.newCDPSession(page);
    await cdp.send('Network.enable');
    await cdp.send('Network.emulateNetworkConditions', {
      offline: false,
      downloadThroughput: (4 * 1024 * 1024) / 8, // bytes/s
      uploadThroughput: (2 * 1024 * 1024) / 8,
      latency: 150,
    });

    const t0 = Date.now();

    const username = uniqueUsername('e2e_ttfq_');
    await registerUser(page, { username, displayName: 'TTFQ 4G' });

    // Home is now visible — start a study session
    await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();

    // Wait for the first question card
    await expect(page.locator('[class*="questionCard_"]')).toBeVisible({ timeout: 60_000 });

    const ttfq = Date.now() - t0;
    console.log(`\n[11.6] TTFQ 4G on ${PROD_URL}: ${ttfq} ms`);
    expect(ttfq, `TTFQ must be < 60 000 ms on 4G, got ${ttfq} ms`).toBeLessThan(60_000);
  });

  test('LCP on landing < 2500 ms on 4G', async ({ page, context }) => {
    const cdp: CDPSession = await context.newCDPSession(page);
    await cdp.send('Network.enable');
    await cdp.send('Network.emulateNetworkConditions', {
      offline: false,
      downloadThroughput: (4 * 1024 * 1024) / 8,
      uploadThroughput: (2 * 1024 * 1024) / 8,
      latency: 150,
    });

    // Inject LCP observer before navigation
    await page.addInitScript(() => {
      (window as unknown as Record<string, unknown>).__lcp = 0;
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          (window as unknown as Record<string, unknown>).__lcp = entry.startTime;
        }
      }).observe({ type: 'largest-contentful-paint', buffered: true });
    });

    await page.goto('/');
    // Give the LCP observer a moment to fire
    await page.waitForTimeout(2000);

    const lcp = await page.evaluate(() => (window as unknown as Record<string, number>).__lcp ?? 0);
    console.log(`\n[11.6] LCP 4G on ${PROD_URL}: ${lcp.toFixed(0)} ms`);
    expect(lcp, `LCP must be < 2500 ms on 4G, got ${lcp.toFixed(0)} ms`).toBeLessThan(2500);
  });
});
