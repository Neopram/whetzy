/**
 * 46.6a (ADR-68, docs/PLAN_UI_AVANZADA.md §7.2): analítica de efectos en el
 * cliente. Cada emisión de feedbackFx y cada cambio de interruptor acaba en un
 * lote a `/analytics/client-events`; sin sesión o con GPC/DNT, nada sale.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { _resetFeedbackFx, emit, TIER } from '../lib/feedbackFx';
import { _resetFxAnalytics, FLUSH_MS, flushFx, startFxAnalytics, trackFxSkipped } from '../lib/fxAnalytics';
import { clientEvents } from '../services/api';
import { DEFAULT_USER_ID, useAppStore } from '../stores/useAppStore';

const send = vi.spyOn(clientEvents, 'send').mockResolvedValue({ accepted: 1 });

function logIn() {
  useAppStore.setState((s) => ({ user: { ...s.user, id: 'u-1' } }));
}

beforeEach(() => {
  vi.useFakeTimers();
  send.mockClear();
  _resetFeedbackFx();
  _resetFxAnalytics();
  useAppStore.setState((s) => ({ user: { ...s.user, id: DEFAULT_USER_ID }, soundEnabled: true, hapticEnabled: true }));
  Object.defineProperty(navigator, 'globalPrivacyControl', { value: undefined, configurable: true });
  Object.defineProperty(navigator, 'doNotTrack', { value: null, configurable: true });
});
afterEach(() => vi.useRealTimers());

describe('fxAnalytics (46.6a)', () => {
  it('agrupa emisiones y las manda a los 10 s, en un solo lote', () => {
    logIn();
    startFxAnalytics();
    emit({ type: 'correct' });
    emit({ type: 'wrong' });
    expect(send).not.toHaveBeenCalled();
    vi.advanceTimersByTime(FLUSH_MS);
    expect(send).toHaveBeenCalledTimes(1);
    const [batch] = send.mock.calls[0];
    expect(batch).toEqual([
      // jsdom: sin primer gesto no suena ni vibra, y así se cuenta.
      { type: 'fx_emitted', tier: 1, fx: 'correct', sounded: false, vibrated: false },
      { type: 'fx_emitted', tier: 1, fx: 'wrong', sounded: false, vibrated: false },
    ]);
  });

  it('sin sesión no manda nada', () => {
    startFxAnalytics();
    emit({ type: 'correct' });
    vi.advanceTimersByTime(FLUSH_MS);
    flushFx();
    expect(send).not.toHaveBeenCalled();
  });

  it.each([
    ['Global Privacy Control', 'globalPrivacyControl', true],
    ['Do Not Track', 'doNotTrack', '1'],
  ])('con %s no manda nada', (_label, key, value) => {
    Object.defineProperty(navigator, key, { value, configurable: true });
    logIn();
    startFxAnalytics();
    emit({ type: 'correct' });
    vi.advanceTimersByTime(FLUSH_MS);
    expect(send).not.toHaveBeenCalled();
  });

  it('cambiar el sonido o la vibración se cuenta; nada más', () => {
    logIn();
    startFxAnalytics();
    useAppStore.getState().toggleSound();
    useAppStore.getState().toggleHaptic();
    useAppStore.setState({ currentScreen: 'profile' });
    flushFx();
    expect(send.mock.calls[0][0]).toEqual([
      { type: 'sound_toggled', enabled: false },
      { type: 'haptic_toggled', enabled: false },
    ]);
  });

  it('solo se salta lo que bloquea (niveles 3 y 4)', () => {
    logIn();
    startFxAnalytics();
    trackFxSkipped('correct');
    trackFxSkipped('level_up');
    flushFx();
    expect(send.mock.calls[0][0]).toEqual([{ type: 'fx_skipped', tier: 4, fx: 'level_up' }]);
  });

  it('50 eventos salen de inmediato, sin esperar al temporizador', () => {
    logIn();
    startFxAnalytics();
    for (let i = 0; i < 50; i++) emit({ type: 'tap' });
    expect(send).toHaveBeenCalledTimes(1);
    expect(send.mock.calls[0][0]).toHaveLength(50);
  });

  it('al cerrar la página manda lo pendiente con keepalive', () => {
    logIn();
    startFxAnalytics();
    emit({ type: 'mission' });
    window.dispatchEvent(new Event('pagehide'));
    expect(send).toHaveBeenCalledWith([expect.objectContaining({ fx: 'mission', tier: 2 })], true);
  });

  it('los niveles son los mismos que valida el servidor', () => {
    const shared = JSON.parse(
      readFileSync(resolve(__dirname, '../../../backend/tests/fixtures/fx_tiers.json'), 'utf-8'),
    );
    expect(TIER).toEqual(shared);
  });
});
