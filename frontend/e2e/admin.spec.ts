import { test, expect, type Route } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { formatViolations, registerUser, uniqueUsername } from './helpers';

/**
 * 44.3 (docs/PLAN_BACKOFFICE.md): pestañas «Usuarios» y «Registro».
 *
 * El dueño necesita rol `owner` y 2FA activa, que un e2e no puede darse a sí
 * mismo sin tocar la base: por eso el primer test simula las rutas
 * `/admin/users*` y `/admin/action-log` y comprueba la pantalla de verdad (lo
 * que se manda y lo que se ve). Las reglas del servidor —solo el dueño, 2FA,
 * motivo, 90 días, registro— las cubren los tests de integración contra
 * Postgres de 44.1 y 44.2. El segundo test va contra el backend real.
 */

const ANA = {
  id: '11111111-2222-3333-4444-555555555555',
  account: {
    username: 'anabanana', display_name: 'Ana', email: 'federica@gmail.com', email_verified: false,
    language: 'es', status: 'active', role: 'user', created_at: '2026-10-01T10:00:00Z', last_active: null,
  },
  plan: {
    subscription_tier: null, subscription_status: null, subscription_expires_at: null, subscription_provider: null,
    paddle_subscription_id: null, granted_tier: null, granted_tier_expires_at: null, certification_purchases: [],
  },
  progress: { target_track_id: null, target_certification_id: null, skills_practiced: 3, answers: 42, level: 2, current_streak: 1 },
  security: { recent_events: [] },
  gdpr: { pending: [] },
};

for (const width of [390, 1280]) {
  test(`el dueño busca, abre una ficha y regala un plan (${width} px)`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await registerUser(page, { username: uniqueUsername('e2e_adm_'), displayName: 'Dueño' });

    const sent: { url: string; body: unknown }[] = [];
    const json = (route: Route, body: unknown) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
    await page.route('**/api/v1/admin/users?**', (r) => json(r, {
      items: [{ id: ANA.id, username: 'anabanana', email_masked: 'fe***@gmail.com', created_at: ANA.account.created_at, status: 'active' }],
      page: 1, page_size: 20, total: 1,
    }));
    await page.route(`**/api/v1/admin/users/${ANA.id}`, (r) => json(r, ANA));
    await page.route(`**/api/v1/admin/users/${ANA.id}/actions/*`, (r) => {
      sent.push({ url: r.request().url(), body: r.request().postDataJSON() });
      return json(r, { ok: true, action: 'grant_plan', data: {} });
    });

    await page.goto('/admin');
    await page.getByRole('button', { name: 'Usuarios', exact: true }).click();
    await page.getByLabel('Buscar por email, usuario o id').fill('fede');
    await page.getByRole('button', { name: 'Buscar', exact: true }).click();
    await expect(page.getByText('fe***@gmail.com')).toBeVisible();
    await page.getByRole('button', { name: /anabanana/ }).click();
    await expect(page.getByRole('heading', { name: 'Ficha de anabanana' })).toBeVisible();
    await expect(page.getByText('federica@gmail.com')).toBeVisible();

    const axeFicha = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
    expect(axeFicha.violations, formatViolations(axeFicha.violations)).toHaveLength(0);
    // Sin desbordamiento horizontal a 390 px.
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({ path: `../docs/ui-snapshots/44.3/ficha-es-${width}.png`, fullPage: true });

    await page.getByRole('button', { name: 'Regalar plan' }).click();
    const confirmar = page.getByRole('button', { name: 'Confirmar' });
    await expect(confirmar).toBeDisabled();
    await page.getByLabel('Días (1–90)').fill('45');
    await page.getByLabel('Motivo (obligatorio)').fill('probador del piloto');
    await page.screenshot({ path: `../docs/ui-snapshots/44.3/regalar-plan-es-${width}.png` });
    await confirmar.click();
    await expect(page.getByRole('status').filter({ hasText: 'Hecho: Regalar plan.' })).toBeVisible();
    expect(sent).toEqual([{ url: expect.stringContaining('/actions/grant_plan'), body: { reason: 'probador del piloto', tier: 'pro', days: 45 } }]);
  });
}

test('un alumno no ve «Admin» en su perfil y el backend le niega la búsqueda', async ({ page }) => {
  await registerUser(page, { username: uniqueUsername('e2e_alu_'), displayName: 'Alumno' });
  await page.getByRole('button', { name: 'Yo', exact: true }).click();
  await expect(page.getByRole('button', { name: /Panel de administración|Admin/ })).toHaveCount(0);

  // Aunque escriba la URL a mano, el servidor dice que no (sin simular nada).
  await page.goto('/admin');
  await page.getByRole('button', { name: 'Usuarios', exact: true }).click();
  await page.getByLabel('Buscar por email, usuario o id').fill('fede');
  const respuesta = page.waitForResponse((r) => r.url().includes('/api/v1/admin/users?'));
  await page.getByRole('button', { name: 'Buscar', exact: true }).click();
  expect((await respuesta).status()).toBe(403);
  await expect(page.getByRole('alert')).toBeVisible();
});
