/**
 * Filas 46.4 / 34.2: todo `var(--x)` sin valor de respaldo de `src/**\/*.css`
 * tiene que estar definido en algún sitio. Una variable sin definir no falla:
 * la propiedad cae a su valor inicial en silencio (fondo transparente, texto
 * del tamaño heredado) y nadie lo ve hasta que alguien mira la pantalla.
 *
 * «Definida» = `--x:` en cualquier `.css` de src, o `'--x'` entre comillas en
 * un `.ts`/`.tsx` que no sea de test (las que se fijan con `style={{ '--x': … }}`).
 * `var(--x, respaldo)` queda fuera: el respaldo es justo lo que cubre la ausencia.
 * Los `var()` anidados sí se miran: en `var(--a, var(--b))` el `--b` no tiene respaldo.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const SRC = resolve(__dirname, '..');

function walk(dir: string, out: string[] = []): string[] {
  for (const f of readdirSync(dir)) {
    const p = join(dir, f);
    if (statSync(p).isDirectory()) walk(p, out);
    else out.push(p);
  }
  return out;
}

const todos = walk(SRC);
const css = todos.filter((f) => f.endsWith('.css'));
const codigo = todos.filter((f) => /\.tsx?$/.test(f) && !f.includes(`${join(SRC, 'test')}`));
const sinComentarios = (s: string) => s.replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, ' '));

function variablesSinDefinir(
  fuentesCss: Array<{ ruta: string; texto: string }>,
  fuentesCodigo: string[],
): string[] {
  const definidas = new Set<string>();
  for (const { texto } of fuentesCss) {
    for (const m of sinComentarios(texto).matchAll(/(--[\w-]+)\s*:/g)) definidas.add(m[1]);
  }
  for (const texto of fuentesCodigo) {
    for (const m of texto.matchAll(/['"`](--[\w-]+)['"`]/g)) definidas.add(m[1]);
  }
  const faltan: string[] = [];
  for (const { ruta, texto } of fuentesCss) {
    sinComentarios(texto).split('\n').forEach((linea, i) => {
      for (const m of linea.matchAll(/var\(\s*(--[\w-]+)\s*\)/g)) {
        if (!definidas.has(m[1])) faltan.push(`${ruta}:${i + 1} ${m[1]}`);
      }
    });
  }
  return faltan;
}

describe('guarda: var(--x) sin respaldo, definida (46.4 / 34.2)', () => {
  it('src/**/*.css no usa ninguna variable sin definir', () => {
    const faltan = variablesSinDefinir(
      css.map((f) => ({ ruta: relative(SRC, f), texto: readFileSync(f, 'utf-8') })),
      codigo.map((f) => readFileSync(f, 'utf-8')),
    );
    expect(faltan).toEqual([]);
  });

  it('el detector ve una variable sin definir, también anidada, y respeta las definidas y las de respaldo', () => {
    const css1 = (texto: string) => [{ ruta: 'x.css', texto }];
    expect(variablesSinDefinir(css1('a { color: var(--nada); }'), [])).toEqual(['x.css:1 --nada']);
    expect(variablesSinDefinir(css1('a { color: var(--a, var(--nada)); }'), [])).toEqual(['x.css:1 --nada']);
    expect(variablesSinDefinir(css1(':root { --x: 1; } a { top: var(--x); }'), [])).toEqual([]);
    expect(variablesSinDefinir(css1('a { top: var(--y, 2px); }'), [])).toEqual([]);
    expect(variablesSinDefinir(css1('a { top: var(--z); }'), ["style={{ '--z': 1 }}"])).toEqual([]);
    expect(variablesSinDefinir(css1('/* var(--c) */ a { top: 0; }'), [])).toEqual([]);
  });
});
