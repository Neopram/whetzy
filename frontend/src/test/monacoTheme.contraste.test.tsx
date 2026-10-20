/**
 * El editor de código (Monaco) usa un tema propio, no `vs-dark`: `vs-dark`
 * pinta las cadenas SQL en rojo puro sobre #1E1E1E (4,17:1), los comentarios a
 * 4,21:1 y las variables predefinidas a 2,92:1, por debajo de WCAG AA (4,5:1).
 * Aquí se mide cada regla del tema contra el fondo del editor, y se comprueba
 * que el componente lo registra y lo usa.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render } from '@testing-library/react';
import { EDITOR_BACKGROUND, WHETZY_DARK, whetzyDarkTheme } from '../lib/monacoTheme';

const props: Record<string, unknown> = {};
vi.mock('../lib/monacoSetup', () => ({}));
vi.mock('@monaco-editor/react', () => ({
  default: (p: Record<string, unknown>) => {
    Object.assign(props, p);
    return null;
  },
}));

function luminancia(hex: string): number {
  const n = parseInt(hex.replace('#', '').slice(0, 6), 16);
  const canal = (v: number) => {
    const s = v / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  };
  return 0.2126 * canal((n >> 16) & 255) + 0.7152 * canal((n >> 8) & 255) + 0.0722 * canal(n & 255);
}
function ratio(a: string, b: string): number {
  const [l1, l2] = [luminancia(a), luminancia(b)];
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
}

afterEach(cleanup);

describe('tema del editor de código', () => {
  it('cada color de token llega a 4,5:1 sobre el fondo del editor', () => {
    const bajos = whetzyDarkTheme.rules
      .filter((r) => r.foreground)
      .map((r) => [r.token, r.foreground!, ratio(r.foreground!, EDITOR_BACKGROUND)] as const)
      .filter(([, , c]) => c < 4.5)
      .map(([t, f, c]) => `${t || '(texto)'} #${f} ${c.toFixed(2)}:1`);
    expect(bajos).toEqual([]);
  });

  it('el texto y los números de línea también', () => {
    const c = whetzyDarkTheme.colors;
    expect(c['editor.background']).toBe(EDITOR_BACKGROUND);
    for (const k of ['editor.foreground', 'editorLineNumber.foreground', 'editorLineNumber.activeForeground']) {
      expect(ratio(c[k], EDITOR_BACKGROUND), k).toBeGreaterThanOrEqual(4.5);
    }
  });

  it('el editor registra el tema antes de montar y lo usa', async () => {
    const { MonacoCodeEditor } = await import('../components/quiz/MonacoCodeEditor');
    render(<MonacoCodeEditor value="SELECT 'x'" language="sql" />);
    expect(props.theme).toBe(WHETZY_DARK);
    const defineTheme = vi.fn();
    (props.beforeMount as (m: unknown) => void)({ editor: { defineTheme } });
    expect(defineTheme).toHaveBeenCalledWith(WHETZY_DARK, whetzyDarkTheme);
  });
});
