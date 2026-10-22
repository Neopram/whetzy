/**
 * INNER JOIN de SQL (40.2). Dos tablas pequeñas y la condición `ON`: el alumno
 * marca qué pares de filas devuelve la consulta. Estado y envío: una lista de
 * `[id de la izquierda, id de la derecha]` (primera columna de cada fila), en
 * cualquier orden (checker `unordered`).
 *
 * Teclado: casillas nativas dentro de un `fieldset` con leyenda. Alternativa
 * textual: las tablas son `<table>` con título y cada casilla dice en palabras
 * las dos filas que une; la consulta equivalente va en un bloque de código.
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { WidgetDefinition, WidgetRenderProps } from '../registry';
import common from '../widget.module.css';
import styles from './SqlJoin.module.css';

type Cell = string | number;
interface Table { name: string; columns: string[]; rows: Cell[][] }
interface On { left: string; right: string }

const MAX_PAIRS = 25;

function asTable(v: unknown): Table | null {
  const t = v as Partial<Table> | null;
  if (!t || typeof t.name !== 'string' || !Array.isArray(t.columns) || !Array.isArray(t.rows)) return null;
  const cell = (c: unknown) => typeof c === 'string' || typeof c === 'number';
  const ok = t.columns.every((c) => typeof c === 'string') && t.rows.length > 0
    && t.rows.every((r) => Array.isArray(r) && r.length === t.columns!.length && r.every(cell));
  return ok ? (t as Table) : null;
}

const describe = (table: Table, row: Cell[]) =>
  `${table.name}(${table.columns.map((c, i) => `${c}=${row[i]}`).join(', ')})`;

function SqlJoin({ params, lang, disabled, onChange }: WidgetRenderProps<Cell[][]>) {
  const { t } = useTranslation('producto');
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const left = asTable(params.left);
  const right = asTable(params.right);
  const on = params.on as Partial<On> | undefined;
  if (!left || !right || typeof on?.left !== 'string' || typeof on.right !== 'string' || left.rows.length * right.rows.length > MAX_PAIRS) {
    return <p role="alert">{t('interactive.unavailable')}</p>;
  }

  const tr = (key: string, o?: Record<string, unknown>) => t(`widgets.sqlJoin.${key}`, { lng: lang, ...o });
  const pairs = left.rows.flatMap((l) => right.rows.map((r) => [l, r] as const));
  const keyOf = (l: Cell[], r: Cell[]) => `${l[0]}|${r[0]}`;
  const toggle = (key: string) => {
    const next = new Set(picked);
    if (!next.delete(key)) next.add(key);
    setPicked(next);
    onChange(next.size ? pairs.filter(([l, r]) => next.has(keyOf(l, r))).map(([l, r]) => [l[0], r[0]]) : null);
  };
  const sql = `SELECT *\nFROM ${left.name}\nINNER JOIN ${right.name}\n  ON ${left.name}.${on.left} = ${right.name}.${on.right};`;

  return (
    <div className={common.area}>
      <pre className={common.code}><code>{sql}</code></pre>
      <div className={styles.tables}>
        {[left, right].map((table) => (
          <div key={table.name} className={common.scroll}>
            <table className={styles.table}>
              <caption>{table.name}</caption>
              <thead><tr>{table.columns.map((c) => <th key={c} scope="col">{c}</th>)}</tr></thead>
              <tbody>{table.rows.map((r, i) => <tr key={i}>{r.map((c, j) => <td key={j}>{c}</td>)}</tr>)}</tbody>
            </table>
          </div>
        ))}
      </div>
      <fieldset className={styles.pairs} disabled={disabled}>
        <legend>{tr('legend')}</legend>
        {pairs.map(([l, r]) => {
          const key = keyOf(l, r);
          return (
            <label key={key} className={styles.pair}>
              <input type="checkbox" checked={picked.has(key)} onChange={() => toggle(key)} />
              <span>{tr('pair', { left: describe(left, l), right: describe(right, r) })}</span>
            </label>
          );
        })}
      </fieldset>
      <p className={common.status} role="status">{tr('selected', { count: picked.size })}</p>
    </div>
  );
}

const definition: WidgetDefinition<Cell[][]> = { render: SqlJoin, serialize: (rows) => rows.map((r) => [...r]) };
export default definition as WidgetDefinition;
