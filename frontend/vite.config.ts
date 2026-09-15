import { createReadStream, existsSync, readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { dirname, extname, resolve } from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig, type Plugin } from 'vite'

/**
 * Makes `vite preview` resolve pretty URLs (`/landing` -> `dist/landing/index.html`)
 * the same way Cloudflare Pages does in production (task 11.11).
 *
 * Without this, `vite preview`'s own SPA fallback (`htmlFallbackMiddleware`)
 * only ever tries `<path>.html` for an extensionless URL with no trailing
 * slash — never `<path>/index.html` — so it silently rewrites `/landing` to
 * `/index.html` before Vite's static file server gets a chance to look for a
 * `landing/` directory. That masked the prerendered `dist/landing/index.html`
 * entirely: Lighthouse kept measuring the plain (un-prerendered) SPA shell
 * against `http://localhost:.../landing`, exactly the URL the acceptance
 * check for 11.11 uses. Cloudflare Pages' real static-asset resolution *does*
 * serve `<path>/index.html` for an exact-match directory before falling back
 * to `_redirects`, so this plugin exists purely to make local `vite preview`
 * measurements trustworthy, not to change any production behavior.
 */
function cloudflarePrettyUrlsPreviewPlugin(): Plugin {
  return {
    name: 'cloudflare-pretty-urls-preview',
    configurePreviewServer(server) {
      // Registering the middleware here (rather than via this hook's return
      // value) runs it before Vite's own sirv/SPA-fallback middlewares, which
      // is required: those already rewrite the URL to `/index.html` by the
      // time any returned ("post") hook would run.
      server.middlewares.use((req, res, next) => {
        if (req.method !== 'GET' && req.method !== 'HEAD' || !req.url) return next();
        const [pathname, search = ''] = req.url.split('?');
        if (pathname.endsWith('/') || pathname.includes('.')) return next();

        const distDir = resolve(server.config.root, server.config.build.outDir);
        if (existsSync(resolve(distDir, `.${pathname}`, 'index.html'))) {
          req.url = `${pathname}/index.html${search ? `?${search}` : ''}`;
        }
        next();
      });
    },
  };
}

/**
 * Serves Pyodide from our own origin instead of cdn.jsdelivr.net (task 12.9).
 *
 * The worker used to `importScripts('https://cdn.jsdelivr.net/pyodide/…')`, so
 * the first time a learner opened an exec question their IP went to a third
 * party with no consent — the same red line 5 breach as the Google font in
 * 12.7, just louder, since this one ships ~13 MB. It also made red line 4
 * (offline first) unachievable for exec questions by construction: a runtime
 * fetched from someone else's CDN cannot be there when the network is not.
 * Self-hosted, the service worker caches it like any other asset.
 *
 * The files come from the `pyodide` npm dependency (Apache-2.0), so the exact
 * bytes are pinned in package-lock.json — nothing is vendored into the repo by
 * hand, which is what kept this open. Only the runtime's own files are copied:
 * Pyodide's *packages* (numpy and friends, hundreds of MB) are not shipped,
 * because the sandbox never calls `loadPackage` — exec questions run stdlib
 * Python only, and `pyodide-lock.json` is included precisely so that a future
 * `loadPackage` fails loudly on a missing file instead of silently reaching out
 * to a CDN again.
 *
 * Dev gets a middleware (the files live outside the project root, so Vite's
 * static server will not serve them); build emits them as assets. Both hang
 * them off `/pyodide/`, which is the `indexURL` the worker passes.
 */
