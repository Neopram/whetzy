/**
 * 42.11: la cola offline no se vacía hasta que el servidor confirma.
 * Cola real sobre fake-indexeddb; solo `quiz.answer` es falso.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { IDBFactory } from 'fake-indexeddb';
import { ApiError } from '../services/api';
import type { PendingAnswer } from '../services/offlineQueue';

const answer = vi.fn();
vi.mock('../services/api', async (importActual) => ({
  ...(await importActual<typeof import('../services/api')>()),
  quiz: { answer: (...args: unknown[]) => answer(...args) },
}));

const make = (id: string, timestamp: number, extra: Partial<PendingAnswer> = {}): PendingAnswer => ({
  id,
  sessionId: 's1',
  questionId: `q-${id}`,
  selectedIndex: 0,
  responseTimeMs: 500,
  timestamp,
  ...extra,
});

async function setup(items: PendingAnswer[]) {
  vi.resetModules();
  vi.stubGlobal('indexedDB', new IDBFactory());
  const queue = await import('../services/offlineQueue');
  for (const it of items) await queue.enqueue(it);
  const { useOfflineSync } = await import('../hooks/useOfflineSync');
  const hook = renderHook(() => useOfflineSync());
  await waitFor(() => expect(hook.result.current.pendingAnswers).toBe(items.length));
  return { queue, hook };
}

async function goOnline(hook: Awaited<ReturnType<typeof setup>>['hook']) {
  act(() => {
    window.dispatchEvent(new Event('online'));
  });
  await waitFor(() => expect(answer).toHaveBeenCalled());
  await waitFor(() => expect(hook.result.current.isSyncing).toBe(false));
}

const sentIds = () => answer.mock.calls.map((c) => c[5]);

describe('useOfflineSync — flush conserva lo que el servidor no confirmó (42.11)', () => {
  // Con llaves: si el hook devuelve el mock, vitest lo llama como teardown.
  beforeEach(() => {
    answer.mockReset();
  });
  afterEach(() => vi.unstubAllGlobals());

  it('si la red cae en la 2.ª de 3, la 2.ª y la 3.ª siguen en la cola', async () => {
    answer
      .mockResolvedValueOnce({})
      .mockRejectedValueOnce(new ApiError('Network error', null))
      .mockResolvedValue({});
    const { queue, hook } = await setup([make('a1', 1), make('a2', 2), make('a3', 3)]);
    await goOnline(hook);
    // Para en el primer fallo transitorio: la 3.ª ni se intenta.
    expect(sentIds()).toEqual(['a1', 'a2']);
    expect((await queue.peekAll()).map((p) => p.id)).toEqual(['a2', 'a3']);
    await waitFor(() => expect(hook.result.current.pendingAnswers).toBe(2));
  });

  it('un 5xx también conserva la respuesta', async () => {
    answer.mockRejectedValue(new ApiError('Bad gateway', 502));
    const { queue, hook } = await setup([make('a1', 1)]);
    await goOnline(hook);
    expect(await queue.pendingCount()).toBe(1);
    await waitFor(() => expect(hook.result.current.pendingAnswers).toBe(1));
  });

  it('un 409 (event_id ya registrado) cuenta como confirmada y sale de la cola', async () => {
    answer.mockRejectedValueOnce(new ApiError('event_id already used', 409)).mockResolvedValue({});
    const { queue, hook } = await setup([make('a1', 1), make('a2', 2)]);
    await goOnline(hook);
    expect(sentIds()).toEqual(['a1', 'a2']);
    expect(await queue.pendingCount()).toBe(0);
    expect(await queue.discardedCount()).toBe(0);
    await waitFor(() => expect(hook.result.current.pendingAnswers).toBe(0));
  });

  it('un 4xx definitivo va a descartes con contador y no bloquea el resto', async () => {
    answer
      .mockRejectedValueOnce(new ApiError('Not found', 404))
      .mockRejectedValueOnce(new ApiError('Unprocessable', 422))
      .mockResolvedValue({});
    const { queue, hook } = await setup([make('a1', 1), make('a2', 2), make('a3', 3)]);
    await goOnline(hook);
    expect(sentIds()).toEqual(['a1', 'a2', 'a3']);
    expect(await queue.pendingCount()).toBe(0);
    expect(await queue.discardedCount()).toBe(2);
    await waitFor(() => expect(hook.result.current.pendingAnswers).toBe(0));
  });

  it('declaredUnknown se guarda al encolar y viaja con true', async () => {
    answer.mockResolvedValue({});
    const { hook } = await setup([make('a1', 1, { declaredUnknown: true }), make('a2', 2)]);
    await goOnline(hook);
    expect(answer.mock.calls[0][4]).toBe(true);
    expect(answer.mock.calls[1][4]).toBe(false);
  });
});
