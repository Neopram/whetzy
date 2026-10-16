/**
 * Explicación del quiz a 390 px (2026-10-16, E2E mobileNoScroll): una fuente
 * que cita la URL tras un guion («CPython docs 3.13 — … — https://docs.python
 * .org/3/reference/executionmodel.html#naming-and-binding») no casa con el
 * patrón «Etiqueta (URL)», se pinta como texto y la URL, sin espacios por donde
 * partir, ensanchaba la página a 424 px. La línea de la fuente tiene que poder
 * partir en cualquier punto.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const css = readFileSync(join(__dirname, '..', 'components', 'quiz', 'SourceLine.module.css'), 'utf8');
const line = css.slice(css.indexOf('.line {'), css.indexOf('}', css.indexOf('.line {')));

describe('la línea de la fuente no ensancha la pantalla', () => {
  it('parte una URL larga en vez de desbordar', () => {
    expect(line).toMatch(/overflow-wrap:\s*anywhere/);
  });
});
