/**
 * El quiz decide como pintar una pregunta por EXCLUSION, no por enumeracion.
 *
 * `EXEC_TYPES` lista los cinco tipos que se responden escribiendo o ejecutando;
 * todo lo demas cae en la rama de opciones. Esa forma es la que hace que
 * `multiple_choice` —1.015 preguntas del banco, el mismo formato que `mcq` con
 * otro nombre— funcione sin que nadie lo declarara en ninguna parte.
 *
 * Lo contrario, una lista de inclusion, es exactamente lo que vacio el pool de
 * la prueba de nivel en los tracks de certificacion enteros: enumeraba tipos y
 * se dejo `multiple_choice` fuera.
 *
 * Este test fija la propiedad, no la lista: cualquier tipo que no sea
 * ejecutable tiene que pintar sus opciones. Si alguien convierte la rama en
 * una enumeracion, se pone rojo.
 */
import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), '..', '..')
const FUENTE = readFileSync(join(RAIZ, 'src/pages/QuizScreen.tsx'), 'utf8')

/** Los cinco que NO se responden eligiendo. */
const EJECUTABLES = ['fill_blank_exec', 'fix_bug', 'fill_blank', 'sql_exec', 'js_exec']
/** Los cuatro que SI. `multiple_choice` es el que se cae de las enumeraciones. */
const CON_OPCIONES = ['mcq', 'multiple_choice', 'true_false', 'code_output']

describe('como decide el quiz que pintar', () => {
  it('EXEC_TYPES enumera solo los que se escriben o ejecutan', () => {
    const m = FUENTE.match(/const EXEC_TYPES = new Set<[^>]*>\(\[([^\]]*)\]\)/)
    expect(m, 'no encuentro EXEC_TYPES en QuizScreen').toBeTruthy()
    const listados = [...m![1].matchAll(/'([a-z_]+)'/g)].map((x) => x[1]).sort()
    expect(listados).toEqual([...EJECUTABLES].sort())
  })

  it.each(CON_OPCIONES)('%s no esta en EXEC_TYPES, asi que pinta opciones', (tipo) => {
    const m = FUENTE.match(/const EXEC_TYPES = new Set<[^>]*>\(\[([^\]]*)\]\)/)
    expect(m![1]).not.toContain(`'${tipo}'`)
  })

  it('la rama de opciones no enumera tipos', () => {
    // `isExecType` e `isInteractive` (40.1, el widget) son las unicas
    // condiciones que apartan una pregunta de las opciones. Si apareciera algo
    // como `type === 'mcq'` decidiendo si se pintan opciones,
    // `multiple_choice` se quedaria sin ellas.
    expect(FUENTE).toContain('const isExecType = question != null && EXEC_TYPES.has(question.type)')
    expect(FUENTE).toContain("const isInteractive = question?.type === 'interactive'")
    expect(FUENTE).toMatch(/\{!isExecType && !isInteractive && \(/)
  })

  it('el union de QuestionPublic conoce los dos nombres del mismo formato', () => {
    const api = readFileSync(join(RAIZ, 'src/services/api.ts'), 'utf8')
    const union = api.slice(api.indexOf('export interface QuestionPublic'))
    for (const tipo of [...CON_OPCIONES, ...EJECUTABLES, 'interactive']) {
      expect(union, `falta '${tipo}' en QuestionPublic['type']`).toContain(`'${tipo}'`)
    }
  })
})
