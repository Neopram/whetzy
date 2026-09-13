/**
 * Tests for src/hooks/usePushNotifications.ts.
 *
 * Shipped with 3.3 and never covered, which is part of why the frontend
 * coverage gate has been failing in CI unnoticed. The behaviour that matters
 * is the refusal path: on a browser without Push, or a signed-out user, or a
 * denied permission, the hook must decline cleanly and never ask the browser
 * for a subscription — a rejected permission prompt is unrecoverable without
 * the user digging into site settings, so asking when we cannot follow through
 * spends a one-shot resource for nothing.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { usePushNotifications } from '../hooks/usePushNotifications';

const TOKEN_KEY = 'whetzy_access_token';

type Harness = {
  requestPermission: ReturnType<typeof vi.fn>;
  subscribe: ReturnType<typeof vi.fn>;
  getSubscription: ReturnType<typeof vi.fn>;
  unsubscribeFn: ReturnType<typeof vi.fn>;
  fetchMock: ReturnType<typeof vi.fn>;
};

function fakeSubscription(endpoint = 'https://push.test/abc') {
  return {
    endpoint,
    toJSON: () => ({ endpoint, keys: { p256dh: 'p', auth: 'a' } }),
    unsubscribe: vi.fn().mockResolvedValue(true),
  };
}

function install({
  permission = 'default' as NotificationPermission,
  existingSub = null as ReturnType<typeof fakeSubscription> | null,
  vapidOk = true,
  supported = true,
}): Harness {
  const requestPermission = vi.fn().mockResolvedValue('granted');
  const subscribe = vi.fn().mockResolvedValue(fakeSubscription());
  const getSubscription = vi.fn().mockResolvedValue(existingSub);
  const unsubscribeFn = existingSub?.unsubscribe ?? vi.fn();

  if (supported) {
    vi.stubGlobal('Notification', { permission, requestPermission });
    Object.defineProperty(navigator, 'serviceWorker', {
      configurable: true,
      value: {
        ready: Promise.resolve({ pushManager: { subscribe, getSubscription } }),
      },
    });
    vi.stubGlobal('PushManager', class {});
  } else {
    // The hook detects support with `'Notification' in window`, so stubbing
    // these to `undefined` is not enough — the key would still be present and
    // the hook would think the browser supports Push. They have to be gone.
    delete (globalThis as Record<string, unknown>).Notification;
    delete (globalThis as Record<string, unknown>).PushManager;
    delete (navigator as unknown as Record<string, unknown>).serviceWorker;
  }

  const fetchMock = vi.fn(async (url: string) => {
    if (String(url).endsWith('/vapid-key')) {
      return vapidOk
        ? { ok: true, json: async () => ({ vapid_public_key: 'BFakeKey_-abc' }) }
        : { ok: false, json: async () => ({}) };
    }
    return { ok: true, json: async () => ({}) };
  });
  vi.stubGlobal('fetch', fetchMock);
  vi.stubGlobal('atob', (s: string) => Buffer.from(s, 'base64').toString('binary'));

  return { requestPermission, subscribe, getSubscription, unsubscribeFn, fetchMock };
}

describe('usePushNotifications', () => {
  beforeEach(() => {
    localStorage.setItem(TOKEN_KEY, 'tok123');
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    localStorage.clear();
    vi.restoreAllMocks();
  });

  describe('support detection', () => {
    it('reports unsupported when the browser lacks Push', () => {
      install({ supported: false });
      const { result } = renderHook(() => usePushNotifications());
      expect(result.current.supported).toBe(false);
      expect(result.current.permission).toBe('unsupported');
    });

    it('reports supported and mirrors the current permission', () => {
      install({ permission: 'granted' });
      const { result } = renderHook(() => usePushNotifications());
      expect(result.current.supported).toBe(true);
      expect(result.current.permission).toBe('granted');
    });
  });

  describe('initial subscription state', () => {
    it('starts unsubscribed when the browser has no subscription', async () => {
      install({ permission: 'granted' });
      const { result } = renderHook(() => usePushNotifications());
      await waitFor(() => expect(result.current.subscribed).toBe(false));
    });

    it('detects an existing subscription', async () => {
      install({ permission: 'granted', existingSub: fakeSubscription() });
      const { result } = renderHook(() => usePushNotifications());
      await waitFor(() => expect(result.current.subscribed).toBe(true));
    });
  });

  describe('subscribe', () => {
    it('refuses without asking the browser when unsupported', async () => {
      const h = install({ supported: false });
      const { result } = renderHook(() => usePushNotifications());
      let ok = true;
      await act(async () => {
        ok = await result.current.subscribe();
      });
      expect(ok).toBe(false);
      expect(h.fetchMock).not.toHaveBeenCalled();
    });

    it('refuses for a signed-out user without prompting', async () => {
      localStorage.clear();
      const h = install({ permission: 'default' });
      const { result } = renderHook(() => usePushNotifications());
      let ok = true;
      await act(async () => {
        ok = await result.current.subscribe();
      });
      expect(ok).toBe(false);
      expect(h.requestPermission).not.toHaveBeenCalled();
    });

    it('gives up when the VAPID key cannot be fetched, before prompting', async () => {
      const h = install({ permission: 'default', vapidOk: false });
      const { result } = renderHook(() => usePushNotifications());
      let ok = true;
      await act(async () => {
        ok = await result.current.subscribe();
      });
      expect(ok).toBe(false);
      expect(h.requestPermission).not.toHaveBeenCalled();
      expect(h.subscribe).not.toHaveBeenCalled();
    });

    it('asks for permission only when it has not been decided', async () => {
      const h = install({ permission: 'granted' });
      const { result } = renderHook(() => usePushNotifications());
      await act(async () => {
        await result.current.subscribe();
      });
      expect(h.requestPermission).not.toHaveBeenCalled();
    });

    it('never re-prompts once the user has denied', async () => {
      const h = install({ permission: 'denied' });
      const { result } = renderHook(() => usePushNotifications());
      let ok = true;
      await act(async () => {
        ok = await result.current.subscribe();
      });
      expect(ok).toBe(false);
      expect(h.requestPermission).not.toHaveBeenCalled();
      expect(h.subscribe).not.toHaveBeenCalled();
    });

    it('subscribes and posts the subscription when permission is granted', async () => {
      const h = install({ permission: 'default' });
      const { result } = renderHook(() => usePushNotifications());
      let ok = false;
      await act(async () => {
        ok = await result.current.subscribe();
      });

      expect(ok).toBe(true);
      expect(h.requestPermission).toHaveBeenCalledOnce();
      expect(h.subscribe).toHaveBeenCalledWith(
        expect.objectContaining({ userVisibleOnly: true }),
      );

      const post = h.fetchMock.mock.calls.find(
        ([, init]) => (init as RequestInit | undefined)?.method === 'POST',
      );
      expect(post).toBeTruthy();
      const init = post![1] as RequestInit;
      expect((init.headers as Record<string, string>).Authorization).toBe('Bearer tok123');
      expect(JSON.parse(init.body as string)).toEqual({
        endpoint: 'https://push.test/abc',
        keys: { p256dh: 'p', auth: 'a' },
      });
      await waitFor(() => expect(result.current.subscribed).toBe(true));
    });

    it('returns false when the browser rejects the subscription', async () => {
      const h = install({ permission: 'granted' });
      h.subscribe.mockRejectedValue(new Error('push service unavailable'));
      const { result } = renderHook(() => usePushNotifications());
      let ok = true;
      await act(async () => {
        ok = await result.current.subscribe();
      });
      expect(ok).toBe(false);
      expect(result.current.subscribed).toBe(false);
    });
  });

  describe('unsubscribe', () => {
    it('deletes server-side and unsubscribes locally', async () => {
      const sub = fakeSubscription();
      const h = install({ permission: 'granted', existingSub: sub });
      const { result } = renderHook(() => usePushNotifications());
      await waitFor(() => expect(result.current.subscribed).toBe(true));

      await act(async () => {
        await result.current.unsubscribe();
      });

      const del = h.fetchMock.mock.calls.find(
        ([, init]) => (init as RequestInit | undefined)?.method === 'DELETE',
      );
      expect(del).toBeTruthy();
      expect(JSON.parse((del![1] as RequestInit).body as string)).toEqual({
        endpoint: sub.endpoint,
      });
      expect(sub.unsubscribe).toHaveBeenCalled();
      await waitFor(() => expect(result.current.subscribed).toBe(false));
    });

    it('is a no-op when there is nothing subscribed', async () => {
      const h = install({ permission: 'granted', existingSub: null });
      const { result } = renderHook(() => usePushNotifications());
      await act(async () => {
        await result.current.unsubscribe();
      });
      const del = h.fetchMock.mock.calls.find(
        ([, init]) => (init as RequestInit | undefined)?.method === 'DELETE',
      );
      expect(del).toBeFalsy();
    });

    it('is a no-op for a signed-out user', async () => {
      localStorage.clear();
      const h = install({ permission: 'granted', existingSub: fakeSubscription() });
      const { result } = renderHook(() => usePushNotifications());
      await act(async () => {
        await result.current.unsubscribe();
      });
      expect(h.fetchMock).not.toHaveBeenCalled();
    });

    it('swallows a failing server delete without throwing', async () => {
      const sub = fakeSubscription();
      const h = install({ permission: 'granted', existingSub: sub });
      h.fetchMock.mockRejectedValue(new Error('offline'));
      const { result } = renderHook(() => usePushNotifications());
      await expect(
        act(async () => {
          await result.current.unsubscribe();
        }),
      ).resolves.not.toThrow();
    });
  });
});
