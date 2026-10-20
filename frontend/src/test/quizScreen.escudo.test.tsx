/**
 * 46.11: cuando el servidor gasta un comodín en una respuesta
 * (`streak_freeze_used`), el quiz levanta el escudo de la TopBar. Sin ese
 * evento, nada: el cliente no lo deduce de los saldos.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { QuizScreen } from '../pages/QuizScreen';
import { useAppStore } from '../stores/useAppStore';
import { quiz as quizApi, type QuestionPublic } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, quiz: { ...actual.quiz, start: vi.fn(), answer: vi.fn(), end: vi.fn() } };
});
vi.mock('@lottiefiles/react-lottie-player', () => ({ Player: () => null }));

const start = quizApi.start as unknown as ReturnType<typeof vi.fn>;
const answer = quizApi.answer as unknown as ReturnType<typeof vi.fn>;

const Q = {
  id: 'q1', skill_id: 'sk1', type: 'mcq', difficulty_tier: 'easy',
  question_es: '¿Cuánto es 1 + 1?', question_en: 'What is 1 + 1?',
  options_es: ['1', '2', '3', '4'], options_en: ['1', '2', '3', '4'],
  correct_answer_es: null, correct_answer_en: null, code_es: null, code_en: null,
} as unknown as QuestionPublic;

async function responder(events: unknown[]) {
  answer.mockResolvedValue({
    correct: true, correct_index: 1, explanation_es: 'Dos.', explanation_en: 'Two.',
    source: null, grade: 3, xp_earned: 10, combo: 1, user_elo: 1500, next_review: null,
    skill_mastery: { sk1: 0.4 }, session_accuracy: 1, next_question: null, next_selection_reason: null, events,
  });
  render(<QuizScreen />);
  await screen.findByText('¿Cuánto es 1 + 1?');
  await act(async () => {});
  fireEvent.keyDown(window, { key: '2' });
  await screen.findByText('Dos.');
}

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
  useAppStore.getState().startQuiz('study', 10);
  useAppStore.setState({ hydrateFromApi: vi.fn().mockResolvedValue(undefined), streakShieldAt: null });
  start.mockResolvedValue({ session_id: 's1', question: Q, selection_reason: null });
});
afterEach(cleanup);

describe('QuizScreen — escudo del comodín (46.11)', () => {
  it('streak_freeze_used del servidor → escudo', async () => {
    await responder([{ type: 'streak_freeze_used', payload: { days: 10 } }]);
    expect(useAppStore.getState().streakShieldAt).not.toBeNull();
  });

  it('sin el evento, no hay escudo', async () => {
    await responder([]);
    expect(useAppStore.getState().streakShieldAt).toBeNull();
  });
});
