/**
 * 40.1: el cliente corrige igual que el servidor. Lee los mismos casos que
 * `backend/tests/unit/test_widget_checkers.py`; si `widgets/checkers.ts` y
 * `services/widgets/checkers.py` se separan, uno de los dos se pone en rojo.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { CHECKERS, check, isCheckerName } from '../widgets/checkers';

interface Caso { checker: string; state: unknown; target: unknown; expected: boolean; why: string }
const CASOS = JSON.parse(
  readFileSync(resolve(__dirname, '../../../backend/tests/fixtures/widget_checker_cases.json'), 'utf-8'),
) as { checkers: string[]; cases: Caso[] };

describe('checkers de interactive (40.1)', () => {
  it.each(CASOS.cases.map((c) => [`${c.checker}: ${c.why}`, c] as const))('%s', (_name, c) => {
    expect(isCheckerName(c.checker)).toBe(true);
    expect(CHECKERS[c.checker as keyof typeof CHECKERS](c.state, c.target)).toBe(c.expected);
  });

  it('el registro es el mismo que el del servidor', () => {
    expect(Object.keys(CHECKERS).sort()).toEqual([...CASOS.checkers].sort());
  });

  it('un checker desconocido o sin estado da incorrecto, como en el servidor', () => {
    expect(check('fuzzy', [1], [1])).toBe(false);
    expect(check('exact', null, [1])).toBe(false);
    expect(check('exact', undefined, [1])).toBe(false);
    expect(check('exact', [1], [1])).toBe(true);
  });
});
