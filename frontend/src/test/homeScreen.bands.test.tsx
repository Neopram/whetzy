/**
 * ADR-60 / D-16 (dueño, 2026-10-12): Hoy no enseña porcentajes del modelo
 * («Dominio medio 84 %») mientras no esté calibrado; enseña un estado
 * cualitativo con las respuestas y aciertos que lo sostienen.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { HomeScreen } from '../pages/HomeScreen';
import { useAppStore } from '../stores/useAppStore';
import { progress as progressApi, gamification, type SkillMasteryDetail } from '../services/api';

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

const skill = (over: Partial<SkillMasteryDetail>): SkillMasteryDetail => ({
  skill_id: 'sk1', name_es: 'Bucles', name_en: 'Loops', module_id: 'mod01',
  p_known: 0.5, elo_rating: 1500, attempts: 0, correct_count: 0,
  accuracy: 0, mastered: false, fsrs_due: null,
  ...over,
});

beforeEach(async () => {
  await i18n.changeLanguage('es');
  useAppStore.setState((s) => ({ user: { ...s.user, language: 'es' } }));
  dashboard.mockResolvedValue({
    level: 1, total_xp: 0, current_streak: 0, max_streak: 0, streak_freeze_available: 0,
    last_active: null, reviews_due: 0, total_sessions: 3,
    tracks: [{
      track_id: 'track01', name_es: 'Python', name_en: 'Python', icon: '🐍', color: '#000',
      average_mastery: 0.84, skills_mastered: 2, total_skills: 10,
    }],
  });
  decaying.mockReturnValue(new Promise(() => {}));
  missions.mockReturnValue(new Promise(() => {}));
});
afterEach(() => { cleanup(); vi.unstubAllEnvs(); });

describe('Hoy — estados con evidencia, sin % del modelo (ADR-60)', () => {
  it('con poca evidencia dice «Evidencia insuficiente» y cuántas respuestas hay', async () => {
    skills.mockResolvedValue([skill({ skill_id: 'a', attempts: 3, correct_count: 2, p_known: 0.84 })]);
    render(<HomeScreen />);
    expect(await screen.findByTestId('home-band')).toHaveTextContent('Evidencia insuficiente');
    expect(screen.getAllByText(/3 respuestas · 2 aciertos/).length).toBeGreaterThan(0);
  });

  it('con evidencia y todo dominado dice «Fuerte»', async () => {
    skills.mockResolvedValue([skill({ skill_id: 'a', attempts: 12, correct_count: 11, p_known: 0.97 })]);
    render(<HomeScreen />);
    expect(await screen.findByTestId('home-band')).toHaveTextContent('Fuerte');
  });

  it('ningún porcentaje del modelo llega a la pantalla', async () => {
    skills.mockResolvedValue([
      skill({ skill_id: 'a', attempts: 12, correct_count: 9, p_known: 0.84 }),
      skill({ skill_id: 'b', attempts: 2, correct_count: 1, p_known: 0.42 }),
    ]);
    render(<HomeScreen />);
    await screen.findByText('Python');
    await screen.findAllByText(/respuestas · /);
    expect(document.body.textContent).not.toMatch(/84 ?%|42 ?%/);
  });
});

describe('Hoy — pasada del 2026-10-15 (PR 1b)', () => {
  it('con 40 respuestas repartidas no dice «menos de 7 respuestas»: lo que falta es por skill', async () => {
    skills.mockResolvedValue(
      Array.from({ length: 8 }, (_, i) => skill({ skill_id: `s${i}`, attempts: 5, correct_count: 1 })),
    );
    render(<HomeScreen />);
    expect(await screen.findByTestId('home-band')).toHaveTextContent('Evidencia insuficiente');
    expect(screen.getByText(/40 respuestas · 8 aciertos/)).toBeInTheDocument();
    expect(screen.getByText(/Ninguna habilidad tiene aún 7 respuestas/)).toBeInTheDocument();
    expect(screen.queryByText(/Menos de 7 respuestas/)).toBeNull();
  });

  it('fuera de desarrollo no enseña el Elo crudo del modelo', async () => {
    vi.stubEnv('DEV', false);
    skills.mockResolvedValue([skill({ skill_id: 'a', elo_rating: 1600, attempts: 5 })]);
    render(<HomeScreen />);
    await screen.findByText('Bucles');
    expect(screen.queryByText(/Elo/)).toBeNull();
  });

  it('sin repasos vencidos pero con skills que se olvidan hoy, no dice «Vuelve mañana»', async () => {
    decaying.mockResolvedValue([
      { skill_id: 'a', name_es: 'Bucles', name_en: 'Loops', days_until_due: 0 },
    ]);
    skills.mockResolvedValue([]);
    render(<HomeScreen />);
    expect(await screen.findByText('Nada vencido en tu calendario de repaso.')).toBeInTheDocument();
    expect(screen.queryByText(/Vuelve mañana/)).toBeNull();
  });

  it('sin misiones de hoy no pinta una tarjeta «0/0»', async () => {
    missions.mockResolvedValue([]);
    skills.mockResolvedValue([]);
    render(<HomeScreen />);
    await screen.findByText('Python');
    expect(screen.queryByText(i18n.t('home.missions'))).toBeNull();
  });

  it('una ruta sin skills dominadas no lleva barra vacía; Proyectos dice «Paso a paso»', async () => {
    dashboard.mockResolvedValue({
      level: 1, total_xp: 0, current_streak: 0, max_streak: 0, streak_freeze_available: 0,
      last_active: null, reviews_due: 0, total_sessions: 3,
      tracks: [{
        track_id: 'track01', name_es: 'Python', name_en: 'Python', icon: '🐍', color: '#000',
        average_mastery: 0.2, skills_mastered: 0, total_skills: 10,
      }],
    });
    skills.mockResolvedValue([]);
    render(<HomeScreen />);
    await screen.findByText('Python');
    expect(screen.queryByRole('progressbar', { name: 'Python' })).toBeNull();
    expect(screen.getByText('Paso a paso')).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/-by-/);
  });
});
