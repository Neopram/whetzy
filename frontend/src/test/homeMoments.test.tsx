/**
 * 46.3b (docs/PLAN_UI_AVANZADA.md §6.2): Hoy celebra una vez lo que cambió
 * desde la última visita (misión completada, skill que sube de banda), con una
 * foto en localStorage. Sin foto previa no se celebra nada.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { HomeScreen } from '../pages/HomeScreen';
import { bandMoments, missionMoments } from '../lib/homeMoments';
import * as fx from '../lib/feedbackFx';
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
const mission = (completed: boolean, progress = completed ? 3 : 2) => ({
  mission: { id: 'm1', type: 'questions_answered', target_value: 3, xp_reward: 20, name_es: 'Responde 3', name_en: 'Answer 3' },
  progress, completed,
});

const today = new Date().toISOString().slice(0, 10);

beforeEach(async () => {
  localStorage.clear();
  await i18n.changeLanguage('es');
  useAppStore.setState((s) => ({ user: { ...s.user, id: 'u1', language: 'es' } }));
  dashboard.mockResolvedValue({
    level: 1, total_xp: 0, current_streak: 0, max_streak: 0, streak_freeze_available: 0,
    last_active: null, reviews_due: 0, total_sessions: 3, tracks: [],
  });
  decaying.mockReturnValue(new Promise(() => {}));
  skills.mockResolvedValue([]);
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('homeMoments — la foto', () => {
  it('misiones: sin foto, nada; de pendiente a completa, una vez', () => {
    expect(missionMoments('u1', '2026-10-18', [{ id: 'm1', completed: false }])).toEqual([]);
    expect(missionMoments('u1', '2026-10-18', [{ id: 'm1', completed: true }])).toEqual(['m1']);
    expect(missionMoments('u1', '2026-10-18', [{ id: 'm1', completed: true }])).toEqual([]);
  });

  it('misiones: la primera visita del día con la misión ya completa no celebra', () => {
    expect(missionMoments('u1', '2026-10-19', [{ id: 'm1', completed: true }])).toEqual([]);
  });

  it('bandas: solo cuenta subir, y una skill nueva no es una subida', () => {
    expect(bandMoments('u1', [{ id: 'a', band: 'insufficient' }, { id: 'b', band: 'strong' }])).toEqual([]);
    expect(bandMoments('u1', [
      { id: 'a', band: 'developing' },
      { id: 'b', band: 'developing' },
      { id: 'c', band: 'strong' },
    ])).toEqual(['a']);
    expect(bandMoments('u1', [{ id: 'a', band: 'developing' }])).toEqual([]);
  });

  it('sin localStorage no revienta y no celebra', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('privado'); });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('privado'); });
    expect(missionMoments('u1', today, [{ id: 'm1', completed: true }])).toEqual([]);
    expect(bandMoments('u1', [{ id: 'a', band: 'strong' }])).toEqual([]);
  });
});

describe('Hoy — momentos (46.3b)', () => {
  it('misión completada desde la última visita: check dibujado y un solo sonido; la siguiente visita, nada', async () => {
    localStorage.setItem(`whetzy_fx_missions_u1_${today}`, JSON.stringify({ m1: false }));
    const emit = vi.spyOn(fx, 'emit');
    missions.mockResolvedValue([mission(true)]);
    render(<HomeScreen />);
    expect(await screen.findByTestId('mission-check')).toBeInTheDocument();
    expect(emit).toHaveBeenCalledTimes(1);
    expect(emit).toHaveBeenCalledWith({ type: 'mission' });

    cleanup();
    emit.mockClear();
    render(<HomeScreen />);
    await screen.findByText('Responde 3');
    expect(screen.queryByTestId('mission-check')).toBeNull();
    expect(emit).not.toHaveBeenCalled();
  });

  it('skill que sube de banda: su nodo lo marca', async () => {
    localStorage.setItem('whetzy_fx_bands_u1', JSON.stringify({ a: 'developing' }));
    missions.mockResolvedValue([]);
    skills.mockResolvedValue([skill({ skill_id: 'a', attempts: 12, correct_count: 11, p_known: 0.97 })]);
    render(<HomeScreen />);
    await waitFor(() => expect(document.querySelector('[data-band-up]')).not.toBeNull());
  });
});
