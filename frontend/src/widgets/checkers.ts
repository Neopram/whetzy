/**
 * Checkers de las preguntas `interactive` (40.1, docs/PLAN_EXPERIENCIA.md §1).
 *
 * Copia exacta de `backend/app/services/widgets/checkers.py`: el servidor
 * puntúa y el cliente vuelve a corregir con el `widget_target` que trae la
 * respuesta, para avisar si los dos veredictos no coinciden. Los dos leen
 * `backend/tests/fixtures/widget_checker_cases.json`; cambiar uno sin el otro
 * pone en rojo `widgetCheckers.test.ts` o `test_widget_checkers.py`.
 *
 * Igualdad JSON: un booleano no es un número, `1` y `1.0` son el mismo número,
 * y el orden de las claves de un objeto no cuenta.
 */

export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };

export function jsonEqual(a: unknown, b: unknown): boolean {
  if (typeof a === 'boolean' || typeof b === 'boolean') return a === b;
  if (typeof a === 'number' && typeof b === 'number') return a === b;
  if (typeof a === 'string' && typeof b === 'string') return a === b;
  if (a === null || b === null) return a === null && b === null;
  if (Array.isArray(a) && Array.isArray(b)) {
    return a.length === b.length && a.every((x, i) => jsonEqual(x, b[i]));
  }
  if (isObject(a) && isObject(b)) {
    const ka = Object.keys(a);
    const kb = Object.keys(b);
    return ka.length === kb.length && ka.every((k) => Object.hasOwn(b, k) && jsonEqual(a[k], b[k]));
  }
  return false;
}

function isObject(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v);
}

/** El estado es exactamente el objetivo (p. ej. la secuencia de sondeos de una búsqueda binaria). */
export function exact(state: unknown, target: unknown): boolean {
  return jsonEqual(state, target);
}

/** Mismos elementos en cualquier orden, con sus repeticiones (las filas de un JOIN). */
export function unordered(state: unknown, target: unknown): boolean {
  if (!Array.isArray(state) || !Array.isArray(target) || state.length !== target.length) return false;
  const remaining = [...target];
  for (const item of state) {
    const i = remaining.findIndex((candidate) => jsonEqual(item, candidate));
    if (i === -1) return false;
    remaining.splice(i, 1);
  }
  return true;
}

export const CHECKERS = { exact, unordered } as const;
export type CheckerName = keyof typeof CHECKERS;

export function isCheckerName(name: string): name is CheckerName {
  return Object.hasOwn(CHECKERS, name);
}

/** Veredicto del cliente. Un checker que no conoce cuenta como incorrecto, igual que en el servidor. */
export function check(checker: string, state: unknown, target: unknown): boolean {
  if (!isCheckerName(checker) || state === undefined || state === null || target === null) return false;
  return CHECKERS[checker](state, target);
}
