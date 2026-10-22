/**
 * Guardia de identidad visual (24.1): ningún `.module.css` lleva un color
 * hex literal. Antes había 6/51 (WhyButton, PlaygroundScreen, ProfileScreen,
 * LessonScreen, ProjectScreen, EvidenceScreen — 88.2 %, bajo el listón del
 * 90 % del criterio); cada literal encontrado o era ya el mismo valor de un
 * token `--le-*`/`--color-*` existente, o necesitaba uno nuevo (marca de
 * lenguaje, editor de código, tarjeta Pro — fijos, no siguen el tema:
 * `--brand-*`, `--le-code-*`, `--le-editor-loading-*`, `--le-pro-card-*`).
 *
 * Los comentarios CSS no cuentan: citar un valor histórico en prosa (`/* el
 * #1a1a2e que había *\/`) no es una regresión de estilo, así que este test
 * los quita antes de mirar.
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

const HEX_LITERAL = /#[0-9a-fA-F]{3,8}\b/g

describe('sin colores hex literales en .module.css (24.1)', () => {
  const files = moduleCssFiles(SRC)

  it('encuentra ficheros .module.css de verdad (la guardia no está vacía)', () => {
    expect(files.length).toBeGreaterThan(30)
  })

  it.each(files)('%s no tiene colores hex fuera de comentarios', (file) => {
    const raw = readFileSync(file, 'utf8')
    const sinComentarios = raw.replace(/\/\*[\s\S]*?\*\//g, '')
    const hallados = sinComentarios.match(HEX_LITERAL) ?? []
    expect(hallados, `${relative(RAIZ, file)}: ${hallados.join(', ')}`).toHaveLength(0)
  })
})
