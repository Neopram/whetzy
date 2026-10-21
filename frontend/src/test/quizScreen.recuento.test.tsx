/**
 * 46.7b (docs/PLAN_UI_AVANZADA.md §6.0 y §6.2): el resumen de sesión (nivel 3)
 * cuenta aciertos, precisión y XP hacia arriba, estampa la nota y deja saltar
 * desde el primer fotograma. Con movimiento reducido no hay recuento: los
 * números salen quietos. Si hay ceremonia, el recuento espera a que se cierre
 * (nunca dos celebraciones a la vez).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { QuizScreen } from '../pages/QuizScreen';
import { useAppStore } from '../stores/useAppStore';
import { quiz as quizApi, progress as progressApi, gamification, type QuestionPublic } from '../services/api';
import * as fx from '../lib/feedbackFx';
import * as fxAnalytics from '../lib/fxAnalytics';

const motionPrefs = vi.hoisted(() => ({ reduce: false }));
vi.mock('framer-motion', async (importOriginal) => {
  const actual = await importOriginal<typeof import('framer-motion')>();
  return { ...actual, useReducedMotion: () => motionPrefs.reduce };
});
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
let cancel: ReturnType<typeof vi.spyOn>;

beforeEach(async () => {
  vi.clearAllMocks();
  motionPrefs.reduce = false;
  await i18n.changeLanguage('es');
  useAppStore.getState().startQuiz('study', 10);
  useAppStore.setState({ hydrateFromApi: vi.fn().mockResolvedValue(undefined) });
  start.mockResolvedValue({ session_id: 's1', question: Q, selection_reason: null });
  end.mockResolvedValue({ total_questions: 10, correct: 7, accuracy: 0.7, max_combo: 4, xp_earned: 70, duration_seconds: 90 });
  skills.mockResolvedValue([]);
  badges.mockResolvedValue([]);
  emit = vi.spyOn(fx, 'emit');
  cancel = vi.spyOn(fx, 'cancelFx');
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

async function cerrarSesion(events: unknown[] = []) {
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
  await screen.findByTestId('summary-grade');
}

const visible = (id: string) => screen.getByTestId(id).querySelector('[aria-hidden="true"]')!.textContent;

describe('Resumen de sesión con recuento (46.7b)', () => {
  it('«Saltar recuento» está desde el primer fotograma y deja los números finales', async () => {
    await cerrarSesion();
    const skip = screen.getByRole('button', { name: 'Saltar recuento' });
    // Recién abierto, el recuento aún no ha llegado al final.
    expect(visible('count-xp')).not.toBe('70');
    fireEvent.click(skip);
    expect(visible('count-correct')).toBe('7/10');
    expect(visible('count-accuracy')).toBe('70%');
    expect(visible('count-xp')).toBe('70');
    expect(cancel).toHaveBeenCalled();
    expect(screen.queryByRole('button', { name: 'Saltar recuento' })).toBeNull();
  });

  it('«Saltar recuento» cuenta como fx_skipped del cierre de sesión (46.6a, nivel 3)', async () => {
    const skipped = vi.spyOn(fxAnalytics, 'trackFxSkipped');
    await cerrarSesion();
    expect(skipped).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Saltar recuento' }));
    expect(skipped).toHaveBeenCalledTimes(1);
    expect(skipped).toHaveBeenCalledWith('session_end');
  });

  it('el lector de pantalla lee el número final, no los intermedios', async () => {
    await cerrarSesion();
    const sr = screen.getByTestId('count-xp').querySelector('.visually-hidden');
    expect(sr).toHaveTextContent('70');
  });

  it('el cierre suena con la nota de la sesión (70 % → B)', async () => {
    await cerrarSesion();
    await waitFor(() => expect(emit).toHaveBeenCalledWith({ type: 'session_end', value: fx.GRADE_RANK.B }));
  });

  it('al acabar el recuento desaparece «Saltar recuento»', async () => {
    await cerrarSesion();
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Saltar recuento' })).toBeNull(), { timeout: 3000 });
    expect(visible('count-xp')).toBe('70');
  });

  it('con movimiento reducido: sin recuento ni botón, los números ya están', async () => {
    motionPrefs.reduce = true;
    await cerrarSesion();
    expect(screen.queryByRole('button', { name: 'Saltar recuento' })).toBeNull();
    expect(visible('count-correct')).toBe('7/10');
    expect(visible('count-xp')).toBe('70');
  });

  it('con ceremonia abierta el recuento espera: un solo «Saltar» a la vez', async () => {
    await cerrarSesion([{ type: 'level_up', payload: { level_before: 1, level: 2 } }]);
    await screen.findByRole('dialog', { name: '¡Subes a nivel 2!' });
    expect(screen.queryByRole('button', { name: 'Saltar recuento' })).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Saltar' }));
    expect(await screen.findByRole('button', { name: 'Saltar recuento' })).toBeInTheDocument();
  });
});
