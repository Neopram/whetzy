/**
 * Tests for src/hooks/useSqlRuntime.ts
 *
 * jsdom has no Worker implementation, so we stub `Worker` with a small
 * controllable fake that records postMessage calls and lets tests drive
 * onmessage/onerror exactly like the real sql-worker.js would.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useSqlRuntime } from '../hooks/useSqlRuntime';

class MockWorker {
  static instances: MockWorker[] = [];
  onmessage: ((ev: { data: any }) => void) | null = null;
  onerror: (() => void) | null = null;
  postMessage = vi.fn();
  terminate = vi.fn();
  constructor(public url: string) {
    MockWorker.instances.push(this);
  }
  emit(data: any) {
    this.onmessage?.({ data });
  }
}

beforeEach(() => {
  MockWorker.instances = [];
  vi.stubGlobal('Worker', MockWorker as unknown as typeof Worker);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('useSqlRuntime — disabled', () => {
  it('stays ready and never creates a worker', () => {
    const { result } = renderHook(() => useSqlRuntime(true));
    expect(result.current.status).toBe('ready');
    expect(MockWorker.instances).toHaveLength(0);
  });

  it('runCode resolves with "SQL engine not active" instead of touching a worker', async () => {
    const { result } = renderHook(() => useSqlRuntime(true));
    const res = await result.current.runCode('SELECT 1');
    expect(res).toEqual({ output: '', error: 'SQL engine not active', timedOut: false });
    expect(MockWorker.instances).toHaveLength(0);
  });
});

describe('useSqlRuntime — enabled lifecycle', () => {
  it('starts loading and creates exactly one worker for /sql-worker.js', () => {
    const { result } = renderHook(() => useSqlRuntime(false));
    expect(result.current.status).toBe('loading');
    expect(MockWorker.instances).toHaveLength(1);
    expect(MockWorker.instances[0].url).toBe('/sql-worker.js');
  });

  it('becomes ready once the worker reports "ready"', async () => {
    const { result } = renderHook(() => useSqlRuntime(false));
    act(() => {
      MockWorker.instances[0].emit({ type: 'ready' });
    });
    await waitFor(() => expect(result.current.status).toBe('ready'));
  });

  it('goes to error status on a "loadError" message', async () => {
    const { result } = renderHook(() => useSqlRuntime(false));
    act(() => {
      MockWorker.instances[0].emit({ type: 'loadError' });
    });
    await waitFor(() => expect(result.current.status).toBe('error'));
  });

  it('goes to error status when the worker itself errors', async () => {
    const { result } = renderHook(() => useSqlRuntime(false));
    act(() => {
      MockWorker.instances[0].onerror?.();
    });
    await waitFor(() => expect(result.current.status).toBe('error'));
  });

  it('terminates the worker on unmount', () => {
    const { unmount } = renderHook(() => useSqlRuntime(false));
    const worker = MockWorker.instances[0];
    unmount();
    expect(worker.terminate).toHaveBeenCalledTimes(1);
  });

  it('switching from enabled to disabled terminates the worker and resets to ready', async () => {
    const { result, rerender } = renderHook(({ disabled }) => useSqlRuntime(disabled), {
      initialProps: { disabled: false },
    });
    const worker = MockWorker.instances[0];
    rerender({ disabled: true });
    expect(worker.terminate).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(result.current.status).toBe('ready'));
  });
});

describe('useSqlRuntime — runCode', () => {
  it('resolves with "SQL engine not ready" when called before the worker is ready', async () => {
    const { result } = renderHook(() => useSqlRuntime(false));
    // Still 'loading' — no 'ready' message emitted yet.
    const res = await result.current.runCode('SELECT 1');
    expect(res).toEqual({ output: '', error: 'SQL engine not ready', timedOut: false });
  });

  it('posts a run message and resolves with the worker result, returning status to ready', async () => {
    const { result } = renderHook(() => useSqlRuntime(false));
    act(() => {
      MockWorker.instances[0].emit({ type: 'ready' });
    });
    await waitFor(() => expect(result.current.status).toBe('ready'));

    let resolved: unknown;
    act(() => {
      result.current.runCode('SELECT * FROM t').then((r) => {
        resolved = r;
      });
    });

    await waitFor(() => expect(result.current.status).toBe('running'));
    const worker = MockWorker.instances[0];
    expect(worker.postMessage).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'run', code: 'SELECT * FROM t' })
    );
    const sentId = worker.postMessage.mock.calls[0][0].id;
    expect(typeof sentId).toBe('string');

    act(() => {
      worker.emit({ type: 'result', id: sentId, output: '1 row', error: null });
    });

    await waitFor(() => expect(resolved).toEqual({ output: '1 row', error: null, timedOut: false }));
    expect(result.current.status).toBe('ready');
  });

  it('defaults a missing error field to null and a missing output to an empty string', async () => {
    const { result } = renderHook(() => useSqlRuntime(false));
    act(() => {
      MockWorker.instances[0].emit({ type: 'ready' });
    });
    await waitFor(() => expect(result.current.status).toBe('ready'));

    let resolved: unknown;
    act(() => {
      result.current.runCode('SELECT 1').then((r) => {
        resolved = r;
      });
    });
    await waitFor(() => expect(result.current.status).toBe('running'));
    const worker = MockWorker.instances[0];
    const sentId = worker.postMessage.mock.calls[0][0].id;

    act(() => {
      worker.emit({ type: 'result', id: sentId });
    });

    await waitFor(() =>
      expect(resolved).toEqual({ output: '', error: null, timedOut: false })
    );
  });

  it('ignores a result message whose id does not match the pending request', async () => {
    const { result } = renderHook(() => useSqlRuntime(false));
    act(() => {
      MockWorker.instances[0].emit({ type: 'ready' });
    });
    await waitFor(() => expect(result.current.status).toBe('ready'));

    let settled = false;
    act(() => {
      result.current.runCode('SELECT 1').then(() => {
        settled = true;
      });
    });
    await waitFor(() => expect(result.current.status).toBe('running'));

    act(() => {
      MockWorker.instances[0].emit({ type: 'result', id: 'someone-elses-id', output: 'nope' });
    });

    // The mismatched id must not resolve the pending call or flip status back.
    expect(settled).toBe(false);
    expect(result.current.status).toBe('running');
  });

  it('resolves with "SQL engine not active" if disabled while nothing is pending', async () => {
    const { result, rerender } = renderHook(({ disabled }) => useSqlRuntime(disabled), {
      initialProps: { disabled: false },
    });
    act(() => {
      MockWorker.instances[0].emit({ type: 'ready' });
    });
    await waitFor(() => expect(result.current.status).toBe('ready'));

    rerender({ disabled: true });
    await waitFor(() => expect(result.current.status).toBe('ready'));

    const res = await result.current.runCode('SELECT 1');
    expect(res).toEqual({ output: '', error: 'SQL engine not active', timedOut: false });
  });
});
