import { spawnSync } from 'node:child_process'
import { createReadStream, existsSync, readFileSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { dirname, extname, resolve } from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv, type Plugin } from 'vite'
import { injectBuildVersion } from './scripts/swVersion.js'

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

/**
 * Monaco's `editor.main` entry pulls in four language *features* — css, html,
 * json and typescript — and each ships a language-service web worker. Together
 * they are ~2 MB gzip of the build, and not one byte of it can ever run:
 * `src/lib/monacoSetup.ts` points MonacoEnvironment.getWorkerUrl at a single
 * self-hosted stub for every label, so these workers are never instantiated.
 * Exec questions need Python and SQL syntax highlighting, which Monaco tokenizes
 * on the main thread.
 *
 * So they are resolved to an empty module instead of being built and uploaded.
 * The editor keeps every feature a learner touches — find, folding, bracket
 * matching, multi-cursor — because those are editor contribs, not these.
 *
 * Each id is asserted to have matched at least once at build end: a Monaco
 * upgrade that moves these paths fails the build rather than silently putting
 * the 2 MB back.
 */
function monacoDropUnusedLanguageServices(): Plugin {
  const DROPPED = ['css', 'html', 'json', 'typescript'];
  const hits = new Map<string, number>(DROPPED.map((n) => [n, 0]));
  const EMPTY = '\0monaco-dropped-language-service';
  // `npm run build` runs twice: the client build, then the SSR build that
  // prerenders the landing hero (11.11). Only the client build contains Monaco,
  // so only it can be held to this assertion.
  let isSsrBuild = false;
  let cdnRepoints = 0;

  return {
    name: 'monaco-drop-unused-language-services',
    apply: 'build',
    enforce: 'pre',
    configResolved(config) {
      isSsrBuild = Boolean(config.build.ssr);
    },
    resolveId(source) {
      const m = source.match(/languages\/features\/([a-z]+)\/register(?:\.js)?$/);
      if (m && hits.has(m[1])) {
        hits.set(m[1], (hits.get(m[1]) ?? 0) + 1);
        return EMPTY;
      }
      return null;
    },
    load(id) {
      return id === EMPTY ? 'export {};' : null;
    },
    /**
     * @monaco-editor/loader ships a default config pointing `paths.vs` at
     * jsDelivr. It is dead here — monacoSetup.ts calls `loader.config({ monaco })`
     * with the bundled instance, and the loader's init() resolves from
     * `state.monaco` and returns before it ever reaches the script injection that
     * would read `paths.vs`. Verified in the loader source, not assumed.
     *
     * Dead or not, it is a third-party URL sitting in what we upload, and the one
     * edit that would revive it (dropping that loader.config call) gives no
     * warning. So it is repointed at our own origin, the way 12.9 repointed
     * Pyodide's: if anything ever does try to load Monaco this way it 404s here,
     * loudly, instead of quietly fetching from someone else's CDN. That also
     * keeps KNOWN_EXCEPTIONS empty, which is the point of that list.
     */
    transform(code, id) {
      if (!id.includes('@monaco-editor') || !id.includes('config')) return null;
      const MARKER = 'https://cdn.jsdelivr.net/npm/monaco-editor@';
      if (!code.includes(MARKER)) return null;
      const replaced = code.replace(
        /https:\/\/cdn\.jsdelivr\.net\/npm\/monaco-editor@[^'"]*/g,
        '/monaco-unused-cdn-path',
      );
      cdnRepoints += 1;
      return { code: replaced, map: null };
    },
    buildEnd() {
      if (isSsrBuild) return;
      if (cdnRepoints === 0) {
        this.error(
          `the @monaco-editor/loader jsDelivr default was not found, so nothing was ` +
            `repointed. Either the package changed or it is no longer in the graph — ` +
            `check which before removing this, because silently shipping a third-party ` +
            `CDN URL is exactly what this prevents.`,
        );
      }
      const missed = DROPPED.filter((n) => (hits.get(n) ?? 0) === 0);
      if (missed.length > 0) {
        this.error(
          `monaco-drop-unused-language-services matched nothing for: ${missed.join(', ')}. ` +
            `Monaco's layout changed, so those language-service workers are back in the ` +
            `bundle. Update the matcher or drop them a different way — do not delete this ` +
            `check.`,
        );
      }
    },
  };
}

/** Un build de produccion sin `VITE_API_URL` es un build que no habla con su
 *  backend, y no se nota: `services/api.ts` cae a la ruta relativa '/api/v1',
 *  Cloudflare la resuelve con el index.html y un 200, y la aplicacion se queda
 *  muda sin un error. Paso, y estuvo asi hasta que alguien probo a registrarse.
 *  Mejor que el build muera aqui. */
function readApiUrlFromEnvFile(): string | undefined {
  const file = resolve(process.cwd(), '.env.production');
  if (!existsSync(file)) return undefined;
  const m = readFileSync(file, 'utf-8').match(/^\s*VITE_API_URL\s*=\s*(.+?)\s*$/m);
  return m?.[1];
}

function requireApiUrl(): Plugin {
  return {
    name: 'require-api-url',
    apply: 'build',
    config(_config, env) {
      if (env.mode !== 'production') return;
      // La fuente de verdad es frontend/.env.production (commiteado). El
      // 2026-09-24 el panel de Cloudflare Pages tenia VITE_API_URL=https://whetzy.com
      // en Produccion: pisaba al fichero y ese era el origen del login en 405.
      // Una variable de entorno distinta se ignora con un aviso en el log del
      // build. Vite carga el entorno despues de los hooks `config`, asi que
      // fijar process.env aqui es lo que acaba en import.meta.env.
      const fromFile = readApiUrlFromEnvFile();
      const fromEnv = process.env.VITE_API_URL;
      if (fromFile && fromEnv && fromEnv !== fromFile) {
        console.warn(
          `[require-api-url] Ignorando VITE_API_URL=${JSON.stringify(fromEnv)} del entorno ` +
            `(p. ej. el panel de Cloudflare); se usa la de frontend/.env.production: ${fromFile}`,
        );
      }
      if (fromFile) process.env.VITE_API_URL = fromFile;
      const url = loadEnv(env.mode, process.cwd(), '').VITE_API_URL;
      if (!url) {
        throw new Error(
          'VITE_API_URL no esta definida. Sin ella el bundle apunta a /api/v1 del ' +
            'propio dominio y la aplicacion se queda sin backend en silencio. ' +
            'Esta en frontend/.env.production; si lo has borrado, vuelve a ponerlo.'
        );
      }
      if (!/^https?:\/\//.test(url)) {
        throw new Error(
          `VITE_API_URL tiene que ser un origen absoluto, y es ${JSON.stringify(url)}. ` +
            'Una ruta relativa es exactamente el fallo que este guardia existe para impedir.'
        );
      }
      // 2026-09-24: el bundle salio con 'https://whetzy.com' como API. Es un
      // origen absoluto y paso el guardia, pero es el propio frontend: el
      // login iba a Cloudflare y volvia 405. La API nunca vive en el dominio
      // del SPA y su ruta siempre acaba en /api/v1. Un subdominio propio
      // (`api.whetzy.com`, 2026-10-17) si vale: es otro host, y comparte sitio
      // con el SPA, que es lo que deja viva la cookie de sesion en Safari.
      const { hostname, pathname } = new URL(url);
      if (/^(www\.)?whetzy\.com$|\.pages\.dev$/.test(hostname) || !/\/api\/v1\/?$/.test(pathname)) {
        throw new Error(
          `VITE_API_URL es ${JSON.stringify(url)}: tiene que ser el origen del backend ` +
            '(no el dominio del frontend) terminado en /api/v1.'
        );
      }
    },
  };
}

/** Pre-renderiza la landing al final de CUALQUIER `vite build`, no solo de
 *  `npm run build`. El 2026-09-24 el panel de Cloudflare Pages ejecutaba
 *  `npx tsc -b && npx vite build` y la landing de produccion salia sin el hero
 *  pre-renderizado (H.32). El script hace su propio build SSR con esta misma
 *  config: la variable WHETZY_PRERENDER_CHILD y `build.ssr` evitan la recursion. */
function prerenderLandingPlugin(): Plugin {
  let isSsr = false;
  return {
    name: 'prerender-landing',
    apply: 'build',
    configResolved(config) {
      isSsr = Boolean(config.build.ssr);
    },
    closeBundle() {
      if (isSsr || process.env.WHETZY_PRERENDER_CHILD) return;
      const r = spawnSync(process.execPath, ['scripts/prerender-landing.mjs'], {
        cwd: process.cwd(),
        stdio: 'inherit',
        env: { ...process.env, WHETZY_PRERENDER_CHILD: '1' },
      });
      if (r.status !== 0) throw new Error('[prerender-landing] fallo; el build no es publicable');
    },
  };
}

/** El commit del que sale el build, para que `check-deployed.mjs` pueda
 *  preguntar «¿lo servido es ESTE commit?» en vez de inferirlo de rasgos del
 *  HTML (canonical, hero) que siguen ahi en un deploy viejo. Cloudflare Pages
 *  inyecta CF_PAGES_COMMIT_SHA en cada build; fuera de Pages se lee de git y,
 *  si el arbol tiene cambios sin commitear, se marca `-dirty`: ese build no es
 *  ningun commit y no debe pasar por uno. */
function buildCommitSha(): string {
  if (process.env.CF_PAGES_COMMIT_SHA) return process.env.CF_PAGES_COMMIT_SHA;
  const head = spawnSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf-8' });
  if (head.status !== 0 || !head.stdout.trim()) return 'unknown';
  const dirty = spawnSync('git', ['status', '--porcelain', '--untracked-files=no'], { encoding: 'utf-8' });
  return `${head.stdout.trim()}${dirty.stdout.trim() ? '-dirty' : ''}`;
}

function buildCommitMetaPlugin(): Plugin {
  const sha = buildCommitSha();
  return {
    name: 'build-commit-meta',
    apply: 'build',
    transformIndexHtml() {
      return [{ tag: 'meta', attrs: { name: 'whetzy-build', content: sha }, injectTo: 'head' }];
    },
  };
}

/** `public/sw.js` lleva su VERSION como el placeholder `__WHETZY_BUILD_SHA__`
 *  (swVersion.mjs) -- lo sustituye aqui por el mismo commit que ya usa el
 *  meta `whetzy-build`, asi que un deploy nuevo siempre trae un CACHE_NAME
 *  nuevo sin que nadie tenga que acordarse de subir una fecha a mano (0.15). */
function swVersionPlugin(): Plugin {
  let isSsr = false;
  const sha = buildCommitSha();
  return {
    name: 'sw-version',
    apply: 'build',
    configResolved(config) {
      isSsr = Boolean(config.build.ssr);
    },
    closeBundle() {
      if (isSsr || process.env.WHETZY_PRERENDER_CHILD) return;
      const swPath = resolve(process.cwd(), 'dist', 'sw.js');
      if (!existsSync(swPath)) return;
      const source = readFileSync(swPath, 'utf-8');
      writeFileSync(swPath, injectBuildVersion(source, sha));
    },
  };
}

/** `tsc -b` dentro de cualquier `vite build` de produccion (30.5). `8a0dce0`
 *  lo quito del script `build` desde la UI web de GitHub y desde entonces el
 *  tipado solo lo comprobaba el comando que el panel de Cloudflare tenga
 *  escrito (`npx tsc -b && npx vite build`), que no esta en el repo y puede
 *  cambiar sin que nadie lo vea. Aqui no depende de quien llame al build. El
 *  build SSR hijo del prerender no lo repite. */
function typecheckPlugin(): Plugin {
  return {
    name: 'typecheck-tsc-b',
    apply: 'build',
    configResolved(config) {
      if (config.build.ssr || process.env.WHETZY_PRERENDER_CHILD) return;
      const tsc = resolve(process.cwd(), 'node_modules', 'typescript', 'bin', 'tsc');
      const r = spawnSync(process.execPath, [tsc, '-b'], { cwd: process.cwd(), stdio: 'inherit' });
      if (r.status !== 0) throw new Error('[typecheck] `tsc -b` fallo; el build no es publicable');
    },
  };
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    typecheckPlugin(),
    buildCommitMetaPlugin(),
    swVersionPlugin(),
    react(),
    cloudflarePrettyUrlsPreviewPlugin(),
    pyodideSelfHostPlugin(),
    monacoDropUnusedLanguageServices(),
    requireApiUrl(),
    prerenderLandingPlugin(),
  ],
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
    // Disable the modulepreload polyfill so Vite emits no inline <script>
    // in the HTML — required for CSP without 'unsafe-inline' (22.2).
    modulePreload: { polyfill: false },
  },
  server: {
    // blogContent.ts reads `content/blog/**/*.md` from the repo root via
    // `import.meta.glob(..., { query: '?raw' })` (26.9, 0.14) — one level
    // above this project's own root, which the dev server denies by default
    // ("Denied ID"). `vite build` doesn't enforce this (verified separately),
    // only the dev server (and vitest, which hits the same check — see
    // vitest.config.ts) do.
    fs: { allow: [resolve(__dirname, '..')] },
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
  // `vite preview` serves dist/, which is the artifact that actually ships — so
  // it is the only place a build-only plugin can be exercised before deploying.
  // Without the same headers and API proxy as the dev server, preview can load
  // the app but not sign in or run an exec question, which is most of what is
  // worth checking there.
  preview: {
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
