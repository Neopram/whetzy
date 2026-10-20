/**
 * 46.1 (docs/PLAN_UI_AVANZADA.md §2 y §6.2): el acierto no tapa el código.
 * - La animación de Lottie va dentro de la tarjeta de respuesta (antes era un
 *   overlay fijo de 160 px a pantalla completa) y, con movimiento reducido,
 *   el Player ni se monta.
 * - El combo lleva un anillo hacia el próximo multiplicador del servidor y
 *   «×3» aparece al 7.º acierto seguido.
 * - Sonido y vibración salen por `lib/feedbackFx` (un evento por nivel).
 * - El «+XP» sale junto al marcador, no en un toast sobre la barra.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import i18n from '../i18n';
import { QuizScreen } from '../pages/QuizScreen';
import { multiplierFor, ringProgress } from '../components/quiz/ComboRing';
import { useAppStore } from '../stores/useAppStore';
import { quiz as quizApi, type QuestionPublic } from '../services/api';
import * as fx from '../lib/feedbackFx';
import * as toast from '../components/common/Toast';

const motionPrefs = vi.hoisted(() => ({ reduce: false }));

vi.mock('framer-motion', async (importOriginal) => {
  const actual = await importOriginal<typeof import('framer-motion')>();
  return { ...actual, useReducedMotion: () => motionPrefs.reduce };
});
vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, quiz: { ...actual.quiz, start: vi.fn(), answer: vi.fn(), end: vi.fn() } };
});
vi.mock('@lottiefiles/react-lottie-player', () => ({
  Player: ({ src }: { src: string }) => <i data-testid="lottie" data-src={src} />,
}));

const start = quizApi.start as unknown as ReturnType<typeof vi.fn>;
const answer = quizApi.answer as unknown as ReturnType<typeof vi.fn>;

const Q = {
  id: 'q1', skill_id: 'sk1', type: 'mcq', difficulty_tier: 'easy',
  question_es: '¿Cuánto es 1 + 1?', question_en: 'What is 1 + 1?',
  options_es: ['1', '2', '3', '4'], options_en: ['1', '2', '3', '4'],
  correct_answer_es: null, correct_answer_en: null, code_es: null, code_en: null,
} as unknown as QuestionPublic;

const res = (over: Record<string, unknown> = {}) => ({
  correct: true, correct_index: 1, explanation_es: 'Uno más uno es dos.', explanation_en: 'One plus one is two.',
  source: null, grade: 3, xp_earned: 10, combo: 1, user_elo: 1500, next_review: null,
  skill_mastery: { sk1: 0.45 }, session_accuracy: 1, next_question: Q, next_selection_reason: null,
  ...over,
});

let emit: ReturnType<typeof vi.spyOn>;
let emitMany: ReturnType<typeof vi.spyOn>;
let toastSpy: ReturnType<typeof vi.spyOn>;

beforeEach(async () => {
  vi.clearAllMocks();
  motionPrefs.reduce = false;
  await i18n.changeLanguage('es');
  useAppStore.getState().startQuiz('study', 10);
  start.mockResolvedValue({ session_id: 's1', question: Q, selection_reason: null });
  emit = vi.spyOn(fx, 'emit');
  emitMany = vi.spyOn(fx, 'emitMany');
  toastSpy = vi.spyOn(toast, 'showToast');
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

async function responder(r: Record<string, unknown>) {
  answer.mockResolvedValueOnce(res(r));
  render(<QuizScreen />);
  await screen.findByText('¿Cuánto es 1 + 1?');
  await act(async () => {});
  fireEvent.keyDown(window, { key: '2' });
  await screen.findByText('Uno más uno es dos.');
}

describe('ComboRing — umbrales del servidor', () => {
  it('multiplicador y avance del anillo hacia 3, 7 y 15', () => {
    expect([0, 2, 3, 6, 7, 14, 15, 30].map(multiplierFor)).toEqual([1, 1, 2, 2, 3, 3, 5, 5]);
    expect(ringProgress(0)).toBe(0);
    expect(ringProgress(3)).toBe(0);
    expect(ringProgress(5)).toBe(0.5);
    expect(ringProgress(15)).toBe(1);
  });
});

describe('QuizScreen — respuesta sin tapar (46.1)', () => {
  it('la animación va dentro de la tarjeta de respuesta', async () => {
    await responder({});
    const anim = screen.getByTestId('lottie');
    expect(anim.closest('[class*="explanationOk"]')).toHaveTextContent('Uno más uno es dos.');
  });

  it('con movimiento reducido no se monta el Player', async () => {
    motionPrefs.reduce = true;
    await responder({});
    expect(screen.queryByTestId('lottie')).toBeNull();
  });

  it('al 7.º acierto seguido aparece «×3» y suena el combo ×3', async () => {
    await responder({ combo: 7 });
    expect(within(screen.getByTestId('combo')).getByText('×3')).toBeInTheDocument();
    expect(emitMany).toHaveBeenCalledWith([{ type: 'correct' }, { type: 'combo', value: 3 }]);
  });

  it('un acierto sin cruzar umbral suena como acierto, y el +XP va junto al marcador', async () => {
    await responder({ combo: 2 });
    expect(emit).toHaveBeenCalledWith({ type: 'correct' });
    expect(emitMany).not.toHaveBeenCalled();
    // 46.10: llega al marcador tras salir de la tarjeta (XP_FLIGHT.departMs).
    expect(await screen.findByRole('status')).toHaveTextContent('+10 XP');
    expect(toastSpy).not.toHaveBeenCalledWith(expect.stringContaining('XP'), 'success');
  });

  it('un fallo suena como fallo', async () => {
    await responder({ correct: false, combo: 0, xp_earned: 3 });
    await waitFor(() => expect(emit).toHaveBeenCalledWith({ type: 'wrong' }));
  });
});