function pyodideSelfHostPlugin(): Plugin {
  const PYODIDE_DIR = dirname(createRequire(import.meta.url).resolve('pyodide/package.json'));
  // Exactly what loadPyodide() touches for a stdlib-only runtime. Listed rather
  // than globbed so that a new file appearing in the package is a deliberate
  // decision, not a silent 13 MB change in what we ship.
  const PYODIDE_BASE = '/pyodide/';
  const FILES = [
    'pyodide.js',
    'pyodide.asm.js',
    'pyodide.asm.wasm',
    'python_stdlib.zip',
    'pyodide-lock.json',
  ];

  /**
   * Pyodide's own bundle calls `setCdnUrl('https://cdn.jsdelivr.net/pyodide/v…/full/')`
   * during bootstrap. That is live configuration, not dead code: it is the base
   * URL `loadPackage` and micropip would fetch from. The sandbox never loads a
   * package today (exec questions are stdlib-only, and 2.2 blocks the imports
   * that would want one), but leaving a third-party CDN configured means the
   * first person who adds `loadPackage` reopens task 12.9 without noticing.
   *
   * So the default is repointed at our own origin. If anything ever does try to
   * fetch a package, it 404s here — loudly, on our domain — instead of quietly
   * fetching from someone else's. The replacement is anchored on the hostname
   * and asserts it matched exactly once, so a Pyodide upgrade that renames the
   * minified variable fails the build instead of silently shipping the CDN.
   */
  function repointCdn(source: string, name: string): string {
    const MARKER = 'https://cdn.jsdelivr.net/pyodide/';
    const at = source.indexOf(MARKER);
    if (at === -1) return source;
    if (source.indexOf(MARKER, at + 1) !== -1) {
      throw new Error(
        `[pyodide-self-host] expected at most one CDN reference in ${name}, found several — ` +
          'check what upstream changed before shipping this.',
      );
    }
    // The URL is a template literal; swap the whole literal, backticks included.
    const open = source.lastIndexOf('`', at);
    const close = source.indexOf('`', at);
    if (open === -1 || close === -1 || open >= at) {
      throw new Error(
        `[pyodide-self-host] the CDN reference in ${name} is no longer a template literal — ` +
          'the rewrite would corrupt the file, so the build stops here instead.',
      );
    }
    return `${source.slice(0, open)}"${PYODIDE_BASE}"${source.slice(close + 1)}`;
  }

  return {
    name: 'pyodide-self-host',
    configureServer(server) {
      server.middlewares.use('/pyodide', (req, res, next) => {
        const name = (req.url ?? '').split('?')[0].replace(/^\//, '');
        if (!FILES.includes(name)) return next();
        res.setHeader('Content-Type', MIME[extname(name)] ?? 'application/octet-stream');
        if (name.endsWith('.js')) {
          // Same rewrite as the build, so dev and prod agree about where a
          // package fetch would go — a difference there is how this kind of
          // thing hides until production.
          res.end(repointCdn(readFileSync(resolve(PYODIDE_DIR, name), 'utf-8'), name));
          return;
        }
        createReadStream(resolve(PYODIDE_DIR, name)).pipe(res);
      });
    },
    generateBundle() {
      for (const name of FILES) {
        const path = resolve(PYODIDE_DIR, name);
        if (!existsSync(path)) {
          this.error(
            `[pyodide-self-host] ${name} is missing from the pyodide package at ${PYODIDE_DIR}. ` +
              'Failing the build on purpose: shipping without it would send the worker back to ' +
              'the CDN at runtime, quietly reopening task 12.9.',
          );
        }
        const raw = readFileSync(path);
        const source = name.endsWith('.js') ? repointCdn(raw.toString('utf-8'), name) : raw;
        this.emitFile({ type: 'asset', fileName: `pyodide/${name}`, source });
      }
    },
  };
}

const MIME: Record<string, string> = {
  '.js': 'text/javascript',
  '.wasm': 'application/wasm',
  '.zip': 'application/zip',
  '.json': 'application/json',
};

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), cloudflarePrettyUrlsPreviewPlugin(), pyodideSelfHostPlugin()],
  build: {
    // Read by scripts/prerender-landing.mjs to find the exact hashed CSS
    // chunk LandingScreen.tsx needs (task 11.11) — its styles (incl. the
    // hero <h1>'s font-size) live in a route-level code-split chunk that
    // isn't otherwise linked from the static HTML shell, only pulled in at
    // runtime when the lazy route import resolves.
    manifest: true,
    // Monaco Editor lazy-chunks are intentionally large (~4 MB unminified /
    // ~1 MB gz). They are code-split and only loaded when a fix_bug or
    // fill_blank_exec question is first shown. The initial bundle stays ≤300 KB gz.
    chunkSizeWarningLimit: 5000,
  },
  server: {
    // Cross-Origin isolation required by SharedArrayBuffer (pyodide interrupt).
    // COEP credentialless allows CDN resources without opt-in CORP headers.
    headers: {
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Embedder-Policy': 'credentialless',
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
