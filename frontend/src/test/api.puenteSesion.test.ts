/**
 * 43.1 (ADR-65 D1, y respuesta del dueño del 2026-10-17): en iPhone, Safari no
 * manda las cookies de la API (`api-production-9751.up.railway.app`) desde
 * `whetzy.com`, porque para él son de terceros. Tras registrarse, `GET /auth/me`
 * llegaba sin sesión (401 en los logs de Railway) y la app volvía a la portada.
 *
 * Puente hasta que exista `api.whetzy.com` (H.59):
 * - El login y el registro ya devuelven los dos tokens en el JSON (`Token`).
 * - Justo después se prueba `/auth/me` solo con la cookie.
 *   - Si la cookie funciona (Chrome, escritorio, local), no se guarda nada y la
 *     sesión sigue solo en cookies HttpOnly.
 *   - Si da 401 (Safari), los tokens se guardan en `sessionStorage`. Duran lo que
 *     la pestaña, sobreviven a recargas y a la navegación de página completa de
 *     `App.tsx`, y viajan como `Authorization: Bearer`. El refresh va en el cuerpo.
 * - Nunca se guardan en `localStorage`.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { auth, logout } from '../services/api';

const KEY = 'whetzy_session_bridge';

function ok(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

function headerOf(call: unknown[], name: string): string | null {
  const init = (call[1] ?? {}) as RequestInit;
  return new Headers(init.headers).get(name);
}

describe('services/api — puente de sesión cuando el navegador no manda cookies (43.1)', () => {
  const fetchMock = vi.fn();

  beforeEach(async () => {
    fetchMock.mockReset();
    vi.stubGlobal('fetch', fetchMock);
    fetchMock.mockResolvedValue(ok({ message: 'ok' }));
    await logout(); // empieza sin tokens de un test anterior
    fetchMock.mockReset();
    sessionStorage.clear();
    localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('sin cookies (la prueba de /auth/me da 401), tras registrarse la siguiente llamada lleva Bearer', async () => {
    fetchMock.mockResolvedValueOnce(ok({ access_token: 'acc-1', refresh_token: 'ref-1' }, 201));
    fetchMock.mockResolvedValueOnce(ok({ detail: 'no cookie' }, 401)); // prueba de cookie
    fetchMock.mockResolvedValueOnce(ok({ id: 'u1' }));

    await auth.register({ email: 'a@b.co', password: 'x', username: 'ab', display_name: 'A', language: 'es' } as never);
    await auth.me();

    expect(headerOf(fetchMock.mock.calls[1], 'Authorization')).toBeNull(); // la prueba va solo con cookie
    expect(headerOf(fetchMock.mock.calls[2], 'Authorization')).toBe('Bearer acc-1');
    expect(JSON.parse(sessionStorage.getItem(KEY) ?? 'null')).toEqual({ access: 'acc-1', refresh: 'ref-1' });
  });

  it('con cookies que funcionan, no se guarda nada y no se manda Authorization', async () => {
    fetchMock.mockResolvedValueOnce(ok({ access_token: 'acc-2', refresh_token: 'ref-2' }));
    fetchMock.mockResolvedValueOnce(ok({ id: 'u1' })); // prueba de cookie: 200
    fetchMock.mockResolvedValueOnce(ok({ id: 'u1' }));

    await auth.login('a@b.co', 'x');
    await auth.me();

    expect(sessionStorage.getItem(KEY)).toBeNull();
    expect(headerOf(fetchMock.mock.calls[2], 'Authorization')).toBeNull();
  });

  it('con el puente activo, un 401 refresca con el refresh en el cuerpo y guarda los tokens nuevos', async () => {
    fetchMock.mockResolvedValueOnce(ok({ access_token: 'acc-3', refresh_token: 'ref-3' }));
    fetchMock.mockResolvedValueOnce(ok({ detail: 'no cookie' }, 401));
    await auth.login('a@b.co', 'x');

    fetchMock.mockResolvedValueOnce(ok({ detail: 'expired' }, 401));
    fetchMock.mockResolvedValueOnce(ok({ access_token: 'acc-4', refresh_token: 'ref-4' }));
    fetchMock.mockResolvedValueOnce(ok({ id: 'u1' }));
    await auth.me();

    const refreshCall = fetchMock.mock.calls[3];
    expect(String(refreshCall[0])).toMatch(/\/auth\/refresh$/);
    expect(JSON.parse(String((refreshCall[1] as RequestInit).body))).toEqual({ refresh_token: 'ref-3' });
    expect(headerOf(fetchMock.mock.calls[4], 'Authorization')).toBe('Bearer acc-4');
    expect(JSON.parse(sessionStorage.getItem(KEY) ?? 'null')).toEqual({ access: 'acc-4', refresh: 'ref-4' });
  });

  it('cerrar sesión borra el puente: la llamada siguiente ya no lleva Authorization', async () => {
    fetchMock.mockResolvedValueOnce(ok({ access_token: 'acc-5', refresh_token: 'ref-5' }));
    fetchMock.mockResolvedValueOnce(ok({ detail: 'no cookie' }, 401));
    await auth.login('a@b.co', 'x');
    fetchMock.mockResolvedValueOnce(ok({ message: 'ok' }));
    await logout();

    fetchMock.mockResolvedValueOnce(ok({ id: 'u1' }));
    await auth.me();

    expect(sessionStorage.getItem(KEY)).toBeNull();
    expect(headerOf(fetchMock.mock.calls[3], 'Authorization')).toBeNull();
  });

  it('los tokens nunca van a localStorage', async () => {
    fetchMock.mockResolvedValueOnce(ok({ access_token: 'acc-6', refresh_token: 'ref-6' }));
    fetchMock.mockResolvedValueOnce(ok({ detail: 'no cookie' }, 401));
    await auth.login('a@b.co', 'x');

    const stored = Object.keys(localStorage).map((k) => localStorage.getItem(k)).join('|');
    expect(stored).not.toContain('acc-6');
    expect(stored).not.toContain('ref-6');
  });

  it('sin tokens (OAuth o cookies de mismo sitio) no manda Authorization y el refresh va sin cuerpo', async () => {
    fetchMock.mockResolvedValueOnce(ok({ detail: 'expired' }, 401));
    fetchMock.mockResolvedValueOnce(ok({ access_token: 'acc-7', refresh_token: 'ref-7' }));
    fetchMock.mockResolvedValueOnce(ok({ id: 'u1' }));
    await auth.me();

    expect(headerOf(fetchMock.mock.calls[0], 'Authorization')).toBeNull();
    expect((fetchMock.mock.calls[1][1] as RequestInit).body ?? null).toBeNull();
    expect(sessionStorage.getItem(KEY)).toBeNull();
  });
});
