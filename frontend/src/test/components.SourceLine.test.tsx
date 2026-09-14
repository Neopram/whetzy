import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { SourceLine } from '../components/quiz/SourceLine';

describe('SourceLine', () => {
  it('turns a source that carries a URL into a followable link', () => {
    render(
      <SourceLine source="AWS Overview whitepaper - Six advantages (https://docs.aws.amazon.com/x)" />
    );
    const link = screen.getByRole('link');
    expect(link.getAttribute('href')).toBe('https://docs.aws.amazon.com/x');
    // The label stays readable next to the link, not swallowed by it.
    expect(screen.getByText(/Six advantages/)).toBeTruthy();
  });

  it('opens externally without handing the opener away', () => {
    render(<SourceLine source="Docs (https://example.com/a)" />);
    const link = screen.getByRole('link');
    expect(link.getAttribute('target')).toBe('_blank');
    expect(link.getAttribute('rel')).toContain('noopener');
    expect(link.getAttribute('rel')).toContain('noreferrer');
  });

  it('leaves a book citation as plain text', () => {
    // Books have no canonical URL, and pointing one at a shop would be an
    // affiliate link wearing a citation's clothes.
    render(<SourceLine source="Fluent Python 2e (Ramalho)" />);
    expect(screen.queryByRole('link')).toBeNull();
    expect(screen.getByText(/Fluent Python 2e \(Ramalho\)/)).toBeTruthy();
  });

  it('does not mistake a parenthetical author for a URL', () => {
    render(<SourceLine source="Clean Code (Martin)" />);
    expect(screen.queryByRole('link')).toBeNull();
  });

  it('only links a URL in the trailing position, not one quoted mid-sentence', () => {
    render(<SourceLine source="See (https://a.example) for the rest of the story" />);
    expect(screen.queryByRole('link')).toBeNull();
  });

  it('handles the plain CPython-style citation the bank mostly uses', () => {
    render(<SourceLine source="CPython docs 3.13 — Data Structures" />);
    expect(screen.queryByRole('link')).toBeNull();
    expect(screen.getByText(/CPython docs 3.13/)).toBeTruthy();
  });
});
