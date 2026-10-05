/**
 * `/health/ready` (backend/app/main.py) solo devuelve `{"status": "ready"}`
 * en éxito y un 503 en fallo — nunca el campo `database`/`db`/`checks` que
 * esta página buscaba antes en el cuerpo de la respuesta. `db` se quedaba en
 * 'unknown' para siempre y 'degraded' era inalcanzable: una base de datos
 * caída se veía exactamente igual que la API entera caída (0.16).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { checkHealth } from '../pages/StatusPage';

describe('checkHealth (0.16)', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('200 con el cuerpo real del backend ({"status":"ready"}) es operational', async () => {
    fetchMock.mockResolvedValue(new Response('{"status":"ready"}', { status: 200 }));
    const result = await checkHealth();
    expect(result.overall).toBe('operational');
    expect(result.api).toBe('up');
    expect(result.db).toBe('up');
  });

  it('503 (el único fallo real de /health/ready, la base de datos) es degraded, no down', async () => {
    fetchMock.mockResolvedValue(
      new Response('{"detail":"Database not ready"}', { status: 503 })
    );
    const result = await checkHealth();
    expect(result.overall).toBe('degraded');
    expect(result.api).toBe('up');
    expect(result.db).toBe('down');
  });

  it('un fetch que ni siquiera consigue respuesta (sin red, proceso caído) es down', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'));
    const result = await checkHealth();
    expect(result.overall).toBe('down');
    expect(result.api).toBe('down');
    expect(result.db).toBe('unknown');
  });
});
