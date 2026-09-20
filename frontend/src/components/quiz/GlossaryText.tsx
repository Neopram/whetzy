import { useMemo } from 'react';
import type { GlossaryTerm } from '../../services/api';
import { splitInlineCode } from '../../lib/question';
import styles from './GlossaryText.module.css';

interface Props {
  text: string;
  terms: GlossaryTerm[];
  lang: 'es' | 'en';
  onPick: (term: GlossaryTerm) => void;
  /** Rendered around the whole thing; defaults to a plain span. */
  as?: 'span' | 'p';
}

function escapeForRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

type Piece = { text: string; term?: GlossaryTerm; code?: boolean };

/**
 * Splits `text` so that glossary terms become tappable.
 *
 * Only the first occurrence of each term is marked. Highlighting every "list"
 * in a paragraph about lists turns the question into a wall of links and buries
 * the one thing the reader came for.
 *
 * El codigo en linea se separa ANTES que los terminos, por dos razones: las
 * comillas simples se veian tal cual en el enunciado («¿Que ventaja tiene
 * `with open("f") as fh:`...»), y un termino del glosario que cayera dentro de
 * un fragmento de codigo se convertia en un boton — enlazar la palabra `list`
 * dentro de `list.append(x)` invita a tocar algo que no es prosa.
 */
function split(text: string, terms: GlossaryTerm[], lang: 'es' | 'en'): Piece[] {
  const trozos = splitInlineCode(text);

  const byLabel = terms
    .map((t) => ({ label: (lang === 'es' ? t.term_es : t.term_en).trim(), term: t }))
    .filter((t) => t.label.length > 2)
    // Longest first, so "duck typing" wins over "typing".
    .sort((a, b) => b.label.length - a.label.length);

  if (byLabel.length === 0) {
    return trozos.map((t) => ({ text: t.text, code: t.code }));
  }

  const pattern = new RegExp(
    `(?<![\\p{L}\\p{N}_])(${byLabel.map((t) => escapeForRegex(t.label)).join('|')})(?![\\p{L}\\p{N}_])`,
    'giu'
  );

  const pieces: Piece[] = [];
  // Compartido entre trozos: «solo la primera aparicion» cuenta en todo el
  // enunciado, no dentro de cada fragmento.
  const used = new Set<string>();

  for (const trozo of trozos) {
    if (trozo.code) {
      pieces.push({ text: trozo.text, code: true });
      continue;
    }

    let last = 0;
    for (const match of trozo.text.matchAll(pattern)) {
      const at = match.index ?? 0;
      const found = match[0];
      const entry = byLabel.find((t) => t.label.toLowerCase() === found.toLowerCase());
      if (!entry || used.has(entry.term.id)) continue;
      used.add(entry.term.id);

      if (at > last) pieces.push({ text: trozo.text.slice(last, at) });
      pieces.push({ text: found, term: entry.term });
      last = at + found.length;
    }
    if (last < trozo.text.length) pieces.push({ text: trozo.text.slice(last) });
  }

  return pieces;
}

export function GlossaryText({ text, terms, lang, onPick, as = 'span' }: Props) {
  const pieces = useMemo(() => split(text, terms, lang), [text, terms, lang]);
  const Wrapper = as;

  return (
    <Wrapper>
      {pieces.map((piece, i) => {
        if (piece.term) {
          return (
            <button
              key={i}
              type="button"
              className={styles.term}
              onClick={() => onPick(piece.term as GlossaryTerm)}
              aria-label={`${piece.text} — ${lang === 'es' ? 'ver definición' : 'see definition'}`}
            >
              {piece.text}
            </button>
          );
        }
        if (piece.code) {
          return (
            <code key={i} className={styles.inlineCode}>
              {piece.text}
            </code>
          );
        }
        return <span key={i}>{piece.text}</span>;
      })}
    </Wrapper>
  );
}
