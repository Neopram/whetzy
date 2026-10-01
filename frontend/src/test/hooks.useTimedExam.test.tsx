/**
 * Tests for the shared timed-exam machinery (17.2).
 *
 * These exist for two reasons. The obvious one is that the hook is new. The
 * other is that `MockExamScreen` still carries its own copy of this logic, and
 * swapping it over to the hook is only safe once the behaviour that matters is
 * pinned down here: the deadline submits exactly once, a failed submission
 * gives the learner their answers back, and the clock never reads negative.
 */
import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { formatClock, useTimedExam } from '../hooks/useTimedExam';

interface Q {
  id: string;
}

function sittingAt(secondsFromNow: number, questions: Q[] = [{ id: 'q1' }, { id: 'q2' }]) {
  return {
    attempt_id: 'att-1',
    expires_at: new Date(Date.now() + secondsFromNow * 1000).toISOString(),
    questions,
  };
}

const ERROR = 'algo ha ido mal';

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe('useTimedExam', () => {
  it('moves from intro to running and exposes the drawn questions', async () => {
    const start = vi.fn().mockResolvedValue(sittingAt(600));
    const submit = vi.fn();
    const { result } = renderHook(() => useTimedExam({ start, submit, errorMessage: ERROR }));

    expect(result.current.phase).toBe('intro');
    await act(async () => {
      await result.current.start();
    });

    expect(result.current.phase).toBe('running');
    expect(result.current.questions).toHaveLength(2);
    expect(result.current.current?.id).toBe('q1');
    expect(result.current.answers).toEqual({});
  });

  it('records answers, one per question', async () => {
    const start = vi.fn().mockResolvedValue(sittingAt(600));
    const { result } = renderHook(() =>
      useTimedExam({ start, submit: vi.fn(), errorMessage: ERROR }),
    );
    await act(async () => {
      await result.current.start();
    });

    act(() => result.current.choose('q1', 2));
    expect(result.current.answers).toEqual({ q1: 2 });

    // Changing your mind replaces rather than appends.
    act(() => result.current.choose('q1', 0));
    expect(result.current.answers).toEqual({ q1: 0 });
  });

  it('submits automatically when the deadline passes, and only once', async () => {
    const start = vi.fn().mockResolvedValue(sittingAt(2));
    const submit = vi.fn().mockResolvedValue({ report: { ok: true }, expired: true });
    const { result } = renderHook(() => useTimedExam({ start, submit, errorMessage: ERROR }));

    await act(async () => {
      await result.current.start();
    });
    expect(submit).not.toHaveBeenCalled();

    // Past the deadline, then several more ticks: a re-render at zero must not
    // fire a second submission.
    await act(async () => {
      vi.advanceTimersByTime(5000);
    });
    await waitFor(() => expect(result.current.phase).toBe('result'));

    expect(submit).toHaveBeenCalledTimes(1);
    expect(result.current.expired).toBe(true);
  });

  it('submits the answers as they are at the deadline, not as they were at mount', async () => {
    // The trap this guards: an interval captured when the exam started would
    // close over the empty answer set and submit a blank paper on time-out.
    const start = vi.fn().mockResolvedValue(sittingAt(2));
    const submit = vi.fn().mockResolvedValue({ report: {}, expired: true });
    const { result } = renderHook(() => useTimedExam({ start, submit, errorMessage: ERROR }));

    await act(async () => {
      await result.current.start();
    });
    act(() => result.current.choose('q1', 3));
    act(() => result.current.choose('q2', 1));

    await act(async () => {
      vi.advanceTimersByTime(5000);
    });
    await waitFor(() => expect(submit).toHaveBeenCalled());

    expect(submit).toHaveBeenCalledWith('att-1', { q1: 3, q2: 1 });
  });

  it('gives the answers back when submitting fails', async () => {
    const start = vi.fn().mockResolvedValue(sittingAt(600));
    const submit = vi.fn().mockRejectedValue(new Error('network'));
    const { result } = renderHook(() => useTimedExam({ start, submit, errorMessage: ERROR }));

    await act(async () => {
      await result.current.start();
    });
    act(() => result.current.choose('q1', 1));

    await act(async () => {
      await result.current.submit();
    });

    expect(result.current.phase).toBe('running');
    expect(result.current.error).toBe(ERROR);
    expect(result.current.answers).toEqual({ q1: 1 });
  });

  it('allows a retry after a failed submission', async () => {
    const start = vi.fn().mockResolvedValue(sittingAt(600));
    const submit = vi
      .fn()
      .mockRejectedValueOnce(new Error('network'))
      .mockResolvedValueOnce({ report: { ok: true }, expired: false });
    const { result } = renderHook(() => useTimedExam({ start, submit, errorMessage: ERROR }));

    await act(async () => {
      await result.current.start();
    });
    await act(async () => {
      await result.current.submit();
    });
    expect(result.current.phase).toBe('running');

    await act(async () => {
      await result.current.submit();
    });
    expect(result.current.phase).toBe('result');
    expect(submit).toHaveBeenCalledTimes(2);
  });

  it('stays on the intro when the exam cannot be started', async () => {
    const start = vi.fn().mockRejectedValue(new Error('500'));
    const { result } = renderHook(() =>
      useTimedExam({ start, submit: vi.fn(), errorMessage: ERROR }),
    );

    await act(async () => {
      await result.current.start();
    });

    expect(result.current.phase).toBe('intro');
    expect(result.current.error).toBe(ERROR);
  });

  it('clears the previous report when a new sitting starts', async () => {
    const start = vi.fn().mockResolvedValue(sittingAt(600));
    const submit = vi.fn().mockResolvedValue({ report: { score: 40 }, expired: false });
    const { result } = renderHook(() => useTimedExam({ start, submit, errorMessage: ERROR }));

    await act(async () => {
      await result.current.start();
    });
    await act(async () => {
      await result.current.submit();
    });
    expect(result.current.report).toEqual({ score: 40 });

    // Retrying must not leave last time's score on screen while the new exam
    // is being drawn.
    await act(async () => {
      await result.current.start();
    });
    expect(result.current.report).toBeNull();
    expect(result.current.expired).toBe(false);
  });

  it('navigates without running off either end', async () => {
    const start = vi.fn().mockResolvedValue(sittingAt(600));
    const { result } = renderHook(() =>
      useTimedExam({ start, submit: vi.fn(), errorMessage: ERROR }),
    );
    await act(async () => {
      await result.current.start();
    });

    expect(result.current.index).toBe(0);
    act(() => result.current.goTo(-1));
    expect(result.current.index).toBe(0);

    act(() => result.current.goTo(1));
    expect(result.current.index).toBe(1);
    act(() => result.current.goTo(99));
    expect(result.current.index).toBe(1);
  });
});

describe('formatClock', () => {
  it('pads to mm:ss', () => {
    expect(formatClock(0)).toBe('00:00');
    expect(formatClock(9)).toBe('00:09');
    expect(formatClock(75)).toBe('01:15');
    expect(formatClock(3600)).toBe('60:00');
  });

  it('never shows a negative clock', () => {
    // A late tick can compute a negative remainder; "-00:03" reads as a bug to
    // someone who has just run out of time.
    expect(formatClock(-3)).toBe('00:00');
  });
});
