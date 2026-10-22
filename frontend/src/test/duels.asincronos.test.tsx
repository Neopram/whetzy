/**
 * Duelos 42.4 / 42.5 (ADR-69 #6, H.52).
 *
 * - `/result` contesta 202 mientras el rival no termina. Para `fetch` un 202
 *   es `ok`, y su cuerpo `{detail}` llegaba a la pantalla como si fuera un
 *   resultado: sin `winner_id` ni `is_draw`, así que salía «Perdiste».
 * - Tras contestar se ve si acertó, la opción buena y la explicación.
 * - Quien vuelve a un duelo a medias sigue por la primera sin contestar.
 * - El copy no promete duelos «en vivo»: son por turnos.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import es from '../i18n/es/common.json';
import en from '../i18n/en/common.json';
import i18n from '../i18n';
import { DuelScreen } from '../pages/DuelScreen';
import { duels, progress, type QuestionPublic } from '../services/api';

describe('duels.result', () => {
  afterEach(() => { vi.unstubAllGlobals(); });

  it('202 (el rival no ha terminado) es null, no un resultado vacío', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Duel is not completed yet' }), { status: 202 }),
    ));
    const { duels: real } = await vi.importActual<typeof import('../services/api')>('../services/api');
    await expect(real.result('d1')).resolves.toBeNull();
  });
});

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    duels: { ...actual.duels, my: vi.fn(), challenge: vi.fn(), answer: vi.fn(), join: vi.fn(), result: vi.fn() },
    progress: { ...actual.progress, skills: vi.fn() },
  };
});

const m = (f: unknown) => f as ReturnType<typeof vi.fn>;
const q = (id: string): QuestionPublic => ({
  id, skill_id: 'sk1', type: 'mcq', difficulty_tier: 'easy', question_es: `Pregunta ${id}`, question_en: id,
  options_es: ['a', 'b'], options_en: ['a', 'b'], correct_answer_es: null, correct_answer_en: null,
} as unknown as QuestionPublic);

const mine = (status: string, isYourTurn: boolean) => ({
  duel_id: 'd1', status, skill_id: 'sk1', opponent_username: 'rival', opponent_avatar: '🦊',
  your_correct: null, opponent_correct: null, winner_id: null, is_your_turn: isYourTurn, created_at: '2026-10-01',
});

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
  m(progress.skills).mockResolvedValue([]);
  m(duels.my).mockResolvedValue([mine('in_progress', true)]);
  m(duels.answer).mockResolvedValue({
    duel_id: 'd1', answers_so_far: 1, completed: false, opponent_completed: false,
    correct: false, correct_index: 1, explanation_es: 'Porque b.', explanation_en: 'Because b.', rival: null,
  });
  m(duels.result).mockResolvedValue(null);
});
afterEach(() => { cleanup(); });

describe('DuelScreen: duelos por turnos', () => {
  it('quien vuelve sigue por la primera sin contestar', async () => {
    m(duels.join).mockResolvedValue({
      duel_id: 'd1', skill_id: 'sk1', opponent_username: 'rival',
      questions: [q('1'), q('2'), q('3')], answered_question_ids: ['1', '2'],
    });
    render(<DuelScreen />);
    fireEvent.click(await screen.findByRole('button', { name: 'Jugar' }));
    expect(await screen.findByText('Pregunta 3')).toBeInTheDocument();
  });

  it('tras contestar dice si acertó, cuál era la buena y por qué', async () => {
    m(duels.join).mockResolvedValue({
      duel_id: 'd1', skill_id: 'sk1', opponent_username: 'rival', questions: [q('1'), q('2')],
    });
    render(<DuelScreen />);
    fireEvent.click(await screen.findByRole('button', { name: 'Jugar' }));
    await screen.findByText('Pregunta 1');
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'a' })); });
    const feedback = await screen.findByTestId('duel-feedback');
    expect(feedback).toHaveTextContent(es.duel.youMissedIt);
    expect(feedback).toHaveTextContent('Porque b.');
    expect(screen.getAllByTestId('duel-option')[1].className).toMatch(/optionCorrect/);
  });

  it('con el rival sin terminar se espera: nunca «Perdiste»', async () => {
    m(duels.join).mockResolvedValue({
      duel_id: 'd1', skill_id: 'sk1', opponent_username: 'rival', questions: [q('1')],
    });
    render(<DuelScreen />);
    fireEvent.click(await screen.findByRole('button', { name: 'Jugar' }));
    await screen.findByText('Pregunta 1');
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'a' })); });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: es.duel.finish })); });
    expect(await screen.findByText(es.duel.waitingResult)).toBeInTheDocument();
    expect(screen.queryByText(es.duel.lost)).not.toBeInTheDocument();
  });

  it('un duelo caducado lo dice y no se puede jugar', async () => {
    m(duels.my).mockResolvedValue([mine('expired', false)]);
    render(<DuelScreen />);
    expect(await screen.findByText(new RegExp(es.duel.status_expired))).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Jugar' })).not.toBeInTheDocument();
    expect(screen.queryByText(es.duel.lost)).not.toBeInTheDocument();
  });
});

describe('copy de duelos', () => {
  it('nadie promete duelos en vivo', () => {
    const all = JSON.stringify(es) + JSON.stringify(en);
    expect(all).not.toMatch(/duelos? en vivo|live duels?|duelos? en tiempo real|real-time duels?/i);
  });
});
