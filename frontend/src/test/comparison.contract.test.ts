import { describe, expect, it } from 'vitest';
import { COMPARISON_CHECKED_ON, COMPARISON_COMPETITORS, COMPARISON_ROWS } from '../lib/comparison';

// La comparativa de la landing es una afirmación pública sobre terceros: si
// tiene filas, tiene fecha de consulta y una celda por competidor.
describe('comparativa de la landing', () => {
  it('lleva fecha ISO si hay filas', () => {
    if (COMPARISON_ROWS.length === 0) return;
    expect(COMPARISON_CHECKED_ON).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it('cada fila tiene una celda por competidor', () => {
    for (const row of COMPARISON_ROWS) {
      expect(row.others, row.label.es).toHaveLength(COMPARISON_COMPETITORS.length);
    }
  });

  it('las celdas de texto están en los dos idiomas', () => {
    for (const row of COMPARISON_ROWS) {
      for (const cell of [row.whetzy, ...row.others]) {
        if (cell && typeof cell === 'object') {
          expect(cell.es.trim(), row.label.es).not.toBe('');
          expect(cell.en.trim(), row.label.en).not.toBe('');
        }
      }
    }
  });
});
