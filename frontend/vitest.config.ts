import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    pool: 'threads',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      include: ['src/hooks/**', 'src/services/**'],
      // usePyodide (Worker API) and db (idb wrapper) require a real browser — excluded from CI coverage
      exclude: ['src/hooks/usePyodide.ts', 'src/services/db.ts'],
      thresholds: { lines: 70, functions: 70, branches: 60 },
    },
  },
});
