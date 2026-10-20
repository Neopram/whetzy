/**
 * 46.12 (docs/PLAN_UI_AVANZADA.md §7.3): Hoy cuenta lo que cambió desde la
 * última foto. El «n/m» de misiones y las skills dominadas de cada ruta cuentan
 * desde su valor anterior, el icono de la ruta que subió hace un toque, y la
 * etiqueta de banda de un nodo que subió entra con AnimatePresence. Sin foto
 * previa nada cuenta ni late.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { HomeScreen } from '../pages/HomeScreen';
import { trackMoments } from '../lib/homeMoments';
import { useAppStore } from '../stores/useAppStore';
import { progress as progressApi, gamification, type SkillMasteryDetail } from '../services/api';

let reduce = false;
vi.mock('framer-motion', async (importOriginal) => {
  const actual = await importOriginal<typeof import('framer-motion')>();
  return { ...actual, useReducedMotion: () => reduce };
});
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
const mission = (id: string, completed: boolean) => ({
  mission: { id, type: 'questions_answered', target_value: 3, xp_reward: 20, name_es: `Misión ${id}`, name_en: `Mission ${id}` },
  progress: completed ? 3 : 1, completed,
});
const today = new Date().toISOString().slice(0, 10);

beforeEach(async () => {
  reduce = false;
  localStorage.clear();
  await i18n.changeLanguage('es');
  useAppStore.setState((s) => ({ user: { ...s.user, id: 'u1', language: 'es' } }));
  dashboard.mockResolvedValue({
    level: 1, total_xp: 0, current_streak: 0, max_streak: 0, streak_freeze_available: 0,
    last_active: null, reviews_due: 0, total_sessions: 3,
    tracks: [{
      track_id: 'track01', name_es: 'Python', name_en: 'Python', icon: '🐍', color: '#000',
      average_mastery: 0.5, skills_mastered: 3, total_skills: 10,
    }],
  });
  decaying.mockReturnValue(new Promise(() => {}));
  skills.mockResolvedValue([]);
  missions.mockResolvedValue([mission('m1', true), mission('m2', false)]);
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe('homeMoments — rutas (46.12)', () => {
  it('sin foto, nada; si sube, el valor anterior; si no, nada', () => {
    expect(trackMoments('u1', [{ id: 't1', mastered: 2 }])).toEqual({});
    expect(trackMoments('u1', [{ id: 't1', mastered: 4 }])).toEqual({ t1: 2 });
    expect(trackMoments('u1', [{ id: 't1', mastered: 4 }])).toEqual({});
  });
});

describe('Hoy — contadores (46.12)', () => {
  it('misiones: el «n/m» cuenta desde las que había completas', async () => {
    localStorage.setItem(`whetzy_fx_missions_u1_${today}`, JSON.stringify({ m1: false, m2: false }));
    render(<HomeScreen />);
    // La foto se lee en un efecto, tras el primer pintado.
    await waitFor(() => expect(screen.getByTestId('missions-count')).toHaveAttribute('data-from', '0'));
    expect(screen.getByTestId('missions-count')).toHaveTextContent('1/2');
  });

  it('rutas: lo dominado cuenta desde la foto y el icono hace un toque', async () => {
    localStorage.setItem('whetzy_fx_tracks_u1', JSON.stringify({ track01: 1 }));
    render(<HomeScreen />);
    await waitFor(() => expect(screen.getByTestId('track-mastered-track01')).toHaveAttribute('data-from', '1'));
    expect(screen.getByTestId('track-mastered-track01')).toHaveTextContent('3/10');
    expect(screen.getByTestId('track-icon-track01')).toHaveAttribute('data-fx', 'tap');
  });

  it('sin foto previa, nada cuenta ni late', async () => {
    render(<HomeScreen />);
    await screen.findByText('Misión m1');
    expect(screen.getByTestId('missions-count')).not.toHaveAttribute('data-from');
    expect(screen.getByTestId('track-mastered-track01')).not.toHaveAttribute('data-from');
    expect(screen.getByTestId('track-icon-track01')).not.toHaveAttribute('data-fx');
  });

  it('con movimiento reducido no cuenta ni late, aunque haya foto', async () => {
    reduce = true;
    localStorage.setItem('whetzy_fx_tracks_u1', JSON.stringify({ track01: 1 }));
    localStorage.setItem(`whetzy_fx_missions_u1_${today}`, JSON.stringify({ m1: false, m2: false }));
    render(<HomeScreen />);
    await screen.findByText('Misión m1');
    await waitFor(() => expect(localStorage.getItem('whetzy_fx_tracks_u1')).toContain('"track01":3'));
    expect(screen.getByTestId('missions-count')).not.toHaveAttribute('data-from');
    expect(screen.getByTestId('track-mastered-track01')).not.toHaveAttribute('data-from');
    expect(screen.getByTestId('track-icon-track01')).not.toHaveAttribute('data-fx');
  });

  it('banda que sube: la etiqueta nueva entra animada', async () => {
    localStorage.setItem('whetzy_fx_bands_u1', JSON.stringify({ a: 'developing' }));
    skills.mockResolvedValue([skill({ skill_id: 'a', attempts: 12, correct_count: 11, p_known: 0.97 })]);
    render(<HomeScreen />);
    await waitFor(() => expect(document.querySelector('[data-band-enter]')).not.toBeNull());
    expect(document.querySelector('[data-band-enter]')).toHaveTextContent('Fuerte');
  });
});
