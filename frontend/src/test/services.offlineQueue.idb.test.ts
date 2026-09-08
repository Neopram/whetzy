/**
 * Happy-path tests for offlineQueue using fake-indexeddb.
 * We polyfill the global `indexedDB` with the in-memory fake before importing the module.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { IDBFactory } from 'fake-indexeddb';

describe('offlineQueue — IDB happy path', () => {
  beforeEach(() => {
    vi.resetModules();
    // Give each test its own fresh IDB instance
    vi.stubGlobal('indexedDB', new IDBFactory());
  });

  const makeAnswer = (id: string) => ({
    id,
    sessionId: 'sess-1',
    questionId: 'q-1',
    selectedIndex: 1,
    responseTimeMs: 800,
    timestamp: Date.now(),
  });

  it('enqueue + pendingCount increments count', async () => {
    const { enqueue, pendingCount } = await import('../services/offlineQueue');
    await enqueue(makeAnswer('a1'));
    await enqueue(makeAnswer('a2'));
    expect(await pendingCount()).toBe(2);
  });

  it('dequeueAll returns items sorted by timestamp and clears the store', async () => {
    const { enqueue, dequeueAll, pendingCount } = await import('../services/offlineQueue');
    await enqueue({ ...makeAnswer('b1'), timestamp: 2000 });
    await enqueue({ ...makeAnswer('b2'), timestamp: 1000 });
    const items = await dequeueAll();
    // Sorted by timestamp ascending
    expect(items[0].id).toBe('b2');
    expect(items[1].id).toBe('b1');
    // Store cleared
    expect(await pendingCount()).toBe(0);
  });

  it('pendingCount returns 0 for empty store', async () => {
    const { pendingCount } = await import('../services/offlineQueue');
    expect(await pendingCount()).toBe(0);
  });

  it('dequeueAll returns [] for empty store', async () => {
    const { dequeueAll } = await import('../services/offlineQueue');
    expect(await dequeueAll()).toEqual([]);
  });
});
