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
  const mapa: Record<string, string> = {}
  // El bloque `:root[data-theme="dark"]` va al final, asi que sus valores pisan
  // a los claros: leidos en orden, `mapa` acaba con el tema oscuro, que es el
  // que ve un usuario por defecto.
  for (const m of css.matchAll(/(--le-[\w-]+):\s*(#[0-9A-Fa-f]{3,8})\s*;/g)) {
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

  it('--le-text NO sirve sobre esas tintas: por eso existen los *-on-tint', () => {
    const fallan = SOBRE_TINTA_FIJA.filter(([, , fondo]) => ratio(t['--le-text'], t[fondo]) < 4.5)
    expect(fallan.length).toBe(SOBRE_TINTA_FIJA.length)
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

describe('rellenos que llevan texto blanco encima', () => {
  const t = tokens()

  it('--le-success-on-tint aguanta blanco; --le-green no', () => {
    expect(ratio('#FFFFFF', t['--le-success-on-tint'])).toBeGreaterThanOrEqual(4.5)
    expect(ratio('#FFFFFF', t['--le-green'])).toBeLessThan(4.5)
  })
})
