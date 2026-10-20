import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { formatViolations } from './helpers';

/**
 * La verificación pública del certificado (y las páginas legales) en el idioma
 * del visitante sin cuenta. Antes salía siempre en español: se aplicaba el
 * `user.language` por defecto del store. La respuesta de verificación se
 * intercepta porque en local no hay un examen final aprobado con código válido.
 */
const SHOTS = '../docs/ui-snapshots/certificado-idioma';
const CERT = {
  code: 'a'.repeat(32), username: 'ada', track_id: 'track01', track_name_es: 'Python Básico',
  track_name_en: 'Python Basics', score_pct: 86.5, questions: 50, issued_at: '2026-10-20T10:00:00Z',
  revoked: false, is_certification: false,
};

async function axe0(page: Page) {
  const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
  expect(r.violations, formatViolations(r.violations)).toHaveLength(0);
}

for (const [locale, lang, title, track] of [
  ['en-US', 'en', 'Certificate check', 'Python Basics'],
  ['es-ES', 'es', 'Comprobación de certificado', 'Python Básico'],
] as const) {
  test.describe(`visitante sin cuenta (${locale})`, () => {
    test.use({ locale });

    test(`certificado público en ${lang}`, async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 900 });
      await page.route('**/exams/certificates/*', (route) =>
        route.request().url().endsWith('/qr') ? route.fulfill({ status: 404 }) : route.fulfill({ json: CERT }));
      await page.goto(`/certificate/${CERT.code}`);
      await expect(page.getByRole('heading', { level: 1 })).toHaveText(title);
      await expect(page.getByText(track)).toBeVisible();
      await expect(page.locator('html')).toHaveAttribute('lang', lang);
      await page.screenshot({ path: `${SHOTS}/certificado-${lang}-390.png` });
      await axe0(page);
    });
  });
}

test.describe('visitante sin cuenta, navegador en inglés', () => {
  test.use({ locale: 'en-US' });
  test('la política de privacidad también sale en inglés', async ({ page }) => {
    await page.goto('/privacy');
    await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  });
});

test('un enlace con ?lang=es manda sobre el navegador', async ({ browser }) => {
  const ctx = await browser.newContext({ locale: 'en-US' });
  const page = await ctx.newPage();
  await page.route('**/exams/certificates/*', (route) => route.fulfill({ json: CERT }));
  await page.goto(`/certificate/${CERT.code}?lang=es`);
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Comprobación de certificado');
  await ctx.close();
});
