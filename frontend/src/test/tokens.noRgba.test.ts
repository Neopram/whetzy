/**
 * Serie 34 (tokens), 2026-10-16: `tokens.noLiterals` solo miraba hex, y por el
 * hueco quedaban 47 `rgba(...)` en 14 `.module.css`. Casi todos eran de la
 * paleta vieja (`rgba(6,182,212)` = #06B6D4 y `rgba(239,68,68)` = #EF4444, no
 * el `--le-brand` ni el `--le-danger` de hoy) o blanco al 2-8 % pensado para
 * fondo oscuro, que en el modo claro no se ve. Un color con transparencia se
 * escribe con `color-mix(in srgb, var(--le-…) N%, transparent)`, que sigue el
 * tema; los velos y sombras, con sus tokens.
 *
 * Los ficheros de tokens (`styles/design-tokens.css`) no
 * son `.module.css`: ahí es donde se definen esos valores.
 */

import { readdirSync, readFileSync, statSync } from 'node:fs'
import { dirname, join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), '..', '..')
const SRC = join(RAIZ, 'src')

function moduleCssFiles(dir: string): string[] {
  const out: string[] = []
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry)
    if (statSync(full).isDirectory()) out.push(...moduleCssFiles(full))
    else if (entry.endsWith('.module.css')) out.push(full)
  }
  return out
}

const COLOR_FUNCTION = /\b(?:rgba?|hsla?)\s*\(/

describe('sin rgb()/hsl() literales en .module.css (serie 34)', () => {
  const files = moduleCssFiles(SRC)

  it('encuentra ficheros .module.css de verdad (la guardia no está vacía)', () => {
    expect(files.length).toBeGreaterThan(30)
  })

  it.each(files)('%s no tiene rgb()/hsl() fuera de comentarios', (file) => {
    const sinComentarios = readFileSync(file, 'utf8').replace(/\/\*[\s\S]*?\*\//g, '')
    const lineas = sinComentarios
      .split('\n')
      .map((l, i) => [i + 1, l] as const)
      .filter(([, l]) => COLOR_FUNCTION.test(l))
    expect(lineas.map(([n, l]) => `${relative(RAIZ, file)}:${n} ${l.trim()}`)).toEqual([])
  })
})
