/**
 * Quiz (design/v2): teclas 1–4 / A–D para responder e Intro para seguir,
 * confirmación al salir cuando ya hay algo respondido, y un resumen que enseña
 * el dominio de cada habilidad antes → después de la sesión con el mismo dato
 * (/progress/skills al empezar y al terminar), no con una estimación.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import i18n from '../i18n';
import { QuizScreen } from '../pages/QuizScreen';
import { useAppStore } from '../stores/useAppStore';
import { quiz as quizApi, progress as progressApi, type QuestionPublic } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    quiz: { ...actual.quiz, start: vi.fn(), answer: vi.fn(), end: vi.fn() },
    progress: { ...actual.progress, skills: vi.fn() },
  };
});
vi.mock('@lottiefiles/react-lottie-player', () => ({ Player: () => null }));

const start = quizApi.start as unknown as ReturnType<typeof vi.fn>;
const answer = quizApi.answer as unknown as ReturnType<typeof vi.fn>;
const end = quizApi.end as unknown as ReturnType<typeof vi.fn>;
const skills = progressApi.skills as unknown as ReturnType<typeof vi.fn>;

const Q = {
  id: 'q1', skill_id: 'sk1', type: 'mcq', difficulty_tier: 'easy',
  question_es: '¿Cuánto es 1 + 1?', question_en: 'What is 1 + 1?',
  options_es: ['1', '2', '3', '4'], options_en: ['1', '2', '3', '4'],
  correct_answer_es: null, correct_answer_en: null, code_es: null, code_en: null,
} as unknown as QuestionPublic;

const skill = (p: number) => ({
  skill_id: 'sk1', name_es: 'Sumas', name_en: 'Sums', module_id: 'm1', p_known: p,
  elo_rating: 1500, attempts: 1, correct_count: 1, accuracy: 1, mastered: false, fsrs_due: null,
});

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
  useAppStore.getState().startQuiz('study', 10);
  // Al terminar, la pantalla refresca el usuario; aquí no hay backend.
  useAppStore.setState({ hydrateFromApi: vi.fn().mockResolvedValue(undefined) });
  start.mockResolvedValue({ session_id: 's1', question: Q, selection_reason: null });
  answer.mockResolvedValue({
    correct: true, correct_index: 1, explanation_es: 'Uno más uno es dos.', explanation_en: 'One plus one is two.',
    source: null, grade: 4, xp_earned: 10, combo: 1, user_elo: 1500, next_review: null,
    skill_mastery: { sk1: 0.45 }, session_accuracy: 1, next_question: null, next_selection_reason: null,
  });
  end.mockResolvedValue({ total_questions: 1, correct: 1, accuracy: 1, max_combo: 1, xp_earned: 10, duration_seconds: 5 });
  skills.mockResolvedValueOnce([skill(0.2)]).mockResolvedValueOnce([skill(0.45)]);
});
afterEach(cleanup);

// El atajo de teclado se engancha en un useEffect, que React ejecuta después de
// pintar: `findBy*` puede volver justo entre medias y la tecla se pierde. Con
// carga pasaba 1 de cada ~5 corridas. Una persona no teclea en ese microsegundo.
const effectsRun = () => act(async () => {});

describe('QuizScreen v2', () => {
  it('responde con la tecla «2», pide confirmación al salir y resume antes → después', async () => {
    render(<QuizScreen />);
    await screen.findByText('¿Cuánto es 1 + 1?');
    await effectsRun();

    fireEvent.keyDown(window, { key: '2' });
    await waitFor(() => expect(answer).toHaveBeenCalledWith('s1', 'q1', 1, expect.any(Number), false));
    await screen.findByText('Uno más uno es dos.');

    // Ya hay algo respondido: cerrar pregunta antes de salir, y «Seguir» lo cancela.
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }));
    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Seguir' }));
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();

    fireEvent.keyDown(window, { key: 'Enter' });
    expect(await screen.findByText('Habilidades de esta sesión')).toBeInTheDocument();
    expect(await screen.findByText('20% → 45%')).toBeInTheDocument();
    expect(screen.getByText(/100% de precisión/)).toBeInTheDocument();
  });

  it('una habilidad sin intentos previos sale como «nueva», no como 0 %', async () => {
    skills.mockReset();
    skills.mockResolvedValueOnce([{ ...skill(0), attempts: 0 }]).mockResolvedValueOnce([skill(0.45)]);
    render(<QuizScreen />);
    await screen.findByText('¿Cuánto es 1 + 1?');
    await effectsRun();
    fireEvent.keyDown(window, { key: '2' });
    await screen.findByText('Uno más uno es dos.');
    fireEvent.keyDown(window, { key: 'Enter' });
    expect(await screen.findByText('nueva → 45%')).toBeInTheDocument();
  });

  it('las letras también eligen opción (c = tercera)', async () => {
    render(<QuizScreen />);
    await screen.findByText('¿Cuánto es 1 + 1?');
    await effectsRun();
    fireEvent.keyDown(window, { key: 'c' });
    await waitFor(() => expect(answer).toHaveBeenCalledWith('s1', 'q1', 2, expect.any(Number), false));
  });

  it('el contador de 30 s se para mientras se decide si salir', async () => {
    const Q2 = { ...Q, id: 'q2', question_es: '¿Cuánto es 2 + 2?' };
    answer.mockResolvedValue({
      correct: true, correct_index: 1, explanation_es: 'Uno más uno es dos.', explanation_en: '',
      source: null, grade: 4, xp_earned: 10, combo: 1, user_elo: 1500, next_review: null,
      skill_mastery: { sk1: 0.45 }, session_accuracy: 1, next_question: Q2, next_selection_reason: null,
    });
    render(<QuizScreen />);
    await screen.findByText('¿Cuánto es 1 + 1?');
    await effectsRun();
    fireEvent.keyDown(window, { key: '2' });
    await screen.findByText('Uno más uno es dos.');
    fireEvent.keyDown(window, { key: 'Enter' });
    await screen.findByText('¿Cuánto es 2 + 2?');
    expect(answer).toHaveBeenCalledTimes(1);

    vi.useFakeTimers();
    try {
      fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }));
      expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      // 40 s con la confirmación abierta: sin pausa, el contador mandaría la
      // pregunta 2 en blanco a los 30.
      for (let i = 0; i < 40; i++) await act(async () => { vi.advanceTimersByTime(1000); });
      expect(answer).toHaveBeenCalledTimes(1);
    } finally {
      vi.useRealTimers();
    }
  });

  it('con las explicaciones de IA apagadas en Ajustes no aparece «¿Por qué?», y reportar sí', async () => {
    useAppStore.setState({ aiExplanations: false });
    try {
      render(<QuizScreen />);
      await screen.findByText('¿Cuánto es 1 + 1?');
      await effectsRun();
      fireEvent.keyDown(window, { key: '2' });
      await screen.findByText('Uno más uno es dos.');
      expect(screen.queryByRole('button', { name: '¿Por qué?' })).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Reportar un problema con esta pregunta' })).toBeInTheDocument();
    } finally {
      useAppStore.setState({ aiExplanations: true });
    }
  });

  it('sin nada respondido, cerrar sale sin preguntar', async () => {
    render(<QuizScreen />);
    await screen.findByText('¿Cuánto es 1 + 1?');
    await effectsRun();
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }));
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
    expect(useAppStore.getState().currentScreen).toBe('home');
    expect(useAppStore.getState().hydrateFromApi).not.toHaveBeenCalled();
  });

  it('salir a mitad refresca el usuario: el XP ya está sumado en el servidor', async () => {
    const hydrate = useAppStore.getState().hydrateFromApi;
    render(<QuizScreen />);
    await screen.findByText('¿Cuánto es 1 + 1?');
    await effectsRun();
    fireEvent.keyDown(window, { key: '2' });
    await screen.findByText('Uno más uno es dos.');
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }));
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Salir' }));
    expect(useAppStore.getState().currentScreen).toBe('home');
    expect(hydrate).toHaveBeenCalledTimes(1);
  });
});
