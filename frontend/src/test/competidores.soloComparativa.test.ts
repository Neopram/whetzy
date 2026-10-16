/**
 * Auditoría de pantallas, 2026-10-15: `/evidence` puntuaba de 0 a 20 a nueve
 * plataformas con nombre (Boot.dev, Platzi, LeetCode…) con notas propias, sin
 * auditar y sin fuente fechada, y daba una cifra de catálogo ajena («500+ de
 * Platzi») que nadie había comprobado. Es publicidad comparativa sin respaldo.
 *
 * La única comparativa pública es la de la portada (`lib/comparison.ts`), con
 * lo comprobado en la web de cada plataforma y la fecha de comprobación. Esta
 * guarda falla si una marca aparece en cualquier otro fichero de `src/`.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { describe, expect, it } from 'vitest';

const SRC = join(__dirname, '..');
const ALLOWED = new Set(['lib/comparison.ts']);
const SKIP_DIRS = new Set(['test']);

const BRANDS = [
  'Boot.dev', 'Sololearn', 'Mimo', 'Exercism', 'Platzi', 'KodeKloud', 'A Cloud Guru',
  'LeetCode', 'freeCodeCamp', 'Codecademy', 'EDteam', 'Coursera', 'Udemy', 'DataCamp',
];
const BRAND_RE = new RegExp(`\\b(${BRANDS.map((b) => b.replace('.', '\\.')).join('|')})\\b`, 'i');

function files(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) return SKIP_DIRS.has(name) ? [] : files(full);
    return /\.(ts|tsx|json)$/.test(name) ? [full] : [];
  });
}

describe('las marcas de la competencia solo viven en la comparativa con fuente', () => {
  const all = files(SRC).map((f) => relative(SRC, f).split('\\').join('/'));

  it('ve la comparativa y la página de evidencia', () => {
    expect(all).toContain('lib/comparison.ts');
    expect(all).toContain('pages/EvidenceScreen.tsx');
  });

  it('ningún otro fichero de src/ nombra a un competidor', () => {
    const offenders = all
      .filter((f) => !ALLOWED.has(f))
      .flatMap((f) => {
        const m = readFileSync(join(SRC, f), 'utf8').match(BRAND_RE);
        return m ? [`${f}: ${m[0]}`] : [];
      });
    expect(offenders).toEqual([]);
  });
});
