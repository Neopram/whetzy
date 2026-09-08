/**
 * Tests for src/hooks/useApi.ts
 */

import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useApi } from '../hooks/useApi';

describe('useApi', () => {
  it('starts in loading state', () => {
    const fetcher = () => new Promise<string>(() => {});
    const { result } = renderHook(() => useApi(fetcher, []));
    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('sets data on successful fetch', async () => {
    const fetcher = vi.fn().mockResolvedValue({ value: 42 });
    const { result } = renderHook(() => useApi(fetcher, []));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual({ value: 42 });
    expect(result.current.error).toBeNull();
  });

  it('sets error string when fetch rejects with Error', async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error('Network down'));
    const { result } = renderHook(() => useApi(fetcher, []));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe('Network down');
  });

  it('sets generic "Error" when rejection is not an Error object', async () => {
    const fetcher = vi.fn().mockRejectedValue('oops');
    const { result } = renderHook(() => useApi(fetcher, []));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe('Error');
  });

  it('reload() re-runs the fetcher', async () => {
    let count = 0;
    const fetcher = vi.fn().mockImplementation(() => Promise.resolve(++count));
    const { result } = renderHook(() => useApi(fetcher, []));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toBe(1);

    result.current.reload();
    await waitFor(() => expect(result.current.data).toBe(2));
    expect(fetcher).toHaveBeenCalledTimes(2);
  });

  it('cancels stale request when unmounted', async () => {
    let resolveFn!: (v: string) => void;
    const fetcher = vi.fn().mockReturnValue(new Promise<string>(r => { resolveFn = r; }));
    const { result, unmount } = renderHook(() => useApi(fetcher, []));
    expect(result.current.loading).toBe(true);
    unmount();
    resolveFn('late data');
    // Shouldn't cause state update / warning after unmount
    await new Promise(r => setTimeout(r, 20));
    // Just verify no exception thrown
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});
