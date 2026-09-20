/**
 * El enunciado de una pregunta y su bloque de codigo son dos cosas distintas.
 *
 * Muchas preguntas del banco traen el codigo dentro del texto, en un bloque
 * cercado con ```. Pintarlo tal cual deja a la vista las comillas y el nombre
 * del lenguaje —«¿Que imprime el siguiente codigo? ```python edad = 20 ...»— y
 * el codigo queda en una sola linea, sin monoespaciada ni saltos. Paso en la
 * pantalla de nivelacion el 2026-09-20, con el quiz haciendolo bien al lado:
 * la funcion vivia dentro de `QuizScreen` y no se podia reutilizar.
 */

export interface EnunciadoPartido {
  /** El texto sin el bloque de codigo. */
  prose: string;
  /** El codigo, ya sin las comillas ni el nombre del lenguaje. */
  code: string | null;
}

/** Separa un bloque cercado con ``` del resto del enunciado. */
export function parseQuestion(text: string): EnunciadoPartido {
  const m = text.match(/```[a-zA-Z]*\n?([\s\S]*?)```/);
  if (m) {
    const code = m[1].replace(/\n$/, '');
    const prose = text.replace(m[0], '').trim();
    return { prose, code };
  }
  return { prose: text, code: null };
}
