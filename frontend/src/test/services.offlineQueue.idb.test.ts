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

  it('peekAll returns items sorted by timestamp and does NOT clear the store (42.11)', async () => {
    const { enqueue, peekAll, pendingCount } = await import('../services/offlineQueue');
    await enqueue({ ...makeAnswer('b1'), timestamp: 2000 });
    await enqueue({ ...makeAnswer('b2'), timestamp: 1000 });
    const items = await peekAll();
    // Sorted by timestamp ascending
    expect(items[0].id).toBe('b2');
    expect(items[1].id).toBe('b1');
    // Store intact until each one is confirmed
    expect(await pendingCount()).toBe(2);
  });

  it('remove deletes only that item', async () => {
    const { enqueue, remove, peekAll } = await import('../services/offlineQueue');
    await enqueue({ ...makeAnswer('c1'), timestamp: 1 });
    await enqueue({ ...makeAnswer('c2'), timestamp: 2 });
    await remove('c1');
    expect((await peekAll()).map((p) => p.id)).toEqual(['c2']);
  });

  it('discard moves the item out of the queue into the discarded store', async () => {
    const { enqueue, discard, pendingCount, discardedCount } = await import('../services/offlineQueue');
    const a = makeAnswer('d1');
    await enqueue(a);
    await discard(a, 404);
    expect(await pendingCount()).toBe(0);
    expect(await discardedCount()).toBe(1);
  });

  it('upgrades a v1 database without losing pending answers', async () => {
    // Una BD v1 (solo `pending_answers`) con una respuesta dentro.
    await new Promise<void>((resolve, reject) => {
      const req = indexedDB.open('whetzy_offline', 1);
      req.onupgradeneeded = () => req.result.createObjectStore('pending_answers', { keyPath: 'id' });
      req.onsuccess = () => {
        const tx = req.result.transaction('pending_answers', 'readwrite');
        tx.objectStore('pending_answers').put(makeAnswer('v1'));
        tx.oncomplete = () => { req.result.close(); resolve(); };
        tx.onerror = () => reject(tx.error);
      };
      req.onerror = () => reject(req.error);
    });
    const { peekAll, discardedCount } = await import('../services/offlineQueue');
    expect((await peekAll()).map((p) => p.id)).toEqual(['v1']);
    expect(await discardedCount()).toBe(0);
  });

  it('pendingCount returns 0 for empty store', async () => {
    const { pendingCount } = await import('../services/offlineQueue');
    expect(await pendingCount()).toBe(0);
  });

  it('peekAll returns [] for empty store', async () => {
    const { peekAll } = await import('../services/offlineQueue');
    expect(await peekAll()).toEqual([]);
  });
});
