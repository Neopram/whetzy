/**
 * Serie 34 (2026-10-16): Marketplace y el perfil público traían su CSS como
 * hoja global (`styles/marketplace.css`, `styles/publicProfile.css`), con
 * clases sin ámbito: `.empty`, `.handle`, `.arrow`, `.bio` en lo más alto,
 * que habrían pisado a cualquier `className="empty"` del resto de la app.
 * Ahora son `.module.css`. Esta guarda falla si un componente vuelve a
 * importar una hoja global; las únicas que quedan están en la lista, cada una
 * con su motivo.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { describe, expect, it } from 'vitest';

const SRC = join(__dirname, '..');

const PERMITIDAS: Record<string, string> = {
  // La base de toda la app: reset, tokens y tipografía.
  'App.tsx': 'global.css',
  // Pendiente: los E2E buscan sus clases planas (`button.option`).
  'pages/OnboardingScreen.tsx': 'onboarding.css',
};

function fuentes(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) return name === 'test' ? [] : fuentes(full);
    return /\.(tsx|ts)$/.test(name) ? [full] : [];
  });
}

describe('el CSS de los componentes va en módulos', () => {
  it('ningún componente importa una hoja global fuera de la lista', () => {
    const globales = fuentes(SRC).flatMap((f) => {
      const rel = relative(SRC, f).split('\\').join('/');
      return [...readFileSync(f, 'utf8').matchAll(/^import\s+['"]([^'"]+\.css)['"]/gm)]
        .map((m) => m[1])
        .filter((css) => !css.endsWith('.module.css'))
        .filter((css) => !(PERMITIDAS[rel] && css.endsWith(PERMITIDAS[rel])))
        .map((css) => `${rel} → ${css}`);
    });
    expect(globales).toEqual([]);
  });
});
