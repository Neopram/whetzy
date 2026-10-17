import { test, expect } from '@playwright/test';
import { completeOnboarding, uniqueUsername } from './helpers';

/**
 * English mirror of onboarding.spec.ts (24.3's own criterion: "e2e ES y EN" —
 * the ES version existed, this one didn't). `playwright.config.ts` pins the
 * default project to `locale: 'es-ES'` and its own comment already says
 * "Los tests bilingües fijan el inglés ellos mismos" — this is that: no
 * separate Playwright project needed, `test.use` overrides the context
 * locale for this file only, and AuthScreen picks English from
 * `navigator.language` on its own (34.11), with no `?lang=en` in the URL.
 */
test.use({ locale: 'en-US' });

test('onboarding (EN): landing → first answered question in < 60 s', async ({ page }) => {
  const start = Date.now();

  const username = uniqueUsername('e2e_ob_en_');
  await page.goto('/auth');
  await expect(page.getByRole('button', { name: 'Sign up' })).toBeVisible();

  // exact: true — "Name" is a case-insensitive substring of "Username", and
  // Playwright's default getByLabel match is substring, so plain 'Name'
  // resolves to both fields (found running this against the real page: ES
  // has no such collision, "Nombre" vs "Usuario" share no substring).
  await page.getByLabel('Name', { exact: true }).fill('Onboarding Test EN');
  await page.getByLabel('Username').fill(username);
  await page.getByLabel('Email').fill(`${username}@example.com`);
  await page.getByLabel('Password').fill('e2e-test-pass-123');
  await page.getByLabel('I confirm I am 13 years old or older').check();
  await page.getByRole('button', { name: 'START LEARNING' }).click();

  // 43.3 (D2): goal → track → experience → placement test, in English.
  await completeOnboarding(page, { lang: 'en', takeTest: true });

  await page.getByRole('button', { name: 'START EXAM' }).click();
  await expect(page.getByText('Question 1 of 20')).toBeVisible({ timeout: 15_000 });
  await page.getByTestId('placement-option').first().click();
  await expect(page.getByText('Question 2 of 20')).toBeVisible({ timeout: 15_000 });

  const elapsed = (Date.now() - start) / 1000;
  expect(elapsed, `Took ${elapsed.toFixed(1)}s — must be < 60s`).toBeLessThan(60);
});
