/**
 * Un ítem de demostración por widget (40.2, ADR-67 D1). No es contenido del
 * banco: no está en `content/`, no lo sirve el servidor ni cuenta para el
 * dominio. Solo lo pinta `/_widgets`, que no entra en el build de producción,
 * para probar cada widget de punta a punta (e2e, axe, peso, LCP) mientras
 * ADR-62 no permita escribir los 30 ítems del piloto.
 *
 * Los objetivos están escritos a mano, no calculados por el widget: el test
 * de contrato los compara con lo que sale de jugar el widget bien.
 */
import type { Json } from './checkers';

export interface WidgetDemo {
  id: string;
  widget: string;
  checker: 'exact' | 'unordered';
  prompt_es: string;
  prompt_en: string;
  params: Record<string, unknown>;
  target: Json;
}

export const DEMOS: WidgetDemo[] = [
  {
    id: 'demo-binary-search',
    widget: 'binarySearch',
    checker: 'exact',
    prompt_es:
      'La lista está ordenada de menor a mayor. Encuentra el 23 con búsqueda binaria: abre siempre la casilla central del tramo que queda (si hay dos centrales, la de la izquierda).',
    prompt_en:
      'The list is sorted in ascending order. Find 23 with binary search: always open the middle cell of the range that is left (if there are two middle cells, the left one).',
    params: { items: [2, 5, 8, 12, 16, 23, 38, 56, 72, 91], target: 23 },
    // lo=0 hi=9 → 4 (16 < 23); lo=5 hi=9 → 7 (56 > 23); lo=5 hi=6 → 5 (23).
    target: [4, 7, 5],
  },
  {
    id: 'demo-cidr',
    widget: 'cidr',
    checker: 'exact',
    prompt_es: 'Un equipo tiene la dirección 192.168.10.77/26. ¿Cuál es su red, su dirección de difusión y cuántos hosts utilizables tiene?',
    prompt_en: 'A host has the address 192.168.10.77/26. What is its network, its broadcast address, and how many usable hosts does it have?',
    params: { ip: '192.168.10.77', prefix: 26 },
    // /26 → bloques de 64: 77 cae en 64–127; 2^6 − 2 = 62 hosts.
    target: { network: '192.168.10.64', broadcast: '192.168.10.127', hosts: 62 },
  },
  {
    id: 'demo-sql-join',
    widget: 'sqlJoin',
    checker: 'unordered',
    prompt_es: 'Marca las filas que devuelve la consulta.',
    prompt_en: 'Mark the rows the query returns.',
    params: {
      kind: 'LEFT',
      left: { name: 'alumnos', columns: ['id', 'nombre'], rows: [[1, 'Ana'], [2, 'Luis'], [3, 'Eva']] },
      right: { name: 'matriculas', columns: ['alumno_id', 'curso'], rows: [[1, 'SQL'], [1, 'Python'], [3, 'Redes']] },
      on: ['id', 'alumno_id'],
    },
    // Ana sale dos veces (dos matrículas), Luis con NULL (LEFT JOIN), Eva una vez.
    target: [
      [1, 'Ana', 1, 'SQL'],
      [1, 'Ana', 1, 'Python'],
      [2, 'Luis', null, null],
      [3, 'Eva', 3, 'Redes'],
    ],
  },
];
