/**
 * `theme.ts` no tenía ningún test (0.6). El 2026-09-24 (929adec) el mismo
 * commit que cambió el tema por defecto a oscuro en `theme.ts` y en
 * `design-tokens.css` dejó `index.html` con `data-theme="light"` sin tocar:
 * cada carga en frío (y la landing pre-renderizada, que existe justo para
 * pintar ya el resultado final) pintaba primero en claro y saltaba a
 * oscuro en cuanto corría `initTheme()` — un flash visible en todas las
 * visitas, y lo contrario de lo que dice el propio comentario de
 * `getStoredTheme`.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { applyTheme, getStoredTheme, initTheme, toggleTheme } from '../theme';

const INDEX_HTML = join(__dirname, '../../index.html');

function freshMetaThemeColor() {
  document.head.innerHTML = '<meta name="theme-color" content="#000000" />';
}

beforeEach(() => {
  localStorage.clear();
  document.documentElement.removeAttribute('data-theme');
  freshMetaThemeColor();
});

afterEach(() => {
  localStorage.clear();
  document.documentElement.removeAttribute('data-theme');
});

describe('theme — oscuro por defecto (0.6)', () => {
  it('getStoredTheme es "dark" sin nada en localStorage', () => {
    expect(getStoredTheme()).toBe('dark');
  });

  it('getStoredTheme ignora un valor guardado que no es "light" ni "dark"', () => {
    localStorage.setItem('whetzy_theme', 'solarized');
    expect(getStoredTheme()).toBe('dark');
  });

  it('getStoredTheme respeta un valor válido guardado', () => {
    localStorage.setItem('whetzy_theme', 'light');
    expect(getStoredTheme()).toBe('light');
  });

  it('applyTheme pone data-theme y el meta theme-color correctos para "dark"', () => {
    applyTheme('dark');
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    expect(document.querySelector('meta[name="theme-color"]')?.getAttribute('content')).toBe(
      '#0A0E1A'
    );
    expect(localStorage.getItem('whetzy_theme')).toBe('dark');
  });

  it('applyTheme pone data-theme y el meta theme-color correctos para "light"', () => {
    applyTheme('light');
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    expect(document.querySelector('meta[name="theme-color"]')?.getAttribute('content')).toBe(
      '#F5F7FB'
    );
  });

  it('toggleTheme alterna y persiste', () => {
    applyTheme('dark');
    const next = toggleTheme();
    expect(next).toBe('light');
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    expect(toggleTheme()).toBe('dark');
  });

  it('initTheme aplica "dark" en una pestaña nueva sin tema guardado', () => {
    initTheme();
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });

  it('el data-theme estático de index.html coincide con el oscuro por defecto de getStoredTheme()', () => {
    // Antes de que corra ningún JS (primer pintado, y el shell que clona
    // prerender-landing.mjs para dist/landing/index.html), el único tema que
    // existe es el que lleva escrito este fichero.
    const html = readFileSync(INDEX_HTML, 'utf-8');
    const match = html.match(/<html[^>]*\sdata-theme="([^"]+)"/);
    expect(match).not.toBeNull();
    expect(match![1]).toBe(getStoredTheme());
  });
});
