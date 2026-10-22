import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { answerCurrentQuestion, formatViolations, markLessonSeen, registerUser, uniqueUsername } from './helpers';

/**
 * 46.6 (ADR-68): tras la primera sesión, una pregunta con tres respuestas
 * cerradas. Contra el backend real: la respuesta sale en el lote de
 * `/analytics/client-events` sin texto libre, y en la segunda sesión ya no se
 * pregunta. axe 0 en el resumen con la encuesta.
 */
const SHOTS = '../docs/ui-snapshots/46.6';

for (const width of [390, 1280]) {
  test(`encuesta tras la primera sesión (${width} px)`, async ({ page }) => {
    test.setTimeout(120_000);
    await page.setViewportSize({ width, height: 900 });
    await registerUser(page, { username: uniqueUsername('e2e_enc_'), displayName: 'Encuesta' });
    await markLessonSeen(page);

    const study = async () => {
      await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();
      await expect(page.locator('[class*="questionCard_"]')).toBeVisible({ timeout: 15_000 });
      for (let i = 0; i < 10; i++) {
        await answerCurrentQuestion(page);
        await page.getByRole('button', { name: /^(SIGUIENTE|VER RESULTADOS)$/ }).click();
      }
      await page.getByRole('button', { name: 'Saltar recuento' }).click({ timeout: 10_000 });
    };

    await study();
    const survey = page.getByRole('region', { name: '¿Te ha servido esta sesión?' });
    await expect(survey).toBeVisible();
    await survey.scrollIntoViewIfNeeded();
    await page.screenshot({ path: `${SHOTS}/encuesta-es-${width}.png`, fullPage: true });
    const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
    expect(results.violations, formatViolations(results.violations)).toHaveLength(0);

    const sent = page.waitForRequest(
      (r) => r.url().includes('/analytics/client-events') && (r.postData() ?? '').includes('first_session_survey'),
      { timeout: 20_000 },
    );
    await survey.getByRole('button', { name: 'Algo' }).click();
    await expect(page.getByRole('status').filter({ hasText: 'Gracias' })).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/gracias-es-${width}.png` });
    const body = JSON.parse((await sent).postData() ?? '{}') as { events: Array<Record<string, unknown>> };
    expect(body.events).toContainEqual({ type: 'first_session_survey', answer: 'somewhat' });

    await page.getByRole('button', { name: 'CONTINUAR' }).click();
    await markLessonSeen(page);
    await study();
    await expect(page.getByTestId('summary-grade')).toBeVisible();
    await expect(page.getByRole('region', { name: '¿Te ha servido esta sesión?' })).toHaveCount(0);
  });
}
