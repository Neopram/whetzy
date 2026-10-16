/**
 * Auditoría de pantallas, 2026-10-16: «←» en ProjectScreen y «✕» en
 * PlaygroundScreen eran botones sin nombre accesible. Un lector de pantalla
 * los anunciaba como «botón» (o leía la flecha) sin decir qué hacen.
 *
 * Esta guarda recorre el JSX contando llaves y comillas (una regex no sirve: el
 * `>` de `onClick={() => …}` cortaría la etiqueta) y falla si un `<button>`
 * solo contiene símbolos sin letras y no lleva `aria-label` ni
 * `aria-labelledby`. Un contenido con expresión (`{t('…')}`) cuenta como texto.
 * El parser de TypeScript no sirve aquí: `typescript` 7 no trae la API de JS.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { describe, expect, it } from 'vitest';

const SRC = join(__dirname, '..');

function tsxFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) return name === 'test' ? [] : tsxFiles(full);
    return name.endsWith('.tsx') ? [full] : [];
  });
}

/** Fin de la etiqueta de apertura que empieza en `start` (`<button`), saltando
 *  lo que haya dentro de llaves y comillas. Devuelve el índice del `>`. */
function openingTagEnd(src: string, start: number): number {
  let depth = 0;
  let quote: string | null = null;
  for (let i = start; i < src.length; i += 1) {
    const c = src[i];
    if (quote) {
      if (c === quote) quote = null;
    } else if (c === '"' || c === "'" || c === '`') {
      quote = c;
    } else if (c === '{') depth += 1;
    else if (c === '}') depth -= 1;
    else if (c === '>' && depth === 0) return i;
  }
  return -1;
}

function unnamedButtons(file: string): string[] {
  const src = readFileSync(file, 'utf8');
  const found: string[] = [];
  const re = /<button\b/g;
  for (let m = re.exec(src); m; m = re.exec(src)) {
    const end = openingTagEnd(src, m.index);
    if (end < 0 || src[end - 1] === '/') continue;
    const attrs = src.slice(m.index, end);
    const close = src.indexOf('</button>', end);
    if (close < 0) continue;
    const inner = src.slice(end + 1, close);
    if (/aria-label(ledby)?=|\{\.\.\./.test(attrs)) continue;
    if (inner.includes('{')) continue; // una expresión: texto traducido u otro contenido
    const shown = inner.replace(/<[^>]*>/g, '').trim();
    if (!/\p{L}|\p{N}/u.test(shown)) {
      const line = src.slice(0, m.index).split('\n').length;
      found.push(`${relative(SRC, file)}:${line} «${shown}»`);
    }
  }
  return found;
}

describe('a11y: ningún botón de solo icono sin nombre', () => {
  const files = [...tsxFiles(join(SRC, 'pages')), ...tsxFiles(join(SRC, 'components'))];

  it('ve las pantallas de la auditoría', () => {
    const names = files.map((f) => relative(SRC, f).split('\\').join('/'));
    expect(names).toContain('pages/ProjectScreen.tsx');
    expect(names).toContain('pages/PlaygroundScreen.tsx');
  });

  it('todo <button> con solo símbolos lleva aria-label', () => {
    expect(files.flatMap(unnamedButtons)).toEqual([]);
  });
});
