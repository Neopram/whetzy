/**
 * Additional api.ts coverage for quiz.end, progress.curriculum, tutor.explain, league.current
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

const makeOk = (body: unknown) =>
  vi.fn().mockResolvedValue({ ok: true, status: 200, json: () => Promise.resolve(body) });

describe('api — extra coverage', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('whetzy_access_token', 'tok');
    vi.resetModules();
  });
  afterEach(() => vi.unstubAllGlobals());

  it('quiz.end returns summary', async () => {
    vi.stubGlobal('fetch', makeOk({ total: 10, correct: 7, xp_earned: 50 }));
    const { quiz } = await import('../services/api');
    const res = await quiz.end('sess1');
    expect((res as { total: number }).total).toBe(10);
  });

  it('quiz.reviewDue returns array', async () => {
    vi.stubGlobal('fetch', makeOk([{ id: 'q1' }]));
    const { quiz } = await import('../services/api');
    const res = await quiz.reviewDue();
    expect(Array.isArray(res)).toBe(true);
  });

  it('progress.curriculum returns curriculum', async () => {
    vi.stubGlobal('fetch', makeOk({ tracks: [] }));
    const { progress } = await import('../services/api');
    const res = await progress.curriculum('track01');
    expect(res).toBeDefined();
  });

  it('tutor.explain returns text', async () => {
    vi.stubGlobal('fetch', makeOk({ explanation: 'Because X' }));
    const { tutor } = await import('../services/api');
    const res = await tutor.explain('q1');
    expect((res as { explanation: string }).explanation).toBe('Because X');
  });

  it('league.current returns league data', async () => {
    vi.stubGlobal('fetch', makeOk({ league: { id: 'bronze' } }));
    const { league } = await import('../services/api');
    const res = await league.current();
    expect(res).toBeDefined();
  });

  it('gamification.missions returns missions array', async () => {
    vi.stubGlobal('fetch', makeOk([{ id: 'm1' }]));
    const { gamification } = await import('../services/api');
    const res = await gamification.missions();
    expect(Array.isArray(res)).toBe(true);
  });

  it('placement.result returns result', async () => {
    vi.stubGlobal('fetch', makeOk({ placement_result: { skill_id: 'sk1' } }));
    const { placement } = await import('../services/api');
    const res = await placement.result('psid1');
    expect(res).toBeDefined();
  });
});
