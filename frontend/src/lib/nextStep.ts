import type { CurriculumResponse, CurriculumSkill } from '../services/api';

/** 43.5 (ADR-65 D7, H.60): se puede practicar si la lección está vista o si el
 *  módulo se desbloqueó por test-out o por ventaja en la prueba de nivel. */
export function canPractice(s: CurriculumSkill): boolean {
  return s.lesson_seen || s.practice_unlocked === true;
}

/** La siguiente lección pendiente de la ruta: la primera skill, por orden de
 *  módulo y de skill, de un módulo no bloqueado, que no se pueda practicar
 *  todavía. null si no queda ninguna: entonces toca practicar. */
export function nextLessonSkillId(cur: CurriculumResponse): string | null {
  for (const mod of [...cur.modules].sort((a, b) => a.order - b.order)) {
    if (mod.status === 'locked') continue;
    const pending = [...mod.skills].sort((a, b) => a.order - b.order).find((s) => !canPractice(s));
    if (pending) return pending.skill_id;
  }
  return null;
}
