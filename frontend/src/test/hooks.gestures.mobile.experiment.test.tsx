/**
 * Tests for three hooks that had 0 % coverage (and pulled the frontend CI
 * job under its 70 % functions threshold): useGestures (used by App.tsx),
 * useIsMobile and useExperimentFlags / useVariant.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import { useGestures } from '../hooks/useGestures';
import { useIsMobile } from '../hooks/use-mobile';
import { useExperimentFlags, useVariant } from '../hooks/useExperiment';
import { API_BASE_URL } from '../services/api';

function touch(type: 'touchstart' | 'touchend', x: number, y: number) {
  const ev = new Event(type) as Event & { touches: unknown; changedTouches: unknown };
  ev.touches = [{ clientX: x, clientY: y }];
  ev.changedTouches = [{ clientX: x, clientY: y }];
  document.dispatchEvent(ev);
}

function swipe(from: [number, number], to: [number, number]) {
  touch('touchstart', ...from);
  touch('touchend', ...to);
}

describe('useGestures', () => {
  const cbs = { onSwipeLeft: vi.fn(), onSwipeRight: vi.fn(), onSwipeUp: vi.fn(), onSwipeDown: vi.fn() };
  beforeEach(() => Object.values(cbs).forEach((f) => f.mockReset()));

  it('detects the four directions past the 50 px threshold', () => {
    renderHook(() => useGestures(cbs));
    swipe([200, 100], [100, 100]);
    swipe([100, 100], [200, 100]);
    swipe([100, 200], [100, 100]);
    swipe([100, 100], [100, 200]);
    expect(cbs.onSwipeLeft).toHaveBeenCalledTimes(1);
    expect(cbs.onSwipeRight).toHaveBeenCalledTimes(1);
    expect(cbs.onSwipeUp).toHaveBeenCalledTimes(1);
    expect(cbs.onSwipeDown).toHaveBeenCalledTimes(1);
  });

  it('ignores short moves and slow swipes', () => {
    renderHook(() => useGestures(cbs));
    swipe([100, 100], [130, 110]);
    const now = vi.spyOn(Date, 'now');
    now.mockReturnValueOnce(0).mockReturnValueOnce(1000);
    swipe([300, 100], [100, 100]);
    now.mockRestore();
    Object.values(cbs).forEach((f) => expect(f).not.toHaveBeenCalled());
  });

  it('stops listening on unmount', () => {
    const { unmount } = renderHook(() => useGestures(cbs));
    unmount();
    swipe([200, 100], [100, 100]);
    expect(cbs.onSwipeLeft).not.toHaveBeenCalled();
  });

  it('survives a re-render with a brand-new callbacks object mid-gesture (0.8)', () => {
    // App.tsx calls useGestures({ onSwipeRight: () => ..., onSwipeLeft: () => ... })
    // -- a fresh object literal every render, not a stable `cbs` like above.
    // If the effect re-subscribed on that identity, a re-render between
    // touchstart and touchend would drop the in-flight gesture.
    const firstRender = { onSwipeLeft: vi.fn(), onSwipeRight: vi.fn() };
    const { rerender } = renderHook(({ cb }) => useGestures(cb), {
      initialProps: { cb: firstRender },
    });

    touch('touchstart', 200, 100);
    const afterRerender = { onSwipeLeft: vi.fn(), onSwipeRight: vi.fn() };
    rerender({ cb: afterRerender });
    touch('touchend', 100, 100);

    expect(afterRerender.onSwipeLeft).toHaveBeenCalledTimes(1);
    expect(afterRerender.onSwipeRight).not.toHaveBeenCalled();
    expect(firstRender.onSwipeLeft).not.toHaveBeenCalled();
  });
});

describe('useIsMobile', () => {
  const original = window.innerWidth;
  afterEach(() => Object.defineProperty(window, 'innerWidth', { value: original, configurable: true }));

  it('follows the window width across resizes', () => {
    Object.defineProperty(window, 'innerWidth', { value: 500, configurable: true });
    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(true);
    act(() => {
      Object.defineProperty(window, 'innerWidth', { value: 1200, configurable: true });
      window.dispatchEvent(new Event('resize'));
    });
    expect(result.current).toBe(false);
  });
});

describe('useExperimentFlags / useVariant', () => {
  const fetchMock = vi.fn();
  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal('fetch', fetchMock);
  });
  afterEach(() => vi.unstubAllGlobals());

  it('asks the API origin, not a relative path, and exposes the flags', async () => {
    fetchMock.mockResolvedValue({ ok: true, json: async () => ({ flags: { hero: 'B' } }) });
    const { result } = renderHook(() => useExperimentFlags());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.flags).toEqual({ hero: 'B' });
    expect(fetchMock.mock.calls[0][0]).toBe(`${API_BASE_URL}/experiments/flags`);
  });

  it('falls back to the default variant when the request fails', async () => {
    const err = vi.spyOn(console, 'error').mockImplementation(() => {});
    fetchMock.mockRejectedValue(new Error('offline'));
    const { result } = renderHook(() => useVariant('hero', 'B'));
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(result.current).toBe('B');
    err.mockRestore();
  });
});
