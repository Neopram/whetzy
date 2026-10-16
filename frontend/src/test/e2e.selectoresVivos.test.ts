/**
 * Los E2E buscan elementos por la clase de CSS module (`[class*="btnNext_"]`).
 * #214 y #216 (2026-10-16) cambiaron los botones de Quiz por el `Button` común
 * y borraron `.btnNext` y `.btnStudy`: `helpers.ts` (de él cuelgan los specs
 * de duelo) y `quiz.spec.ts` se quedaron buscando clases que ya no existían, y
 * ni vitest ni el nivel 2 corren los E2E. Esta guarda falla si un E2E nombra
 * una clase que no está en ningún `.module.css` de `src/`. Límite: si otra
 * pantalla conserva una clase con el mismo nombre (`.btnStudy` sigue en
 * Hoy), la guarda no lo ve; por eso los botones se buscan por su
 * nombre accesible, no por la clase.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const ROOT = join(__dirname, '..', '..');

function files(dir: string, ext: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) return files(full, ext);
    return name.endsWith(ext) ? [full] : [];
  });
}

const css = files(join(ROOT, 'src'), '.module.css').map((f) => readFileSync(f, 'utf8')).join('\n');
const used = new Map<string, string[]>();
for (const f of files(join(ROOT, 'e2e'), '.ts')) {
  for (const m of readFileSync(f, 'utf8').matchAll(/class\*=["']([A-Za-z][\w-]*)_["']/g)) {
    used.set(m[1], [...(used.get(m[1]) ?? []), f.slice(ROOT.length + 1)]);
  }
}

describe('los E2E solo buscan clases que existen', () => {
  it('encuentra selectores por clase en los E2E', () => {
    expect(used.size).toBeGreaterThan(5);
  });

  it('cada [class*="X_"] tiene su .X en algún módulo CSS', () => {
    const dead = [...used].filter(([cls]) => !new RegExp(`\\.${cls}\\b`).test(css)).map(([cls, where]) => `${cls} (${where.join(', ')})`);
    expect(dead).toEqual([]);
  });
});
