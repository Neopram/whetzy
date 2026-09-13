import { existsSync } from 'node:fs'
import { resolve } from 'node:path'
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

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), cloudflarePrettyUrlsPreviewPlugin()],
  build: {
    // Read by scripts/prerender-landing.mjs to find the exact hashed CSS
    // chunk LandingScreen.tsx needs (task 11.11) — its styles (incl. the
    // hero <h1>'s font-size) live in a route-level code-split chunk that
    // isn't otherwise linked from the static HTML shell, only pulled in at
    // runtime when the lazy route import resolves.
    manifest: true,
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
