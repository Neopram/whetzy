/**
 * 43.3 (ADR-65 D2): las horas por semana ya no se preguntan en el onboarding;
 * se eligen en Perfil y van al servidor (`onboarding_weekly_time`).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { ProfileScreen } from '../pages/ProfileScreen';
import { useAppStore } from '../stores/useAppStore';
import { auth } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    auth: { ...actual.auth, updateMe: vi.fn().mockResolvedValue({}) },
    gamification: { ...actual.gamification, badges: vi.fn().mockResolvedValue([]) },
    billing: {
      ...actual.billing,
      subscription: vi.fn().mockResolvedValue({ is_premium: false }),
      paddleConfig: vi.fn().mockResolvedValue({ enabled: false, prices: {} }),
    },
  };
});

const updateMe = auth.updateMe as unknown as ReturnType<typeof vi.fn>;

beforeEach(async () => {
  await i18n.changeLanguage('es');
  updateMe.mockClear();
  useAppStore.getState().updateUser({ weeklyTime: null });
});
afterEach(cleanup);

describe('Perfil — tiempo por semana (43.3)', () => {
  it('se elige aquí y se guarda en el servidor', () => {
    render(<ProfileScreen />);
    const group = screen.getByRole('group', { name: 'Tiempo por semana' });
    const option = screen.getByRole('button', { name: '3-10 h' });
    expect(group.contains(option)).toBe(true);
    expect(option).toHaveAttribute('aria-pressed', 'false');

    fireEvent.click(option);
    expect(updateMe).toHaveBeenCalledWith({ onboarding_weekly_time: 1 });
    expect(useAppStore.getState().user.weeklyTime).toBe(1);
    expect(screen.getByRole('button', { name: '3-10 h' })).toHaveAttribute('aria-pressed', 'true');
  });
});
