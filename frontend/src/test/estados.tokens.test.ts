/**
 * 46.3a (docs/PLAN_UI_AVANZADA.md §2): los estados vacío, de carga, de error y
 * el esqueleto forman una sola familia y pintan solo con los tokens canónicos
 * `--le-*` (`styles/design-tokens.css`), no con los del sistema viejo
 * (`theme/tokens.css`, borrado en 46.4; `--color-*`, `--text-*`, `--bg-*`, `--border-color`).
 *
 * El caso que lo motivó: «Reintentar» al pasar el ratón ponía el texto en
 * `--bg-light`, que en modo claro vale #F5F7FB: texto casi blanco sobre un
 * fondo claro.
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const COMMON = join(dirname(fileURLToPath(import.meta.url)), '..', 'components', 'common');
const ESTADOS = ['EmptyState', 'ErrorState', 'LoadingState', 'Skeleton'];

describe('estados comunes — un solo sistema de tokens (46.3a)', () => {
  for (const nombre of ESTADOS) {
    it(`${nombre}.module.css solo usa variables --le-*`, () => {
      const css = readFileSync(join(COMMON, `${nombre}.module.css`), 'utf8');
      const viejas = [...css.matchAll(/var\((--(?!le-)[\w-]+)/g)].map((m) => m[1]);
      expect(viejas).toEqual([]);
    });
  }

  it('el hover de «Reintentar» usa un color de texto que sigue al tema', () => {
    const css = readFileSync(join(COMMON, 'ErrorState.module.css'), 'utf8');
    const hover = css.slice(css.indexOf('.retryBtn:hover'), css.indexOf('}', css.indexOf('.retryBtn:hover')));
    expect(hover).toMatch(/color:\s*var\(--le-text\)/);
  });
});
