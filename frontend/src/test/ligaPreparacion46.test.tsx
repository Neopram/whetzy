/**
 * 46.13 (docs/PLAN_UI_AVANZADA.md §7.3 y §6.2): la Liga entra escalonada (podio
 * y filas) y la ▲ de la zona de ascenso late una vez; Preparación escalona sus
 * dominios. Ninguna ceremonia de ascenso: el servidor aún no aplica ascensos
 * (§6.2) y celebrar uno que no ocurre es mentir. Con movimiento reducido,
 * nada de eso.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { LeagueScreen } from '../pages/LeagueScreen';
import { ReadinessScreen } from '../pages/ReadinessScreen';
import { content, exams, league as leagueApi } from '../services/api';

let reduce = false;
vi.mock('framer-motion', async (importOriginal) => {
  const actual = await importOriginal<typeof import('framer-motion')>();
  return { ...actual, useReducedMotion: () => reduce };
});
vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    league: { current: vi.fn(), setParticipation: vi.fn() },
    exams: { ...actual.exams, certificationReadiness: vi.fn() },
    content: { ...actual.content, tracks: vi.fn() },
  };
});

const current = leagueApi.current as unknown as ReturnType<typeof vi.fn>;
const readiness = exams.certificationReadiness as unknown as ReturnType<typeof vi.fn>;
const tracks = content.tracks as unknown as ReturnType<typeof vi.fn>;

const member = (rank: number, me = false) => ({
  rank, user_id: `u${rank}`, username: `u${rank}`, display_name: `Alumno ${rank}`,
  avatar_emoji: '🦊', xp_earned: 1000 - rank * 50, is_current_user: me,
});

beforeEach(async () => {
  reduce = false;
  await i18n.changeLanguage('es');
  current.mockResolvedValue({
    league: { id: 'oro', name: 'Oro', tier: 'gold', min_xp: 0 },
    week_start: '2026-10-19',
    standings: [1, 2, 3, 4, 5, 6, 7].map((r) => member(r, r === 5)),
    promotion_zone: 5, demotion_zone: 1, total_members: 7, participating: true,
  });
  readiness.mockResolvedValue({
    track_id: 'track09', overall_p_known: 0.4,
    domains: [
      { domain_id: 'd1', name_es: 'Uno', name_en: 'One', weight_pct: 60, p_known_mean: 0.2, skills_assessed: 1, skills_total: 3, ready: false },
      { domain_id: 'd2', name_es: 'Dos', name_en: 'Two', weight_pct: 40, p_known_mean: 0.9, skills_assessed: 3, skills_total: 3, ready: true },
    ],
  });
  tracks.mockResolvedValue([{
    id: 'track09', name_es: 'PCEP', name_en: 'PCEP', order: 9, icon: '🐍', color: '#000', total_questions: 267,
    is_certification: true, cert_provider: 'Python Institute', exam_question_count: 30, exam_duration_minutes: 40,
  }]);
});
afterEach(cleanup);

describe('Liga (46.13)', () => {
  it('podio y filas entran escalonados; la ▲ late una vez; sin ceremonia de ascenso', async () => {
    render(<LeagueScreen />);
    await screen.findByText('Alumno 4');
    expect(screen.getByTestId('league-podium')).toHaveAttribute('data-enter', 'stagger');
    expect(screen.getByTestId('league-rows')).toHaveAttribute('data-enter', 'stagger');
    const promos = screen.getAllByText('▲');
    expect(promos).toHaveLength(2); // rangos 4 y 5: el podio no lleva flecha
    for (const p of promos) expect(p).toHaveAttribute('data-fx', 'pulse-once');
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('con movimiento reducido no hay escalonado ni latido', async () => {
    reduce = true;
    render(<LeagueScreen />);
    await screen.findByText('Alumno 4');
    expect(screen.getByTestId('league-podium')).not.toHaveAttribute('data-enter');
    expect(screen.getByTestId('league-rows')).not.toHaveAttribute('data-enter');
    for (const p of screen.getAllByText('▲')) expect(p).not.toHaveAttribute('data-fx');
  });
});

describe('Preparación (46.13)', () => {
  it('los dominios entran escalonados', async () => {
    render(<ReadinessScreen trackId="track09" onExit={() => {}} />);
    await screen.findByText('Uno');
    expect(screen.getByRole('list')).toHaveAttribute('data-enter', 'stagger');
  });

  it('con movimiento reducido, sin escalonado', async () => {
    reduce = true;
    render(<ReadinessScreen trackId="track09" onExit={() => {}} />);
    await screen.findByText('Uno');
    expect(screen.getByRole('list')).not.toHaveAttribute('data-enter');
  });
});
