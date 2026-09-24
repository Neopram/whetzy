/**
 * Performance budget spec (8.3).
 *
 * Targets run against the dev server (no minification, no tree-shaking) so the
 * budgets are intentionally generous — they exist to catch catastrophic
 * regressions (a 10 MB library, a sync-blocking script, etc.) not to enforce
 * exact production numbers.
 *
 * Production targets (verified by scripts/check-bundle.mjs + manual Lighthouse):
 *   LCP  < 2.5 s   (Lighthouse Good)
 *   TTI  < 3.5 s   (Lighthouse Good)
 *   JS bundle < 300 KB gzip (measured: 175 KB)
 *
 * CI targets for this spec (dev server on a shared vCPU):
 *   LCP  < 8 s
 *   domInteractive < 10 s  (proxy for TTI on an SPA)
 */

import { test, expect } from '@playwright/test';

const LCP_BUDGET_MS = 8_000;
const DOM_INTERACTIVE_BUDGET_MS = 10_000;

test.describe('perf-budget', () => {
  test('auth page LCP within budget', async ({ page }) => {
    // Inject LCP observer BEFORE navigation so it catches paint events.
    await page.addInitScript(() => {
      (window as unknown as Record<string, unknown>).__lcpTime = 0;
      const obs = new PerformanceObserver((list) => {
        const e = list.getEntries();
        if (e.length) {
          (window as unknown as Record<string, unknown>).__lcpTime =
            (e[e.length - 1] as PerformancePaintTiming).startTime;
        }
      });
      obs.observe({ entryTypes: ['largest-contentful-paint'] });
    });

    await page.goto('/');
    // Wait for at least one painted element to be visible
    await expect(page.locator('button, input, h1, h2').first()).toBeVisible({ timeout: LCP_BUDGET_MS });

    const lcp = await page.evaluate(
      () => (window as unknown as Record<string, unknown>).__lcpTime as number,
    );
    // If LCP never fired (headless quirk), use navigation timing as fallback
    const timing = lcp > 0 ? lcp : await page.evaluate(() => {
      const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return nav.loadEventEnd;
    });
    expect(timing, `LCP/load ${timing.toFixed(0)} ms exceeds ${LCP_BUDGET_MS} ms budget`).toBeLessThan(LCP_BUDGET_MS);
  });

  test('auth page domInteractive within budget', async ({ page }) => {
    // /auth, no '/': sin sesión '/' es la landing, cuyas CTA son enlaces y no
    // tiene button ni input que esperar.
    await page.goto('/auth');
    // Wait for React to mount (at least one interactive element visible)
    await expect(page.locator('button, input').first()).toBeVisible({ timeout: DOM_INTERACTIVE_BUDGET_MS });

    const domInteractive = await page.evaluate(() => {
      const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return nav.domInteractive;
    });
    expect(
      domInteractive,
      `domInteractive ${domInteractive.toFixed(0)} ms exceeds ${DOM_INTERACTIVE_BUDGET_MS} ms budget`,
    ).toBeLessThan(DOM_INTERACTIVE_BUDGET_MS);
  });
});
