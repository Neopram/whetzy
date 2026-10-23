/**
 * Revisión de UI del 2026-10-23: Hoy pintaba «Evidencia insuficiente» mientras
 * las skills cargaban y también si la petición fallaba, porque la banda sale de
 * `skills.data ?? []` y `overallBand([])` es `insufficient`. Un fallo de red se
 * leía como un diagnóstico del alumno.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
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
  useAppStore.setState((s) => ({ user: { ...s.user, language: 'es' } }));
  dashboard.mockReturnValue(new Promise(() => {}));
  decaying.mockReturnValue(new Promise(() => {}));
  missions.mockReturnValue(new Promise(() => {}));
});
afterEach(() => { cleanup(); vi.clearAllMocks(); });

describe('Hoy — la banda no se inventa sin datos', () => {
  it('mientras cargan las skills no dice «Evidencia insuficiente»', async () => {
    skills.mockReturnValue(new Promise(() => {}));
    render(<HomeScreen />);
    expect(await screen.findByTestId('home-band-loading')).toBeInTheDocument();
    expect(screen.queryByTestId('home-band')).toBeNull();
    // La banda guarda su sitio mientras carga (sin salto al llegar los datos),
    // pero oculta: ni se ve ni la lee el lector de pantalla.
    const visibles = screen
      .queryAllByText(i18n.t('bands.insufficient'))
      .filter((el) => !el.closest('[aria-hidden="true"]'));
    expect(visibles).toHaveLength(0);
  });

  it('si la petición falla lo dice y deja reintentar, sin banda', async () => {
    skills.mockRejectedValueOnce(new Error('Network error'));
    render(<HomeScreen />);
    expect(await screen.findByText(i18n.t('home.bandError'))).toBeInTheDocument();
    expect(screen.queryByTestId('home-band')).toBeNull();

    skills.mockResolvedValueOnce([]);
    const calls = skills.mock.calls.length;
    fireEvent.click(screen.getByRole('button', { name: i18n.t('home.retryBand') }));
    expect(skills.mock.calls.length).toBe(calls + 1);
    expect(await screen.findByTestId('home-band')).toBeInTheDocument();
  });
});
