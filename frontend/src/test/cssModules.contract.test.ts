/**
 * Cada `styles.x` de un componente tiene que existir en su CSS module.
 *
 * Una clase que no existe no da error: `styles.x` vale `undefined` y el
 * elemento se pinta sin estilo. El 2026-09-24 los commits «Obsidian Radiant»
 * reescribieron los .module.css con nombres nuevos y dejaron los .tsx con los
 * viejos: 276 de 761 referencias apuntaban a nada (QuizScreen 59/60,
 * TracksScreen 56/59, HomeScreen 42/44…) y la pantalla de login salia con los
 * botones en gris sobre negro.
 *
 * Trinquete: BASELINE es la deuda medida ese dia. Ningun fichero puede
 * empeorar ni aparecer uno nuevo con clases rotas; al arreglar uno, baja su
 * numero aqui (el test avisa si ya esta por debajo). Ledger 34.0; la base
 * quedo vacia en 34.1, asi que hoy cualquier clase sin definir es un rojo.
 */
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { describe, expect, it } from 'vitest';

const SRC = join(__dirname, '..');

// Pagada entera en 34.1 (2026-09-24): 276 → 0. Desde aquí, estricta.
const BASELINE: Record<string, number> = {};

function tsxFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) return name === 'test' ? [] : tsxFiles(full);
    return name.endsWith('.tsx') ? [full] : [];
  });
}

function definedClasses(css: string): Set<string> {
  const noComments = css.replace(/\/\*[\s\S]*?\*\//g, '').replace(/url\([^)]*\)/g, '');
  let selectors = noComments;
  // Quitar cuerpos de reglas (anidados incluidos) para quedarse con selectores.
  for (let i = 0; i < 5; i++) selectors = selectors.replace(/\{[^{}]*\}/g, '{}');
  return new Set([...selectors.matchAll(/\.([A-Za-z_][\w-]*)/g)].map((m) => m[1]));
}

function missingByFile(): Record<string, string[]> {
  const out: Record<string, string[]> = {};
  for (const file of tsxFiles(SRC)) {
    const src = readFileSync(file, 'utf-8');
    const imp = src.match(/import styles from '([^']+\.module\.css)'/);
    if (!imp) continue;
    const cssPath = join(dirname(file), imp[1]);
    const rel = relative(SRC, file).split('\\').join('/');
    if (!existsSync(cssPath)) {
      out[rel] = ['<el CSS module no existe>'];
      continue;
    }
    const defined = definedClasses(readFileSync(cssPath, 'utf-8'));
    const used = new Set([
      ...[...src.matchAll(/styles\.([A-Za-z_]\w*)/g)].map((m) => m[1]),
      ...[...src.matchAll(/styles\['([^']+)'\]/g)].map((m) => m[1]),
    ]);
    const missing = [...used].filter((c) => !defined.has(c)).sort();
    if (missing.length) out[rel] = missing;
  }
  return out;
}

describe('contrato .tsx ↔ .module.css', () => {
  const missing = missingByFile();

  it('ningún fichero empeora ni aparece uno nuevo con clases sin definir', () => {
    const worse = Object.entries(missing)
      .filter(([f, list]) => list.length > (BASELINE[f] ?? 0))
      .map(([f, list]) => `${f}: ${list.length} (base ${BASELINE[f] ?? 0}) — ${list.join(' ')}`);
    expect(worse).toEqual([]);
  });

  it('la base no guarda deuda ya pagada (bájala al arreglar)', () => {
    const stale = Object.entries(BASELINE)
      .filter(([f, n]) => (missing[f]?.length ?? 0) < n)
      .map(([f, n]) => `${f}: ahora ${missing[f]?.length ?? 0}, base ${n}`);
    expect(stale).toEqual([]);
  });
});
