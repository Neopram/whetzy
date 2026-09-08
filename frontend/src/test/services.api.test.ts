/**
 * Tests for src/services/api.ts
 * Uses vi.stubGlobal('fetch', ...) so no real network calls.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Reset module state between tests because api.ts stores tokens in module-scope vars.
const makeFetch = (status: number, body: unknown, ok = status >= 200 && status < 300) =>
  vi.fn().mockResolvedValue({
    ok,
    status,
    json: () => Promise.resolve(body),
  });

describe('api service — isAuthenticated / logout', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.resetModules();
  });

  it('returns false when no token stored', async () => {
    const { isAuthenticated } = await import('../services/api');
    expect(isAuthenticated()).toBe(false);
  });

  it('logout clears stored tokens', async () => {
    localStorage.setItem('whetzy_access_token', 'tok');
    localStorage.setItem('whetzy_refresh_token', 'ref');
    const { logout, isAuthenticated } = await import('../services/api');
    expect(isAuthenticated()).toBe(true);
    logout();
    expect(isAuthenticated()).toBe(false);
    expect(localStorage.getItem('whetzy_access_token')).toBeNull();
  });
});

describe('api service — auth.login', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.resetModules();
  });
  afterEach(() => vi.unstubAllGlobals());

  it('stores tokens and returns them on success', async () => {
    vi.stubGlobal('fetch', makeFetch(200, { access_token: 'at1', refresh_token: 'rt1' }));
    const { auth, isAuthenticated } = await import('../services/api');
    const result = await auth.login('user@example.com', 'pass');
    expect(result.access_token).toBe('at1');
    expect(isAuthenticated()).toBe(true);
    expect(localStorage.getItem('whetzy_access_token')).toBe('at1');
  });

  it('throws on 401', async () => {
    vi.stubGlobal('fetch', makeFetch(401, { detail: 'Incorrect email or password' }, false));
    const { auth } = await import('../services/api');
    await expect(auth.login('bad@example.com', 'wrong')).rejects.toThrow(
      'Incorrect email or password',
    );
  });
});

describe('api service — auth.register', () => {
  beforeEach(() => { localStorage.clear(); vi.resetModules(); });
  afterEach(() => vi.unstubAllGlobals());

  it('persists tokens on success', async () => {
    vi.stubGlobal(
      'fetch',
      makeFetch(201, { access_token: 'at2', refresh_token: 'rt2' }),
    );
    const { auth, isAuthenticated } = await import('../services/api');
    await auth.register({
      email: 'new@example.com',
      username: 'newuser',
      display_name: 'New',
      password: 'securepass',
      language: 'es',
    });
    expect(isAuthenticated()).toBe(true);
  });
});

describe('api service — request retries on 401', () => {
  beforeEach(() => { localStorage.clear(); vi.resetModules(); });
  afterEach(() => vi.unstubAllGlobals());

  it('refreshes token and retries on 401', async () => {
    let call = 0;
    const mockFetch = vi.fn().mockImplementation((_url: string, _opts: unknown) => {
      call++;
      if (call === 1) {
        // First call to /auth/me → 401
        return Promise.resolve({ ok: false, status: 401, json: () => Promise.resolve({}) });
      }
      if (call === 2) {
        // Token refresh → success
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ access_token: 'new-at', refresh_token: 'new-rt' }),
        });
      }
      // Retry of /auth/me with new token → success
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ id: 'u1' }) });
    });
    // Seed a refresh token so tryRefresh can proceed
    localStorage.setItem('whetzy_refresh_token', 'rt-old');
    vi.stubGlobal('fetch', mockFetch);
    const { auth } = await import('../services/api');
    const me = await auth.me();
    expect((me as { id: string }).id).toBe('u1');
    expect(call).toBe(3);
  });
});
