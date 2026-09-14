import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { GlossaryText } from '../components/quiz/GlossaryText';
import { trackIdFromSkillId } from '../hooks/useGlossary';
import type { GlossaryTerm } from '../services/api';

const term = (over: Partial<GlossaryTerm> & { id: string }): GlossaryTerm => ({
  track_id: 'track01',
  term_es: 'Variable',
  term_en: 'Variable',
  definition_es: 'def es',
  definition_en: 'def en',
  source: 'CPython docs',
  order: 1,
  ...over,
});

const TERMS: GlossaryTerm[] = [
  term({ id: 'g1', term_es: 'variable', term_en: 'variable' }),
  term({ id: 'g2', term_es: 'tipado pato', term_en: 'duck typing' }),
  term({ id: 'g3', term_es: 'tipado', term_en: 'typing' }),
];

describe('trackIdFromSkillId', () => {
  it('derives the track from the skill id convention', () => {
    expect(trackIdFromSkillId('sk070105')).toBe('track07');
    expect(trackIdFromSkillId('sk010101')).toBe('track01');
  });

  it('returns null for anything that does not match, rather than guessing', () => {
    expect(trackIdFromSkillId('sk_exec23')).toBeNull();
    expect(trackIdFromSkillId('')).toBeNull();
    expect(trackIdFromSkillId('track07')).toBeNull();
  });
});

describe('GlossaryText', () => {
  it('turns a known term into a button and leaves the rest as text', async () => {
    const onPick = vi.fn();
    render(<GlossaryText text="Una variable en Python" terms={TERMS} lang="es" onPick={onPick} />);

    const button = screen.getByRole('button', { name: /variable/i });
    await userEvent.click(button);

    expect(onPick).toHaveBeenCalledOnce();
    expect(onPick.mock.calls[0][0].id).toBe('g1');
    expect(screen.getByText(/Una/)).toBeTruthy();
  });

  it('marks only the first occurrence, so a paragraph does not become a wall of links', () => {
    render(
      <GlossaryText text="variable, variable y variable" terms={TERMS} lang="es" onPick={vi.fn()} />
    );
    expect(screen.getAllByRole('button')).toHaveLength(1);
  });

  it('prefers the longest term so a compound is not broken by its own substring', async () => {
    const onPick = vi.fn();
    render(<GlossaryText text="esto es duck typing puro" terms={TERMS} lang="en" onPick={onPick} />);

    await userEvent.click(screen.getByRole('button', { name: /duck typing/i }));
    expect(onPick.mock.calls[0][0].id).toBe('g2');
  });

  it('does not match inside a longer word', () => {
    render(<GlossaryText text="variables y variabilidad" terms={TERMS} lang="es" onPick={vi.fn()} />);
    expect(screen.queryAllByRole('button')).toHaveLength(0);
  });

  it('renders plain text when the track has no glossary', () => {
    render(<GlossaryText text="sin glosario aquí" terms={[]} lang="es" onPick={vi.fn()} />);
    expect(screen.queryAllByRole('button')).toHaveLength(0);
    expect(screen.getByText(/sin glosario aquí/)).toBeTruthy();
  });

  it('matches the label of the language being displayed', () => {
    const { rerender } = render(
      <GlossaryText text="duck typing" terms={TERMS} lang="en" onPick={vi.fn()} />
    );
    expect(screen.getAllByRole('button')).toHaveLength(1);

    // The same English text shown while reading Spanish has no Spanish label in it.
    rerender(<GlossaryText text="duck typing" terms={TERMS} lang="es" onPick={vi.fn()} />);
    expect(screen.queryAllByRole('button')).toHaveLength(0);
  });

  it('survives a term containing regex metacharacters', () => {
    const tricky = [term({ id: 'g9', term_es: 'f-string (PEP 498)', term_en: 'f-string (PEP 498)' })];
    render(
      <GlossaryText text="usa f-string (PEP 498) aquí" terms={tricky} lang="es" onPick={vi.fn()} />
    );
    expect(screen.getAllByRole('button')).toHaveLength(1);
  });
});
