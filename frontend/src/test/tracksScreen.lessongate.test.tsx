/**
 * 32.4: la lección bloquea el quiz. `TracksScreen` deshabilita "Practicar"
 * en un módulo hasta que al menos una de sus lecciones esté vista
 * (`CurriculumSkill.lesson_seen`) -- el backend igual lo exige en
 * `/quiz/start`, pero un botón que siempre lleva a un 200 vacío es peor
 * experiencia que uno deshabilitado con la razón.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import '../i18n';
import { TracksScreen } from '../pages/TracksScreen';
import { content as contentApi, exams as examsApi, progress as progressApi } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    content: { tracks: vi.fn() },
    exams: { ...actual.exams, trackBlueprint: vi.fn() },
    progress: { ...actual.progress, curriculum: vi.fn() },
  };
});

const tracks = contentApi.tracks as unknown as ReturnType<typeof vi.fn>;
const trackBlueprint = examsApi.trackBlueprint as unknown as ReturnType<typeof vi.fn>;
const curriculum = progressApi.curriculum as unknown as ReturnType<typeof vi.fn>;

const TRACK = {
  id: 'track01', name_es: 'Python', name_en: 'Python', order: 1, icon: '🐍', color: '#000',
  total_questions: 10, is_certification: false, cert_provider: null,
  exam_question_count: null, exam_duration_minutes: null,
};

function skill(id: string, lesson_seen: boolean) {
  return {
    skill_id: id, name_es: id, name_en: id, order: 1,
    p_known: 0, mastered: false, attempts: 0, lesson_seen,
  };
}

function curriculumWith(skills: ReturnType<typeof skill>[]) {
  return {
    track_id: 'track01', name_es: 'Python', name_en: 'Python', icon: '🐍', color: '#000',
    mastery_threshold: 0.95,
    modules: [{
      id: 'm01', name_es: 'M1', name_en: 'M1', order: 0,
      description_es: '', description_en: '', min_mastery_to_unlock: 0.7,
      level: 1, average_mastery: 0, status: 'available' as const,
      prerequisite_id: null, prerequisite_met: true, skills,
    }],
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  tracks.mockResolvedValue([TRACK]);
  trackBlueprint.mockRejectedValue(new Error('no blueprint in this test'));
});
afterEach(cleanup);

async function openModule() {
  render(<TracksScreen />);
  const header = await screen.findByRole('button', { expanded: false });
  header.click();
}

describe('TracksScreen — bloqueo de quiz sin lección (32.4)', () => {
  it('deshabilita Practicar cuando ningún skill del módulo tiene lección vista', async () => {
    curriculum.mockResolvedValue(curriculumWith([skill('sk1', false), skill('sk2', false)]));
    await openModule();

    const practicar = await screen.findByRole('button', { name: /practicar|practice/i });
    expect(practicar).toBeDisabled();
    expect(screen.getByText(/abre la lección|open this module's lesson/i)).toBeInTheDocument();
  });

  it('habilita Practicar en cuanto un skill del módulo tiene lección vista', async () => {
    curriculum.mockResolvedValue(curriculumWith([skill('sk1', true), skill('sk2', false)]));
    await openModule();

    const practicar = await screen.findByRole('button', { name: /practicar|practice/i });
    await waitFor(() => expect(practicar).not.toBeDisabled());
    expect(screen.queryByText(/abre la lección|open this module's lesson/i)).not.toBeInTheDocument();
  });
});
