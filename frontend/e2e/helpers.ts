import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';

/** Fills the registration form and submits it, landing on the home screen. */
export async function registerUser(page: Page, opts: { username: string; displayName: string }) {
  const { username, displayName } = opts;
  // NOTE: use a real, deliverable-looking domain — python's email-validator
  // (used by pydantic's EmailStr on the backend) rejects reserved TLDs like
  // .test/.example/.invalid as "special-use" even though RFC 2606 reserves
  // them for exactly this purpose.
  const email = `${username}@example.com`;

  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Crear cuenta' })).toBeVisible();

  await page.getByLabel('Nombre').fill(displayName);
  await page.getByLabel('Usuario').fill(username);
  await page.getByLabel('Correo electrónico').fill(email);
  await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
  await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();

  // Successful registration lands on the home screen (bottom nav visible).
  await expect(page.getByRole('button', { name: 'Inicio' })).toBeVisible({ timeout: 15_000 });
}

/** Unique-enough username per test run so re-runs don't collide on a shared DB. */
export function uniqueUsername(prefix: string): string {
  return `${prefix}${Date.now().toString(36)}${Math.floor(Math.random() * 1000)}`;
}

/**
 * Answers whatever question is currently on screen in QuizScreen and waits
 * for the feedback panel. Handles both MCQ questions (click an option) and
 * exec-type questions (fill_blank_exec / fix_bug: run up to 3 times — the
 * app auto-submits as incorrect on the 3rd attempt, so this always reaches
 * feedback without needing Pyodide to actually produce the right answer).
 */
export async function answerCurrentQuestion(page: Page) {
  const options = page.locator('[class*="options_"] button');
  if (await options.count() > 0) {
    await options.first().click();
  } else {
    const runBtn = page.locator('[class*="btnRun_"]');
    await expect(runBtn).toBeVisible({ timeout: 10_000 });
    for (let attempt = 0; attempt < 3; attempt++) {
      if (await page.locator('[class*="explanation_"]').isVisible().catch(() => false)) break;
      await expect(runBtn).toBeEnabled({ timeout: 60_000 });
      await runBtn.click();
      await page.waitForTimeout(500);
    }
  }
  await expect(page.locator('[class*="explanation_"]')).toBeVisible({ timeout: 10_000 });
}

/** Registers a user and completes one 10-question study session so they have
 * skill history — required by the backend before /duels/challenge accepts a
 * challenge ("You haven't studied any skill yet"). */
export async function registerAndCompleteAQuiz(page: Page, opts: { username: string; displayName: string }) {
  await registerUser(page, opts);
  await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();
  await expect(page.locator('[class*="questionCard_"]')).toBeVisible({ timeout: 15_000 });
  for (let i = 0; i < 10; i++) {
    await answerCurrentQuestion(page);
    await page.locator('[class*="btnNext_"]').click();
  }
  await expect(page.locator('[class*="summaryGrade_"]')).toBeVisible({ timeout: 10_000 });
  await page.locator('[class*="btnStudy_"]').click();
  await expect(page.getByRole('button', { name: 'Inicio' })).toBeVisible();
}
