/**
 * 43.5 (ADR-65 D7, H.60): «Estudiar» abre la siguiente lección pendiente de
 * la ruta activa y solo practica cuando no queda ninguna. Antes arrancaba
 * siempre un quiz, y con una cuenta nueva acababa en «Abre una lección primero».
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { HomeScreen } from '../pages/HomeScreen';
import { useAppStore } from '../stores/useAppStore';
import { gamification, progress as progressApi, type CurriculumModule, type CurriculumSkill } from '../services/api';
import { canPractice, nextLessonSkillId } from '../lib/nextStep';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    progress: {
      ...actual.progress, dashboard: vi.fn(), decaying: vi.fn(), skills: vi.fn(), curriculum: vi.fn(),
    },
    gamification: { ...actual.gamification, missions: vi.fn() },
  };
});

const m = (f: unknown) => f as ReturnType<typeof vi.fn>;

const sk = (id: string, order: number, over: Partial<CurriculumSkill> = {}): CurriculumSkill => ({
  skill_id: id, name_es: `ES ${id}`, name_en: `EN ${id}`, order, p_known: 0, mastered: false,
  attempts: 0, lesson_seen: false, practice_unlocked: false, ...over,
});

const mod = (id: string, order: number, skills: CurriculumSkill[], status: CurriculumModule['status'] = 'available'): CurriculumModule => ({
  id, name_es: id, name_en: id, order, description_es: '', description_en: '', min_mastery_to_unlock: 0.7,
  level: 1, average_mastery: 0, status, prerequisite_id: null, prerequisite_met: status !== 'locked', skills,
});

const cur = (modules: CurriculumModule[]) => ({
  track_id: 'track01', name_es: 'P', name_en: 'P', icon: '', color: '', mastery_threshold: 0.95, modules,
});

describe('nextLessonSkillId', () => {
  it('la primera pendiente por orden de módulo y de skill, saltando módulos bloqueados', () => {
    const c = cur([
      mod('m2', 2, [sk('b1', 1)], 'locked'),
      mod('m1', 1, [sk('a2', 2), sk('a1', 1, { lesson_seen: true })]),
    ]);
    expect(nextLessonSkillId(c)).toBe('a2');
  });

  it('una skill desbloqueada por test-out o por la prueba no cuenta como pendiente', () => {
    expect(canPractice(sk('x', 1, { practice_unlocked: true }))).toBe(true);
    expect(nextLessonSkillId(cur([mod('m1', 1, [sk('a1', 1, { practice_unlocked: true })])]))).toBeNull();
  });
});

describe('Hoy: lección primero', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    await i18n.changeLanguage('es');
    useAppStore.setState((s) => ({ user: { ...s.user, language: 'es' }, activeTrackId: 'track01' }));
    m(progressApi.dashboard).mockResolvedValue({
      level: 1, total_xp: 0, current_streak: 0, max_streak: 0, streak_freeze_available: 0,
      last_active: null, reviews_due: 0, total_sessions: 0, tracks: [],
    });
    m(progressApi.decaying).mockResolvedValue([]);
    m(progressApi.skills).mockResolvedValue([]);
    m(gamification.missions).mockReturnValue(new Promise(() => {}));
  });
  afterEach(cleanup);

  it('con una cuenta nueva, «Estudiar» abre la primera lección', async () => {
    const startLesson = vi.fn();
    const startQuiz = vi.fn();
    useAppStore.setState({ startLesson, startQuiz });
    m(progressApi.curriculum).mockResolvedValue(cur([mod('m1', 1, [sk('a1', 1), sk('a2', 2)])]));
    render(<HomeScreen />);
    expect(await screen.findByText('Lección: ES a1')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'ESTUDIAR AHORA' }));
    expect(startLesson).toHaveBeenCalledWith('a1');
    expect(startQuiz).not.toHaveBeenCalled();
  });

  it('con todas las lecciones vistas o desbloqueadas, practica', async () => {
    const startLesson = vi.fn();
    const startQuiz = vi.fn();
    useAppStore.setState({ startLesson, startQuiz });
    m(progressApi.curriculum).mockResolvedValue(
      cur([mod('m1', 1, [sk('a1', 1, { lesson_seen: true }), sk('a2', 2, { practice_unlocked: true })])]),
    );
    render(<HomeScreen />);
    expect(await screen.findByText('Sesión adaptativa · 10 preguntas')).toBeTruthy();
    // Espera a que el currículo cargue antes de pulsar.
    await vi.waitFor(() => expect(progressApi.curriculum).toHaveBeenCalled());
    fireEvent.click(screen.getByRole('button', { name: 'ESTUDIAR AHORA' }));
    expect(startQuiz).toHaveBeenCalledWith('study', 10, { trackId: 'track01' });
    expect(startLesson).not.toHaveBeenCalled();
  });
});
