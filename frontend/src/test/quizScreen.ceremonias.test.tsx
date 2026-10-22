/**
 * 46.7: al cerrar la sesión, los hitos de nivel 4 que dio el servidor salen
 * como UNA ceremonia y el resto como tarjetas del resumen; sin hitos, solo
 * suena el cierre de sesión (nivel 3).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { QuizScreen } from '../pages/QuizScreen';
import { useAppStore } from '../stores/useAppStore';
import { quiz as quizApi, progress as progressApi, gamification, type QuestionPublic } from '../services/api';
import * as fx from '../lib/feedbackFx';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    quiz: { ...actual.quiz, start: vi.fn(), answer: vi.fn(), end: vi.fn() },
    progress: { ...actual.progress, skills: vi.fn() },
    gamification: { ...actual.gamification, badges: vi.fn() },
  };
});
vi.mock('@lottiefiles/react-lottie-player', () => ({ Player: () => null }));

const start = quizApi.start as unknown as ReturnType<typeof vi.fn>;
const answer = quizApi.answer as unknown as ReturnType<typeof vi.fn>;
const end = quizApi.end as unknown as ReturnType<typeof vi.fn>;
const skills = progressApi.skills as unknown as ReturnType<typeof vi.fn>;
const badges = gamification.badges as unknown as ReturnType<typeof vi.fn>;

const Q = {
  id: 'q1', skill_id: 'sk1', type: 'mcq', difficulty_tier: 'easy',
  question_es: '¿Cuánto es 1 + 1?', question_en: 'What is 1 + 1?',
  options_es: ['1', '2', '3', '4'], options_en: ['1', '2', '3', '4'],
  correct_answer_es: null, correct_answer_en: null, code_es: null, code_en: null,
} as unknown as QuestionPublic;

let emit: ReturnType<typeof vi.spyOn>;

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
  useAppStore.getState().startQuiz('study', 10);
  useAppStore.setState({ hydrateFromApi: vi.fn().mockResolvedValue(undefined) });
  start.mockResolvedValue({ session_id: 's1', question: Q, selection_reason: null });
  end.mockResolvedValue({ total_questions: 1, correct: 1, accuracy: 1, max_combo: 1, xp_earned: 10, duration_seconds: 5 });
  skills.mockResolvedValue([]);
  badges.mockResolvedValue([{ badge: { id: 'b1', name_es: 'Constante', name_en: 'Steady', icon: '', description_es: '', description_en: '', criteria_type: 'streak', criteria_value: 3 }, earned_at: '' }]);
  emit = vi.spyOn(fx, 'emit');
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

async function sesionDeUna(events: unknown[]) {
  answer.mockResolvedValue({
    correct: true, correct_index: 1, explanation_es: 'Dos.', explanation_en: 'Two.',
    source: null, grade: 3, xp_earned: 10, combo: 1, user_elo: 1500, next_review: null,
    skill_mastery: { sk1: 0.4 }, session_accuracy: 1, next_question: null, next_selection_reason: null,
    events,
  });
  render(<QuizScreen />);
  await screen.findByText('¿Cuánto es 1 + 1?');
  await act(async () => {});
  fireEvent.keyDown(window, { key: '2' });
  await screen.findByText('Dos.');
  fireEvent.keyDown(window, { key: 'Enter' });
}

describe('QuizScreen — ceremonias al cerrar (46.7)', () => {
  it('nivel e insignia en la misma sesión: una ceremonia (nivel) y una tarjeta (insignia)', async () => {
    await sesionDeUna([
      { type: 'badge_earned', payload: { badge_id: 'b1' } },
      { type: 'level_up', payload: { level_before: 1, level: 2 } },
    ]);
    expect(await screen.findByRole('dialog', { name: '¡Subes a nivel 2!' })).toBeInTheDocument();
    expect(screen.getAllByRole('dialog')).toHaveLength(1);
    await waitFor(() =>
      expect(screen.getByRole('region', { name: 'También en esta sesión' })).toHaveTextContent('Nueva insignia: Constante'),
    );
    expect(emit).toHaveBeenCalledWith({ type: 'level_up' });
    expect(emit).not.toHaveBeenCalledWith(expect.objectContaining({ type: 'session_end' }));
    fireEvent.click(screen.getByRole('button', { name: 'Saltar' }));
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('sin hitos de nivel 4: sin ceremonia, suena el cierre de sesión', async () => {
    await sesionDeUna([{ type: 'combo_multiplier', payload: { multiplier: 2 } }]);
    // Espera opcional: si el resumen no sale, no se espera el plazo global de 5 s.
    await screen.findByText('Habilidades de esta sesión', {}, { timeout: 1000 }).catch(() => null);
    // 46.7b: el cierre lleva la nota de la sesión (1/1 → S).
    await waitFor(() => expect(emit).toHaveBeenCalledWith({ type: 'session_end', value: fx.GRADE_RANK.S }));
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(screen.queryByRole('region', { name: 'También en esta sesión' })).toBeNull();
  });
});
