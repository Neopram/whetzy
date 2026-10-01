/**
 * 34.12: `t('home.days')` se llamaba sin `{ count }`, así que i18next nunca
 * elegía la forma singular — «Tu racha: 1 días» en vez de «Tu racha: 1 día».
 * `home.decayInDays` tenía el mismo hueco (`{{count}} días` para 1 día).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { HomeScreen } from '../pages/HomeScreen';
import { useAppStore } from '../stores/useAppStore';
import { progress as progressApi, gamification } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    progress: { ...actual.progress, dashboard: vi.fn(), decaying: vi.fn(), skills: vi.fn() },
    gamification: { ...actual.gamification, missions: vi.fn() },
  };
});

const dashboard = progressApi.dashboard as unknown as ReturnType<typeof vi.fn>;
const decaying = progressApi.decaying as unknown as ReturnType<typeof vi.fn>;
const skills = progressApi.skills as unknown as ReturnType<typeof vi.fn>;
const missions = gamification.missions as unknown as ReturnType<typeof vi.fn>;

beforeEach(async () => {
  await i18n.changeLanguage('es');
  // Nunca se resuelven dentro del test: la aserción se hace en el render
  // síncrono, antes de que estas promesas lleguen a asentarse, que es
  // exactamente cuando `streak` cae al valor de la store (línea 36 de
  // HomeScreen.tsx: `dash.data?.current_streak ?? user.currentStreak`).
  dashboard.mockReturnValue(new Promise(() => {}));
  decaying.mockReturnValue(new Promise(() => {}));
  skills.mockReturnValue(new Promise(() => {}));
  missions.mockReturnValue(new Promise(() => {}));
});
afterEach(cleanup);

describe('HomeScreen — pluralización de la racha (34.12)', () => {
  it('ES: racha de 1 día dice "1 día", no "1 días"', () => {
    useAppStore.setState((s) => ({ user: { ...s.user, currentStreak: 1, language: 'es' } }));
    render(<HomeScreen />);
    expect(screen.getByText(/Tu racha: 1 día\b/)).toBeInTheDocument();
    expect(screen.queryByText(/Tu racha: 1 días/)).not.toBeInTheDocument();
  });

  it('ES: racha de 5 días dice "5 días"', () => {
    useAppStore.setState((s) => ({ user: { ...s.user, currentStreak: 5, language: 'es' } }));
    render(<HomeScreen />);
    expect(screen.getByText(/Tu racha: 5 días/)).toBeInTheDocument();
  });

  it('EN: a 1-day streak says "1 day", not "1 days"', async () => {
    await i18n.changeLanguage('en');
    useAppStore.setState((s) => ({ user: { ...s.user, currentStreak: 1, language: 'en' } }));
    render(<HomeScreen />);
    expect(screen.getByText(/Your streak: 1 day\b/)).toBeInTheDocument();
    expect(screen.queryByText(/Your streak: 1 days/)).not.toBeInTheDocument();
  });
});

describe('i18n — home.days y home.decayInDays pluralizan en los dos idiomas (34.12)', () => {
  it('home.days: singular/plural correctos en ES y EN', async () => {
    await i18n.changeLanguage('es');
    expect(i18n.t('home.days', { count: 1 })).toBe('día');
    expect(i18n.t('home.days', { count: 2 })).toBe('días');
    await i18n.changeLanguage('en');
    expect(i18n.t('home.days', { count: 1 })).toBe('day');
    expect(i18n.t('home.days', { count: 2 })).toBe('days');
  });

  it('home.decayInDays: singular/plural correctos en ES y EN', async () => {
    await i18n.changeLanguage('es');
    expect(i18n.t('home.decayInDays', { count: 1 })).toBe('en 1 día');
    expect(i18n.t('home.decayInDays', { count: 3 })).toBe('en 3 días');
    await i18n.changeLanguage('en');
    expect(i18n.t('home.decayInDays', { count: 1 })).toBe('in 1 day');
    expect(i18n.t('home.decayInDays', { count: 3 })).toBe('in 3 days');
  });
});
