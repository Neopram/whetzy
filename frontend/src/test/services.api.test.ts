/**
 * Tests for src/services/api.ts — HttpOnly cookie auth.
 * Uses vi.stubGlobal('fetch', ...) so no real network calls.
 *
 * `isAuthenticated()` reads the `whetzy_logged_in` non-HttpOnly cookie, not
 * localStorage tokens (removed in 22.15) — but only same-site, since it's
 * host-only to whichever domain answered the login. `App.tsx` stopped using
 * it for the initial decision in production, where frontend and backend are
 * different domains and the cookie is never visible there (30.9).
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

const makeFetch = (status: number, body: unknown, ok = status >= 200 && status < 300) =>
  vi.fn().mockResolvedValue({
    ok,
    status,
    json: () => Promise.resolve(body),
  });

function setLoggedInCookie(value = '1') {
  document.cookie = `whetzy_logged_in=${value}; path=/`;
}

function clearLoggedInCookie() {
  document.cookie = 'whetzy_logged_in=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
}

describe('api service — isAuthenticated', () => {
  beforeEach(() => {
    clearLoggedInCookie();
    localStorage.clear();
    vi.resetModules();
  });

  it('returns false when no cookie set', async () => {
    const { isAuthenticated } = await import('../services/api');
    expect(isAuthenticated()).toBe(false);
  });

  it('returns true when whetzy_logged_in cookie is set', async () => {
    setLoggedInCookie();
    const { isAuthenticated } = await import('../services/api');
    expect(isAuthenticated()).toBe(true);
  });

  it('clears legacy localStorage tokens on import', async () => {
    localStorage.setItem('whetzy_access_token', 'old');
    localStorage.setItem('whetzy_refresh_token', 'old');
    await import('../services/api');
    expect(localStorage.getItem('whetzy_access_token')).toBeNull();
    expect(localStorage.getItem('whetzy_refresh_token')).toBeNull();
  });
});

describe('api service — auth.login', () => {
  beforeEach(() => {
    clearLoggedInCookie();
    localStorage.clear();
    vi.resetModules();
  });
  afterEach(() => vi.unstubAllGlobals());

  it('returns tokens on success and sends credentials: include', async () => {
    const mockFetch = makeFetch(200, { access_token: 'at1', refresh_token: 'rt1' });
    vi.stubGlobal('fetch', mockFetch);
    const { auth } = await import('../services/api');
    const result = await auth.login('user@example.com', 'pass');
    expect(result.access_token).toBe('at1');
    expect(mockFetch.mock.calls[0][1].credentials).toBe('include');
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
  beforeEach(() => { clearLoggedInCookie(); localStorage.clear(); vi.resetModules(); });
  afterEach(() => vi.unstubAllGlobals());

  it('returns tokens on success with credentials: include', async () => {
    vi.stubGlobal(
      'fetch',
      makeFetch(201, { access_token: 'at2', refresh_token: 'rt2' }),
    );
    const { auth } = await import('../services/api');
    const result = await auth.register({
      email: 'new@example.com',
      username: 'newuser',
      display_name: 'New',
      password: 'securepass',
      language: 'es',
    });
    expect(result.access_token).toBe('at2');
  });
});

describe('api service — logout', () => {
  beforeEach(() => { clearLoggedInCookie(); localStorage.clear(); vi.resetModules(); });
  afterEach(() => vi.unstubAllGlobals());

  it('calls POST /auth/logout with credentials: include', async () => {
    const mockFetch = makeFetch(200, { message: 'Logged out successfully' });
    vi.stubGlobal('fetch', mockFetch);
    const { logout } = await import('../services/api');
    await logout();
    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, opts] = mockFetch.mock.calls[0];
    expect(String(url)).toContain('/auth/logout');
    expect(opts.method).toBe('POST');
    expect(opts.credentials).toBe('include');
  });

  it('does not throw when there is no session left to revoke (401)', async () => {
    vi.stubGlobal('fetch', makeFetch(401, {}, false));
    const { logout } = await import('../services/api');
    await expect(logout()).resolves.toBeUndefined();
  });
});

describe('api service — request retries on 401 via cookie refresh', () => {
  beforeEach(() => { clearLoggedInCookie(); localStorage.clear(); vi.resetModules(); });
  afterEach(() => vi.unstubAllGlobals());

  it('refreshes via cookie and retries on 401', async () => {
    setLoggedInCookie();
    let call = 0;
    const mockFetch = vi.fn().mockImplementation((_url: string, _opts: unknown) => {
      call++;
      if (call === 1) {
        return Promise.resolve({ ok: false, status: 401, json: () => Promise.resolve({}) });
      }
      if (call === 2) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ access_token: 'new-at', refresh_token: 'new-rt' }),
        });
      }
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ id: 'u1' }) });
    });
    vi.stubGlobal('fetch', mockFetch);
    const { auth } = await import('../services/api');
    const me = await auth.me();
    expect((me as { id: string }).id).toBe('u1');
    expect(call).toBe(3);
    const refreshCall = mockFetch.mock.calls[1];
    expect(refreshCall[1].credentials).toBe('include');
  });
});
