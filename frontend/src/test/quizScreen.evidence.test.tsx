/**
 * El servidor corrige; el cliente solo aporta la prueba (2026-10-01).
 *
 * Hasta hoy la web mandaba `selected_index: 1` y nada más, y el servidor se lo
 * creía: cualquier ejecutable se daba por resuelto desde la API (producción,
 * q130103_fbe001). Ahora un ejecutable manda la salida que dio el código y un
 * `fill_blank` manda el texto escrito, que es lo que el servidor compara.
 *
 * Y `fill_blank` pinta su código: 11 preguntas del banco pedían adivinar qué
 * imprimía un código que la pantalla no enseñaba.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { QuizScreen } from '../pages/QuizScreen';
import { useAppStore } from '../stores/useAppStore';
import { quiz as quizApi } from '../services/api';

const runCode = vi.fn();

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, quiz: { ...actual.quiz, start: vi.fn(), answer: vi.fn() } };
});
vi.mock('../hooks/useRuntime', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../hooks/useRuntime')>();
  return { ...actual, useRuntime: () => ({ status: 'ready', runCode }) };
});
vi.mock('@lottiefiles/react-lottie-player', () => ({ Player: () => null }));

const start = quizApi.start as unknown as ReturnType<typeof vi.fn>;
const answer = quizApi.answer as unknown as ReturnType<typeof vi.fn>;

function serve(question: Record<string, unknown>) {
  start.mockResolvedValue({
    session_id: 's1',
    question: {
      skill_id: 'sk1',
      difficulty_tier: 'easy',
      options_es: null,
      options_en: null,
      explanation_es: '',
      explanation_en: '',
      ...question,
    },
    selection_reason: null,
  });
}

const FEEDBACK = {
  correct: true, correct_index: null, explanation_es: '', explanation_en: '', source: null, grade: 4,
  xp_earned: 10, combo: 1, user_elo: 1200, next_review: null, skill_mastery: {}, session_accuracy: 1,
  next_question: null, next_selection_reason: null,
};

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
  answer.mockResolvedValue(FEEDBACK);
  useAppStore.getState().startQuiz('study', 10);
});
afterEach(() => cleanup());

describe('QuizScreen — prueba que corrige el servidor', () => {
  it('fill_blank enseña el código y manda el texto escrito', async () => {
    serve({
      id: 'q_fb', type: 'fill_blank',
      question_es: '¿Qué imprime este código?\n```python\nprint(len("hola"))\n```',
      question_en: 'What does this code print?\n```python\nprint(len("hola"))\n```',
      correct_answer_es: '4', correct_answer_en: '4',
    });
    // Dentro de act: quiz.start resuelve en una microtarea y el efecto que
    // limpia la respuesta al cambiar de pregunta tiene que haber corrido antes
    // de teclear; si no, con carga, pisa lo escrito y el test falla al azar.
    await act(async () => { render(<QuizScreen />); });

    expect(await screen.findByText('print(len("hola"))')).toBeInTheDocument();
    fireEvent.change(screen.getByPlaceholderText(i18n.t('quiz.fillBlankPlaceholder')), { target: { value: '4' } });
    fireEvent.keyDown(screen.getByPlaceholderText(i18n.t('quiz.fillBlankPlaceholder')), { key: 'Enter' });

    await waitFor(() => expect(answer).toHaveBeenCalledTimes(1));
    expect(answer.mock.calls[0][6]).toEqual({ answerText: '4' });
  });

  it('un ejecutable manda la salida que dio el código', async () => {
    serve({
      id: 'q_ex', type: 'fill_blank_exec',
      question_es: 'Completa:\n```python\nx = ___\nprint(x + 1)\n```',
      question_en: 'Complete:\n```python\nx = ___\nprint(x + 1)\n```',
      correct_answer_es: '2', correct_answer_en: '2',
    });
    runCode.mockResolvedValue({ output: '2\n', error: null, timedOut: false });
    // Dentro de act: quiz.start resuelve en una microtarea y el efecto que
    // limpia la respuesta al cambiar de pregunta tiene que haber corrido antes
    // de teclear; si no, con carga, pisa lo escrito y el test falla al azar.
    await act(async () => { render(<QuizScreen />); });

    const input = await screen.findByPlaceholderText(i18n.t('quiz.fillBlankPlaceholder'));
    fireEvent.change(input, { target: { value: '1' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => expect(answer).toHaveBeenCalledTimes(1));
    expect(runCode).toHaveBeenCalledWith('x = 1\nprint(x + 1)', 5000);
    expect(answer.mock.calls[0][6]).toEqual({ execOutput: '2\n' });
  });
});
