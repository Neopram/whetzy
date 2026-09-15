/**
 * Tests for src/hooks/useRuntime.ts
 *
 * The underlying runtimes (usePyodide, useSqlRuntime) are mocked at the
 * module boundary: usePyodide drives a real Pyodide WebWorker (excluded
 * from coverage, see vitest.config.ts) and useSqlRuntime already has its
 * own dedicated worker-level tests. What useRuntime itself is responsible
 * for — routing status/runCode to the right underlying runtime, disabling
 * the inactive one, and the js stub — is what these tests exercise.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useRuntime, runtimeForQuestion } from '../hooks/useRuntime';

const pyodideMock = vi.fn();
const sqlRuntimeMock = vi.fn();

vi.mock('../hooks/usePyodide', () => ({
  usePyodide: (disabled: boolean) => pyodideMock(disabled),
}));
vi.mock('../hooks/useSqlRuntime', () => ({
  useSqlRuntime: (disabled: boolean) => sqlRuntimeMock(disabled),
}));

describe('useRuntime', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    pyodideMock.mockReturnValue({
      status: 'ready',
      runCode: vi.fn().mockResolvedValue({ output: 'py-out', error: null, timedOut: false }),
    });
    sqlRuntimeMock.mockReturnValue({
      status: 'loading',
      runCode: vi.fn().mockResolvedValue({ output: 'sql-out', error: null, timedOut: false }),
    });
  });

  it('routes to the python runtime and disables sql', () => {
    const { result } = renderHook(() => useRuntime('python'));
    expect(result.current.status).toBe('ready');
    expect(pyodideMock).toHaveBeenCalledWith(false);
    expect(sqlRuntimeMock).toHaveBeenCalledWith(true);
  });

  it('python runCode delegates to usePyodide.runCode', async () => {
    const { result } = renderHook(() => useRuntime('python'));
    await expect(result.current.runCode('print(1)')).resolves.toEqual({
      output: 'py-out',
      error: null,
      timedOut: false,
    });
  });

  it('routes to the sql runtime and disables python', () => {
    const { result } = renderHook(() => useRuntime('sql'));
    expect(result.current.status).toBe('loading');
    expect(pyodideMock).toHaveBeenCalledWith(true);
    expect(sqlRuntimeMock).toHaveBeenCalledWith(false);
  });

  it('sql runCode delegates to useSqlRuntime.runCode', async () => {
    const { result } = renderHook(() => useRuntime('sql'));
    await expect(result.current.runCode('SELECT 1')).resolves.toEqual({
      output: 'sql-out',
      error: null,
      timedOut: false,
    });
  });

  it('js runtime is always reported ready and disables both real runtimes', () => {
    const { result } = renderHook(() => useRuntime('js'));
    expect(result.current.status).toBe('ready');
    expect(pyodideMock).toHaveBeenCalledWith(true);
    expect(sqlRuntimeMock).toHaveBeenCalledWith(true);
  });

  it('js runCode always resolves with the stub result, ignoring its input', async () => {
    const { result } = renderHook(() => useRuntime('js'));
    await expect(result.current.runCode('console.log(1)')).resolves.toEqual({
      output: '',
      error: 'JS runtime not yet available',
      timedOut: false,
    });
  });
});

describe('runtimeForQuestion', () => {
  it('maps sql_exec to the sql runtime', () => {
    expect(runtimeForQuestion('sql_exec')).toBe('sql');
  });

  it('maps js_exec to the js runtime', () => {
    expect(runtimeForQuestion('js_exec')).toBe('js');
  });

  it('defaults every other question type to python', () => {
    expect(runtimeForQuestion('fill_blank_exec')).toBe('python');
    expect(runtimeForQuestion('fix_bug')).toBe('python');
    expect(runtimeForQuestion('multiple_choice')).toBe('python');
  });

  it('defaults to python when the question type is undefined', () => {
    expect(runtimeForQuestion(undefined)).toBe('python');
  });
});
