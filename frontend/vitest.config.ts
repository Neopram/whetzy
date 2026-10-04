import { resolve } from 'node:path';
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    // blogContent.ts reads `content/blog/**/*.md` from the repo root via
    // `import.meta.glob(..., { query: '?raw' })` (26.9, 0.14) — one level
    // above this project's own root, which Vite's dev-server transform
    // denies by default ("Denied ID"). `vite build` doesn't enforce this
    // (verified: a production build reads the same glob fine), only the
    // dev-server-style pipeline vitest also runs on does.
    fs: { allow: [resolve(__dirname, '..')] },
  },
  test: {
    environment: 'jsdom',
    pool: 'threads',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    // e2e/** and e2e-prod/** are Playwright tests (test.describe/test from
    // @playwright/test, a different runner) — vitest's default glob would
    // otherwise pick them up and fail on the unfamiliar test.describe() call.
    // Any new Playwright directory must be listed here too; CI caught e2e-prod
    // missing from this list the same day it was added.
    exclude: ['**/node_modules/**', '**/e2e/**', '**/e2e-prod/**'],
    coverage: {
      provider: 'v8',
      include: ['src/hooks/**', 'src/services/**'],
      // usePyodide (Worker API) and db (idb wrapper) require a real browser — excluded from CI coverage
      exclude: ['src/hooks/usePyodide.ts', 'src/services/db.ts'],
      thresholds: { lines: 70, functions: 70, branches: 60 },
    },
  },
});
