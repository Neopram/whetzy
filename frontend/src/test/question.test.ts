/**
 * El enunciado nunca enseña la sintaxis con la que se escribio.
 *
 * Dos formas de marcar codigo en el banco y las dos se veian en crudo:
 *
 *   - bloque cercado con ``` — «¿Que imprime? ```python edad = 20 ...», todo
 *     en una linea y con el nombre del lenguaje a la vista
 *   - comillas simples dentro de la frase — «¿Que ventaja tiene
 *     `with open("f") as fh:` sobre `fh = open("f")`?»
 *
 * El alumno lee esas comillas como parte de la respuesta. Ambas vistas en
 * produccion el 2026-09-20.
 */
import { describe, expect, it } from 'vitest'
import { parseQuestion, splitInlineCode } from '../lib/question'

describe('bloque de codigo cercado', () => {
  it('saca el codigo del enunciado', () => {
    const { prose, code } = parseQuestion(
      '¿Qué imprime este código?\n```python\nx = 1\nprint(x)\n```'
    )
    expect(prose).toBe('¿Qué imprime este código?')
    expect(code).toBe('x = 1\nprint(x)')
  })

  it('no deja ni las comillas ni el nombre del lenguaje', () => {
    const { prose, code } = parseQuestion('Mira:\n```js\nlet a = 1;\n```')
    expect(prose).not.toContain('```')
    expect(prose).not.toContain('js')
    expect(code).toBe('let a = 1;')
  })

  it('un enunciado sin bloque se queda como esta', () => {
    const { prose, code } = parseQuestion('¿Cuánto es 2 + 2?')
    expect(prose).toBe('¿Cuánto es 2 + 2?')
    expect(code).toBeNull()
  })
})

describe('codigo dentro de la frase', () => {
  it('separa cada fragmento entre comillas', () => {
    const t = splitInlineCode('¿Qué ventaja tiene `with open("f")` sobre `open("f")`?')
    expect(t.filter((x) => x.code).map((x) => x.text)).toEqual([
      'with open("f")',
      'open("f")',
    ])
    expect(t.map((x) => x.text).join('')).not.toContain('`')
  })

  it('el texto reconstruido no pierde nada salvo las comillas', () => {
    const original = 'Usa `len(x)` para medir y `sum(x)` para sumar.'
    const t = splitInlineCode(original)
    expect(t.map((x) => x.text).join('')).toBe(original.replace(/`/g, ''))
  })

  it('una comilla suelta se queda como texto', () => {
    // Mas vale enseñar una comilla de mas que comerse media frase por un
    // backtick olvidado al autorar.
    const t = splitInlineCode('Esto tiene una ` sola comilla')
    expect(t).toHaveLength(1)
    expect(t[0].code).toBe(false)
    expect(t[0].text).toBe('Esto tiene una ` sola comilla')
  })

  it('un enunciado sin comillas devuelve un solo trozo de texto', () => {
    const t = splitInlineCode('¿Cuánto es 2 + 2?')
    expect(t).toEqual([{ text: '¿Cuánto es 2 + 2?', code: false }])
  })

  it('no cruza saltos de linea', () => {
    // Si cruzara, un bloque mal cerrado se tragaria el enunciado entero.
    const t = splitInlineCode('primera `linea\nsegunda` tercera')
    expect(t.some((x) => x.code)).toBe(false)
  })

  it('las dos formas se combinan: primero el bloque, luego la frase', () => {
    const { prose, code } = parseQuestion(
      'Usa `len()` aquí:\n```python\nprint(len([1,2]))\n```'
    )
    expect(code).toBe('print(len([1,2]))')
    const t = splitInlineCode(prose)
    expect(t.filter((x) => x.code).map((x) => x.text)).toEqual(['len()'])
  })
})
