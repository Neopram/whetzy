/**
 * check-e2e-target.mjs — guardia de H.15.
 *
 * La suite e2e local registra un usuario nuevo por test (`e2e/helpers.ts`).
 * El navegador no habla con el backend directamente: habla con el dev server de
 * vite, que reenvia `/api` a donde diga `server.proxy` en `vite.config.ts`. Si
 * ese target apunta a la API de produccion —como quedo en el arbol de trabajo
 * de la sesion aq— entonces `npm run test:e2e` **escribe en la DB de
 * produccion**, y nada en la salida de Playwright lo delata: los tests pasan
 * igual, solo que los usuarios acaban en el sitio equivocado.
 *
 * Dos lineas mal puestas y un fallo silencioso e irreversible. Esto corre en
 * `pretest:e2e`, antes de que Playwright arranque nada.
 *
 * `E2E_BASE_URL` (que usa `test:e2e:prod`) desactiva el `webServer` local, asi
 * que ahi el proxy de vite no interviene y la comprobacion no aplica.
 */
import { loadConfigFromFile } from 'vite';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '..');

const LOOPBACK = /^https?:\/\/(localhost|127\.0\.0\.1|\[::1\]|0\.0\.0\.0)(:\d+)?$/;

if (process.env.E2E_BASE_URL) {
  console.log(
    `[e2e-target] E2E_BASE_URL=${process.env.E2E_BASE_URL} — sin webServer local, ` +
      'el proxy de vite no interviene. Nada que comprobar.',
  );
  process.exit(0);
}

const loaded = await loadConfigFromFile(
  { command: 'serve', mode: 'development' },
  resolve(ROOT, 'vite.config.ts'),
  ROOT,
);

if (!loaded?.config) {
  console.error('[e2e-target] FAIL — no se pudo cargar vite.config.ts');
  process.exit(1);
}

/** Todos los targets de proxy declarados, en `server` y en `preview`. */
const targets = [];
for (const where of ['server', 'preview']) {
  const proxy = loaded.config[where]?.proxy ?? {};
  for (const [route, entry] of Object.entries(proxy)) {
    const target = typeof entry === 'string' ? entry : entry?.target;
    if (typeof target === 'string') targets.push({ where, route, target });
  }
}

if (targets.length === 0) {
  console.log('[e2e-target] no hay proxies declarados en vite.config.ts');
  process.exit(0);
}

const offenders = targets.filter(t => !LOOPBACK.test(t.target.replace(/\/$/, '')));

for (const t of targets) {
  const ok = !offenders.includes(t);
  console.log(`  ${ok ? 'OK  ' : 'FAIL'} ${t.where}.proxy['${t.route}'] -> ${t.target}`);
}

if (offenders.length > 0) {
  console.error(
    `\n[e2e-target] FAIL — ${offenders.length} proxy(s) apuntan fuera de localhost.\n` +
      'La suite e2e crea usuarios reales en cada test; con esto puesto los crearia\n' +
      'en el destino de arriba. Devuelve el target a http://127.0.0.1:8000 antes de\n' +
      'correr e2e, o exporta E2E_BASE_URL si de verdad quieres correr contra un\n' +
      'despliegue (test:e2e:prod).',
  );
  process.exit(1);
}

console.log('\n[e2e-target] PASS — todo el trafico de e2e se queda en localhost');
