/**
 * Plan ganado con referidos (ADR-57): desbloquea lo mismo que el de pago
 * (`isPremium`), pero `/auth/me` lo manda aparte de `is_premium`, que el
 * checkout usa para saber si ya hay suscripción y si un pago llegó.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useAppStore } from '../stores/useAppStore';
import { auth, type UserRead } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, auth: { ...actual.auth, me: vi.fn() } };
});

const me = auth.me as unknown as ReturnType<typeof vi.fn>;

const BASE: UserRead = {
  id: 'u1', email: 'ana@example.com', username: 'ana', display_name: 'Ana', language: 'es',
  avatar_emoji: '🙂', level: 1, total_xp: 0, current_streak: 0, max_streak: 0,
  streak_freeze_available: 1, last_active: null, created_at: '2026-10-01T00:00:00Z',
  is_premium: false,
};

afterEach(() => useAppStore.getState().signOut());

describe('store — plan ganado', () => {
  it('sin pago ni plan ganado no hay premium', async () => {
    me.mockResolvedValue(BASE);
    await useAppStore.getState().hydrateFromApi();
    const u = useAppStore.getState().user;
    expect([u.isPremium, u.grantedTier, u.grantedUntil]).toEqual([false, null, null]);
  });

  it('un plan ganado en fecha desbloquea como uno de pago y guarda hasta cuándo', async () => {
    me.mockResolvedValue({ ...BASE, granted_tier: 'plus', granted_tier_expires_at: '2026-11-07T12:00:00Z' });
    await useAppStore.getState().hydrateFromApi();
    const u = useAppStore.getState().user;
    expect([u.isPremium, u.grantedTier, u.grantedUntil]).toEqual([true, 'plus', '2026-11-07T12:00:00Z']);
  });
});
