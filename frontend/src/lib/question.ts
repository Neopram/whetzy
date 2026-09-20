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

export interface Trozo {
  text: string;
  /** true cuando el trozo venia entre comillas simples y es codigo. */
  code: boolean;
}

/**
 * Parte la prosa en trozos de texto y trozos de codigo en linea.
 *
 * Los enunciados usan comillas simples para nombrar codigo dentro de la frase
 * —«¿Que ventaja tiene `with open("f") as fh:` sobre `fh = open("f")`?»— y sin
 * tratarlas el alumno lee las comillas como si fueran parte de la respuesta.
 *
 * Las comillas sueltas se quedan como texto: es mas seguro enseñar una comilla
 * de mas que comerse media frase por un backtick olvidado al autorar.
 */
export function splitInlineCode(text: string): Trozo[] {
  const trozos: Trozo[] = [];
  const patron = /`([^`\n]+)`/g;
  let ultimo = 0;

  for (const m of text.matchAll(patron)) {
    const at = m.index ?? 0;
    if (at > ultimo) trozos.push({ text: text.slice(ultimo, at), code: false });
    trozos.push({ text: m[1], code: true });
    ultimo = at + m[0].length;
  }

  if (ultimo < text.length) trozos.push({ text: text.slice(ultimo), code: false });
  return trozos.length > 0 ? trozos : [{ text, code: false }];
}
