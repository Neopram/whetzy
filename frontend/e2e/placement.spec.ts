import { test, expect } from '@playwright/test';
import { registerUser, uniqueUsername } from './helpers';

/**
 * Prueba de nivel hasta el resultado (ledger 35.2).
 *
 * Dos caminos, porque el servidor decide si hay módulos saltables y eso depende
 * de cuántas se aciertan:
 *
 * 1. Real: se contesta la prueba entera contra el servidor y la pantalla tiene
 *    que decir lo mismo que `/placement/result` (o la lista con la regla y
 *    «aciertos de total», o «aún no dominas ningún módulo»).
 * 2. Resultado fijado: el mismo recorrido, pero `/placement/result` devuelve un
 *    módulo saltable conocido, para comprobar el texto exacto de la regla y del
 *    recuento, que el camino real no garantiza que aparezca.
 */
async function openPlacement(page: import('@playwright/test').Page) {
  await page.getByRole('button', { name: 'Rutas' }).click();
  await page.getByRole('button', { name: /¿Ya sabes algo de esto\?/ }).click();
  await page.getByRole('button', { name: 'COMENZAR EXAMEN' }).click();
}

async function answerUntilResult(page: import('@playwright/test').Page) {
  // El motor para a las 50 preguntas como mucho o antes, cuando el error
  // estándar baja de 0,30 (engine/placement.py); ~1 s por pregunta.
  const result = page.getByRole('heading', { name: /Tu nivel estimado/ });
  const option = page.getByTestId('placement-option').first();
  const deadline = Date.now() + 150_000;
  while (Date.now() < deadline) {
    if (await result.isVisible()) return;
    if (await option.isVisible().catch(() => false) && await option.isEnabled().catch(() => false)) {
      await option.click().catch(() => undefined);
    }
    await page.waitForTimeout(200);
  }
  await expect(result).toBeVisible();
}

test.describe('placement result', () => {
  test('the result screen says what the server decided', async ({ page }) => {
    test.setTimeout(200_000);
    await registerUser(page, { username: uniqueUsername('e2e_place_'), displayName: 'E2E Place' });
    const resultResponse = page.waitForResponse((r) => r.url().includes('/placement/result'), { timeout: 170_000 });

    await openPlacement(page);
    await answerUntilResult(page);

    const body = (await (await resultResponse).json()) as {
      module_recommendations: { can_skip: boolean; accuracy: number; questions_seen: number }[];
    };
    const skippable = body.module_recommendations.filter((m) => m.can_skip);
    if (skippable.length === 0) {
      await expect(page.getByText('aún no dominas ningún módulo entero')).toBeVisible();
    } else {
      await expect(page.getByText(/Un módulo se da por sabido cuando aciertas al menos el 70 %/)).toBeVisible();
      const m = skippable[0];
      const correct = Math.round(m.accuracy * m.questions_seen);
      await expect(page.getByText(`${correct} de ${m.questions_seen}`, { exact: false }).first()).toBeVisible();
    }
  });

  test('a skipped module shows the rule and its count', async ({ page }) => {
    test.setTimeout(200_000);
    await registerUser(page, { username: uniqueUsername('e2e_place2_'), displayName: 'E2E Place Two' });
    await page.route('**/placement/result**', async (route) => {
      const real = await route.fetch();
      const body = await real.json();
      body.module_recommendations = [
        { module_id: 'mod0101', module_name_es: 'Módulo fijado', module_name_en: 'Pinned module', accuracy: 0.75, questions_seen: 8, can_skip: true },
      ];
      await route.fulfill({ response: real, json: body });
    });

    await openPlacement(page);
    await answerUntilResult(page);

    await expect(page.getByText('Puedes saltarte 1 módulo')).toBeVisible();
    await expect(page.getByText(/Un módulo se da por sabido cuando aciertas al menos el 70 % de 8 o más preguntas suyas/)).toBeVisible();
    await expect(page.getByText('Módulo fijado')).toBeVisible();
    await expect(page.getByText(/6 de 8 · 75%/)).toBeVisible();
  });
});
