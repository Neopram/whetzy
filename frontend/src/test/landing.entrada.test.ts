/**
 * 46.14: las páginas sueltas de entrada (landing, acceso, restablecer,
 * verificar, estado) entran con `PageEnter` (`data-fx="enter"`, probado en
 * pageEnter.test.tsx). Faltaba el test del cableado: que `App.tsx` envuelva de
 * verdad cada una. Sin él, quitar el envoltorio de la landing no rompía nada y
 * la entrada se perdía en silencio.
 *
 * La landing, además, con `fade={false}`: su hero prerenderizado es el LCP y
 * entrar desde opacidad 0 lo ocultaría hasta que arranque el JS.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const app = readFileSync(resolve(__dirname, '..', 'App.tsx'), 'utf-8');

/** Cuerpo de `function <nombre>(` hasta la llave de cierre de primer nivel. */
function cuerpo(nombre: string): string {
  const ini = app.indexOf(`function ${nombre}(`);
  expect(ini, `function ${nombre} en App.tsx`).toBeGreaterThanOrEqual(0);
  const fin = app.indexOf('\n}\n', ini);
  return app.slice(ini, fin);
}

describe('entrada de las páginas sueltas (46.14)', () => {
  it('la landing entra con PageEnter y sin fundido (no oculta el LCP)', () => {
    expect(cuerpo('LandingPage')).toMatch(/<PageEnter fade=\{false\}>\s*<LandingScreen \/>\s*<\/PageEnter>/);
  });

  it('todas las rutas de landing pasan por LandingPage, no por LandingScreen suelta', () => {
    const sueltas = app.split('\n').filter((l) => l.includes('<LandingScreen') && !l.includes('PageEnter'));
    expect(sueltas).toEqual([]);
  });

  it.each([
    ['acceso', 'AuthRoute', /<PageEnter>\s*<AuthScreen/],
    ['estado', 'App', /<PageEnter><StatusPage \/><\/PageEnter>/],
    ['restablecer', 'App', /<PageEnter><ResetPasswordPage/],
    ['verificar correo', 'App', /<PageEnter><VerifyEmailPage/],
  ])('%s entra con PageEnter', (_n, fn, re) => {
    expect(cuerpo(fn)).toMatch(re);
  });
});
