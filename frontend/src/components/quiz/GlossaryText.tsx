import { useMemo } from 'react';
import type { GlossaryTerm } from '../../services/api';
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

type Piece = { text: string; term?: GlossaryTerm };

/**
 * Splits `text` so that glossary terms become tappable.
 *
 * Only the first occurrence of each term is marked. Highlighting every "list"
 * in a paragraph about lists turns the question into a wall of links and buries
 * the one thing the reader came for.
 */
function split(text: string, terms: GlossaryTerm[], lang: 'es' | 'en'): Piece[] {
  if (terms.length === 0) return [{ text }];

  const byLabel = terms
    .map((t) => ({ label: (lang === 'es' ? t.term_es : t.term_en).trim(), term: t }))
    .filter((t) => t.label.length > 2)
    // Longest first, so "duck typing" wins over "typing".
    .sort((a, b) => b.label.length - a.label.length);

  if (byLabel.length === 0) return [{ text }];

  const pattern = new RegExp(
    `(?<![\\p{L}\\p{N}_])(${byLabel.map((t) => escapeForRegex(t.label)).join('|')})(?![\\p{L}\\p{N}_])`,
    'giu'
  );

  const pieces: Piece[] = [];
  const used = new Set<string>();
  let last = 0;

  for (const match of text.matchAll(pattern)) {
    const at = match.index ?? 0;
    const found = match[0];
    const entry = byLabel.find((t) => t.label.toLowerCase() === found.toLowerCase());
    if (!entry || used.has(entry.term.id)) continue;
    used.add(entry.term.id);

    if (at > last) pieces.push({ text: text.slice(last, at) });
    pieces.push({ text: found, term: entry.term });
    last = at + found.length;
  }

  if (last < text.length) pieces.push({ text: text.slice(last) });
  return pieces;
}

export function GlossaryText({ text, terms, lang, onPick, as = 'span' }: Props) {
  const pieces = useMemo(() => split(text, terms, lang), [text, terms, lang]);
  const Wrapper = as;

  return (
    <Wrapper>
      {pieces.map((piece, i) =>
        piece.term ? (
          <button
            key={i}
            type="button"
            className={styles.term}
            onClick={() => onPick(piece.term as GlossaryTerm)}
            aria-label={`${piece.text} — ${lang === 'es' ? 'ver definición' : 'see definition'}`}
          >
            {piece.text}
          </button>
        ) : (
          <span key={i}>{piece.text}</span>
        )
      )}
    </Wrapper>
  );
}
