/**
 * 34.6/34.7 (2026-10-24): lo que axe no marca pero un lector de pantalla oye mal.
 * - Liga: ▲ y ▼ se leían «triángulo negro hacia arriba»; ahora dicen la zona.
 * - Barra inferior: «Main navigation» fijo en inglés también en español.
 * - Auth: las dos pestañas (Crear cuenta / Iniciar sesión) no decían cuál está
 *   activa; cambian de modo, no tienen paneles, así que `aria-pressed`.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { LeagueScreen } from '../pages/LeagueScreen';
import { BottomNav } from '../components/layout/BottomNav';
import { AuthScreen } from '../pages/AuthScreen';
import { auth, league as leagueApi } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    league: { current: vi.fn(), setParticipation: vi.fn() },
    auth: { ...actual.auth, oauthProviders: vi.fn(), startOAuth: vi.fn() },
  };
});

const row = (rank: number) => ({
  rank, user_id: `u${rank}`, username: `u${rank}`, display_name: `U${rank}`, avatar_emoji: '🦊',
  xp_earned: 100 - rank, is_current_user: rank === 1,
});

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
  (auth.oauthProviders as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ providers: [] });
});
afterEach(cleanup);

describe('nombres accesibles', () => {
  it('Liga: las flechas dicen zona de ascenso y de descenso', async () => {
    (leagueApi.current as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      league: { id: 'bronze', name: 'Bronce', tier: 'bronze', min_xp: 0 },
      week_start: '2026-10-19',
      // Las flechas van en las filas, del 4.º puesto en adelante (1-3 son el podio).
      standings: [1, 2, 3, 4, 5, 6, 7, 8].map(row),
      promotion_zone: 5, demotion_zone: 2, total_members: 8, participating: true,
    });
    render(<LeagueScreen />);
    expect(await screen.findAllByRole('img', { name: i18n.t('league.promotionZone') })).toHaveLength(2);
    expect(screen.getAllByRole('img', { name: i18n.t('league.demotionZone') })).toHaveLength(2);
  });

  it('barra inferior: su nombre va en el idioma de la app', () => {
    render(<BottomNav />);
    expect(screen.getByRole('navigation', { name: 'Navegación principal' })).toBeInTheDocument();
  });

  it('Auth: la pestaña activa lo dice', async () => {
    window.history.replaceState(null, '', '/auth');
    render(<AuthScreen onAuthed={() => {}} />);
    const register = await screen.findByRole('button', { name: i18n.t('auth.register') });
    const login = screen.getByRole('button', { name: i18n.t('auth.login') });
    const [on, off] = register.getAttribute('aria-pressed') === 'true' ? [register, login] : [login, register];
    expect(on).toHaveAttribute('aria-pressed', 'true');
    expect(off).toHaveAttribute('aria-pressed', 'false');
    fireEvent.click(off);
    expect(off).toHaveAttribute('aria-pressed', 'true');
    expect(on).toHaveAttribute('aria-pressed', 'false');
  });
});
