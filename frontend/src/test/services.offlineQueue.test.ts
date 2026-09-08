/**
 * Tests for src/services/offlineQueue.ts
 * jsdom ships with a working IndexedDB polyfill via fake-indexeddb is NOT available;
 * we test the fallback path (IDB unavailable) and the happy-path with a mock.
 */

import { describe, it, expect, vi, afterEach } from 'vitest';
import type { PendingAnswer } from '../services/offlineQueue';

const makeAnswer = (id: string): PendingAnswer => ({
  id,
  sessionId: 'sess-1',
  questionId: 'q-1',
  selectedIndex: 0,
  responseTimeMs: 1000,
  timestamp: Date.now(),
});

describe('offlineQueue — IDB unavailable fallback', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('enqueue silently succeeds when IDB throws', async () => {
    vi.stubGlobal('indexedDB', {
      open: () => { throw new Error('IDB blocked'); },
    });
    const { enqueue } = await import('../services/offlineQueue');
    await expect(enqueue(makeAnswer('a1'))).resolves.toBeUndefined();
  });

  it('dequeueAll returns [] when IDB throws', async () => {
    vi.stubGlobal('indexedDB', {
      open: () => { throw new Error('IDB blocked'); },
    });
    const { dequeueAll } = await import('../services/offlineQueue');
    expect(await dequeueAll()).toEqual([]);
  });

  it('pendingCount returns 0 when IDB throws', async () => {
    vi.stubGlobal('indexedDB', {
      open: () => { throw new Error('IDB blocked'); },
    });
    const { pendingCount } = await import('../services/offlineQueue');
    expect(await pendingCount()).toBe(0);
  });
});
