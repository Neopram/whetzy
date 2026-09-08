import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { registerUser, uniqueUsername } from './helpers';

test.describe('WCAG 2.2 AA — axe-core', () => {
  test('auth screen has zero violations', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /Whetzy/i }).or(page.locator('h1,h2').first())).toBeVisible({ timeout: 10_000 }).catch(() => undefined);

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
      .analyze();

    expect(results.violations, formatViolations(results.violations)).toHaveLength(0);
  });

  test('home screen has zero violations after login', async ({ page }) => {
    const username = uniqueUsername('e2e_a11y_');
    await registerUser(page, { username, displayName: 'A11y Test' });

    await expect(page.getByRole('button', { name: 'ESTUDIAR AHORA' })).toBeVisible({ timeout: 10_000 });

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
      .analyze();

    expect(results.violations, formatViolations(results.violations)).toHaveLength(0);
  });

  test('legal screen (privacy) has zero violations', async ({ page }) => {
    await page.goto('/privacy');
    await expect(page.locator('h1')).toBeVisible({ timeout: 10_000 });

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
      .analyze();

    expect(results.violations, formatViolations(results.violations)).toHaveLength(0);
  });
});

type AxeViolation = { id: string; impact?: string | null; description: string; nodes: { html: string }[] };

function formatViolations(violations: AxeViolation[]): string {
  if (!violations.length) return '';
  return violations
    .map((v) => `[${v.impact ?? 'unknown'}] ${v.id}: ${v.description}\n  ${v.nodes.map((n) => n.html).join('\n  ')}`)
    .join('\n\n');
}
