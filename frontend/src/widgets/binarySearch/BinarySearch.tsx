/**
 * Búsqueda binaria (40.2): una lista ordenada con los valores tapados. El
 * alumno abre casillas una a una; cada apertura dice si el valor es menor,
 * mayor o el buscado, y descarta la mitad que ya no puede contenerlo. El
 * estado es la secuencia de posiciones abiertas; se corrige con `exact` contra
 * la secuencia de centros (redondeando hacia abajo).
 *
 * Teclado: cada casilla es un botón. Alternativa textual: el registro de
 * aperturas, que además se anuncia en una región `aria-live`.
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { WidgetRenderProps } from '../registry';
import styles from './BinarySearch.module.css';

export interface BinarySearchParams {
  items: number[];
  target: number;
}

export interface BinarySearchState {
  probes: number[];
}

type Verdict = 'lower' | 'higher' | 'found';

export function parseParams(params: Record<string, unknown>): BinarySearchParams {
  const items = params.items;
  const target = params.target;
  if (!Array.isArray(items) || !items.every((n) => typeof n === 'number') || typeof target !== 'number') {
    throw new Error('binarySearch: params {items: number[], target: number}');
  }
  return { items: items as number[], target };
}

/** Qué dice abrir la posición `i`: el valor es menor, mayor o el buscado. */
export function verdictAt(p: BinarySearchParams, i: number): Verdict {
  const v = p.items[i];
  return v === p.target ? 'found' : v < p.target ? 'lower' : 'higher';
}

/** Posiciones aún posibles tras las aperturas hechas, como [lo, hi] (vacío si lo > hi). */
export function remaining(p: BinarySearchParams, probes: number[]): [number, number] {
  let lo = 0;
  let hi = p.items.length - 1;
  for (const i of probes) {
    const v = verdictAt(p, i);
    if (v === 'lower') lo = Math.max(lo, i + 1);
    else if (v === 'higher') hi = Math.min(hi, i - 1);
  }
  return [lo, hi];
}

export function BinarySearch({ params, disabled, onChange }: WidgetRenderProps<BinarySearchState>) {
  const { t } = useTranslation('producto');
  const p = parseParams(params);
  const [probes, setProbes] = useState<number[]>([]);
  const [lo, hi] = remaining(p, probes);
  const found = probes.some((i) => verdictAt(p, i) === 'found');
  const last = probes.at(-1);

  const open = (i: number) => {
    if (disabled || found || probes.includes(i) || i < lo || i > hi) return;
    const next = [...probes, i];
    setProbes(next);
    // Solo hay algo que enviar cuando el valor buscado ha salido.
    onChange(verdictAt(p, i) === 'found' ? { probes: next } : null);
  };

  const reset = () => {
    setProbes([]);
    onChange(null);
  };

  const describe = (i: number) =>
    t(`widgets.binarySearch.verdict.${verdictAt(p, i)}`, { value: p.items[i], target: p.target });

  return (
    <div className={styles.widget}>
      <p className={styles.goal}>{t('widgets.binarySearch.goal', { target: p.target, n: p.items.length })}</p>
      <ol className={styles.cells} aria-label={t('widgets.binarySearch.list')}>
        {p.items.map((value, i) => {
          const opened = probes.includes(i);
          const out = !opened && (i < lo || i > hi || found);
          const state = opened ? verdictAt(p, i) : out ? 'out' : 'closed';
          return (
            <li key={i}>
              <button
                type="button"
                className={`${styles.cell} ${styles[state]}`}
                onClick={() => open(i)}
                disabled={disabled || opened || out}
                aria-label={
                  opened
                    ? t('widgets.binarySearch.cellOpen', { pos: i, value })
                    : out
                      ? t('widgets.binarySearch.cellOut', { pos: i })
                      : t('widgets.binarySearch.cellClosed', { pos: i })
                }
              >
                <span className={styles.pos} aria-hidden="true">{i}</span>
                <span className={styles.value} aria-hidden="true">{opened ? value : '?'}</span>
              </button>
            </li>
          );
        })}
      </ol>
      <p className={styles.live} role="status" aria-live="polite">
        {last === undefined ? t('widgets.binarySearch.start') : describe(last)}
      </p>
      {probes.length > 0 && (
        <ol className={styles.log} aria-label={t('widgets.binarySearch.log')}>
          {probes.map((i, k) => (
            <li key={k}>{t('widgets.binarySearch.logLine', { k: k + 1, pos: i, text: describe(i) })}</li>
          ))}
        </ol>
      )}
      {!disabled && probes.length > 0 && (
        <button type="button" className={styles.reset} onClick={reset}>
          {t('widgets.reset')}
        </button>
      )}
    </div>
  );
}
