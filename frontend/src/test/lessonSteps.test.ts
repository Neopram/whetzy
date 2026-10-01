import { describe, expect, it } from 'vitest';
import { chunkBody, lessonSteps, parseSource } from '../lib/lessonSteps';
import type { LessonRead } from '../services/api';

const BODY =
  'Una variable es un nombre que apunta a un valor guardado en memoria. ' +
  'En Python no escribes el tipo de dato antes del nombre: el intérprete lo infiere. ' +
  'Aquí basta con age = 25 para crear la variable. '.repeat(6) +
  'Si height = 1.75, Python guarda un decimal. ¿Y si cambias el tipo? No se queja.';

describe('chunkBody', () => {
  it('no pierde ni añade texto: unir las tarjetas devuelve el cuerpo', () => {
    const chunks = chunkBody(BODY);
    expect(chunks.length).toBeGreaterThan(1);
    expect(chunks.join(' ')).toBe(BODY.trim().replace(/\s+/g, ' '));
  });

  it('no corta dentro de un número decimal', () => {
    expect(chunkBody(BODY).some((c) => c.endsWith('1.') || c.startsWith('75'))).toBe(false);
  });

  it('respeta los saltos de párrafo', () => {
    expect(chunkBody('Uno.\n\nDos.')).toEqual(['Uno.', 'Dos.']);
  });

  it('cada tarjeta queda cerca del objetivo salvo una frase suelta más larga', () => {
    for (const c of chunkBody(BODY)) expect(c.length).toBeLessThan(520);
  });
});

describe('lessonSteps', () => {
  const lesson = (over: Partial<LessonRead>): LessonRead => ({
    id: 'l1', skill_id: 'sk', title_es: 'T', title_en: 'T', body_es: BODY, body_en: 'Short. Body.',
    example_code: 'print(1)', example_output: '1', source: 'S', order: 1, ...over,
  });

  it('termina cada lección con su ejemplo cuando lo tiene', () => {
    const steps = lessonSteps([lesson({})], 'es');
    expect(steps.at(-1)).toEqual({ kind: 'example', lesson: 0 });
    expect(steps.filter((s) => s.kind === 'text').length).toBeGreaterThan(1);
  });

  it('sin código no hay paso de ejemplo', () => {
    expect(lessonSteps([lesson({ example_code: null })], 'en')).toEqual([
      { kind: 'text', lesson: 0, text: 'Short. Body.' },
    ]);
  });
});

describe('parseSource', () => {
  it('separa nombre y URL', () => {
    expect(parseSource('Python Docs — https://docs.python.org/3/tutorial/')).toEqual({
      label: 'Python Docs', url: 'https://docs.python.org/3/tutorial/',
    });
  });

  it('sin URL deja el texto como está', () => {
    expect(parseSource('CPython docs 3.13')).toEqual({ label: 'CPython docs 3.13', url: null });
  });
});
