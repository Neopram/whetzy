#!/usr/bin/env node
/**
 * Dev-only bundle check (34.3).
 *
 * `/_ui` (src/pages/UiKitScreen.tsx) exists to review every base component
 * in its variants without hunting through the whole app for where each one
 * is used. It is gated behind `import.meta.env.DEV` in App.tsx, which Vite
 * evaluates at build time — the intent is that `npm run build` produces a
 * bundle with no reference to it at all, dead-code-eliminated, not a page
 * that is merely hidden behind a runtime check a curious visitor could
 * defeat by hitting the URL in production.
 *
 * This is the thing that could quietly break: someone imports UiKitScreen
 * unconditionally somewhere else (a shared layout, a debug menu wired to a
 * keyboard shortcut) and the whole showcase — every component's markup and
 * styles — ships to every visitor. A source-level check can't catch that;
 * only the actual production bundle can.
 *
 * Run after a build:  node scripts/check-dev-only.mjs
 */
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const ASSETS_DIR = resolve(process.cwd(), 'dist', 'assets');
const NEEDLE = 'UiKitScreen';

if (!existsSync(ASSETS_DIR)) {
  console.error(
    '\n[dev-only] FAIL — dist/assets does not exist.\n' +
      '  Build first: npm run build\n',
  );
  process.exit(1);
}

const jsFiles = readdirSync(ASSETS_DIR).filter((f) => f.endsWith('.js'));
console.log(`\n[dev-only] checking ${jsFiles.length} bundle file(s) for ${JSON.stringify(NEEDLE)}\n`);

const offenders = jsFiles.filter((f) => readFileSync(resolve(ASSETS_DIR, f), 'utf-8').includes(NEEDLE));

if (offenders.length > 0) {
  console.error(
    `  FAIL  ${JSON.stringify(NEEDLE)} found in the production bundle: ${offenders.join(', ')}\n` +
      '        The /_ui showcase (34.3) is meant to be dead-code-eliminated by\n' +
      '        import.meta.env.DEV, not merely hidden behind a runtime check.\n',
  );
  process.exit(1);
}

console.log(`[dev-only] PASS — ${NEEDLE} is absent from the production bundle\n`);
