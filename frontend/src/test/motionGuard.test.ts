/**
 * 46.16 (docs/PLAN_UI_AVANZADA.md §7.6): el orden del movimiento, vigilado.
 *
 * 1. Con movimiento reducido, CSS se apaga en un solo sitio: el bloque global
 *    de `styles/global.css`. Si alguien lo quita, todas las @keyframes vuelven
 *    a moverse para quien pidió que no.
 * 2. framer lo apaga `MotionConfig reducedMotion="user"` en App.
 * 3. Ninguna duración de framer pasa de 0,7 s (nivel 2 de §6.0) ni ninguna
 *    animación se repite sin fin sin una anotación `fx-budget:` en esa línea
 *    o la anterior que diga por qué (el resumen y las ceremonias, niveles 3–4,
 *    y el pulso del nodo actual del mapa).
 * 4. Los tokens de duración de lib/motion.ts y el presupuesto por nivel de
 *    feedbackFx son el mismo número.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { DUR } from '../lib/motion';
import { TIER_BUDGET } from '../lib/feedbackFx';

const SRC = resolve(__dirname, '..');
const read = (p: string) => readFileSync(join(SRC, p), 'utf-8');

function sources(): string[] {
  const out: string[] = [];
  const walk = (dir: string) => {
    for (const f of readdirSync(dir)) {
      const p = join(dir, f);
      if (statSync(p).isDirectory()) { if (f !== 'test') walk(p); }
      else if (/\.(ts|tsx)$/.test(p)) out.push(p);
    }
  };
  walk(SRC);
  return out;
}

function violations(re: RegExp, over: (m: RegExpMatchArray) => boolean): string[] {
  return sources().flatMap((f) => {
    const lines = readFileSync(f, 'utf-8').split('\n');
    return lines.flatMap((line, i) =>
      // Los comentarios que nombran una animación no son una animación.
      (/^\s*(\/\/|\*|\/\*)/.test(line) ? [] : [...line.matchAll(re)])
        .filter(over)
        .filter(() => !/fx-budget:/.test(line) && !/fx-budget:/.test(lines[i - 1] ?? ''))
        .map(() => `${relative(SRC, f)}:${i + 1}`),
    );
  });
}

describe('guarda de movimiento (46.16)', () => {
  it('el bloque global de movimiento reducido sigue en global.css', () => {
    const css = read('styles/global.css');
    const block = css.match(/@media \(prefers-reduced-motion: reduce\)\s*\{([\s\S]*?)\n\}/)?.[1] ?? '';
    expect(block).toMatch(/\*, \*::before, \*::after\s*\{[^}]*animation-duration: 0\.01ms !important;[^}]*animation-iteration-count: 1 !important;/);
  });

  it('App envuelve la app en MotionConfig reducedMotion="user"', () => {
    expect(read('App.tsx')).toMatch(/<MotionConfig reducedMotion="user">/);
  });

  it('ninguna duración de framer pasa de 0,7 s sin anotación', () => {
    expect(violations(/duration: ?(\d*\.?\d+)/g, (m) => Number(m[1]) > DUR.milestone)).toEqual([]);
  });

  it('nada se repite sin fin sin anotación', () => {
    expect(violations(/repeat: ?Infinity/g, () => true)).toEqual([]);
  });

  it('tokens y presupuesto por nivel son el mismo número', () => {
    expect(TIER_BUDGET[0].maxMs).toBe(DUR.micro * 1000);
    expect(TIER_BUDGET[1].maxMs).toBe(DUR.response * 1000);
    expect(TIER_BUDGET[2].maxMs).toBe(DUR.milestone * 1000);
    expect(TIER_BUDGET[3].maxMs).toBe(DUR.close * 1000);
    expect(TIER_BUDGET[4].maxMs).toBe(DUR.ceremony * 1000);
  });
});
