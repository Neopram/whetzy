/**
 * Tests for src/hooks/useOfflineSync.ts
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useOfflineSync } from '../hooks/useOfflineSync';

// Mock the services this hook depends on
vi.mock('../services/offlineQueue', () => ({
  peekAll: vi.fn().mockResolvedValue([]),
  remove: vi.fn().mockResolvedValue(undefined),
  discard: vi.fn().mockResolvedValue(undefined),
  pendingCount: vi.fn().mockResolvedValue(0),
}));

vi.mock('../services/api', () => ({
  ApiError: class ApiError extends Error {},
  quiz: {
    answer: vi.fn().mockResolvedValue({}),
  },
}));

import * as offlineQueue from '../services/offlineQueue';

describe('useOfflineSync', () => {
  beforeEach(() => {
    vi.mocked(offlineQueue.pendingCount).mockResolvedValue(0);
    vi.mocked(offlineQueue.peekAll).mockResolvedValue([]);
  });

  afterEach(() => vi.clearAllMocks());

  it('reports isOnline from navigator.onLine', () => {
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true });
    const { result } = renderHook(() => useOfflineSync());
    expect(result.current.isOnline).toBe(true);
  });

  it('starts with isSyncing = false and pendingAnswers = 0', async () => {
    const { result } = renderHook(() => useOfflineSync());
    await waitFor(() => expect(result.current.isSyncing).toBe(false));
    expect(result.current.pendingAnswers).toBe(0);
  });

  it('updates pendingAnswers from IDB on mount', async () => {
    vi.mocked(offlineQueue.pendingCount).mockResolvedValue(3);
    const { result } = renderHook(() => useOfflineSync());
    await waitFor(() => expect(result.current.pendingAnswers).toBe(3));
  });

  it('goes offline when "offline" event fires', async () => {
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true });
    const { result } = renderHook(() => useOfflineSync());
    act(() => {
      window.dispatchEvent(new Event('offline'));
    });
    await waitFor(() => expect(result.current.isOnline).toBe(false));
  });

  it('goes online and flushes queue when "online" event fires', async () => {
    vi.mocked(offlineQueue.peekAll).mockResolvedValue([
      { id: 'a1', sessionId: 's1', questionId: 'q1', selectedIndex: 0, responseTimeMs: 500, timestamp: 1 },
    ]);
    const { result } = renderHook(() => useOfflineSync());
    act(() => {
      window.dispatchEvent(new Event('online'));
    });
    await waitFor(() => expect(result.current.isOnline).toBe(true));
    await waitFor(() => expect(result.current.isSyncing).toBe(false));
    // Confirmed by the server → removed; pending comes from pendingCount()
    expect(offlineQueue.remove).toHaveBeenCalledWith('a1');
    expect(result.current.pendingAnswers).toBe(0);
  });

  it('cleans up listeners on unmount', () => {
    const removeSpy = vi.spyOn(window, 'removeEventListener');
    const { unmount } = renderHook(() => useOfflineSync());
    unmount();
    expect(removeSpy).toHaveBeenCalledWith('online', expect.any(Function));
    expect(removeSpy).toHaveBeenCalledWith('offline', expect.any(Function));
    removeSpy.mockRestore();
  });
});
