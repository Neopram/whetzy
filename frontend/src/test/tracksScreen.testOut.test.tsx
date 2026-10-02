/**
 * O1.4: saltar un módulo con una prueba (17.2). El backend y TrackExamScreen
 * tenían el test-out desde la 17.2 y ningún botón lo abría. Se ofrece en los
 * módulos disponibles, solo si el backend puede montar la prueba, y con las
 * cifras que da el propio backend.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { TracksScreen } from '../pages/TracksScreen';
import { useAppStore } from '../stores/useAppStore';
import { content as contentApi, exams as examsApi, progress as progressApi } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    content: { tracks: vi.fn() },
    exams: { ...actual.exams, trackBlueprint: vi.fn(), testOutBlueprint: vi.fn() },
    progress: { ...actual.progress, curriculum: vi.fn() },
  };
});

const tracks = contentApi.tracks as unknown as ReturnType<typeof vi.fn>;
const trackBlueprint = examsApi.trackBlueprint as unknown as ReturnType<typeof vi.fn>;
const testOutBlueprint = examsApi.testOutBlueprint as unknown as ReturnType<typeof vi.fn>;
const curriculum = progressApi.curriculum as unknown as ReturnType<typeof vi.fn>;

const TRACK = {
  id: 'track01', name_es: 'Python', name_en: 'Python', order: 1, icon: '🐍', color: '#000',
  total_questions: 10, is_certification: false, cert_provider: null,
  exam_question_count: null, exam_duration_minutes: null,
};

function curriculumWith(status: 'available' | 'completed' | 'locked') {
  return {
    track_id: 'track01', name_es: 'Python', name_en: 'Python', icon: '🐍', color: '#000',
    mastery_threshold: 0.95,
    modules: [{
      id: 'm01', name_es: 'M1', name_en: 'M1', order: 0,
      description_es: '', description_en: '', min_mastery_to_unlock: 0.7,
      level: 1, average_mastery: status === 'completed' ? 0.8 : 0, status,
      prerequisite_id: null, prerequisite_met: status !== 'locked',
      skills: [{ skill_id: 'sk1', name_es: 'sk1', name_en: 'sk1', order: 1, p_known: 0, mastered: false, attempts: 0, lesson_seen: true }],
    }],
  };
}

const BP = { module_id: 'm01', skills: 4, questions: 8, duration_minutes: 15, pass_pct: 70, available: true };

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
  tracks.mockResolvedValue([TRACK]);
  trackBlueprint.mockRejectedValue(new Error('sin blueprint en este test'));
  useAppStore.setState({ trackExamTargetId: null });
});
afterEach(cleanup);

async function openModule() {
  render(<TracksScreen />);
  fireEvent.click(await screen.findByRole('button', { expanded: false }));
}

describe('TracksScreen — saltar un módulo (O1.4)', () => {
  it('módulo disponible: ofrece la prueba con las cifras del backend y la abre', async () => {
    curriculum.mockResolvedValue(curriculumWith('available'));
    testOutBlueprint.mockResolvedValue(BP);
    await openModule();

    const offer = await screen.findByRole('button', { name: /salta este módulo/i });
    expect(offer).toHaveTextContent('8 preguntas · 15 minutos · se aprueba con 70 %');
    expect(testOutBlueprint).toHaveBeenCalledWith('m01');
    fireEvent.click(offer);
    const s = useAppStore.getState();
    expect([s.trackExamKind, s.trackExamTargetId, s.trackExamQuestionCount, s.trackExamDurationMinutes, s.trackExamPassPct])
      .toEqual(['test_out', 'm01', 8, 15, 70]);
  });

  it('sin preguntas suficientes para montarla, no hay botón', async () => {
    curriculum.mockResolvedValue(curriculumWith('available'));
    testOutBlueprint.mockResolvedValue({ ...BP, available: false });
    await openModule();
    await vi.waitFor(() => expect(testOutBlueprint).toHaveBeenCalled());
    await screen.findByRole('button', { name: /practicar/i });
    expect(screen.queryByRole('button', { name: /salta este módulo/i })).toBeNull();
  });

  it.each(['completed', 'locked'] as const)('módulo %s: no se ofrece', async (status) => {
    curriculum.mockResolvedValue(curriculumWith(status));
    testOutBlueprint.mockResolvedValue(BP);
    await openModule();
    await screen.findByText('sk1');
    expect(testOutBlueprint).not.toHaveBeenCalled();
    expect(screen.queryByRole('button', { name: /salta este módulo/i })).toBeNull();
  });
});
