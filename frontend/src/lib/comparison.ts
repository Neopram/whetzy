/** Comparativa de la landing: solo lo que se comprobó en páginas públicas.
 *
 *  Cada celda es lo que la página pública de ese competidor dice u ofrece,
 *  consultada en `COMPARISON_CHECKED_ON` sin registrarse (ver
 *  docs/COMPETENCIA.md). `null` = no se pudo comprobar en abierto: se pinta
 *  como «no comprobado», nunca como un «no». Si esta lista está vacía, la
 *  landing no muestra la sección.
 */
export type ComparisonCell = true | false | null | { es: string; en: string };

export interface ComparisonRow {
  label: { es: string; en: string };
  whetzy: ComparisonCell;
  others: ComparisonCell[];
}

export const COMPARISON_CHECKED_ON = '';
export const COMPARISON_COMPETITORS: string[] = [];
export const COMPARISON_ROWS: ComparisonRow[] = [];
