/**
 * `public/sw.js` llevaba su `VERSION` como una fecha escrita a mano
 * (0.15) — ningún paso del build la tocaba, así que un cambio en la lógica
 * del propio service worker sin que alguien subiera esa fecha dejaba
 * `CACHE_NAME` igual que antes y el `activate` no borraba ninguna caché
 * vieja (el mismo bug que `whetzy-v1`, descrito en la cabecera del propio
 * fichero). `injectBuildVersion` sustituye el placeholder por el commit
 * real del build — ver `vite.config.ts` (`swVersionPlugin`).
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { injectBuildVersion, SW_VERSION_PLACEHOLDER } from '../../scripts/swVersion';

describe('injectBuildVersion (0.15)', () => {
  it('sustituye el placeholder por el sha dado', () => {
    const source = `const VERSION = '${SW_VERSION_PLACEHOLDER}';`;
    expect(injectBuildVersion(source, 'abc1234')).toBe("const VERSION = 'abc1234';");
  });

  it('sustituye todas las apariciones, no solo la primera', () => {
    const source = `${SW_VERSION_PLACEHOLDER} y otra vez ${SW_VERSION_PLACEHOLDER}`;
    expect(injectBuildVersion(source, 'X')).toBe('X y otra vez X');
  });

  it('revienta si el placeholder no está — nunca debe colarse una versión fija', () => {
    expect(() => injectBuildVersion("const VERSION = 'v2-2026-09-19';", 'abc1234')).toThrow(
      /no contiene/
    );
  });
});

describe('public/sw.js — contrato con el placeholder (0.15)', () => {
  it('declara VERSION con el placeholder, no una fecha a mano', () => {
    const swSource = readFileSync(join(__dirname, '../../public/sw.js'), 'utf-8');
    expect(swSource).toContain(`const VERSION = '${SW_VERSION_PLACEHOLDER}';`);
  });
});
