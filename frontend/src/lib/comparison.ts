/** Comparativa de la landing: solo lo que se comprobó en páginas públicas.
 *
 *  Cada celda es lo que la página pública de ese competidor dice u ofrece,
 *  consultada en `COMPARISON_CHECKED_ON` sin registrarse (ver
 *  docs/COMPETENCIA.md §2, con la URL y el texto de cada dato). `null` = no se
 *  pudo comprobar en abierto: se pinta como «no comprobado», nunca como un
 *  «no». Si esta lista está vacía, la landing no muestra la sección.
 *
 *  Precios en USD tal como los sirve cada web a una salida de red en EE. UU.;
 *  en otros países pueden cambiar (EDteam, por ejemplo, fija precio local en
 *  BO/CO/MX/PE). Al cambiar una cifra, cambia también la fecha.
 */
export type ComparisonCell = true | false | null | { es: string; en: string };

export interface ComparisonRow {
  label: { es: string; en: string };
  whetzy: ComparisonCell;
  others: ComparisonCell[];
}

// Whetzy: precios del dueño (ADR-41). El anual aún no está fijado.
const NO_YEARLY = { es: 'Sin anual aún', en: 'No yearly plan yet' };

export const COMPARISON_CHECKED_ON = '2026-09-24';
export const COMPARISON_COMPETITORS: string[] = ['Codecademy', 'Platzi', 'EDteam'];
export const COMPARISON_ROWS: ComparisonRow[] = [
  {
    // codecademy.com/es redirige a la home en inglés; platzi y ed.team sirven lang="es".
    label: { es: 'Web en español', en: 'Site in Spanish' },
    whetzy: true,
    others: [false, true, true],
  },
  {
    label: { es: 'Plan gratuito', en: 'Free plan' },
    whetzy: true,
    others: [
      { es: 'Basic, limitado', en: 'Basic, limited' },
      { es: 'Algunos cursos', en: 'Some courses' },
      { es: '9 cursos', en: '9 courses' },
    ],
  },
  {
    label: { es: 'Pago mensual (USD)', en: 'Monthly plan (USD)' },
    whetzy: { es: '14,99 (Pro)', en: '14.99 (Pro)' },
    others: [
      { es: '29,99', en: '29.99' },
      { es: '49', en: '49' },
      { es: '30', en: '30' },
    ],
  },
  {
    label: { es: 'Pago anual, al mes (USD)', en: 'Yearly plan, per month (USD)' },
    whetzy: NO_YEARLY,
    others: [
      { es: '14,99', en: '14.99' },
      { es: '≈21 (249/año)', en: '≈21 (249/yr)' },
      { es: '20 (240/año)', en: '20 (240/yr)' },
    ],
  },
];
