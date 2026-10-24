import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { formatViolations, registerUser, uniqueUsername, waitForAnimations } from './helpers';

/**
 * 34.8: axe en cada ruta. `accessibility.spec.ts` cubre Auth, landing, Hoy,
 * Perfil, Stats, Liga, Rutas, Quiz y Privacidad; aquí, todas las demás, para
 * que ninguna pantalla quede sin medir (el 2026-10-01 dos interruptores sin
 * nombre pasaron meses sin que nadie lo viera, porque nadie medía su pantalla).
 *
 * Se mide la pantalla asentada: sin la Home que se va, sin BootSplash y sin
 * esqueletos visibles. Un usuario recién registrado es justo lo que ve casi todo
 * el mundo la primera vez: estados vacíos, introducciones, sin datos.
 */
type StoreW = { __whetzyStore: { setState: (s: object) => void; getState: () => { user: object } } };
const TAGS = ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'];

async function settled(page: Page, { busy = true } = {}) {
  await expect(page.locator('[data-boot-splash]')).toHaveCount(0, { timeout: 15_000 });
  if (busy) await expect(page.locator('[aria-busy="true"]:visible')).toHaveCount(0, { timeout: 20_000 });
  await waitForAnimations(page);
}

async function audit(page: Page, label: string) {
  const r = await new AxeBuilder({ page }).withTags(TAGS).analyze();
  // soft: un fallo en una pantalla no tapa los de las siguientes.
  expect.soft(r.violations, `${label}\n${formatViolations(r.violations)}`).toHaveLength(0);
}

const PUBLIC = [
  // accessibility.spec las mide solo en oscuro; aquí, los dos temas.
  '/landing',
  '/privacy',
  '/terms',
  '/refund',
  '/evidence',
  '/status',
  '/es/carrera',
  '/en/career',
  '/es/empresas',
  '/en/enterprise',
  '/blog',
  '/reset-password?token=e2e-no-valido',
  '/checkout?plan=pro',
  '/delete-account',
  '/_ui',
  // Verificador adversario de 34.9 (2026-10-24): estas faltaban. Con un código
  // que no existe se mide la página de «no encontrado», que es la que ve quien
  // llega con un enlace roto.
  '/login',
  '/register',
  '/verify-email?token=e2e-no-valido',
  '/verify/E2E-NO-VALIDO',
  '/certificate/E2E-NO-VALIDO',
  '/report/e2e-no-valido',
  '/u/e2e-no-existe',
  '/r/E2E-NO-VALIDO',
];

// El oscuro es el de por defecto; el claro se mantiene (decisión del dueño del
// 2026-10-15) y nadie lo medía. theme.ts lo lee de localStorage al arrancar.
async function useTheme(page: Page, theme: 'dark' | 'light') {
  await page.addInitScript((th) => {
    try { localStorage.setItem('whetzy_theme', th); } catch { /* sin almacenamiento */ }
  }, theme);
}

for (const theme of ['dark', 'light'] as const) for (const path of PUBLIC) {
  test(`axe sin sesión: ${path} (${theme})`, async ({ page }) => {
    await useTheme(page, theme);
    await page.goto(path);
    // Sin sesión, /checkout manda a /auth?next=…: se mide donde acaba, no el
    // fundido de la redirección (17 falsos contrastes en claro, 2026-10-24).
    if (path.startsWith('/checkout')) await page.waitForURL(/\/auth\?next=/, { timeout: 15_000 });
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 15_000 });
    // /_ui enseña a propósito esqueletos y botones cargando: siempre ocupado.
    await settled(page, { busy: path !== '/_ui' });
    await audit(page, `${path} (${theme})`);
  });
}

// Pantallas internas sin ruta propia: se entra por el store, como hace la app.
const IN_APP: { screen: string; state?: object }[] = [
  // Las de la barra inferior: accessibility.spec las mide solo en es/oscuro.
  { screen: 'tracks' },
  { screen: 'stats' },
  { screen: 'league' },
  { screen: 'profile' },
  { screen: 'duels' },
  { screen: 'wallet' },
  { screen: 'marketplace' },
  { screen: 'playground' },
  { screen: 'projects' },
  { screen: 'instructor' },
  { screen: 'readiness', state: { readinessTrackId: 'track09' } },
  { screen: 'lesson', state: { lessonSkillId: 'sk010101' } },
  { screen: 'placement', state: { placementTrackId: 'track01' } },
  { screen: 'mockexam', state: { mockExamTrackId: 'track09' } },
  { screen: 'trackexam', state: { trackExamTargetId: 'track01', trackExamKind: 'track_final' } },
];

const RUNS = [
  { lang: 'es', theme: 'dark' },
  { lang: 'en', theme: 'dark' },
  { lang: 'es', theme: 'light' },
  { lang: 'en', theme: 'light' },
] as const;

for (const { lang, theme } of RUNS) {
  test(`axe con sesión, pantallas internas (${lang}, ${theme})`, async ({ page }) => {
    test.setTimeout(240_000);
    await useTheme(page, theme);
    await registerUser(page, { username: uniqueUsername(`e2e_axe_${lang}_`), displayName: 'Axe Rutas' });
    await page.evaluate((l) => {
      const w = window as unknown as StoreW;
      w.__whetzyStore.setState({ user: { ...w.__whetzyStore.getState().user, language: l } });
    }, lang);
    await settled(page);
    await audit(page, `home (${lang}, ${theme})`);

    for (const { screen, state } of IN_APP) {
      await page.evaluate(([s, extra]) => {
        (window as unknown as StoreW).__whetzyStore.setState({ ...(extra as object), currentScreen: s });
      }, [screen, state ?? {}] as const);
      await expect(page.getByTestId('home-active-track')).toHaveCount(0);
      await settled(page);
      // Sin su parámetro, Preparación y Examen de ruta rebotan a Rutas (App.tsx)
      // y se mediría otra pantalla; Prueba de nivel rebota a Hoy (arriba).
      if (screen !== 'tracks') {
        await expect(page.getByRole('heading', { level: 1, name: /^(Rutas de aprendizaje|Learning paths)$/ })).toHaveCount(0);
      }
      await audit(page, `${screen} (${lang}, ${theme})`);
      await page.evaluate(() => (window as unknown as StoreW).__whetzyStore.setState({ currentScreen: 'home' }));
      await expect(page.getByTestId('home-active-track')).toBeVisible({ timeout: 15_000 });
    }

    // /admin con un usuario que no es el dueño: la pantalla de acceso denegado.
    await page.goto('/admin');
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 15_000 });
    await settled(page);
    await audit(page, `/admin sin permiso (${lang}, ${theme})`);
  });
}
