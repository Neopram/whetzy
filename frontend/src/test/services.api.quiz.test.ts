/**
 * Tests for quiz, progress, glossary, placement sections of api.ts
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

const makeOk = (body: unknown) =>
  vi.fn().mockResolvedValue({ ok: true, status: 200, json: () => Promise.resolve(body) });

const makeErr = (status: number, detail: string) =>
  vi.fn().mockResolvedValue({
    ok: false,
    status,
    json: () => Promise.resolve({ detail }),
  });

describe('api — quiz', () => {
  beforeEach(() => {
    localStorage.clear();
    document.cookie = 'whetzy_logged_in=1; path=/';
    vi.resetModules();
  });
  afterEach(() => vi.unstubAllGlobals());

  it('quiz.start returns session data', async () => {
    vi.stubGlobal('fetch', makeOk({ session_id: 'sid1', question: { id: 'q1' } }));
    const { quiz } = await import('../services/api');
    const res = await quiz.start('track01', 'skill01');
    expect((res as { session_id: string }).session_id).toBe('sid1');
  });

  it('quiz.answer sends correct payload', async () => {
    const mockFetch = makeOk({ correct: true, xp_earned: 10 });
    vi.stubGlobal('fetch', mockFetch);
    const { quiz } = await import('../services/api');
    await quiz.answer('sess1', 'q1', 0, 1500);
    const callBody = JSON.parse((mockFetch.mock.calls[0][1] as RequestInit).body as string);
    expect(callBody.session_id).toBe('sess1');
    expect(callBody.selected_index).toBe(0);
    expect(callBody.response_time_ms).toBe(1500);
  });

  it('throws on HTTP error with detail message', async () => {
    vi.stubGlobal('fetch', makeErr(422, 'Invalid session'));
    const { quiz } = await import('../services/api');
    await expect(quiz.start('track01', 'skill01')).rejects.toThrow('Invalid session');
  });
});

describe('api — progress', () => {
  beforeEach(() => {
    localStorage.clear();
    document.cookie = 'whetzy_logged_in=1; path=/';
    vi.resetModules();
  });
  afterEach(() => vi.unstubAllGlobals());

  it('progress.dashboard returns data', async () => {
    vi.stubGlobal('fetch', makeOk({ total_questions_answered: 5, overall_accuracy: 0.8 }));
    const { progress: progressApi } = await import('../services/api');
    const dash = await progressApi.dashboard();
    expect((dash as { total_questions_answered: number }).total_questions_answered).toBe(5);
  });

  it('progress.skills returns array', async () => {
    vi.stubGlobal('fetch', makeOk([{ skill_id: 'sk1', p_known: 0.7 }]));
    const { progress: progressApi } = await import('../services/api');
    const skills = await progressApi.skills();
    expect(Array.isArray(skills)).toBe(true);
  });
});

describe('api — glossary', () => {
  beforeEach(() => {
    localStorage.clear();
    document.cookie = 'whetzy_logged_in=1; path=/';
    vi.resetModules();
  });
  afterEach(() => vi.unstubAllGlobals());

  it('glossary.list returns terms', async () => {
    vi.stubGlobal('fetch', makeOk([{ id: 'g1', term_es: 'Hola' }]));
    const { glossary: glossaryApi } = await import('../services/api');
    const terms = await glossaryApi.forTrack('track01');
    expect(Array.isArray(terms)).toBe(true);
  });
});

describe('api — placement', () => {
  beforeEach(() => {
    localStorage.clear();
    document.cookie = 'whetzy_logged_in=1; path=/';
    vi.resetModules();
  });
  afterEach(() => vi.unstubAllGlobals());

  it('placement.start returns placement data', async () => {
    vi.stubGlobal('fetch', makeOk({ session_id: 'psid', question: { id: 'pq1' } }));
    const { placement: placementApi } = await import('../services/api');
    // `start` necesita el track: el motor CAT elige el pool por ruta.
    const res = await placementApi.start('track01');
    expect((res as { session_id: string }).session_id).toBe('psid');
  });
});
