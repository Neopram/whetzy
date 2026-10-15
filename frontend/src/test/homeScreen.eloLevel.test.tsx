/**
 * 24.4: el «nivel» que se mostraba en Home venía de XP (`user.level`,
 * `_level_from_xp` en el backend), no de Elo — el motor sí calcula un Elo
 * real por skill (`skills.data[].elo_rating`, ya llega al cliente) y nunca
 * se pintaba en ningún sitio. Aquí se muestra la media de las skills con
 * al menos un intento; una skill sin intentos se queda en el 1500 de
 * arranque, sin señal real, así que no cuenta — mostrarla sería un dato
 * inventado, justo lo que el criterio de 24.4 prohíbe.
 *
 * 2026-10-15 (plan de pantallas, PR 1b, ADR-60): el Elo es un número crudo
 * del modelo y solo se pinta con `import.meta.env.DEV`. Vitest corre en
 * desarrollo, así que estos casos siguen vigilando el cálculo; que no salga
 * en producción lo vigila homeScreen.bands.test.tsx.
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

function skill(over: Partial<SkillMasteryDetail>): SkillMasteryDetail {
  return {
    skill_id: 'sk1', name_es: 'Bucles', name_en: 'Loops', module_id: 'mod01',
    p_known: 0.5, elo_rating: 1500, attempts: 0, correct_count: 0,
    accuracy: 0, mastered: false, fsrs_due: null,
    ...over,
  };
}

beforeEach(async () => {
  await i18n.changeLanguage('es');
  dashboard.mockReturnValue(new Promise(() => {}));
  decaying.mockReturnValue(new Promise(() => {}));
  missions.mockReturnValue(new Promise(() => {}));
});
afterEach(cleanup);

describe('HomeScreen — Elo medio visible en Territorio (24.4)', () => {
  it('con skills practicadas, muestra la media real de su elo_rating', async () => {
    skills.mockResolvedValue([
      skill({ skill_id: 'a', elo_rating: 1600, attempts: 5 }),
      skill({ skill_id: 'b', elo_rating: 1400, attempts: 3 }),
    ]);
    useAppStore.setState((s) => ({ user: { ...s.user, language: 'es' } }));
    render(<HomeScreen />);
    await screen.findByText('Elo: 1500');
  });

  it('una skill sin intentos no cuenta en la media (se queda en el 1500 de arranque)', async () => {
    skills.mockResolvedValue([
      skill({ skill_id: 'a', elo_rating: 1650, attempts: 4 }),
      skill({ skill_id: 'b', elo_rating: 1500, attempts: 0 }),
    ]);
    render(<HomeScreen />);
    await screen.findByText('Elo: 1650');
  });

  it('sin ninguna skill con intentos, no se muestra ningún Elo (dato inventado)', async () => {
    skills.mockResolvedValue([skill({ skill_id: 'a', elo_rating: 1500, attempts: 0 })]);
    render(<HomeScreen />);
    await screen.findByText('Tu territorio');
    expect(screen.queryByText(/Elo: /)).not.toBeInTheDocument();
  });

  it('EN: la etiqueta y el hint también están traducidos', async () => {
    await i18n.changeLanguage('en');
    skills.mockResolvedValue([skill({ skill_id: 'a', elo_rating: 1523, attempts: 2 })]);
    useAppStore.setState((s) => ({ user: { ...s.user, language: 'en' } }));
    render(<HomeScreen />);
    const badge = await screen.findByText('Elo: 1523');
    expect(badge).toHaveAttribute('title', expect.stringContaining('Average Elo'));
  });
});
