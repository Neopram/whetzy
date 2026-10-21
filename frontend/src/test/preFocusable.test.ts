/**
 * 2026-10-21, CI de #321: `competir.spec.ts` salió rojo «al azar» con axe
 * `scrollable-region-focusable` sobre el `<pre>` del código del examen. No era
 * azar: la pregunta es aleatoria y solo las de línea larga desbordan a 390 px.
 * Un `<pre>` con `overflow: auto` que desborda tiene que poder enfocarse, o con
 * teclado no se lee el final de la línea.
 *
 * La guarda mira cada `<pre className={styles.x}>` de `src/` y, si la clase
 * tiene `overflow`/`overflow-x` `auto` o `scroll` en su `.module.css`, exige
 * `tabIndex={0}` en la misma etiqueta.
 */

import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import { dirname, join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

const SRC = join(dirname(fileURLToPath(import.meta.url)), '..')

function tsxFiles(dir: string): string[] {
  const out: string[] = []
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry)
    if (statSync(full).isDirectory()) {
      if (entry !== 'test') out.push(...tsxFiles(full))
    } else if (entry.endsWith('.tsx') && !entry.includes('.test.')) out.push(full)
  }
  return out
}

/** Clases de un .module.css cuyo bloque desborda con scroll. */
function scrollingClasses(css: string): Set<string> {
  const out = new Set<string>()
  const rule = /([^{}]+)\{([^{}]*)\}/g
  for (const m of css.matchAll(rule)) {
    if (!/overflow(?:-x)?\s*:\s*(?:auto|scroll)/.test(m[2])) continue
    for (const c of m[1].matchAll(/\.([A-Za-z_][\w-]*)/g)) out.add(c[1])
  }
  return out
}

const PRE = /<pre\s+className=\{styles\.(\w+)\}([^>]*)>/g

function offenders(): string[] {
  const bad: string[] = []
  for (const file of tsxFiles(SRC)) {
    const src = readFileSync(file, 'utf8')
    const imp = src.match(/import\s+styles\s+from\s+'(\.[^']+\.module\.css)'/)
    if (!imp) continue
    const cssPath = join(dirname(file), imp[1])
    if (!existsSync(cssPath)) continue
    const scrolling = scrollingClasses(readFileSync(cssPath, 'utf8'))
    for (const m of src.matchAll(PRE)) {
      if (scrolling.has(m[1]) && !/tabIndex=\{0\}/.test(m[2])) {
        bad.push(`${relative(SRC, file)}: <pre className={styles.${m[1]}}>`)
      }
    }
  }
  return bad
}

describe('<pre> con scroll se puede enfocar (axe scrollable-region-focusable)', () => {
  it('detecta clases con overflow auto (la guarda no está vacía)', () => {
    expect(scrollingClasses('.a, .b { overflow-x: auto; }\n.c { color: red; }')).toEqual(new Set(['a', 'b']))
    const quiz = readFileSync(join(SRC, 'pages', 'QuizScreen.module.css'), 'utf8')
    expect(scrollingClasses(quiz).has('codeBlock')).toBe(true)
  })

  it('todo <pre> con scroll lleva tabIndex={0}', () => {
    expect(offenders()).toEqual([])
  })
})
