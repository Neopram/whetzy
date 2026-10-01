/**
 * Duelos (design/v2): la lista enseña el nombre de la habilidad, no su id
 * («sk010102», auditoría), y el tiempo de respuesta que llega al motor se mide
 * desde que se muestra cada pregunta (antes, desde que se montó la pantalla,
 * así que crecía pregunta a pregunta).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { DuelScreen } from '../pages/DuelScreen';
import { duels, progress, type QuestionPublic } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    duels: { ...actual.duels, my: vi.fn(), challenge: vi.fn(), answer: vi.fn(), join: vi.fn() },
    progress: { ...actual.progress, skills: vi.fn() },
  };
});

const m = (f: unknown) => f as ReturnType<typeof vi.fn>;
const q = (id: string): QuestionPublic => ({
  id, skill_id: 'sk010102', type: 'mcq', difficulty_tier: 'easy', question_es: `Pregunta ${id}`, question_en: id,
  options_es: ['a', 'b'], options_en: ['a', 'b'], correct_answer_es: null, correct_answer_en: null,
} as unknown as QuestionPublic);

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
  m(progress.skills).mockResolvedValue([{
    skill_id: 'sk010102', name_es: 'Tipos numéricos', name_en: 'Numeric types', module_id: 'm', p_known: 0.3,
    elo_rating: 1500, attempts: 2, correct_count: 1, accuracy: 0.5, mastered: false, fsrs_due: null,
  }]);
  m(duels.my).mockResolvedValue([{
    duel_id: 'd1', status: 'pending', skill_id: 'sk010102', opponent_username: 'rival', opponent_avatar: '🦊',
    your_correct: null, opponent_correct: null, winner_id: null, is_your_turn: false, created_at: '2026-10-01',
  }]);
  m(duels.challenge).mockResolvedValue({ duel_id: 'd2', opponent_username: 'rival', questions: [q('1'), q('2')] });
  m(duels.answer).mockResolvedValue({});
});
afterEach(() => { cleanup(); vi.useRealTimers(); });

describe('DuelScreen v2', () => {
  it('la lista dice el nombre de la habilidad, no su id', async () => {
    render(<DuelScreen />);
    expect(await screen.findByText(/Tipos numéricos · Pendiente/)).toBeInTheDocument();
    expect(screen.queryByText(/sk010102/)).not.toBeInTheDocument();
  });

  it('el tiempo de respuesta empieza en cada pregunta, no al montar', async () => {
    render(<DuelScreen />);
    await screen.findByText(/Tipos numéricos/);
    fireEvent.click(screen.getByRole('button', { name: 'Retar' }));
    fireEvent.change(screen.getByPlaceholderText('Nombre de usuario'), { target: { value: 'rival' } });
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date('2026-10-01T10:00:00Z'));
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Retar' })); });
    await screen.findByText('Pregunta 1');

    vi.setSystemTime(new Date('2026-10-01T10:00:05Z'));
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'a' })); });
    fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
    await screen.findByText('Pregunta 2');

    vi.setSystemTime(new Date('2026-10-01T10:00:08Z'));
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'a' })); });

    const times = m(duels.answer).mock.calls.map((c) => (c[1] as { response_time_ms: number }).response_time_ms);
    expect(times).toEqual([5000, 3000]);
  });
});
