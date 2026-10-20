/**
 * 46.11 (docs/PLAN_UI_AVANZADA.md §7.3): la llama de la TopBar crece con la
 * racha (1–6 / 7–29 / ≥ 30 días) y, el día que el servidor gasta un comodín
 * (`streak_freeze_used`), un escudo la cubre y se anuncia en texto.
 */
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { act, cleanup, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { StreakFlame, flameTier } from '../components/layout/StreakFlame';
import { useAppStore } from '../stores/useAppStore';

beforeEach(async () => {
  await i18n.changeLanguage('es');
  useAppStore.setState({ streakShieldAt: null });
});
afterEach(cleanup);

describe('StreakFlame (46.11)', () => {
  it.each([
    [0, 1], [1, 1], [6, 1],
    [7, 2], [29, 2],
    [30, 3], [100, 3],
  ])('%i días → tamaño %i', (days, tier) => {
    expect(flameTier(days)).toBe(tier);
  });

  it('pinta el tamaño de su tramo', () => {
    render(<StreakFlame days={30} />);
    const flame = screen.getByTestId('streak-flame');
    expect(flame).toHaveAttribute('data-tier', '3');
    expect(flame).toHaveAttribute('width', '24');
  });

  it('sin comodín gastado no hay escudo', () => {
    render(<StreakFlame days={8} />);
    expect(screen.queryByTestId('streak-shield')).toBeNull();
    expect(screen.queryByRole('status')).toBeNull();
  });

  it('el comodín gastado pone el escudo y lo dice', async () => {
    render(<StreakFlame days={8} />);
    act(() => useAppStore.getState().showStreakShield());
    expect(screen.getByTestId('streak-shield')).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('Comodín usado: tu racha sigue');
  });

  it('EN', async () => {
    await i18n.changeLanguage('en');
    render(<StreakFlame days={8} />);
    act(() => useAppStore.getState().showStreakShield());
    expect(screen.getByRole('status')).toHaveTextContent('Streak freeze used: your streak lives on');
  });
});
