/**
 * 0.13 — dos huecos en services/api.ts alrededor de la sesión:
 *
 * 1. `request()` dejaba escapar el `TypeError` en bruto de `fetch()` cuando
 *    no hay red (sin wifi, DNS caído…), en vez de envolverlo en `ApiError`.
 *    Todo `err instanceof ApiError` de la app — incluido el de App.tsx que
 *    decide si perder la red debe cerrar la sesión mirando `esTransitorio`
 *    — daba `false` para ese caso: un wifi que se cae un segundo se trataba
 *    como "la sesión ya no vale" en vez de "reintenta en un rato".
 *
 * 2. Un 401 definitivo (sesión caducada, refresh también falla) solo se
 *    manejaba en el chequeo inicial de App.tsx. Cualquier otra llamada a
 *    mitad de sesión no tenía ninguna salida de vuelta al login.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, auth, logout, setOnSessionExpired } from '../services/api';

describe('services/api — red caída no es lo mismo que sesión caducada (0.13)', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    setOnSessionExpired(null);
  });

  it('un fetch que rechaza (sin red) se envuelve en ApiError con status null, no un TypeError en bruto', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(auth.me()).rejects.toMatchObject({
      name: 'ApiError',
      status: null,
    });
  });

  it('ese ApiError de red cuenta como transitorio (esTransitorio) — no debe cerrar la sesión', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'));

    try {
      await auth.me();
      expect.unreachable('auth.me() tenía que rechazar');
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).esTransitorio).toBe(true);
    }
  });

  it('una red caída no dispara el aviso global de sesión caducada', async () => {
    const onExpired = vi.fn();
    setOnSessionExpired(onExpired);
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(auth.me()).rejects.toBeInstanceOf(ApiError);
    expect(onExpired).not.toHaveBeenCalled();
  });

  it('un 401 que sobrevive al refresh SÍ dispara el aviso global de sesión caducada', async () => {
    const onExpired = vi.fn();
    setOnSessionExpired(onExpired);
    // La petición real, y el intento de refresh, los dos 401.
    fetchMock.mockResolvedValue(new Response('{}', { status: 401 }));

    await expect(auth.me()).rejects.toMatchObject({ status: 401 });
    expect(onExpired).toHaveBeenCalledTimes(1);
  });

  it('un 401 que SÍ consigue refrescar no dispara el aviso (no hubo sesión caducada)', async () => {
    const onExpired = vi.fn();
    setOnSessionExpired(onExpired);
    fetchMock
      .mockResolvedValueOnce(new Response('{}', { status: 401 })) // la llamada real
      .mockResolvedValueOnce(new Response('{}', { status: 200 })) // /auth/refresh
      .mockResolvedValueOnce(new Response('{"id":"u1"}', { status: 200 })); // reintento

    await auth.me();
    expect(onExpired).not.toHaveBeenCalled();
  });

  it('logout() disparado desde onSessionExpired no entra en bucle infinito con la sesión realmente caducada', async () => {
    // Reproduce la cadena que encontró el dueño (revisión de #153): un 401
    // definitivo llama a onSessionExpired -> signOut() -> logout() sin
    // esperar. Si logout() reintenta el refresh como cualquier otra llamada,
    // su propio 401 vuelve a llamar a onSessionExpired, que vuelve a llamar
    // a logout(), sin fin -- dos peticiones a la API por vuelta mientras la
    // pestaña siga abierta. El tope de abajo convierte ese bucle en un fallo
    // rápido del test en vez de colgarlo (igual que hizo el dueño: "sin
    // tope, el worker de vitest murió").
    const onExpired = vi.fn(() => {
      void logout();
    });
    setOnSessionExpired(onExpired);

    let calls = 0;
    const CAP = 20;
    fetchMock.mockImplementation(async () => {
      calls += 1;
      if (calls > CAP) throw new Error(`bucle infinito: más de ${CAP} peticiones`);
      return new Response('{}', { status: 401 });
    });

    await expect(auth.me()).rejects.toMatchObject({ status: 401 });
    // Deja que el logout() disparado sin esperar desde onSessionExpired
    // termine su propia cadena de promesas.
    await new Promise((resolve) => setTimeout(resolve, 20));

    expect(calls).toBeLessThan(10);
  });
});
