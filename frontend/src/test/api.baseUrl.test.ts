/**
 * Ningun `fetch` fuera de services/api.ts puede apuntar a una ruta relativa
 * '/api/...' ni a localhost: en produccion el frontend vive en whetzy.com
 * y la API en otro origen, asi que esas llamadas van a Cloudflare.
 *
 * Paso de verdad el 2026-09-24: el login devolvia 405, y al buscar la causa
 * aparecieron cinco llamadas mas con el mismo fallo (push, preferencias,
 * admin, experimentos, banner). Todas deben usar `API_BASE_URL`.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { describe, expect, it } from 'vitest';

const SRC = join(__dirname, '..');
const SKIP = new Set(['test', 'entry-server']);

function sourceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) return SKIP.has(name) ? [] : sourceFiles(full);
    return /\.(ts|tsx)$/.test(name) ? [full] : [];
  });
}

const FORBIDDEN = [
  { re: /fetch\(\s*['"`]\/api\//, why: "fetch a ruta relativa '/api/...'" },
  { re: /['"`]\/api\/v1\/[a-z]/, why: "literal '/api/v1/<recurso>' (usa API_BASE_URL)" },
  { re: /localhost:8000/, why: 'origen de desarrollo codificado' },
  { re: /VITE_API_BASE\b/, why: 'variable VITE_API_BASE, que no existe (es VITE_API_URL)' },
  // 2026-09-25, verificador de 30.7: DeleteAccountScreen resolvía la API por su
  // cuenta (`VITE_API_URL || '/api/v1'`) y ninguna regla de arriba lo veía.
  { re: /import\.meta\.env\.VITE_API_URL/, why: 'lee VITE_API_URL por su cuenta (importa API_BASE_URL)' },
  { re: /['"`]\/api\/v1['"`]/, why: "respaldo relativo '/api/v1' (importa API_BASE_URL)" },
];

describe('origen de la API', () => {
  it('solo services/api.ts decide a donde van las llamadas', () => {
    const hits: string[] = [];
    for (const file of sourceFiles(SRC)) {
      const rel = relative(SRC, file);
      if (rel === join('services', 'api.ts')) continue;
      readFileSync(file, 'utf-8')
        .split('\n')
        .forEach((line, i) => {
          if (/^\s*(\/\/|\*)/.test(line)) return; // comentarios
          for (const { re, why } of FORBIDDEN) if (re.test(line)) hits.push(`${rel}:${i + 1} — ${why}`);
        });
    }
    expect(hits).toEqual([]);
  });
});
