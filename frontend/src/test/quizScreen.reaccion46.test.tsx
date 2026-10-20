/**
 * 46.10 (docs/PLAN_UI_AVANZADA.md §7.3): la opción reacciona a la respuesta.
 * La correcta late, la elegida mal tiembla y «No lo sé» no castiga a nadie.
 * El «+XP» nace en la tarjeta y aterriza en el marcador.
 * Con movimiento reducido no hay pulso, ni sacudida, ni vuelo: el «+XP» sale
 * directamente en el marcador.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import i18n from '../i18n';
import { QuizScreen } from '../pages/QuizScreen';
import { useAppStore } from '../stores/useAppStore';
import { quiz as quizApi, type QuestionPublic } from '../services/api';

let reduce = false;
vi.mock('framer-motion', async (importOriginal) => {
  const actual = await importOriginal<typeof import('framer-motion')>();
  return { ...actual, useReducedMotion: () => reduce };
});
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

function res(correct: boolean, xp: number) {
  return {
    correct, correct_index: 1, explanation_es: 'Dos.', explanation_en: 'Two.',
    source: null, grade: 3, xp_earned: xp, combo: correct ? 1 : 0, user_elo: 1500, next_review: null,
    skill_mastery: { sk1: 0.4 }, session_accuracy: 1, next_question: null, next_selection_reason: null, events: [],
  };
}

const option = (label: string) => screen.getAllByRole('button').find((b) => b.textContent?.startsWith(label))!;

async function open() {
  render(<QuizScreen />);
  await screen.findByText('¿Cuánto es 1 + 1?');
  await act(async () => {});
}

beforeEach(async () => {
  vi.clearAllMocks();
  reduce = false;
  await i18n.changeLanguage('es');
  useAppStore.getState().startQuiz('study', 10);
  useAppStore.setState({ hydrateFromApi: vi.fn().mockResolvedValue(undefined) });
  start.mockResolvedValue({ session_id: 's1', question: Q, selection_reason: null });
});
afterEach(() => cleanup());

describe('QuizScreen — la opción reacciona (46.10)', () => {
  it('acierto: la correcta late y el «+XP» vuela de la tarjeta al marcador', async () => {
    answer.mockResolvedValue(res(true, 12));
    await open();
    fireEvent.keyDown(window, { key: '2' });
    await screen.findByText('Dos.');
    expect(option('B')).toHaveAttribute('data-fx', 'pulse');
    expect(option('A')).not.toHaveAttribute('data-fx');
    // Nace en la tarjeta…
    expect(within(screen.getByTestId('feedback-panel')).getByText('+12 XP')).toBeInTheDocument();
    // …y aterriza en el marcador.
    await waitFor(() => expect(within(screen.getByTestId('xp-badge')).getByText('+12 XP')).toBeInTheDocument());
    expect(within(screen.getByTestId('feedback-panel')).queryByText('+12 XP')).toBeNull();
  });

  it('fallo: la elegida tiembla y la correcta late para que se vea cuál era', async () => {
    answer.mockResolvedValue(res(false, 0));
    await open();
    fireEvent.keyDown(window, { key: '1' });
    await screen.findByText('Dos.');
    expect(option('A')).toHaveAttribute('data-fx', 'shake');
    expect(option('B')).toHaveAttribute('data-fx', 'pulse');
  });

  it('«No lo sé»: nada tiembla ni late', async () => {
    answer.mockResolvedValue(res(false, 0));
    await open();
    fireEvent.click(screen.getAllByRole('button', { name: 'No lo sé' })[0]);
    await screen.findByText('Dos.');
    for (const l of ['A', 'B', 'C', 'D']) expect(option(l)).not.toHaveAttribute('data-fx');
  });

  it('con movimiento reducido: sin pulso ni vuelo; el «+XP» sale ya en el marcador', async () => {
    reduce = true;
    answer.mockResolvedValue(res(true, 12));
    await open();
    fireEvent.keyDown(window, { key: '2' });
    await screen.findByText('Dos.');
    expect(option('B')).not.toHaveAttribute('data-fx');
    expect(within(screen.getByTestId('xp-badge')).getByText('+12 XP')).toBeInTheDocument();
    expect(within(screen.getByTestId('feedback-panel')).queryByText('+12 XP')).toBeNull();
  });
});
