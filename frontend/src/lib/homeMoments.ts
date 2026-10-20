/**
 * Momentos de Hoy (46.3b, docs/PLAN_UI_AVANZADA.md §6.2): qué ha cambiado
 * desde la última vez que se abrió la pantalla, para celebrarlo una vez.
 *
 * Se guarda una foto por usuario en localStorage: las misiones del día (clave
 * con la fecha, porque cada día son otras) y la banda de cada skill (sin
 * fecha, porque subir de banda puede pasar en cualquier sesión). Sin foto
 * previa no se celebra nada: no se inventa un logro el primer día ni tras
 * borrar los datos del navegador. «Evidencia insuficiente» es la banda más
 * baja, así que llegar a ella nunca cuenta como subida.
 */
import type { EvidenceBand } from './evidenceBand';

const RANK: Record<EvidenceBand, number> = { insufficient: 0, developing: 1, strong: 2 };

export interface HomeMoments {
  missionsDone: string[];
  skillsUp: string[];
}

const missionsKey = (userId: string, day: string) => `whetzy_fx_missions_${userId}_${day}`;
const bandsKey = (userId: string) => `whetzy_fx_bands_${userId}`;

function read<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

function write(key: string, value: unknown): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch { /* modo privado: sin foto no hay momentos, y no pasa nada */ }
}

/** Misiones que están completas ahora y no lo estaban en la foto de hoy. */
export function missionMoments(
  userId: string,
  day: string,
  missions: { id: string; completed: boolean }[],
): string[] {
  const before = read<Record<string, boolean>>(missionsKey(userId, day));
  write(missionsKey(userId, day), Object.fromEntries(missions.map((m) => [m.id, m.completed])));
  if (!before) return [];
  return missions.filter((m) => m.completed && before[m.id] === false).map((m) => m.id);
}

/** Skills que han subido de banda desde la última foto. */
export function bandMoments(
  userId: string,
  skills: { id: string; band: EvidenceBand }[],
): string[] {
  const before = read<Record<string, EvidenceBand>>(bandsKey(userId));
  write(bandsKey(userId), { ...before, ...Object.fromEntries(skills.map((s) => [s.id, s.band])) });
  if (!before) return [];
  return skills.filter((s) => s.id in before && RANK[s.band] > RANK[before[s.id]]).map((s) => s.id);
}

/**
 * 46.15 D: insignias ganadas desde la última visita a Perfil. Como en las
 * bandas, sin foto previa no se celebra nada.
 */
export function badgeMoments(userId: string, earned: string[]): string[] {
  const key = `whetzy_fx_badges_${userId}`;
  const before = read<string[]>(key);
  write(key, earned);
  if (!before) return [];
  const seen = new Set(before);
  return earned.filter((id) => !seen.has(id));
}
