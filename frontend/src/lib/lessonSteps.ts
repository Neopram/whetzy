import type { LessonRead } from '../services/api';

/** Un paso de la lección: un trozo del texto o el ejemplo de esa lección. */
export type LessonStep =
  | { kind: 'text'; lesson: number; text: string }
  | { kind: 'example'; lesson: number };

// ~3 frases por tarjeta: el cuerpo llega como un solo párrafo de ~1.350
// caracteres (mediana del contenido el 2026-10-01) y en el móvil era un muro.
const TARGET = 420;

/**
 * Parte el texto en frases y las agrupa en tarjetas de ~TARGET caracteres.
 * No reescribe nada: cada carácter del cuerpo sale tal cual en alguna tarjeta.
 * Corta tras . ! ? solo si sigue mayúscula o signo de apertura, para no partir
 * «1.75» ni «e.g. foo».
 */
export function chunkBody(body: string): string[] {
  const paragraphs = body.split(/\n+/).map((p) => p.trim()).filter(Boolean);
  const chunks: string[] = [];
  for (const para of paragraphs) {
    const sentences = para.split(/(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡"«(])/);
    let current = '';
    for (const s of sentences) {
      if (current && current.length + s.length + 1 > TARGET) {
        chunks.push(current);
        current = s;
      } else {
        current = current ? `${current} ${s}` : s;
      }
    }
    if (current) chunks.push(current);
  }
  return chunks;
}

export function lessonSteps(lessons: LessonRead[], lang: 'es' | 'en'): LessonStep[] {
  return lessons.flatMap((l, i) => {
    const text = chunkBody(lang === 'en' ? l.body_en : l.body_es)
      .map((t): LessonStep => ({ kind: 'text', lesson: i, text: t }));
    return l.example_code ? [...text, { kind: 'example', lesson: i } as LessonStep] : text;
  });
}

/** «Python Docs — https://…» → nombre y enlace; sin URL, solo el nombre. */
export function parseSource(source: string): { label: string; url: string | null } {
  const m = source.match(/^(.*?)\s*[—–-]\s*(https?:\/\/\S+)\s*$/);
  if (m) return { label: m[1] || m[2], url: m[2] };
  if (/^https?:\/\/\S+$/.test(source.trim())) return { label: source.trim(), url: source.trim() };
  return { label: source, url: null };
}
