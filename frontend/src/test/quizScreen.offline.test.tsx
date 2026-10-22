/**
 * 42.11: una respuesta que no llega al servidor se guarda en la cola offline.
 *
 * QuizScreen solo encolaba con `!navigator.onLine` o un `TypeError`, pero
 * `request()` (services/api.ts) convierte el fallo de `fetch` en
 * `ApiError('Network error', null)`: con el wifi «conectado» y la red caída de
 * verdad, o un 502 durante un deploy, la respuesta se perdía.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { QuizScreen } from '../pages/QuizScreen';
import { useAppStore } from '../stores/useAppStore';
import { ApiError, quiz as quizApi, type QuestionPublic } from '../services/api';
import { enqueue } from '../services/offlineQueue';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, quiz: { ...actual.quiz, start: vi.fn(), answer: vi.fn(), end: vi.fn() } };
});
vi.mock('../services/offlineQueue', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/offlineQueue')>();
  return { ...actual, enqueue: vi.fn().mockResolvedValue(undefined) };
});
vi.mock('@lottiefiles/react-lottie-player', () => ({ Player: () => null }));

const start = quizApi.start as unknown as ReturnType<typeof vi.fn>;
const answer = quizApi.answer as unknown as ReturnType<typeof vi.fn>;
const queued = enqueue as unknown as ReturnType<typeof vi.fn>;

const Q = {
  id: 'q1', skill_id: 'sk1', type: 'mcq', difficulty_tier: 'easy',
  question_es: '¿Cuánto es 1 + 1?', question_en: 'What is 1 + 1?',
  options_es: ['1', '2', '3', '4'], options_en: ['1', '2', '3', '4'],
  correct_answer_es: null, correct_answer_en: null, code_es: null, code_en: null,
} as unknown as QuestionPublic;

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
  useAppStore.getState().startQuiz('study', 10);
  useAppStore.setState({ hydrateFromApi: vi.fn().mockResolvedValue(undefined) });
  start.mockResolvedValue({ session_id: 's1', question: Q, selection_reason: null });
});
afterEach(() => cleanup());

async function answerWith(error: unknown) {
  answer.mockRejectedValue(error);
  render(<QuizScreen />);
  await screen.findByText('¿Cuánto es 1 + 1?');
  await act(async () => { fireEvent.keyDown(window, { key: '2' }); });
  await act(async () => {});
}

describe('QuizScreen — respuestas sin red (42.11)', () => {
  it('con el navegador «en línea» y la red caída, la respuesta se encola', async () => {
    await answerWith(new ApiError('Network error', null));
    expect(queued).toHaveBeenCalledTimes(1);
    expect(queued.mock.calls[0][0]).toMatchObject({ sessionId: 's1', questionId: 'q1', selectedIndex: 1 });
  });

  it('un 502 (deploy en curso) también se encola', async () => {
    await answerWith(new ApiError('Bad Gateway', 502));
    expect(queued).toHaveBeenCalledTimes(1);
  });

  it('un 4xx no se encola: reintentarlo no lo arregla', async () => {
    await answerWith(new ApiError('Unprocessable', 422));
    expect(queued).not.toHaveBeenCalled();
  });
});
