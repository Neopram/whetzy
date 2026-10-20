/**
 * 46.3c (docs/PLAN_UI_AVANZADA.md §2, ola 1): «Tu mayor palanca», que hasta
 * ahora solo salía en Preparación, sube a la primera tarjeta de Hoy cuando la
 * ruta activa es una certificación. Es el mismo cálculo que Preparación
 * (peso × lo que le falta al dominio), no uno nuevo. En una ruta que no es de
 * certificación no hay dominios de examen y no se pide la preparación.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, within } from '@testing-library/react';
import i18n from '../i18n';
import { HomeScreen } from '../pages/HomeScreen';
import { useAppStore } from '../stores/useAppStore';
import {
  content as contentApi,
  exams,
  gamification,
  progress as progressApi,
  type CertificationReadiness,
  type DomainReadiness,
} from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    progress: { ...actual.progress, dashboard: vi.fn(), decaying: vi.fn(), skills: vi.fn(), curriculum: vi.fn() },
    gamification: { ...actual.gamification, missions: vi.fn() },
    content: { ...actual.content, tracks: vi.fn() },
    exams: { ...actual.exams, certificationReadiness: vi.fn() },
  };
});

const dashboard = progressApi.dashboard as unknown as ReturnType<typeof vi.fn>;
const decaying = progressApi.decaying as unknown as ReturnType<typeof vi.fn>;
const skills = progressApi.skills as unknown as ReturnType<typeof vi.fn>;
const curriculum = progressApi.curriculum as unknown as ReturnType<typeof vi.fn>;
const missions = gamification.missions as unknown as ReturnType<typeof vi.fn>;
const tracks = contentApi.tracks as unknown as ReturnType<typeof vi.fn>;
const readiness = exams.certificationReadiness as unknown as ReturnType<typeof vi.fn>;

const dom = (id: string, name: string, weight: number, mean: number | null, ready = false): DomainReadiness =>
  ({
    domain_id: id, name_es: name, name_en: name, weight_pct: weight, p_known_mean: mean, ready,
    skills_assessed: 1, skills_total: 3, answers: 0, correct: 0,
  }) as unknown as DomainReadiness;

const track = (id: string, isCert: boolean) =>
  ({ id, name_es: id, name_en: id, is_certification: isCert, icon: 'x', color: '#000', order: 1 });

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
  useAppStore.setState((s) => ({ user: { ...s.user, language: 'es', targetCertificationId: null }, activeTrackId: 'track_cert' }));
  dashboard.mockResolvedValue({
    level: 1, total_xp: 0, current_streak: 0, max_streak: 0, streak_freeze_available: 0,
    last_active: null, reviews_due: 0, total_sessions: 0, total_questions_answered: 0, overall_accuracy: 0,
    tracks: [],
  });
  decaying.mockResolvedValue([]);
  skills.mockResolvedValue([]);
  curriculum.mockResolvedValue({ track_id: 'track_cert', modules: [] });
  missions.mockReturnValue(new Promise(() => {}));
  tracks.mockResolvedValue([track('track_cert', true), track('track_py', false)]);
  readiness.mockResolvedValue({
    track_id: 'track_cert',
    domains: [
      { ...dom('d1', 'Pesado casi listo', 40, 0.7), answers: 12, correct: 9 } as DomainReadiness,  // 40 × 0,05 = 2
      dom('d2', 'Medio a cero', 20, 0),         // 20 × 0,75 = 15 ← palanca
      dom('d3', 'Ya listo', 40, 0.9, true),
    ],
    ready_for_simulacro: false,
  } as unknown as CertificationReadiness);
});
afterEach(() => cleanup());

describe('Hoy — «Tu mayor palanca» arriba (46.3c)', () => {
  it('con una certificación activa, la palanca es la primera tarjeta y es la misma que en Preparación', async () => {
    render(<HomeScreen />);
    const lever = await screen.findByRole('region', { name: 'Tu mayor palanca' });
    expect(within(lever).getByText(/Medio a cero: vale el 20 % del examen/)).toBeInTheDocument();
    expect(within(lever).getByRole('button', { name: 'Practicar esta certificación' })).toBeInTheDocument();
    // Antes que el estado y que «Siguiente paso»: es lo primero tras el saludo.
    const band = await screen.findByTestId('home-band');
    expect(lever.compareDocumentPosition(band) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(readiness).toHaveBeenCalledWith('track_cert');
  });

  it('practicar desde Hoy arranca el estudio de esa certificación', async () => {
    const startQuiz = vi.fn();
    useAppStore.setState({ startQuiz } as never);
    render(<HomeScreen />);
    const lever = await screen.findByRole('region', { name: 'Tu mayor palanca' });
    within(lever).getByRole('button', { name: 'Practicar esta certificación' }).click();
    expect(startQuiz).toHaveBeenCalledWith('study', 10, { trackId: 'track_cert' });
  });

  it('con la ruta de aprendizaje activa, sale la palanca de la certificación elegida en el onboarding', async () => {
    const startQuiz = vi.fn();
    useAppStore.setState((s) => ({
      activeTrackId: 'track_py', startQuiz, user: { ...s.user, targetCertificationId: 'track_cert' },
    }) as never);
    render(<HomeScreen />);
    const lever = await screen.findByRole('region', { name: 'Tu mayor palanca' });
    // La certificación no es la ruta activa: la tarjeta dice cuál es.
    expect(within(lever).getByText(/· track_cert/)).toBeInTheDocument();
    within(lever).getByRole('button', { name: 'Practicar esta certificación' }).click();
    expect(readiness).toHaveBeenCalledWith('track_cert');
    expect(startQuiz).toHaveBeenCalledWith('study', 10, { trackId: 'track_cert' });
  });

  it('en una ruta que no es de certificación y sin certificación elegida no se pide la preparación ni hay palanca', async () => {
    useAppStore.setState((s) => ({ activeTrackId: 'track_py', user: { ...s.user, targetCertificationId: null } }));
    render(<HomeScreen />);
    await screen.findByTestId('home-band');
    await vi.waitFor(() => expect(tracks).toHaveBeenCalled());
    await new Promise((r) => setTimeout(r, 0));
    expect(readiness).not.toHaveBeenCalled();
    expect(screen.queryByRole('region', { name: 'Tu mayor palanca' })).toBeNull();
  });

  it('sin ninguna respuesta en la certificación no hay palanca: lo primero sigue siendo la lección', async () => {
    readiness.mockResolvedValue({
      track_id: 'track_cert', domains: [dom('d1', 'A', 60, null), dom('d2', 'B', 40, null)],
      ready_for_simulacro: false,
    } as unknown as CertificationReadiness);
    render(<HomeScreen />);
    await screen.findByTestId('home-band');
    await vi.waitFor(() => expect(readiness).toHaveBeenCalled());
    await new Promise((r) => setTimeout(r, 0));
    expect(screen.queryByRole('region', { name: 'Tu mayor palanca' })).toBeNull();
  });

  it('con todos los dominios listos no hay palanca que enseñar', async () => {
    readiness.mockResolvedValue({
      track_id: 'track_cert', domains: [{ ...dom('d1', 'A', 50, 0.9, true), answers: 20 } as DomainReadiness, dom('d2', 'B', 50, 0.8, true)],
      ready_for_simulacro: true,
    } as unknown as CertificationReadiness);
    render(<HomeScreen />);
    await screen.findByTestId('home-band');
    await vi.waitFor(() => expect(readiness).toHaveBeenCalled());
    expect(screen.queryByRole('region', { name: 'Tu mayor palanca' })).toBeNull();
  });
});
