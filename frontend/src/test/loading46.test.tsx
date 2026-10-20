/**
 * 46.14 (docs/PLAN_UI_AVANZADA.md §7.4): las pantallas cargan con un esqueleto
 * con la forma de lo que viene, no con un «Cargando…» suelto. El lector de
 * pantalla oye «Cargando» (`role="status"`, `aria-busy`); el esqueleto no se
 * pinta si los datos llegan en menos de 150 ms (sin parpadeo).
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen } from '@testing-library/react';
import { Loading, LOADING_DELAY_MS } from '../components/common/Loading';

afterEach(() => { cleanup(); vi.useRealTimers(); });

describe('Loading (46.14)', () => {
  it('anuncia la carga al momento y pinta el esqueleto pasados 150 ms', () => {
    vi.useFakeTimers();
    render(<Loading label="Cargando" shape="list" />);
    const status = screen.getByRole('status');
    expect(status).toHaveAttribute('aria-busy', 'true');
    expect(status).toHaveTextContent('Cargando');
    expect(status.querySelector('[data-skeleton]')).toBeNull();
    act(() => { vi.advanceTimersByTime(LOADING_DELAY_MS); });
    expect(status.querySelectorAll('[data-skeleton]').length).toBeGreaterThan(0);
  });

  it.each(['line', 'text', 'list', 'card'] as const)('forma «%s»', (shape) => {
    vi.useFakeTimers();
    render(<Loading label="Cargando" shape={shape} />);
    act(() => { vi.advanceTimersByTime(LOADING_DELAY_MS); });
    expect(screen.getByRole('status')).toHaveAttribute('data-shape', shape);
  });
});

/** Ningún «Cargando…» suelto como único contenido de un bloque. Los botones que
 *  dicen «Enviando…» (ternario dentro del botón) son otra cosa y no cuentan. */
describe('guarda: sin «Cargando…» suelto (46.14)', () => {
  const root = resolve(__dirname, '..');
  const files: string[] = [];
  const walk = (dir: string) => {
    for (const f of readdirSync(dir)) {
      const p = join(dir, f);
      if (statSync(p).isDirectory()) { if (f !== 'test') walk(p); }
      else if (p.endsWith('.tsx')) files.push(p);
    }
  };
  walk(join(root, 'pages'));
  walk(join(root, 'components'));
  const BARE = /<(p|div|span)\b[^>]*>\s*\{(?:cur\.error \?\? )?t\(['"][\w.]*loading['"]\)\}\s*<\/\1>/;

  it('pages/ y components/', () => {
    const hits = files.flatMap((f) =>
      readFileSync(f, 'utf-8').split('\n')
        .map((line, i) => (BARE.test(line) ? `${relative(root, f)}:${i + 1}` : null))
        .filter((x): x is string => x !== null),
    );
    expect(hits).toEqual([]);
  });
});
