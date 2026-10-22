/**
 * 42.3 — `tryRefresh` no compartía la promesa en curso: con el access token
 * caducado, cada petición que volvía con 401 lanzaba su propio
 * `POST /auth/refresh`. Home pide varias cosas a la vez al montar, así que eran
 * varios refresh simultáneos con el mismo refresh token; si el backend lo rota,
 * el segundo llega con uno ya gastado, da 401 y `forgetTokens()` tira la sesión
 * que el primero acababa de renovar.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { auth, setOnSessionExpired } from '../services/api';

describe('services/api — un solo refresh para varios 401 a la vez (42.3)', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    setOnSessionExpired(null);
  });

  function esRefresh(url: unknown): boolean {
    return String(url).endsWith('/auth/refresh');
  }

  it('dos peticiones con 401 simultáneo ⇒ un único POST /auth/refresh y las dos se reintentan', async () => {
    // El refresh no contesta hasta que las dos peticiones han visto su 401.
    let soltarRefresh: () => void = () => {};
    const refreshPendiente = new Promise<void>((r) => {
      soltarRefresh = r;
    });
    let refrescado = false;
    const vistas401: string[] = [];

    fetchMock.mockImplementation(async (url: unknown) => {
      if (esRefresh(url)) {
        await refreshPendiente;
        refrescado = true;
        return new Response('{}', { status: 200 });
      }
      if (!refrescado) {
        vistas401.push(String(url));
        return new Response('{}', { status: 401 });
      }
      return new Response('{"id":"u1"}', { status: 200 });
    });

    const a = auth.me();
    const b = auth.me();
    await vi.waitFor(() => expect(vistas401).toHaveLength(2));
    soltarRefresh();

    await expect(Promise.all([a, b])).resolves.toEqual([{ id: 'u1' }, { id: 'u1' }]);

    const refreshes = fetchMock.mock.calls.filter(([url]) => esRefresh(url));
    expect(refreshes).toHaveLength(1);
    // 2 originales con 401 + 1 refresh + 2 reintentos.
    expect(fetchMock).toHaveBeenCalledTimes(5);
  });

  it('la promesa compartida se suelta al terminar: un 401 posterior vuelve a refrescar', async () => {
    let fase = 0; // 0: 401 → refresh → ok; 1: otra vez 401 → refresh → ok
    let pendiente401 = true;
    fetchMock.mockImplementation(async (url: unknown) => {
      if (esRefresh(url)) {
        pendiente401 = false;
        return new Response('{}', { status: 200 });
      }
      if (pendiente401) return new Response('{}', { status: 401 });
      return new Response(`{"id":"u${fase}"}`, { status: 200 });
    });

    await expect(auth.me()).resolves.toEqual({ id: 'u0' });
    fase = 1;
    pendiente401 = true;
    await expect(auth.me()).resolves.toEqual({ id: 'u1' });

    expect(fetchMock.mock.calls.filter(([url]) => esRefresh(url))).toHaveLength(2);
  });

  it('también se suelta tras un refresh fallido: el siguiente 401 lo intenta de nuevo', async () => {
    const onExpired = vi.fn();
    setOnSessionExpired(onExpired);
    let refreshOk = false;
    let pendiente401 = true;
    fetchMock.mockImplementation(async (url: unknown) => {
      if (esRefresh(url)) {
        if (refreshOk) pendiente401 = false;
        return new Response('{}', { status: refreshOk ? 200 : 401 });
      }
      if (pendiente401) return new Response('{}', { status: 401 });
      return new Response('{"id":"u1"}', { status: 200 });
    });

    await expect(auth.me()).rejects.toMatchObject({ status: 401 });
    expect(onExpired).toHaveBeenCalledTimes(1);

    refreshOk = true;
    await expect(auth.me()).resolves.toEqual({ id: 'u1' });
    expect(fetchMock.mock.calls.filter(([url]) => esRefresh(url))).toHaveLength(2);
  });
});
