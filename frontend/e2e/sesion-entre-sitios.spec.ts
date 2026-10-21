import { test, expect, type Request } from '@playwright/test';
import { suppressOnboarding, uniqueUsername } from './helpers';

/**
 * 43.1 (ADR-65 D1), criterio «e2e con cookies de terceros bloqueadas:
 * registro → Hoy». Corre en el proyecto `entre-sitios` de playwright.config:
 * el frontend en `localhost:5198` y la API en `127.0.0.1:8000`, dos sitios
 * distintos, con Chromium bloqueando las cookies de terceros. Es el caso de
 * Safari en iPhone con la API en `*.up.railway.app`.
 *
 * Sustituye como prueba del criterio a `sesion-sin-cookies.spec.ts`, que quita
 * `Set-Cookie` en el mismo origen: el verificador §7 del 2026-10-17 lo dio por
 * no reproducible porque no ejercita un sitio distinto.
 */
const API = 'http://127.0.0.1:8000';

test('API en otro sitio y cookies de terceros bloqueadas: registro → Hoy, y sigue tras recargar', async ({ page }) => {
  const sentCookie: string[] = [];
  const bearerOnMe: boolean[] = [];
  const pending: Promise<void>[] = [];
  const onRequest = (req: Request) => {
    if (!req.url().startsWith(API)) return;
    pending.push(
      req.allHeaders().then((h) => {
        if (h['cookie']) sentCookie.push(`${req.method()} ${req.url()}`);
        if (req.url().endsWith('/api/v1/auth/me') && req.method() === 'GET') {
          bearerOnMe.push(Boolean(h['authorization']));
        }
      }).catch(() => { /* la petición murió con la recarga */ }),
    );
  };
  // Las cabeceras se leen al terminar la petición. Con `request`, el CI del
  // 2026-10-21 (#321) se quedó 56 s en `Promise.all`: la traza muestra seis
  // peticiones a la API abortadas por `page.reload()` (status -1) y su
  // `allHeaders()` sin resolver en el headless shell del runner. En local
  // (Chromium y headless shell 1194) no se reproduce. Una petición abortada no
  // dispara `requestfinished`; las que llegan a la API sí, y son las que importan.
  page.on('requestfinished', onRequest);

  const username = uniqueUsername('e2e_xsite_');
  await page.goto('/auth');
  await page.getByLabel('Nombre').fill('Entre Sitios');
  await page.getByLabel('Usuario').fill(username);
  await page.getByLabel('Correo electrónico').fill(`${username}@example.com`);
  await page.getByLabel('Contraseña').fill('e2e-test-pass-123');
  await page.getByLabel('Confirmo que tengo 13 años o más').check();
  await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();

  // El onboarding solo aparece si `/auth/me` respondió con el usuario: hay
  // sesión sin cookie. Se salta igual que en el resto de specs (recarga incluida).
  await suppressOnboarding(page);

  const study = page.getByRole('button', { name: 'ESTUDIAR AHORA' });
  await expect(study).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('button', { name: 'Crear cuenta' })).toHaveCount(0);

  // Una recarga más (pull-to-refresh en el iPhone): sigue en Hoy, no en la portada.
  await page.reload();
  await expect(study).toBeVisible({ timeout: 15_000 });

  page.off('requestfinished', onRequest);
  const settled = await Promise.race([
    Promise.all(pending).then(() => true),
    new Promise<boolean>((r) => setTimeout(() => r(false), 10_000)),
  ]);
  expect(settled, 'las cabeceras de las peticiones a la API se leyeron').toBe(true);
  expect(await page.context().cookies(API)).toEqual([]);
  expect(sentCookie, 'ninguna petición a la API lleva cookie').toEqual([]);
  expect(bearerOnMe.length).toBeGreaterThan(0);
  expect(bearerOnMe.at(-1), 'la sesión viaja como Authorization').toBe(true);
});
