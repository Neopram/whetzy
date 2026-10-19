/**
 * 40.1: una pregunta `interactive` en el quiz. El estado del widget viaja
 * serializado como `widget_state`, no hay cuenta atrás, y cuando llega la
 * respuesta el cliente vuelve a corregir con `widget_target`: si su veredicto
 * no es el del servidor, lo marca.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { QuizScreen } from '../pages/QuizScreen';
import { useAppStore } from '../stores/useAppStore';
import { quiz as quizApi, progress as progressApi, gamification, type QuestionPublic } from '../services/api';
import type { WidgetRenderProps } from '../widgets/registry';

const registry = vi.hoisted(() => ({ present: true }));
vi.mock('../widgets/registry', () => ({
  loadWidget: async (name: string) => {
    if (!registry.present || name !== 'fake') return null;
    return {
      render: ({ onChange, disabled }: WidgetRenderProps<number[]>) => (
        <button type="button" disabled={disabled} onClick={() => onChange([5, 7])}>Sondear 5 y 7</button>
      ),
      serialize: (s: number[]) => s,
    };
  },
}));
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

const Q = {
  id: 'qi1', skill_id: 'sk1', type: 'interactive', difficulty_tier: 'easy',
  question_es: 'Busca el 7.', question_en: 'Find 7.',
  options_es: null, options_en: null, correct_answer_es: null, correct_answer_en: null,
  interactive: { widget: 'fake', params: { items: [1, 3, 5, 7] }, checker: 'exact' },
  expected_time_ms: 30000,
} as unknown as QuestionPublic;

function respuesta(correct: boolean, target: unknown) {
  return {
    correct, correct_index: null, explanation_es: 'Mitad y derecha.', explanation_en: 'Middle then right.',
    source: null, grade: 3, xp_earned: 10, combo: 1, user_elo: 1500, next_review: null,
    skill_mastery: { sk1: 0.4 }, session_accuracy: 1, next_question: null, next_selection_reason: null,
    events: [], widget_target: target,
  };
}

beforeEach(async () => {
  vi.clearAllMocks();
  registry.present = true;
  await i18n.changeLanguage('es');
  useAppStore.getState().startQuiz('study', 10);
  useAppStore.setState({ hydrateFromApi: vi.fn().mockResolvedValue(undefined) });
  start.mockResolvedValue({ session_id: 's1', question: Q, selection_reason: null });
  (progressApi.skills as unknown as ReturnType<typeof vi.fn>).mockResolvedValue([]);
  (gamification.badges as unknown as ReturnType<typeof vi.fn>).mockResolvedValue([]);
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

async function abrir() {
  render(<QuizScreen />);
  await screen.findByText('Busca el 7.');
  await act(async () => {});
}

describe('Pregunta interactive (40.1)', () => {
  it('envía el estado serializado del widget y no lleva cuenta atrás', async () => {
    answer.mockResolvedValue(respuesta(true, [5, 7]));
    await abrir();
    expect(screen.queryByLabelText(/segundos|seconds/i)).toBeNull();
    const comprobar = screen.getByRole('button', { name: 'Comprobar' });
    expect(comprobar).toBeDisabled();
    fireEvent.click(await screen.findByRole('button', { name: 'Sondear 5 y 7' }));
    fireEvent.click(comprobar);
    await screen.findByText('Mitad y derecha.');
    expect(answer).toHaveBeenCalledWith('s1', 'qi1', null, expect.any(Number), false, undefined, { widgetState: [5, 7] });
    // Deja correr el efecto que vuelve a corregir antes de afirmar que no hay discrepancia.
    await act(async () => {});
    expect(document.querySelector('[data-checker-mismatch]')).toBeNull();
  });

  it('si el checker del cliente no da lo mismo que el servidor, lo marca', async () => {
    const error = vi.spyOn(console, 'error').mockImplementation(() => {});
    // El servidor dice «correcto» con un objetivo que el cliente no aprueba.
    answer.mockResolvedValue(respuesta(true, [7, 5]));
    await abrir();
    fireEvent.click(await screen.findByRole('button', { name: 'Sondear 5 y 7' }));
    fireEvent.click(screen.getByRole('button', { name: 'Comprobar' }));
    await screen.findByText('Mitad y derecha.');
    await waitFor(() => expect(document.querySelector('[data-checker-mismatch]')).not.toBeNull());
    expect(error).toHaveBeenCalledWith(expect.stringContaining('[interactive]'));
  });

  it('«No lo sé» es una respuesta, como en los demás tipos', async () => {
    answer.mockResolvedValue(respuesta(false, [5, 7]));
    await abrir();
    fireEvent.click(await screen.findByRole('button', { name: 'No lo sé' }));
    await screen.findByText('Mitad y derecha.');
    expect(answer).toHaveBeenCalledWith('s1', 'qi1', null, expect.any(Number), true, undefined, {});
  });

  it('un widget que esta versión no tiene lo dice y no deja enviar', async () => {
    registry.present = false;
    await abrir();
    expect(await screen.findByRole('alert')).toHaveTextContent('Este ejercicio no se puede abrir');
    expect(screen.queryByRole('button', { name: 'Comprobar' })).toBeNull();
  });
});
