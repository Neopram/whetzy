/**
 * Serie 34 (coherencia visual): el `Button` común no lo usaba ninguna pantalla
 * real; cada una pintaba sus botones de acción con su propio CSS (degradado en
 * Auth, plano en Duelo). Desde el 2026-10-16 las acciones principales de Auth,
 * las páginas de contraseña y verificación, Duelo y Borrar cuenta usan el
 * común. Esta guarda falla si alguna vuelve a su clase propia.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const PAGES = join(__dirname, '..', 'pages');
const read = (f: string) => readFileSync(join(PAGES, f), 'utf8');

const ADOPTED: Record<string, RegExp> = {
  'AuthScreen.tsx': /<button[^>]*className=\{styles\.submit\}/,
  'ForgotPasswordPage.tsx': /<button[^>]*className=\{styles\.submit\}/,
  'ResetPasswordPage.tsx': /<button[^>]*className=\{styles\.submit\}/,
  'VerifyEmailPage.tsx': /<button[^>]*className=\{styles\.submit\}/,
  'DuelScreen.tsx': /className=\{styles\.(btnPrimary|btnSecondary|btnPlay)\}/,
  'DeleteAccountScreen.tsx': /<button\b/,
};

describe('las acciones principales usan el Button común', () => {
  for (const [file, handMade] of Object.entries(ADOPTED)) {
    it(file, () => {
      const src = read(file);
      expect(src).toContain("from '../components/common/Button'");
      expect(src).not.toMatch(handMade);
    });
  }

  it('el CSS de Auth ya no pinta su propio botón (degradado)', () => {
    const css = readFileSync(join(PAGES, 'AuthScreen.module.css'), 'utf8');
    const submit = css.slice(css.indexOf('.submit {'), css.indexOf('}', css.indexOf('.submit {')));
    expect(submit).not.toMatch(/gradient|background/);
  });
});
