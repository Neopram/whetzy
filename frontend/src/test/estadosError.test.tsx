/**
 * Revisión de UI del 2026-10-23: varias pantallas confundían un fallo de red
 * con «no hay nada». Estadísticas decía «sin datos», Perfil «sin insignias»,
 * Proyecto «no encontrado» y Duelos «no tienes duelos» cuando la API fallaba.
 * Un fallo se dice como fallo y se puede reintentar.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import i18n from '../i18n';
import { StatsScreen } from '../pages/StatsScreen';
import { ProfileScreen } from '../pages/ProfileScreen';
import { ProjectScreen } from '../pages/ProjectScreen';
import { DuelScreen } from '../pages/DuelScreen';
import { duels, gamification, progress, projects } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    progress: { ...actual.progress, dashboard: vi.fn(), skills: vi.fn() },
    gamification: { ...actual.gamification, badges: vi.fn() },
    projects: { ...actual.projects, list: vi.fn(), get: vi.fn() },
    duels: { ...actual.duels, my: vi.fn() },
  };
});

const m = (f: unknown) => f as ReturnType<typeof vi.fn>;
const fail = () => Promise.reject(new Error('Network error'));

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
});
afterEach(cleanup);

describe('Un fallo de red no se pinta como vacío', () => {
  it('Estadísticas: dice que no cargó y reintenta, no «sin datos»', async () => {
    m(progress.dashboard).mockImplementation(fail);
    m(progress.skills).mockImplementation(fail);
    render(<StatsScreen />);
    const alerts = await screen.findAllByText(i18n.t('common.loadError'));
    expect(alerts.length).toBe(2);
    expect(screen.queryByText(i18n.t('stats.noData'))).toBeNull();

    m(progress.dashboard).mockResolvedValue({ tracks: [], total_xp: 0, total_questions_answered: 0 });
    const before = m(progress.dashboard).mock.calls.length;
    fireEvent.click(screen.getAllByRole('button', { name: i18n.t('common.retry') })[0]);
    expect(m(progress.dashboard).mock.calls.length).toBe(before + 1);
  });

  it('Perfil: un fallo de insignias no dice «sin insignias»', async () => {
    m(gamification.badges).mockImplementation(fail);
    render(<ProfileScreen />);
    const grid = (await screen.findByText(i18n.t('profile.badges'))).closest('section') ?? document.body;
    expect(await within(grid as HTMLElement).findByText(i18n.t('common.loadError'))).toBeInTheDocument();
    expect(screen.queryByText(i18n.t('profile.noBadges'))).toBeNull();
  });

  it('Proyectos: la lista que no carga lo dice', async () => {
    m(projects.list).mockImplementation(fail);
    render(<ProjectScreen />);
    expect(await screen.findByText(i18n.t('common.loadError'))).toBeInTheDocument();
  });

  it('Proyecto: un fallo al abrirlo no dice «no encontrado»; las tarjetas se abren con teclado', async () => {
    m(projects.list).mockResolvedValue([{
      id: 'p1', slug: 'calc', name_es: 'Calculadora', name_en: 'Calculator', difficulty: 1,
      runtime: 'python', source_license: 'MIT', track_id: 'track01',
    }]);
    m(projects.get).mockImplementation(fail);
    render(<ProjectScreen />);
    // Era un <div> con onClick: con teclado no se podía abrir ningún proyecto.
    const card = await screen.findByRole('button', { name: /Calculadora/ });
    fireEvent.click(card);
    expect(await screen.findByText(i18n.t('common.loadError'))).toBeInTheDocument();
    expect(screen.queryByText(i18n.t('project.notFound'))).toBeNull();
  });

  it('Duelos: la lista que no carga no dice «no tienes duelos»', async () => {
    m(duels.my).mockImplementation(fail);
    render(<DuelScreen />);
    expect(await screen.findByText(i18n.t('common.loadError'))).toBeInTheDocument();
    expect(screen.queryByText(i18n.t('duel.noDuels'))).toBeNull();

    m(duels.my).mockResolvedValue([]);
    fireEvent.click(screen.getByRole('button', { name: i18n.t('common.retry') }));
    expect(await screen.findByText(i18n.t('duel.noDuels'))).toBeInTheDocument();
  });
});
