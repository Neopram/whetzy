/**
 * Duelo, partida grabada: quien juega segundo ve, tras contestar cada pregunta,
 * cómo le fue al rival en esa misma pregunta (acierto y tiempo), con lo que
 * manda el servidor en `rival`. Quien juega primero (sin `rival`) no ve nada,
 * y lo del rival no pasa a la pregunta siguiente.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { DuelScreen } from '../pages/DuelScreen';
import { useAppStore } from '../stores/useAppStore';
import { duels, progress, type QuestionPublic } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    progress: { ...actual.progress, skills: vi.fn() },
    duels: { ...actual.duels, my: vi.fn(), challenge: vi.fn(), answer: vi.fn(), join: vi.fn(), result: vi.fn() },
  };
});

const m = (f: unknown) => f as ReturnType<typeof vi.fn>;
const q = (id: string): QuestionPublic => ({
  id, skill_id: 'sk010102', type: 'mcq', difficulty_tier: 'easy', question_es: `Pregunta ${id}`, question_en: `Question ${id}`,
  options_es: ['a', 'b'], options_en: ['a', 'b'], correct_answer_es: null, correct_answer_en: null,
} as unknown as QuestionPublic);

beforeEach(() => {
  vi.clearAllMocks();
  useAppStore.setState((s) => ({ user: { ...s.user, id: 'me', language: 'es' } }));
  m(progress.skills).mockResolvedValue([]);
  m(duels.my).mockResolvedValue([]);
  m(duels.challenge).mockResolvedValue({ duel_id: 'd1', skill_id: 's', opponent_username: 'rival', questions: [q('1'), q('2')] });
});
afterEach(cleanup);

async function startAndAnswerFirst() {
  render(<DuelScreen />);
  fireEvent.click(await screen.findByRole('button', { name: /Retar|Challenge/ }));
  fireEvent.change(screen.getByRole('textbox'), { target: { value: 'rival' } });
  await act(async () => { fireEvent.click(screen.getAllByRole('button', { name: /Retar|Challenge/ }).at(-1)!); });
  await act(async () => { fireEvent.click((await screen.findAllByTestId('duel-option'))[0]); });
}

describe('Duelo — partida grabada', () => {
  it('con la partida del rival: tras contestar, su acierto y su tiempo en esa pregunta', async () => {
    await i18n.changeLanguage('es');
    m(duels.answer)
      .mockResolvedValueOnce({ duel_id: 'd1', answers_so_far: 1, completed: false, opponent_completed: true, rival: { correct: true, response_time_ms: 4230 } })
      .mockResolvedValueOnce({ duel_id: 'd1', answers_so_far: 2, completed: true, opponent_completed: true, rival: { correct: false, response_time_ms: 9000 } });
    await startAndAnswerFirst();
    expect(screen.getByTestId('duel-rival')).toHaveTextContent('rival acertó esta en 4,2 s');
    // 42.4: una sola región viva, con el veredicto propio y el del rival.
    expect(screen.getByRole('status')).toContainElement(screen.getByTestId('duel-rival'));

    // Siguiente pregunta: lo de la anterior no se arrastra.
    fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
    expect(screen.queryByTestId('duel-rival')).toBeNull();
    await act(async () => { fireEvent.click(screen.getAllByTestId('duel-option')[1]); });
    expect(screen.getByTestId('duel-rival')).toHaveTextContent('rival falló esta (9 s)');
  });

  it('en inglés, con el separador decimal inglés', async () => {
    await i18n.changeLanguage('en');
    useAppStore.setState((s) => ({ user: { ...s.user, language: 'en' } }));
    m(duels.answer).mockResolvedValue({ duel_id: 'd1', answers_so_far: 1, completed: false, opponent_completed: true, rival: { correct: true, response_time_ms: 4230 } });
    await startAndAnswerFirst();
    expect(screen.getByTestId('duel-rival')).toHaveTextContent('rival got this one right in 4.2 s');
  });

  it('quien juega primero (el servidor no manda `rival`): nada que enseñar', async () => {
    await i18n.changeLanguage('es');
    m(duels.answer).mockResolvedValue({ duel_id: 'd1', answers_so_far: 1, completed: false, opponent_completed: false, rival: null });
    await startAndAnswerFirst();
    expect(screen.getByRole('button', { name: 'Siguiente' })).toBeInTheDocument();
    expect(screen.queryByTestId('duel-rival')).toBeNull();
  });
});
