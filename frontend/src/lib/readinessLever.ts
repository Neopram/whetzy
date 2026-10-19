import type { DomainReadiness } from '../services/api';

// El mismo umbral que usa el backend para marcar un dominio «listo»
// (exams.py, READY_THRESHOLD). Solo ordena la palanca: no se enseña (ADR-60).
export const READY_THRESHOLD = 0.75;

/** El dominio que más acerca al aprobado: peso × lo que le falta hasta el
 *  umbral. Un dominio pesado a medias gana a uno ligero a cero. Lo usan
 *  Preparación y Hoy (46.3c), así que las dos dicen la misma palanca. */
export function biggestLever(domains: DomainReadiness[]): DomainReadiness | undefined {
  return [...domains]
    .filter((d) => !d.ready)
    .sort((a, b) => b.weight_pct * (READY_THRESHOLD - (b.p_known_mean ?? 0)) - a.weight_pct * (READY_THRESHOLD - (a.p_known_mean ?? 0)))[0];
}
