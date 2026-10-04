import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, render } from '@testing-library/react';
import { useNoIndexMeta } from '../pages/marketing/useNoIndexMeta';

function Probe({ title, lang }: { title: string; lang: 'es' | 'en' }) {
  useNoIndexMeta(title, lang);
  return null;
}

afterEach(() => {
  cleanup();
  document.head.querySelectorAll('meta[name="robots"]').forEach((el) => el.remove());
});

describe('useNoIndexMeta', () => {
  it('sets the title and html lang', () => {
    render(<Probe title="Not available" lang="en" />);
    expect(document.title).toBe('Not available');
    expect(document.documentElement.lang).toBe('en');
  });

  it('creates a noindex robots meta when none exists', () => {
    render(<Probe title="x" lang="es" />);
    expect(document.querySelector('meta[name="robots"]')?.getAttribute('content')).toBe('noindex');
    expect(document.querySelectorAll('meta[name="robots"]')).toHaveLength(1);
  });

  it('removes the robots tag on unmount when it created it', () => {
    const { unmount } = render(<Probe title="x" lang="es" />);
    unmount();
    expect(document.querySelector('meta[name="robots"]')).toBeNull();
  });

  it('restores a pre-existing robots tag on unmount instead of deleting it', () => {
    const existing = document.createElement('meta');
    existing.setAttribute('name', 'robots');
    existing.setAttribute('content', 'index, follow');
    document.head.appendChild(existing);

    const { unmount } = render(<Probe title="x" lang="es" />);
    expect(document.querySelector('meta[name="robots"]')?.getAttribute('content')).toBe('noindex');
    unmount();
    expect(document.querySelector('meta[name="robots"]')?.getAttribute('content')).toBe('index, follow');
  });

  it('restores the previous title and lang on unmount', () => {
    document.title = 'previous';
    document.documentElement.lang = 'es';
    const { unmount } = render(<Probe title="x" lang="en" />);
    unmount();
    expect(document.title).toBe('previous');
    expect(document.documentElement.lang).toBe('es');
  });
});
