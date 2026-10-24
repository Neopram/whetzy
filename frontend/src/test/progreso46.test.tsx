/**
 * 46.15 bloque D (docs/PLAN_UI_AVANZADA.md §7.5): las pantallas de progreso.
 * - Perfil: las insignias entran escalonadas y la que se ganó desde la última
 *   visita brilla una vez (foto propia, como Hoy y Rutas).
 * - Estadísticas: las barras crecen desde 0 al entrar; las listas, escalonadas.
 * - Cartera, informe de dominio y perfil público: listas escalonadas.
 * - Certificado público: el sello se dibuja solo si el servidor lo da por
 *   válido; revocado, no hay sello.
 * Con movimiento reducido, nada de eso.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { ProfileScreen } from '../pages/ProfileScreen';
import { StatsScreen } from '../pages/StatsScreen';
import WalletScreen from '../pages/WalletScreen';
import { MasteryReportScreen } from '../pages/MasteryReportScreen';
import PublicProfileScreen from '../pages/PublicProfileScreen';
import { CertificateScreen } from '../pages/CertificateScreen';
import { badgeMoments } from '../lib/homeMoments';
import { useAppStore } from '../stores/useAppStore';
import {
  certificates, economy, gamification, masteryReports, profiles, progress,
} from '../services/api';

let reduce = false;
vi.mock('framer-motion', async (importOriginal) => {
  const actual = await importOriginal<typeof import('framer-motion')>();
  return { ...actual, useReducedMotion: () => reduce };
});
vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    gamification: { ...actual.gamification, badges: vi.fn() },
    progress: { ...actual.progress, dashboard: vi.fn(), skills: vi.fn() },
    economy: { ...actual.economy, balance: vi.fn(), prices: vi.fn(), referralCode: vi.fn() },
    masteryReports: { buy: vi.fn(), mine: vi.fn(), get: vi.fn() },
    profiles: { get: vi.fn() },
    certificates: { ...actual.certificates, verify: vi.fn() },
  };
});

const m = (f: unknown) => f as ReturnType<typeof vi.fn>;
const badge = (id: string) => ({
  badge: {
    id, name_es: `Insignia ${id}`, name_en: `Badge ${id}`, icon: '★',
    description_es: '', description_en: '', criteria_type: 'x', criteria_value: 1,
  },
  earned_at: '2026-10-20T00:00:00Z',
});

beforeEach(async () => {
  vi.clearAllMocks();
  reduce = false;
  localStorage.clear();
  await i18n.changeLanguage('es');
  useAppStore.setState((s) => ({ user: { ...s.user, id: 'u1', language: 'es' } }));
});
afterEach(cleanup);

describe('foto de insignias (46.15 D)', () => {
  it('sin foto, nada; luego, solo las nuevas', () => {
    expect(badgeMoments('u1', ['a'])).toEqual([]);
    expect(badgeMoments('u1', ['a', 'b'])).toEqual(['b']);
    expect(badgeMoments('u1', ['a', 'b'])).toEqual([]);
  });
});

describe('Perfil — insignias (46.15 D)', () => {
  it('entran escalonadas y la nueva brilla una vez', async () => {
    localStorage.setItem('whetzy_fx_badges_u1', JSON.stringify(['a']));
    m(gamification.badges).mockResolvedValue([badge('a'), badge('b')]);
    render(<ProfileScreen />);
    const grid = await screen.findByTestId('badges-grid');
    expect(grid).toHaveAttribute('data-enter', 'stagger');
    await waitFor(() => expect(screen.getByText('Insignia b').closest('[data-fx]')).toHaveAttribute('data-fx', 'new'));
    expect(screen.getByText('Insignia a').closest('[data-fx]')).toBeNull();
  });

  it('con movimiento reducido, ni escalonado ni brillo', async () => {
    reduce = true;
    localStorage.setItem('whetzy_fx_badges_u1', JSON.stringify(['a']));
    m(gamification.badges).mockResolvedValue([badge('a'), badge('b')]);
    render(<ProfileScreen />);
    const grid = await screen.findByTestId('badges-grid');
    await screen.findByText('Insignia b');
    expect(grid).not.toHaveAttribute('data-enter');
    await waitFor(() => expect(localStorage.getItem('whetzy_fx_badges_u1')).toContain('b'));
    expect(screen.getByText('Insignia b').closest('[data-fx]')).toBeNull();
  });
});

describe('Estadísticas (46.15 D)', () => {
  function mockStats() {
    m(progress.dashboard).mockResolvedValue({
      level: 1, total_xp: 10, current_streak: 0, max_streak: 0, streak_freeze_available: 0,
      last_active: null, reviews_due: 0, total_sessions: 1, total_questions_answered: 12,
      tracks: [{
        track_id: 'track01', name_es: 'Python', name_en: 'Python', icon: '🐍', color: '#000',
        average_mastery: 0.5, skills_mastered: 3, total_skills: 10,
      }],
    });
    m(progress.skills).mockResolvedValue([{
      skill_id: 'a', name_es: 'Bucles', name_en: 'Loops', module_id: 'm', p_known: 0.5, elo_rating: 1500,
      attempts: 8, correct_count: 5, accuracy: 0.6, mastered: false, fsrs_due: null,
    }]);
  }

  it('las barras crecen desde 0 y las listas entran escalonadas', async () => {
    mockStats();
    render(<StatsScreen />);
    const bar = await screen.findByRole('progressbar');
    expect(bar.firstElementChild).toHaveAttribute('data-fx', 'grow');
    await screen.findByText('Bucles');
    for (const list of screen.getAllByRole('list')) expect(list).toHaveAttribute('data-enter', 'stagger');
  });

  it('con movimiento reducido, barra quieta y sin escalonado', async () => {
    reduce = true;
    mockStats();
    render(<StatsScreen />);
    const bar = await screen.findByRole('progressbar');
    expect(bar.firstElementChild).not.toHaveAttribute('data-fx');
    await screen.findByText('Bucles');
    for (const list of screen.getAllByRole('list')) expect(list).not.toHaveAttribute('data-enter');
  });
});

describe('Cartera, informe y perfil público (46.15 D)', () => {
  it('cartera: listas escalonadas', async () => {
    m(economy.balance).mockResolvedValue({ balance: 10, currency: 'credits', expires_in_days: 90 });
    m(economy.referralCode).mockResolvedValue({ code: 'X', share_url: '' });
    m(economy.prices).mockResolvedValue({
      credit_value_usd: 0.01,
      grifos: [{ event: 'referral_welcome', credits: 200, cap: 'once' }],
      sumideros: [{ item: 'freeze_streak_1day', cost: 150 }],
    });
    render(<WalletScreen />);
    await screen.findByText('Te registras con el código de un amigo');
    const lists = screen.getAllByRole('list');
    expect(lists.length).toBeGreaterThan(0);
    for (const list of lists) expect(list).toHaveAttribute('data-enter', 'stagger');
  });

  it('informe de dominio: rutas escalonadas', async () => {
    m(masteryReports.get).mockResolvedValue({
      code: 'abc', created_at: '2026-10-02T10:00:00Z',
      snapshot: {
        generated_at: '2026-10-02T10:00:00Z', display_name: 'Ana', username: 'ana',
        total_questions_answered: 240, overall_accuracy: 0.81, max_streak: 12,
        tracks: [{
          track_id: 'track01', name_es: 'Python básico', name_en: 'Python basics', icon: '🐍',
          average_mastery: 0.62, skills_mastered: 3, total_skills: 10, mastered_skills: [],
        }],
      },
    });
    render(<MasteryReportScreen code="abc" />);
    await screen.findByText('Python básico');
    expect(screen.getByTestId('report-tracks')).toHaveAttribute('data-enter', 'stagger');
  });

  it('perfil público: certificados y proyectos escalonados', async () => {
    m(profiles.get).mockResolvedValue({
      username: 'ada', display_name: 'Ada', avatar_emoji: '🦉', joined_at: '2026-01-15T00:00:00Z',
      current_streak: 1, mastery_avg: 0, skills_mastered: 1,
      certificates: [{ code: 'c1', track_name_es: 'Python', track_name_en: 'Python', issued_at: '2026-09-01T00:00:00Z' }],
      projects_completed: [{ slug: 'p', name_es: 'API', name_en: 'API', completed_at: '2026-08-01T00:00:00Z' }],
    });
    render(<PublicProfileScreen handle="ada" />);
    await screen.findByText('API');
    expect(screen.getByTestId('public-certs')).toHaveAttribute('data-enter', 'stagger');
    expect(screen.getByTestId('public-projects')).toHaveAttribute('data-enter', 'stagger');
  });
});

describe('Certificado público (46.15 D)', () => {
  const CERT = {
    code: 'a'.repeat(32), username: 'ada', track_id: 'track01', track_name_es: 'Python', track_name_en: 'Python',
    score_pct: 86.5, questions: 20, issued_at: '2026-09-15T10:00:00Z', revoked: false,
  };

  it('válido: el sello se dibuja', async () => {
    m(certificates.verify).mockResolvedValue(CERT);
    render(<CertificateScreen code={CERT.code} />);
    expect(await screen.findByTestId('drawn-check')).toHaveAttribute('data-fx', 'draw');
  });

  it('revocado: no hay sello', async () => {
    m(certificates.verify).mockResolvedValue({ ...CERT, revoked: true });
    render(<CertificateScreen code={CERT.code} />);
    await screen.findByRole('heading', { level: 1 });
    await waitFor(() => expect(certificates.verify).toHaveBeenCalled());
    expect(screen.queryByTestId('drawn-check')).toBeNull();
  });
});

describe('Stagger — presupuesto (46.15 D)', () => {
  it('una lista larga no alarga la entrada: el escalonado total cabe en DUR.response', async () => {
    const { staggerFor } = await import('../components/common/Stagger');
    const { DUR } = await import('../lib/motion');
    expect(staggerFor(3)).toBeCloseTo(0.04);
    // 35 rutas del catálogo a 0,04 s eran 1,4 s de espera antes de la última.
    expect(staggerFor(35) * 35).toBeLessThanOrEqual(DUR.response + 1e-9);
  });
});

// Tabla §7.5 rehecha contra el código (2026-10-24): «cifras con CountUp» en
// Stats y «el saldo cuenta al cambiar» en Cartera estaban prometidas y no hechas.
describe('Cifras que cuentan (46.15 D)', () => {
  it('Stats: las cifras del resumen cuentan al llegar los datos; el lector oye el valor final', async () => {
    m(progress.dashboard).mockResolvedValue({
      level: 1, total_xp: 1500, current_streak: 0, max_streak: 0, streak_freeze_available: 0,
      last_active: null, reviews_due: 0, total_sessions: 1, total_questions_answered: 12, tracks: [],
    });
    m(progress.skills).mockResolvedValue([]);
    render(<StatsScreen />);
    const q = await screen.findByTestId('stats-questions');
    await waitFor(() => expect(q).toHaveAttribute('data-fx', 'count'));
    expect(q.querySelector('.visually-hidden')).toHaveTextContent('12');
  });

  it('Stats con movimiento reducido: la cifra sale ya final, sin contar', async () => {
    reduce = true;
    m(progress.dashboard).mockResolvedValue({
      level: 1, total_xp: 1500, current_streak: 0, max_streak: 0, streak_freeze_available: 0,
      last_active: null, reviews_due: 0, total_sessions: 1, total_questions_answered: 12, tracks: [],
    });
    m(progress.skills).mockResolvedValue([]);
    render(<StatsScreen />);
    const q = await screen.findByTestId('stats-questions');
    await waitFor(() => expect(q.querySelector('[aria-hidden="true"]')).toHaveTextContent('12'));
    expect(q).not.toHaveAttribute('data-fx');
  });

  it('Cartera: el saldo no cuenta al entrar, sí cuando cambia (canjear un código)', async () => {
    m(economy.balance).mockResolvedValue({ balance: 10, currency: 'credits', expires_in_days: 90 });
    m(economy.referralCode).mockResolvedValue({ code: 'X', share_url: '' });
    m(economy.prices).mockResolvedValue({ credit_value_usd: 0.01, grifos: [], sumideros: [] });
    vi.spyOn(economy, 'redeemPromo').mockResolvedValue({ credits: 50, balance: 60 } as never);
    render(<WalletScreen />);
    const amount = await screen.findByTestId('wallet-balance');
    expect(amount).not.toHaveAttribute('data-fx');
    fireEvent.change(screen.getByLabelText(i18n.t('wallet.promoPlaceholder')), { target: { value: 'HOLA' } });
    fireEvent.click(screen.getByRole('button', { name: i18n.t('wallet.redeem') }));
    await waitFor(() => expect(amount).toHaveAttribute('data-fx', 'count'));
    expect(amount.querySelector('.visually-hidden')).toHaveTextContent('60');
  });
});
