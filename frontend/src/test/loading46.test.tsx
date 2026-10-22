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
  // La clave acaba en «loading» o lleva sufijo («playground.loadingEditor») y la
  // llamada puede traer texto de respaldo: `t('common.loading', 'Cargando...')`.
  // La regex anterior pedía `loading')}` pelado y no veía ninguno de los dos.
  const BARE = /<(p|div|span)\b[^>]*>\s*\{(?:cur\.error \?\? )?t\(['"][\w.]*[lL]oading\w*['"](?:\s*,\s*(?:'[^']*'|"[^"]*"))?\)\}\s*<\/\1>/;

  // Un esqueleto con su etiqueta solo para el lector de pantalla no es un «Cargando…» suelto.
  const suelto = (line: string) => BARE.test(line) && !line.includes('visually-hidden');

  it('la regex ve las variantes con sufijo, con respaldo y dentro de un fallback', () => {
    expect(BARE.test(`return <div className={s.a}>{t('common.loading', 'Cargando...')}</div>`)).toBe(true);
    expect(BARE.test(`<Suspense fallback={<div className={s.a}>{t('playground.loadingEditor')}</div>}>`)).toBe(true);
    expect(BARE.test(`<Suspense fallback={<p className={s.loading}>{t('playground.loadingEditor')}</p>}>`)).toBe(true);
    expect(BARE.test(`<span>{t('x.loading')}</span>`)).toBe(true);
    expect(BARE.test(`<button>{busy ? t('x.sending') : t('x.send')}</button>`)).toBe(false);
    expect(suelto(`<span className="visually-hidden">{t('quiz.why.loadingSr')}</span>`)).toBe(false);
    expect(BARE.test(`<Loading label={t('home.loading')} shape="line" />`)).toBe(false);
  });

  it('pages/ y components/', () => {
    const hits = files.flatMap((f) =>
      readFileSync(f, 'utf-8').split('\n')
        .map((line, i) => (suelto(line) ? `${relative(root, f)}:${i + 1}` : null))
        .filter((x): x is string => x !== null),
    );
    expect(hits).toEqual([]);
  });
});
