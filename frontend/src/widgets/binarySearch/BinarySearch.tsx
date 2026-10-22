/**
 * Búsqueda binaria (40.2). El alumno sondea celdas de una lista ordenada hasta
 * dar con `goal`; tras cada sondeo el widget descarta la mitad que no puede
 * contener el objetivo y la celda queda fuera de juego. Estado y envío: la
 * lista de valores sondeados, en orden (checker `exact`).
 *
 * Teclado: cada celda es un botón (Tab / Enter / Espacio). Alternativa textual:
 * el registro de sondeos (`<ol>`) y la línea `role="status"` dicen lo mismo que
 * el dibujo, con el rango que queda.
 */
import { useId, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { WidgetDefinition, WidgetRenderProps } from '../registry';
import common from '../widget.module.css';
import styles from './BinarySearch.module.css';

const isNums = (v: unknown): v is number[] => Array.isArray(v) && v.length > 0 && v.every((x) => Number.isFinite(x));

/** Rango de posiciones que aún pueden contener `goal` tras los sondeos (`lo > hi`: ya no queda nada). */
export function rangeAfter(items: number[], goal: number, probes: number[]): { lo: number; hi: number; found: boolean } {
  let lo = 0;
  let hi = items.length - 1;
  let found = false;
  for (const value of probes) {
    const i = items.indexOf(value);
    if (value === goal) found = true;
    else if (value < goal) lo = Math.max(lo, i + 1);
    else hi = Math.min(hi, i - 1);
  }
  return { lo, hi, found };
}

function BinarySearch({ params, lang, disabled, onChange }: WidgetRenderProps<number[]>) {
  const { t } = useTranslation('producto');
  const goalId = useId();
  const [probes, setProbes] = useState<number[]>([]);
  const items = isNums(params.items) ? params.items : null;
  const goal = typeof params.goal === 'number' ? params.goal : null;
  const range = useMemo(
    () => (items && goal !== null ? rangeAfter(items, goal, probes) : null),
    [items, goal, probes],
  );
  if (!items || goal === null || !range) return <p role="alert">{t('interactive.unavailable')}</p>;

  const tr = (key: string, o?: Record<string, unknown>) => t(`widgets.binarySearch.${key}`, { lng: lang, ...o });
  const probe = (value: number) => {
    const next = [...probes, value];
    setProbes(next);
    onChange(next);
  };
  const reset = () => {
    setProbes([]);
    onChange(null);
  };
  const verdict = (value: number) =>
    value === goal ? tr('found', { value }) : tr(value < goal ? 'tooLow' : 'tooHigh', { value, goal });
  const last = probes.length ? probes[probes.length - 1] : null;
  const over = disabled || range.found;

  return (
    <div className={common.area}>
      <p className={common.hint} id={goalId}>{tr('goal', { goal })}</p>
      <ul className={styles.cells} aria-labelledby={goalId}>
        {items.map((value, i) => {
          const outside = i < range.lo || i > range.hi;
          const state = value === goal && probes.includes(value) ? 'found' : probes.includes(value) ? 'probed' : outside ? 'out' : 'open';
          return (
            <li key={i}>
              <button
                type="button"
                className={`${common.btn} ${styles.cell} ${state === 'found' ? styles.found : state === 'probed' ? styles.probed : state === 'out' ? styles.out : ''}`}
                disabled={over || outside || probes.includes(value)}
                aria-label={tr('cell', { pos: i + 1, value, state: tr(`state.${state}`) })}
                onClick={() => probe(value)}
              >
                {value}
              </button>
            </li>
          );
        })}
      </ul>
      <p className={common.status} role="status">
        {last === null ? tr('empty') : `${verdict(last)} ${range.found ? '' : range.lo > range.hi ? tr('noneLeft') : tr('left', { lo: range.lo + 1, hi: range.hi + 1 })}`}
      </p>
      {probes.length > 0 && (
        <ol className={common.log} aria-label={tr('log')}>
          {probes.map((value, n) => <li key={n}>{verdict(value)}</li>)}
        </ol>
      )}
      <button type="button" className={common.btn} onClick={reset} disabled={disabled || probes.length === 0}>
        {tr('reset')}
      </button>
    </div>
  );
}

const definition: WidgetDefinition<number[]> = { render: BinarySearch, serialize: (probes) => [...probes] };
export default definition as WidgetDefinition;
