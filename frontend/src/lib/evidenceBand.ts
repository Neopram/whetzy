// ADR-60 (UX-DEC-01) y D-17 del dueño (2026-10-12): mientras el modelo no esté
// calibrado, la interfaz no enseña «Knowledge 84 %». Enseña un estado
// cualitativo con la evidencia observable que lo sostiene (respuestas y
// aciertos); los umbrales se quedan aquí, internos.

export type EvidenceBand = 'strong' | 'developing' | 'insufficient';

/** ADR-60: «Evidencia insuficiente» por debajo de 7 respuestas. */
export const MIN_EVIDENCE_ANSWERS = 7;

/** Una skill es «Fuerte» cuando el motor la da por dominada (BKT ≥ 0,95). */
const STRONG_P_KNOWN = 0.95;

export function bandForSkill(s: { attempts: number; p_known: number }): EvidenceBand {
  if (s.attempts < MIN_EVIDENCE_ANSWERS) return 'insufficient';
  return s.p_known >= STRONG_P_KNOWN ? 'strong' : 'developing';
}

/** Un dominio del examen: el backend ya decide `ready`; aquí solo se exige evidencia. */
export function bandForDomain(d: { answers?: number; ready: boolean }): EvidenceBand {
  if ((d.answers ?? 0) < MIN_EVIDENCE_ANSWERS) return 'insufficient';
  return d.ready ? 'strong' : 'developing';
}

/** Varias piezas a la vez: «Fuerte» solo si todas lo son; sin evidencia en
 *  ninguna, insuficiente; cualquier mezcla, en desarrollo. */
export function overallBand(bands: EvidenceBand[]): EvidenceBand {
  if (bands.every((b) => b === 'insufficient')) return 'insufficient';
  if (bands.every((b) => b === 'strong')) return 'strong';
  return 'developing';
}

/** Para un examen hace falta evidencia en cada dominio: uno sin ella basta para decirlo. */
export function examBand(bands: EvidenceBand[]): EvidenceBand {
  if (bands.length === 0 || bands.some((b) => b === 'insufficient')) return 'insufficient';
  return bands.every((b) => b === 'strong') ? 'strong' : 'developing';
}
