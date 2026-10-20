/**
 * 46.15 bloque C (docs/PLAN_UI_AVANZADA.md §7.5): las pantallas de competir.
 * - Examen: el reloj late una vez al entrar en los 5 últimos minutos, sin sonido.
 * - Simulacro, examen de ruta y duelo: el resultado del servidor cierra la
 *   sesión con un efecto de nivel 3 (`session_end`), una sola vez, y el
 *   veredicto entra. Sin resultado del servidor (duelo aún sin rival), nada.
 * Con movimiento reducido no late ni entra nada.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { ExamSitting } from '../components/exam/ExamSitting';
import { MockExamScreen } from '../pages/MockExamScreen';
import { TrackExamScreen } from '../pages/TrackExamScreen';
import { DuelScreen } from '../pages/DuelScreen';
import { onFx, type FxEvent } from '../lib/feedbackFx';
import { useAppStore } from '../stores/useAppStore';
import { duels, exams, progress, type QuestionPublic } from '../services/api';

let reduce = false;
vi.mock('framer-motion', async (importOriginal) => {
  const actual = await importOriginal<typeof import('framer-motion')>();
  return { ...actual, useReducedMotion: () => reduce };
});
vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    exams: {
      ...actual.exams, certificationAccess: vi.fn(), startMock: vi.fn(), submitMock: vi.fn(),
      startTrackExam: vi.fn(), submitTrackExam: vi.fn(),
    },
    progress: { ...actual.progress, skills: vi.fn() },
    duels: { ...actual.duels, my: vi.fn(), challenge: vi.fn(), answer: vi.fn(), join: vi.fn(), result: vi.fn() },
  };
});

const m = (f: unknown) => f as ReturnType<typeof vi.fn>;
const q = (id: string): QuestionPublic => ({
  id, skill_id: 'sk010102', type: 'mcq', difficulty_tier: 'easy', question_es: `Pregunta ${id}`, question_en: id,
  options_es: ['a', 'b'], options_en: ['a', 'b'], correct_answer_es: null, correct_answer_en: null,
} as unknown as QuestionPublic);

let seen: FxEvent[] = [];
let off = () => {};
beforeEach(async () => {
  vi.clearAllMocks();
  reduce = false;
  seen = [];
  off = onFx((e) => seen.push(e));
  await i18n.changeLanguage('es');
  useAppStore.setState((s) => ({ user: { ...s.user, id: 'me', language: 'es' } }));
});
afterEach(() => { off(); cleanup(); });

const sessionEnds = () => seen.filter((e) => e.type === 'session_end').length;

describe('Examen — el reloj (46.15 C)', () => {
  const sitting = (secondsLeft: number) => (
    <ExamSitting
      title="Simulacro" questions={[q('1')]} index={0} onGo={() => {}} answers={{}}
      onChoose={() => {}} secondsLeft={secondsLeft} grading={false} error={null} onSubmit={() => {}}
    />
  );

  it('late al entrar en los 5 últimos minutos, no antes, y sin sonido', () => {
    const { rerender } = render(sitting(301));
    expect(screen.getByRole('timer')).not.toHaveAttribute('data-fx');
    rerender(sitting(300));
    expect(screen.getByRole('timer')).toHaveAttribute('data-fx', 'urgent');
    expect(seen).toEqual([]);
  });

  it('con movimiento reducido no late (el color y el texto ya avisan)', () => {
    reduce = true;
    const { rerender } = render(sitting(301));
    rerender(sitting(299));
    expect(screen.getByRole('timer')).not.toHaveAttribute('data-fx');
  });
});

describe('Simulacro — resultado (46.15 C)', () => {
  it('el veredicto entra y la sesión se cierra una vez', async () => {
    m(exams.certificationAccess).mockResolvedValue({
      track_id: 'track08', price_usd: 39.99, paywall_enabled: false, purchased: false, available: false, can_start: false,
    });
    m(exams.startMock).mockResolvedValue({
      attempt_id: 'a1', track_id: 'track08', duration_minutes: 90, started_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 90 * 60_000).toISOString(), questions: [q('1')],
    });
    m(exams.submitMock).mockResolvedValue({
      attempt_id: 'a1', status: 'submitted', expired: false, certificate: null,
      report: {
        track_id: 'track08', questions: 1, answered: 1, unanswered: 0, correct: 1, raw_pct: 100,
        per_domain: [], elapsed_seconds: 60, duration_minutes: 90, scoring_note_es: 'n', scoring_note_en: 'n',
        per_domain_caveat_es: 'c', per_domain_caveat_en: 'c', pass_pct: 70, passed: true,
        pass_note_es: 'umbral', pass_note_en: 'x',
      },
    });
    render(<MockExamScreen trackId="track08" questionCount={65} durationMinutes={90} />);
    fireEvent.click(await screen.findByRole('button', { name: /EMPEZAR SIMULACRO|EMPEZAR/ }));
    fireEvent.click(await screen.findByRole('radio', { name: 'a' }));
    fireEvent.click(screen.getByRole('button', { name: /ENTREGAR/ }));
    const verdict = await screen.findByTestId('exam-verdict');
    expect(verdict).toHaveAttribute('data-fx', 'reveal');
    await waitFor(() => expect(sessionEnds()).toBe(1));
  });
});

describe('Examen de ruta — resultado (46.15 C)', () => {
  it('el veredicto entra y la sesión se cierra una vez; con movimiento reducido, sin entrada', async () => {
    reduce = true;
    m(exams.startTrackExam).mockResolvedValue({
      attempt_id: 't1', track_id: 'track01', module_id: null, kind: 'track_final', duration_minutes: 75, pass_pct: 70,
      started_at: new Date().toISOString(), expires_at: new Date(Date.now() + 75 * 60_000).toISOString(), questions: [q('1')],
    });
    m(exams.submitTrackExam).mockResolvedValue({
      attempt_id: 't1', status: 'submitted', expired: false, certificate: null, mastery_updated: {},
      report: {
        track_id: 'track01', module_id: null, kind: 'track_final', questions: 1, answered: 1, unanswered: 0,
        correct: 0, raw_pct: 0, pass_pct: 70, passed: false, per_skill: [], elapsed_seconds: 60,
        duration_minutes: 75, scoring_note_es: 'n', scoring_note_en: 'n',
      },
    });
    render(<TrackExamScreen kind="track_final" targetId="track01" questionCount={50} durationMinutes={75} passPct={70} />);
    fireEvent.click(await screen.findByRole('button', { name: 'EMPEZAR EXAMEN' }));
    fireEvent.click(await screen.findByRole('radio', { name: 'a' }));
    fireEvent.click(screen.getByRole('button', { name: /ENTREGAR/ }));
    const verdict = await screen.findByRole('heading', { name: 'No aprobado' });
    expect(verdict).not.toHaveAttribute('data-fx');
    // El sonido y la vibración siguen sus propios interruptores: el efecto se emite igual.
    await waitFor(() => expect(sessionEnds()).toBe(1));
  });
});

describe('Duelo — resultado (46.15 C)', () => {
  async function playToEnd() {
    m(progress.skills).mockResolvedValue([]);
    m(duels.my).mockResolvedValue([]);
    m(duels.challenge).mockResolvedValue({ duel_id: 'd2', opponent_username: 'rival', questions: [q('1')] });
    m(duels.answer).mockResolvedValue({});
    render(<DuelScreen />);
    fireEvent.click(await screen.findByRole('button', { name: 'Retar' }));
    fireEvent.change(screen.getByPlaceholderText('Nombre de usuario'), { target: { value: 'rival' } });
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Retar' })); });
    await act(async () => { fireEvent.click(await screen.findByRole('button', { name: 'a' })); });
    fireEvent.click(screen.getByRole('button', { name: 'Finalizar' }));
  }

  it('con el resultado del servidor: el desenlace entra y la sesión se cierra', async () => {
    m(duels.result).mockResolvedValue({
      duel_id: 'd2', status: 'completed', skill_id: 's', challenger: {}, opponent: {},
      winner_id: 'me', is_draw: false, created_at: '', weak_skill_id: null,
    });
    await playToEnd();
    const outcome = await screen.findByText('¡Ganaste!');
    expect(outcome).toHaveAttribute('data-fx', 'reveal');
    await waitFor(() => expect(sessionEnds()).toBe(1));
  });

  it('sin resultado aún (el rival no ha jugado): ni efecto ni desenlace', async () => {
    m(duels.result).mockRejectedValue(new Error('202'));
    await playToEnd();
    expect(await screen.findByText(/Cuando tu oponente termine/)).toBeInTheDocument();
    expect(sessionEnds()).toBe(0);
  });
});
