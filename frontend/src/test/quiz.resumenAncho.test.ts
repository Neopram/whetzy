/**
 * Resumen del quiz a 390 px (2026-10-16): la fila de cada habilidad tenía tres
 * columnas (nombre, barra de 4.5rem, %) y, al pasar a bandas (ADR-60, #204), la
 * barra desapareció y los dos chips cayeron en la columna de 4.5rem con
 * `nowrap`: la página medía 611 px de ancho. Una rejilla de dos columnas
 * tampoco sirve: con dos chips largos («Evidencia insuficiente») la columna
 * `auto` se lo come todo y el nombre queda a una letra por línea. La fila es
 * flex que parte línea: si las bandas no caben, bajan debajo del nombre.
 * Comprobado con Playwright (scrollWidth 390 en 390 px).
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const css = readFileSync(join(__dirname, '..', 'pages', 'QuizScreen.module.css'), 'utf8');
const rule = (sel: string) => {
  const i = css.indexOf(`${sel} {`);
  return i < 0 ? '' : css.slice(i, css.indexOf('}', i));
};

describe('resumen del quiz: la fila de habilidades cabe en el móvil', () => {
  it('la fila parte línea en vez de fijar columnas', () => {
    const item = rule('.movedItem');
    expect(item).toMatch(/display:\s*flex/);
    expect(item).toMatch(/flex-wrap:\s*wrap/);
    expect(item).not.toMatch(/grid-template-columns/);
  });

  it('el nombre conserva un ancho base y no se estruja', () => {
    expect(rule('.movedName')).toMatch(/flex:\s*1 1 \d+(\.\d+)?rem/);
  });

  it('las bandas pueden partir línea', () => {
    const pct = rule('.movedPct');
    expect(pct).not.toMatch(/nowrap/);
    expect(pct).toMatch(/flex-wrap:\s*wrap/);
  });
});
