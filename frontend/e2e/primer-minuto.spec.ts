import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { formatViolations, markLessonSeen, uniqueUsername } from './helpers';

/**
 * 46.3 (docs/PLAN_UI_AVANZADA.md §2, ola 1): un usuario recién registrado ve la
 * prueba de nivel o «Tu mayor palanca» sin hacer scroll a 390 px, con axe 0 en
 * Onboarding y Hoy.
 *
 * Elige «Certificarme», Seguridad y redes (track13) e ISC2 CC (track40): el
 * onboarding deja activa la ruta de aprendizaje y guarda la certificación
 * aparte, así que la palanca de Hoy sale de esa certificación (46.3c). Sin
 * ninguna respuesta en ella, lo primero sigue siendo la siguiente lección:
 * practicar entonces daría «Empieza por la lección».
 */
test.use({ viewport: { width: 390, height: 844 } });

async function expectNoAxeViolations(page: Page, where: string) {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(results.violations, `${where}\n${formatViolations(results.violations)}`).toHaveLength(0);
}

test('primer minuto a 390 px: prueba de nivel en el onboarding y mayor palanca en Hoy, sin scroll', async ({ page, baseURL }) => {
  const username = uniqueUsername('e2e_pm_');
  await page.goto('/auth');
  await page.getByLabel('Nombre').fill('Primer Minuto');
  await page.getByLabel('Usuario').fill(username);
  await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
  await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
  await page.getByLabel('Confirmo que tengo 16 años o más').check();
  await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();

  const onboarding = page.getByTestId('onboarding');
  await expect(onboarding).toBeVisible({ timeout: 15_000 });
  await onboarding.getByRole('button', { name: 'Certificarme', exact: true }).click();
  await onboarding.getByTestId('track-track13').click();
  await onboarding.getByTestId('cert-track40').click();
  await onboarding.getByRole('button', { name: 'Empiezo de cero' }).click();

  // La prueba de nivel se presenta con lo que mide y cuánto dura, a la vista.
  await expect(onboarding.getByRole('heading', { name: '¿Hacemos la prueba de nivel?' })).toBeInViewport();
  await expect(onboarding.getByText(/20 preguntas de .*unos 10 minutos/)).toBeInViewport();
  await expect(onboarding.getByRole('button', { name: 'Hacer la prueba' })).toBeInViewport();
  await expectNoAxeViolations(page, 'Onboarding — prueba de nivel');

  await onboarding.getByRole('button', { name: 'Empiezo de cero' }).click();
  await expect(onboarding).toHaveCount(0);

  // Recién llegado, sin respuestas: lo primero es la siguiente lección.
  await expect(page.getByTestId('home-next')).toBeInViewport({ timeout: 15_000 });
  const lever = page.getByRole('region', { name: 'Tu mayor palanca' });
  await expect(lever).toHaveCount(0);

  // Una respuesta en ISC2 CC (lección vista + «No lo sé» por la API, que vale
  // para cualquier tipo de pregunta) y Hoy ya tiene palanca que enseñar.
  // Un POST con cookie de sesión tiene que traer un Origin permitido (CSRF, S.13).
  const headers = { Origin: new URL(baseURL!).origin };
  await markLessonSeen(page, 'sk400101');
  const start = await page.request.post('/api/v1/quiz/start', { headers, data: { track_id: 'track40', mode: 'study' } });
  expect(start.ok(), await start.text()).toBeTruthy();
  const session = await start.json();
  expect(session.question, JSON.stringify(session.selection_reason)).not.toBeNull();
  const answer = await page.request.post('/api/v1/quiz/answer', {
    headers,
    data: { session_id: session.session_id, question_id: session.question.id, declared_unknown: true, response_time_ms: 1500 },
  });
  expect(answer.ok(), await answer.text()).toBeTruthy();
  await page.reload();

  // Hoy: la palanca de la certificación elegida es lo primero tras el saludo.
  await expect(lever).toBeVisible({ timeout: 15_000 });
  await expect(lever).toContainText('ISC2 CC');
  await expect(lever.getByRole('button', { name: 'Practicar esta certificación' })).toBeInViewport();
  await expectNoAxeViolations(page, 'Hoy — mayor palanca');
});
