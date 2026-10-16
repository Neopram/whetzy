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
  test('se llega desde la ruta y, sin banco reservado, avisa de que aún no está disponible', async ({ page }) => {
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

    // Cerrado a propósito hasta que el banco reservado esté completo (9b470b9,
    // `MOCK_EXAM_RESERVED_POOL_ENABLED=False`): el alumno ve el aviso y el
    // botón deshabilitado, no un examen hecho con preguntas que ya practicó.
    // Cuando se encienda el flag, el recorrido completo (presentarlo, 65
    // preguntas, entregar y el resultado) vuelve: está en el historial de
    // este fichero (2026-10-16, antes de este cambio).
    await expect(section.getByRole('note')).toContainText('Todavía no está disponible');
    await expect(section.getByRole('button', { name: /PRESENTAR EXAMEN CERTIFICADOR/ })).toBeDisabled();
  });
});
