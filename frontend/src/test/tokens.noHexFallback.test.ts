/**
 * Guardia de 34.2: ningún `var(--token, #hexfallback)` en el código. Un
 * respaldo hexadecimal en un `var()` es un color literal disfrazado — si el
 * token nunca se define (como `--color-cyan` en ProfileScreen.tsx, que no
 * existía en ningún fichero de tokens y siempre caía al respaldo) o si el
 * fallback diverge del valor real del token, el sitio pinta un color que
 * nadie decidió a propósito. `grep -c 'var(--x, #' en src/` debe dar 0
 * (criterio archivado de 34.2).
 */

import { readdirSync, readFileSync, statSync } from 'node:fs'
import { dirname, join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), '..', '..')
const SRC = join(RAIZ, 'src')
const EXT = new Set(['.css', '.tsx', '.ts'])

function sourceFiles(dir: string): string[] {
  const out: string[] = []
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry)
    if (statSync(full).isDirectory()) out.push(...sourceFiles(full))
    else if (EXT.has(entry.slice(entry.lastIndexOf('.')))) out.push(full)
  }
  return out
}

const VAR_WITH_HEX_FALLBACK = /var\(\s*--[\w-]+\s*,\s*#[0-9a-fA-F]{3,8}\b/g

describe('sin var(--token, #hex) en todo src/ (34.2)', () => {
  const files = sourceFiles(SRC)

  it('recorre ficheros de verdad (la guardia no está vacía)', () => {
    expect(files.length).toBeGreaterThan(100)
  })

  it('ningún fichero tiene un respaldo hex dentro de un var()', () => {
    const hallados: string[] = []
    for (const file of files) {
      const matches = readFileSync(file, 'utf8').match(VAR_WITH_HEX_FALLBACK)
      if (matches) hallados.push(`${relative(RAIZ, file)}: ${matches.join(', ')}`)
    }
    expect(hallados).toHaveLength(0)
  })
})
