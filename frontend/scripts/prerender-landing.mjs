#!/usr/bin/env node
/**
 * Prerenders the marketing landing hero into a static `dist/landing/index.html`
 * at build time (task 11.11). The mobile LCP element is the hero <h1>, which is
 * plain React text that otherwise can't paint until the client JS bundle boots
 * (~3.1-3.2s on Lighthouse's mobile throttling profile, see
 * scripts/lighthouse-landing.mjs). Prerendering lets it paint with the initial
 * HTML response instead.
 *
 * The hero copy has exactly ONE source of truth: this script never touches the
 * copy itself. It compiles src/entry-server/landingEntry.tsx — a thin wrapper
 * around the real `LandingScreen` component — with Vite's own SSR build
 * (`vite build` with `build.ssr` set, i.e. the programmatic equivalent of
 * `vite build --ssr`), which is what correctly handles LandingScreen.tsx's
 * `import './LandingScreen.css'` (plain Node cannot import CSS; hand-rolling a
 * transpile step was explicitly rejected for task 11.11). It then runs the
 * compiled bundle in this Node process and calls `renderToStaticMarkup` on the
 * actual component.
 *
 * Language: renders the Spanish (default) copy, matching index.html's static
 * `<html lang="es">` defaults and the site's default `lng: 'es'` (see
 * src/i18n.ts). The `?lang=en` variant is unaffected as a route — Cloudflare
 * still serves this same static file for it (query strings don't change which
 * file matches), so an EN visitor briefly sees the ES hero text until
 * LandingScreen's client-side `resolveLandingLang` picks up `?lang=en` and
 * React re-renders in English. That flash is a real, deliberate trade-off:
 * pre-rendering a second static file per language would need a build-time
 * fan-out this task doesn't attempt, and the EN variant is not what
 * Lighthouse's LCP budget (run against plain /landing) is graded on.
 *
 * Must run after the normal client `vite build` (it edits dist/index.html's
 * output, not the source, and reads dist/.vite/manifest.json — see
 * `build.manifest: true` in vite.config.ts) — see the `build` script in
 * package.json.
 *
 * Critical CSS: LandingScreen.tsx is a lazily-routed page, so its styles
 * (`LandingScreen.css`, which sets the hero <h1>'s actual font-size via
 * `.lnd-hero__h1`) live in their own route-level, code-split CSS chunk. That
 * chunk is normally only linked into the page at runtime, when the JS router
 * dynamically imports the route. If we prerendered the hero markup but left
 * that stylesheet out of the static HTML, the browser would first paint the
 * <h1> at the *unstyled* browser-default size, then — once the JS bundle
 * loads and applies the real CSS — repaint it noticeably larger. Chrome's LCP
 * algorithm records the largest paint it sees, so that second, bigger paint
 * becomes the reported LCP instead of the first one, silently erasing the
 * whole benefit of prerendering. So this script also looks up that chunk's
 * hashed filename from the manifest (never hand-typed — it changes every
 * build) and links it in the static file's <head> too.
 */
import { existsSync } from 'node:fs';
import { mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { build } from 'vite';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SSR_OUT_DIR = resolve(ROOT, 'dist-ssr'); // already in .gitignore
const DIST_DIR = resolve(ROOT, 'dist');
const LANDING_ENTRY = resolve(ROOT, 'src/entry-server/landingEntry.tsx');
const LANDING_SRC_KEY = 'src/pages/LandingScreen.tsx'; // manifest key, i.e. the source module path
const ROOT_MARKER = '<div id="root"></div>';
const HEAD_CLOSE = '</head>';

async function buildSsrBundle() {
  await build({
    root: ROOT,
    logLevel: 'warn',
    build: {
      ssr: LANDING_ENTRY,
      outDir: SSR_OUT_DIR,
      emptyOutDir: true,
      minify: false,
      rollupOptions: {
        output: { entryFileNames: 'landing-entry.mjs' },
      },
    },
  });
  return resolve(SSR_OUT_DIR, 'landing-entry.mjs');
}

/** Reads the client build's manifest and returns the hashed CSS href(s) Vite
 * emitted for LandingScreen.tsx's own route-level chunk (not the shared/global
 * CSS, which is already linked in dist/index.html). */
async function readLandingCssHrefs() {
  const manifestPath = resolve(DIST_DIR, '.vite/manifest.json');
  if (!existsSync(manifestPath)) {
    throw new Error(
      '[prerender-landing] dist/.vite/manifest.json not found — is `build.manifest: true` still set in vite.config.ts?',
    );
  }
  const manifest = JSON.parse(await readFile(manifestPath, 'utf-8'));
  const entry = manifest[LANDING_SRC_KEY];
  
  let cssFiles = entry?.css ?? [];
  if (cssFiles.length === 0) {
    for (const key of Object.keys(manifest)) {
      if (key.includes('LandingScreen') && manifest[key].file?.endsWith('.css')) {
        cssFiles.push(manifest[key].file);
      }
    }
  }

  return cssFiles.map((href) => `/${href}`);
}

async function main() {
  const shellPath = resolve(DIST_DIR, 'index.html');
  if (!existsSync(shellPath)) {
    throw new Error(
      '[prerender-landing] dist/index.html not found — run the client `vite build` before this script',
    );
  }

  const [entryPath, cssHrefs] = await Promise.all([buildSsrBundle(), readLandingCssHrefs()]);
  if (cssHrefs.length === 0) {
    throw new Error('[prerender-landing] LandingScreen manifest entry has no CSS — expected LandingScreen.css to produce one');
  }

  const { renderLandingHtml } = await import(pathToFileURL(entryPath).href);
  const heroHtml = renderLandingHtml();

  if (!heroHtml.includes('lnd-hero__h1')) {
    throw new Error('[prerender-landing] rendered markup is missing the hero — aborting, not writing a broken file');
  }

  const shell = await readFile(shellPath, 'utf-8');
  if (!shell.includes(ROOT_MARKER)) {
    throw new Error(`[prerender-landing] expected to find ${JSON.stringify(ROOT_MARKER)} in dist/index.html`);
  }
  if (!shell.includes(HEAD_CLOSE)) {
    throw new Error(`[prerender-landing] expected to find ${JSON.stringify(HEAD_CLOSE)} in dist/index.html`);
  }

  // Render-blocking on purpose: this must apply before first paint, or the
  // hero repaints larger once the JS bundle loads the same stylesheet later
  // (see the file-level comment on why that would erase the LCP win).
  const cssLinks = cssHrefs.map((href) => `<link rel="stylesheet" crossorigin href="${href}">`).join('');

  // Same assets, same shell, every other route unaffected — only the root's
  // initial content changes and one extra (already-produced) stylesheet is
  // linked, so /landing gets a prepainted, correctly-styled hero while every
  // other route still gets an empty root exactly as today.
  const landingHtml = shell
    .replace(ROOT_MARKER, `<div id="root">${heroHtml}</div>`)
    .replace(HEAD_CLOSE, `${cssLinks}${HEAD_CLOSE}`);

  const landingDir = resolve(DIST_DIR, 'landing');
  await mkdir(landingDir, { recursive: true });
  await writeFile(resolve(landingDir, 'index.html'), landingHtml, 'utf-8');

  console.log(`[prerender-landing] wrote dist/landing/index.html (+ ${cssHrefs.join(', ')})`);
}

main()
  .catch((err) => {
    console.error(err);
    process.exitCode = 1;
  })
  .finally(() => rm(SSR_OUT_DIR, { recursive: true, force: true }));