/**
 * 39.34: la lección muestra el 429 `free_daily_quota` con la hora de
 * reinicio, en vez del mensaje genérico "no se pudo cargar" que se
 * mostraba antes para cualquier fallo (incluido este, hasta que api.ts
 * dejó de descartar el `detail` estructurado del backend).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import '../i18n';
import { LessonScreen } from '../pages/LessonScreen';
import { ApiError, lessonsApi } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, lessonsApi: { forSkill: vi.fn() } };
});

const forSkill = lessonsApi.forSkill as unknown as ReturnType<typeof vi.fn>;

beforeEach(() => vi.clearAllMocks());
afterEach(cleanup);

describe('LessonScreen — cupo diario Free (39.34)', () => {
  it('muestra el mensaje de cupo con la hora de reinicio, no el error genérico', async () => {
    forSkill.mockRejectedValue(
      new ApiError('free_daily_quota', 429, {
        code: 'free_daily_quota',
        kind: 'lessons',
        limit: 5,
        resets_at: '2026-09-28T00:00:00+00:00',
      }),
    );

    render(<LessonScreen skillId="sk010101" onExit={() => {}} />);

    expect(await screen.findByText(/5/)).toBeInTheDocument();
    expect(screen.queryByText(/no se pudo cargar|could not be loaded/i)).not.toBeInTheDocument();
  });

  it('sigue mostrando el error genérico para un fallo que no es de cupo', async () => {
    forSkill.mockRejectedValue(new Error('network down'));

    render(<LessonScreen skillId="sk010101" onExit={() => {}} />);

    expect(await screen.findByText(/no se pudo cargar|could not be loaded/i)).toBeInTheDocument();
  });
});
