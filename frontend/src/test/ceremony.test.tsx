/**
 * 46.7 (docs/PLAN_UI_AVANZADA.md §6.0 y §6.4): como mucho una ceremonia por
 * sesión, saltable, con sonido una vez; el resto, tarjetas quietas. Solo hitos
 * que mandó el servidor (`events[]`, 46.1b).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { Ceremony, CeremonyCards, pickCeremony, type CeremonyEvent } from '../components/quiz/Ceremony';
import * as fx from '../lib/feedbackFx';
import type { ServerFxEvent } from '../services/api';

const level: CeremonyEvent = { type: 'level_up', payload: { level_before: 2, level: 3 } };
const badge: CeremonyEvent = { type: 'badge_earned', payload: { badge_id: 'first_10' } };
const streak: CeremonyEvent = { type: 'streak_milestone', payload: { days: 7 } };
const combo: ServerFxEvent = { type: 'combo_multiplier', payload: { multiplier: 3 } };
const mission: ServerFxEvent = { type: 'mission_completed', payload: { mission_id: 'm1' } };

beforeEach(async () => { await i18n.changeLanguage('es'); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.useRealTimers(); });

describe('pickCeremony', () => {
  it('dos hitos de nivel 4 → una ceremonia (la de más peso) y una tarjeta', () => {
    expect(pickCeremony([badge, combo, level, mission])).toEqual({ ceremony: level, cards: [badge] });
  });
  it('la racha pesa más que la insignia', () => {
    expect(pickCeremony([badge, streak])).toEqual({ ceremony: streak, cards: [badge] });
  });
  it('sin hitos de nivel 4 no hay ceremonia', () => {
    expect(pickCeremony([combo, mission])).toEqual({ ceremony: null, cards: [] });
  });
});

describe('Ceremony', () => {
  it('suena una vez, se puede saltar y avisa de que se saltó', () => {
    const emit = vi.spyOn(fx, 'emit');
    const onDone = vi.fn();
    render(<Ceremony event={level} onDone={onDone} />);
    expect(screen.getByRole('dialog', { name: '¡Subes a nivel 3!' })).toBeInTheDocument();
    expect(emit).toHaveBeenCalledTimes(1);
    expect(emit).toHaveBeenCalledWith({ type: 'level_up' });
    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }));
    fireEvent.click(screen.getByRole('button', { name: 'Continuar' }));
    expect(onDone).toHaveBeenCalledTimes(1);
    expect(onDone).toHaveBeenCalledWith(true);
  });

  it('se cierra sola a los 3 s sin contar como saltada', () => {
    vi.useFakeTimers();
    const onDone = vi.fn();
    render(<Ceremony event={streak} onDone={onDone} />);
    expect(screen.getByRole('dialog', { name: '¡7 días seguidos!' })).toBeInTheDocument();
    act(() => { vi.advanceTimersByTime(2999); });
    expect(onDone).not.toHaveBeenCalled();
    act(() => { vi.advanceTimersByTime(1); });
    expect(onDone).toHaveBeenCalledWith(false);
  });

  it('Escape la cierra', () => {
    const onDone = vi.fn();
    render(<Ceremony event={badge} badgeName="Constante" onDone={onDone} />);
    expect(screen.getByRole('dialog', { name: 'Nueva insignia: Constante' })).toBeInTheDocument();
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onDone).toHaveBeenCalledWith(true);
  });

  it('en inglés', async () => {
    await i18n.changeLanguage('en');
    render(<Ceremony event={level} onDone={() => {}} />);
    expect(screen.getByRole('dialog', { name: 'Level 3!' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Continue' })).toBeInTheDocument();
  });
});

describe('CeremonyCards', () => {
  it('el resto sale como tarjetas, sin sonido', () => {
    const emit = vi.spyOn(fx, 'emit');
    render(<CeremonyCards cards={[badge]} badgeNames={new Map([['first_10', 'Constante']])} />);
    expect(screen.getByRole('region', { name: 'También en esta sesión' })).toHaveTextContent('Nueva insignia: Constante');
    expect(emit).not.toHaveBeenCalled();
  });
});
