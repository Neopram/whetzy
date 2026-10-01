import { test, expect } from '@playwright/test';
import { answerCurrentQuestion, uniqueUsername } from './helpers';

/**
 * 34.4's own criterion: "390 px sin scroll horizontal" on the funnel that
 * decides whether someone stays — Auth and Onboarding — in both languages.
 * A page wider than its own viewport is the classic mobile bug (a fixed-width
 * element, an unwrapped long string) that a desktop-viewport review never
 * catches. `document.documentElement.scrollWidth > clientWidth` is the same
 * check DevTools' own "no horizontal overflow" warning uses.
 */
const VIEWPORT = { width: 390, height: 844 };

async function expectNoHorizontalScroll(page: import('@playwright/test').Page, where: string) {
  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
  expect(
    overflow.scrollWidth,
    `${where}: scrollWidth ${overflow.scrollWidth}px > clientWidth ${overflow.clientWidth}px — horizontal scroll at 390px`,
  ).toBeLessThanOrEqual(overflow.clientWidth);
}

test.describe('390px, sin scroll horizontal (34.4)', () => {
  test.use({ viewport: VIEWPORT });

  test('Auth (ES): login y registro', async ({ page }) => {
    await page.goto('/auth');
    await expect(page.getByRole('button', { name: 'Crear cuenta' })).toBeVisible();
    await expectNoHorizontalScroll(page, 'Auth ES — register');

    await page.getByRole('button', { name: 'Iniciar sesión' }).click();
    await expect(page.getByLabel('Correo electrónico')).toBeVisible();
    await expectNoHorizontalScroll(page, 'Auth ES — login');
  });

  test('Auth (EN): sign up and log in', async ({ page }) => {
    await page.goto('/auth?lang=en');
    await expect(page.getByRole('button', { name: 'Sign up' })).toBeVisible();
    await expectNoHorizontalScroll(page, 'Auth EN — register');

    await page.getByRole('button', { name: 'Log in' }).click();
    await expect(page.getByLabel('Email')).toBeVisible();
    await expectNoHorizontalScroll(page, 'Auth EN — login');
  });

  test('Onboarding (ES): las 3 preguntas de segmento y el paso de idioma', async ({ page }) => {
    const username = uniqueUsername('e2e_scroll_es_');
    await page.goto('/auth');
    await page.getByLabel('Nombre').fill('Scroll Test');
    await page.getByLabel('Usuario').fill(username);
    await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
    await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
    await page.getByLabel('Confirmo que tengo 13 años o más').check();
    await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();

    const onboarding = page.getByTestId('onboarding');
    await expect(onboarding).toBeVisible({ timeout: 15_000 });
    await expectNoHorizontalScroll(page, 'Onboarding ES — pregunta 1');
    for (let i = 0; i < 3; i++) {
      await onboarding.locator('button.option').first().click();
      await page.waitForTimeout(700);
    }
    await expectNoHorizontalScroll(page, 'Onboarding ES — paso de idioma');
  });

  test('Onboarding (EN): the 3 segment questions and the language step', async ({ page }) => {
    const username = uniqueUsername('e2e_scroll_en_');
    await page.goto('/auth?lang=en');
    await page.getByLabel('Name', { exact: true }).fill('Scroll Test EN');
    await page.getByLabel('Username').fill(username);
    await page.getByLabel('Email').fill(`${username}@example.com`);
    await page.getByLabel('Password').fill('e2e-test-pass-123');
    await page.getByLabel('I confirm I am 13 years old or older').check();
    await page.getByRole('button', { name: 'START LEARNING' }).click();

    const onboarding = page.getByTestId('onboarding');
    await expect(onboarding).toBeVisible({ timeout: 15_000 });
    await expectNoHorizontalScroll(page, 'Onboarding EN — question 1');
    for (let i = 0; i < 3; i++) {
      await onboarding.locator('button.option').first().click();
      await page.waitForTimeout(700);
    }
    await expectNoHorizontalScroll(page, 'Onboarding EN — language step');
  });

  test('Home (ES): tras terminar el onboarding y la primera pregunta', async ({ page }) => {
    const username = uniqueUsername('e2e_scroll_home_');
    await page.goto('/auth');
    await page.getByLabel('Nombre').fill('Scroll Home');
    await page.getByLabel('Usuario').fill(username);
    await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
    await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
    await page.getByLabel('Confirmo que tengo 13 años o más').check();
    await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();

    const onboarding = page.getByTestId('onboarding');
    await expect(onboarding).toBeVisible({ timeout: 15_000 });
    for (let i = 0; i < 3; i++) {
      await onboarding.locator('button.option').first().click();
      await page.waitForTimeout(700);
    }
    await onboarding.getByRole('button', { name: /Español/ }).click();

    await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();
    await page.getByRole('button', { name: 'Ir a las lecciones' }).click();
    await page.locator('[aria-expanded="false"]').first().click();
    await page.getByRole('button', { name: /Aprender/ }).first().click();
    const closeLesson = page.getByRole('button', { name: 'Cerrar' });
    await expect(closeLesson).toBeVisible({ timeout: 15_000 });
    await closeLesson.click();

    await page.getByRole('button', { name: 'Hoy', exact: true }).click();
    await expectNoHorizontalScroll(page, 'Home ES');
    await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();
    await expect(page.locator('[class*="questionCard_"]')).toBeVisible({ timeout: 15_000 });
    await expectNoHorizontalScroll(page, 'Quiz ES');
    await answerCurrentQuestion(page);
    await expectNoHorizontalScroll(page, 'Quiz ES — feedback');
  });
});
