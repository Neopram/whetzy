/**
 * Primer «ESTUDIAR AHORA» de una cuenta nueva (32.4): el backend responde sin
 * pregunta y con `pool: "needs_lesson"`. La pantalla decía «Sin preguntas
 * disponibles» con un 🤔, como si la app estuviera vacía, cuando lo que falta es
 * abrir la primera lección. Visto recorriendo el alta de un alumno (2026-10-01).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { QuizScreen } from '../pages/QuizScreen';
import { useAppStore } from '../stores/useAppStore';
import { quiz as quizApi } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, quiz: { ...actual.quiz, start: vi.fn() } };
});
vi.mock('@lottiefiles/react-lottie-player', () => ({ Player: () => null }));

const start = quizApi.start as unknown as ReturnType<typeof vi.fn>;

function sinPregunta(pool: string) {
  start.mockResolvedValue({
    session_id: 's1',
    question: null,
    selection_reason: { pool, skill_strategy: null, difficulty_target: 0.7, expected_p: null },
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  useAppStore.getState().startQuiz('study', 10);
});
afterEach(async () => {
  cleanup();
  await i18n.changeLanguage('es');
});

describe('QuizScreen — falta ver la lección (needs_lesson)', () => {
  it.each([
    ['es', 'Empieza por la lección', 'Sin preguntas disponibles'],
    ['en', 'Start with the lesson', 'No questions available'],
  ])('%s: titula por lo que falta, no «sin preguntas»', async (lang, titulo, viejo) => {
    await i18n.changeLanguage(lang);
    sinPregunta('needs_lesson');

    render(<QuizScreen />);

    expect(await screen.findByRole('heading', { name: titulo })).toBeInTheDocument();
    expect(screen.queryByText(viejo)).not.toBeInTheDocument();
  });

  it('un banco vacío de verdad sigue diciendo «Sin preguntas disponibles»', async () => {
    sinPregunta('no_skills');

    render(<QuizScreen />);

    expect(await screen.findByRole('heading', { name: 'Sin preguntas disponibles' })).toBeInTheDocument();
  });
});
