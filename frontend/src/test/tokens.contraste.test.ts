/**
 * Guardia de contraste sobre los tokens, no sobre capturas.
 *
 * El modo oscuro es el tema por defecto de la app, y en el se colaron cuatro
 * combinaciones ilegibles a la vez (medidas en produccion el 2026-09-20):
 * el idioma seleccionado en el registro a 1.08:1, las pildoras de misiones y
 * racha a 1.1:1, el dia de hoy a 1.7:1 y el logo y la pestana activa a 2.75:1.
 *
 * Todas venian del mismo error: usar un token que sigue al tema (`--le-text`)
 * encima de una tinta que **no** sigue al tema, o usar un color de relleno
 * (`--le-brand-deep`) como si fuera un glifo. Este test fija las parejas.
 */

import { readdirSync, readFileSync, type Dirent } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

// `__dirname` no existe en el modulo ESM que compila `tsc -b`.
const RAIZ = join(dirname(fileURLToPath(import.meta.url)), '..', '..')

function tokens(): Record<string, string> {
  const css = readFileSync(join(RAIZ, 'src/styles/design-tokens.css'), 'utf8')
  // Solo el primer bloque `:root { … }`: desde la serie 34 es el tema oscuro
  // Obsidian, el que ve un usuario por defecto. El claro vive aparte, en
  // `:root[data-theme="light"]`, y solo si el usuario lo elige.
  const inicio = css.indexOf(':root {')
  const bloque = css.slice(inicio, css.indexOf('\n}\n', inicio))
  const mapa: Record<string, string> = {}
  for (const m of bloque.matchAll(/(--le-[\w-]+):\s*(#[0-9A-Fa-f]{3,8})\s*;/g)) {
    mapa[m[1]] = m[2]
  }
  return mapa
}

function luminancia(hex: string): number {
  const h = hex.replace('#', '')
  const pleno = h.length === 3 ? h.split('').map((c) => c + c).join('') : h.slice(0, 6)
  const n = parseInt(pleno, 16)
  const canal = (v: number) => {
    const s = v / 255
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4)
  }
  return 0.2126 * canal((n >> 16) & 255) + 0.7152 * canal((n >> 8) & 255) + 0.0722 * canal(n & 255)
}

function ratio(a: string, b: string): number {
  const l1 = luminancia(a)
  const l2 = luminancia(b)
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05)
}

function hojasDeEstilo(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e: Dirent) =>
    e.isDirectory()
      ? hojasDeEstilo(join(dir, e.name))
      : e.name.endsWith('.css')
        ? [join(dir, e.name)]
        : [],
  )
}

/** Texto sobre una tinta clara FIJA (igual en ambos temas) -> color fijo. */
const SOBRE_TINTA_FIJA: Array<[string, string, string]> = [
  ['idioma seleccionado en el registro', '--le-brand-on-tint', '--le-brand-light'],
  ['pildora de racha', '--le-success-on-tint', '--le-green-light'],
  ['pildora de misiones', '--le-warning-text', '--le-orange-light'],
]

describe('texto sobre tintas que no cambian con el tema', () => {
  const t = tokens()

  it.each(SOBRE_TINTA_FIJA)('%s cumple AA', (_nombre, texto, fondo) => {
    expect(t[texto], `falta ${texto}`).toBeDefined()
    expect(t[fondo], `falta ${fondo}`).toBeDefined()
    expect(ratio(t[texto], t[fondo])).toBeGreaterThanOrEqual(4.5)
  })

})

describe('texto de la app sobre fondo y superficie (tema oscuro por defecto)', () => {
  const t = tokens()
  const TEXTOS = ['--le-text', '--le-text-secondary', '--le-text-muted', '--le-danger-text', '--le-success-text', '--le-warning-text', '--le-brand-text']
  const FONDOS = ['--le-bg', '--le-surface', '--le-bg-elevated']

  it.each(TEXTOS.flatMap((x) => FONDOS.map((f) => [x, f])))('%s sobre %s cumple AA', (texto, fondo) => {
    expect(ratio(t[texto], t[fondo])).toBeGreaterThanOrEqual(4.5)
  })
})

describe('color de marca como glifo en el tema oscuro', () => {
  const t = tokens()

  it('--le-brand-text se lee sobre la superficie oscura', () => {
    expect(ratio(t['--le-brand-text'], t['--le-surface'])).toBeGreaterThanOrEqual(4.5)
  })

  it('--le-brand-deep NO, que es por lo que no debe usarse como texto', () => {
    expect(ratio(t['--le-brand-deep'], t['--le-surface'])).toBeLessThan(4.5)
  })

  it('ninguna hoja usa --le-brand-deep como `color`', () => {
    const culpables: string[] = []
    for (const f of hojasDeEstilo(join(RAIZ, 'src'))) {
      const nombre = f.split(/[\\/]/).pop() ?? f
      for (const linea of readFileSync(f, 'utf8').split('\n')) {
        // `border-color:` y `box-shadow:` son rellenos y siguen valiendo; lo que
        // no puede ser es un glifo, que en la superficie oscura queda a 2.75:1.
        if (/(^|[^-])color:\s*var\(--le-brand-deep\)/.test(linea)) {
          culpables.push(`${nombre}: ${linea.trim()}`)
        }
      }
    }
    // HomeScreen lo pone sobre un `background: #fff` explicito, donde da 5.19:1.
    expect(culpables.filter((c) => !c.startsWith('HomeScreen.module.css'))).toEqual([])
  })
})

describe('rellenos que llevan texto encima', () => {
  const t = tokens()
  // Como en la landing: sobre cian, verde, rojo o morado el texto es oscuro
  // (--le-text-inverse). El blanco sobre el cian se queda en 2,4:1.
  const RELLENOS = ['--le-brand', '--le-green', '--le-green-dark', '--le-danger', '--le-red', '--le-orange', '--le-purple', '--le-gold']

  it.each(RELLENOS)('--le-text-inverse sobre %s cumple AA', (fondo) => {
    expect(ratio(t['--le-text-inverse'], t[fondo])).toBeGreaterThanOrEqual(4.5)
  })

  it('el blanco NO sirve sobre el cian de marca: por eso ningún botón lo usa', () => {
    expect(ratio('#FFFFFF', t['--le-brand'])).toBeLessThan(4.5)
  })
})
