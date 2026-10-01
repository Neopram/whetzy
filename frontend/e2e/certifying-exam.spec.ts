import { test, expect } from '@playwright/test';
import { registerUser, uniqueUsername } from './helpers';

/**
 * Examen certificador (38.7, ADR-49), de punta a punta contra un servidor real:
 * se llega desde la ruta de certificación, anuncia el pago único, usa el
 * blueprint oficial (65 preguntas) y el resultado declara aprobado o no, con el
 * aviso de que no sustituye al examen oficial del proveedor. Con
 * `CERTIFICATION_PAYWALL` apagado (hasta H.19) cualquiera puede presentarse.
 */
test.describe('certifying exam', () => {
  test('se presenta desde la ruta y declara el resultado', async ({ page }) => {
    const username = uniqueUsername('e2e_cert_');
    await registerUser(page, { username, displayName: 'E2E Cert' });

    await page.getByRole('button', { name: 'Rutas' }).click();
    // Rutas abre la ruta en curso; el catálogo está detrás de «Todas las rutas».
    await page.getByRole('button', { name: /Todas las rutas/ }).click();
    await page.getByRole('button', { name: /AWS Certified Cloud Practitioner/ }).click();
    await page.getByRole('button', { name: /Simulacro de examen|Mock exam/ }).click();

    const section = page.getByTestId('certifying');
    await expect(section).toBeVisible({ timeout: 10_000 });
    await expect(section.getByText(/Pago único de 39,99 \$/)).toBeVisible();
    await page.screenshot({ path: 'test-results/certifying-intro.png', fullPage: true });

    await section.getByRole('button', { name: /PRESENTAR EXAMEN CERTIFICADOR/ }).click();
    await expect(page.getByRole('radiogroup')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText(/de 65/)).toBeVisible();

    for (let i = 0; i < 64; i++) {
      await page.getByRole('button', { name: /^Siguiente$/ }).click();
    }
    await page.getByRole('button', { name: /^ENTREGAR$/ }).click();

    await expect(page.getByText('Resultado del examen certificador')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText(/No aprobado/)).toBeVisible();
    await expect(page.getByText(/no sustituye al examen oficial del proveedor/)).toBeVisible();
    await expect(page.getByRole('button', { name: /VOLVER A PRESENTARLO/ })).toBeVisible();
    await page.screenshot({ path: 'test-results/certifying-result.png', fullPage: true });
  });
});
