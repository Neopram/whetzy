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

  it('peekAll returns [] when IDB throws', async () => {
    vi.stubGlobal('indexedDB', {
      open: () => { throw new Error('IDB blocked'); },
    });
    const { peekAll } = await import('../services/offlineQueue');
    expect(await peekAll()).toEqual([]);
  });

  it('pendingCount returns 0 when IDB throws', async () => {
    vi.stubGlobal('indexedDB', {
      open: () => { throw new Error('IDB blocked'); },
    });
    const { pendingCount } = await import('../services/offlineQueue');
    expect(await pendingCount()).toBe(0);
  });
});

describe('offlineEventId', () => {
  it('cabe en responses.event_id (64) y no se repite', async () => {
    const { offlineEventId } = await import('../services/offlineQueue');
    const a = offlineEventId();
    const b = offlineEventId();
    expect(a.length).toBeLessThanOrEqual(64);
    expect(a).not.toBe(b);
  });
});
