import { test, expect } from '@playwright/test';
import { completeOnboarding, uniqueUsername } from './helpers';

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

  test('Onboarding (ES): objetivo, rejilla de rutas, experiencia y prueba', async ({ page }) => {
    const username = uniqueUsername('e2e_scroll_es_');
    await page.goto('/auth');
    await page.getByLabel('Nombre').fill('Scroll Test');
    await page.getByLabel('Usuario').fill(username);
    await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
    await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
    await page.getByLabel('Confirmo que tengo 13 años o más').check();
    await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();

    // 43.3 (D2): cada paso, sobre todo la rejilla de 24 rutas agrupadas.
    const onboarding = page.getByTestId('onboarding');
    await expect(onboarding).toBeVisible({ timeout: 15_000 });
    await expectNoHorizontalScroll(page, 'Onboarding ES — objetivo');
    await onboarding.getByRole('button', { name: 'Las dos cosas' }).click();
    await expect(onboarding.getByTestId('track-track01')).toBeVisible({ timeout: 15_000 });
    await expectNoHorizontalScroll(page, 'Onboarding ES — rutas');
    await onboarding.getByTestId('track-track01').click();
    await expectNoHorizontalScroll(page, 'Onboarding ES — certificación');
    await onboarding.getByRole('button', { name: 'Ahora no' }).click();
    await expectNoHorizontalScroll(page, 'Onboarding ES — experiencia');
    await onboarding.getByRole('button', { name: 'Empiezo de cero' }).click();
    await expectNoHorizontalScroll(page, 'Onboarding ES — prueba de nivel');
  });

  test('Onboarding (EN): goal, track grid, experience and test', async ({ page }) => {
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
    await expectNoHorizontalScroll(page, 'Onboarding EN — goal');
    await onboarding.getByRole('button', { name: 'Both' }).click();
    await expect(onboarding.getByTestId('track-track01')).toBeVisible({ timeout: 15_000 });
    await expectNoHorizontalScroll(page, 'Onboarding EN — tracks');
    await onboarding.getByTestId('track-track01').click();
    await expectNoHorizontalScroll(page, 'Onboarding EN — certification');
    await onboarding.getByRole('button', { name: 'Not now' }).click();
    await expectNoHorizontalScroll(page, 'Onboarding EN — experience');
    await onboarding.getByRole('button', { name: "I'm starting from zero" }).click();
    await expectNoHorizontalScroll(page, 'Onboarding EN — placement test');
  });

  test('Home (ES): tras el onboarding, y la primera pregunta de la prueba de nivel', async ({ page }) => {
    const username = uniqueUsername('e2e_scroll_home_');
    await page.goto('/auth');
    await page.getByLabel('Nombre').fill('Scroll Home');
    await page.getByLabel('Usuario').fill(username);
    await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
    await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
    await page.getByLabel('Confirmo que tengo 13 años o más').check();
    await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();

    // 43.3 (D2): «empiezo de cero» va a Hoy.
    await completeOnboarding(page);
    await expect(page.getByRole('button', { name: 'Hoy', exact: true })).toBeVisible({ timeout: 15_000 });
    await expectNoHorizontalScroll(page, 'Home ES');

    // La primera pregunta, la de la prueba de nivel de su ruta (Rutas → prueba).
    await page.getByRole('button', { name: 'Rutas' }).click();
    await page.getByRole('button', { name: /¿Ya sabes algo de esto\?/ }).click();
    await page.getByRole('button', { name: 'COMENZAR EXAMEN' }).click();
    await expect(page.getByTestId('placement-option').first()).toBeVisible({ timeout: 15_000 });
    await expectNoHorizontalScroll(page, 'Prueba de nivel ES');
    await page.getByTestId('placement-option').first().click();
    await expectNoHorizontalScroll(page, 'Prueba de nivel ES — respuesta');
  });
});
