/**
 * Tests for src/hooks/useDocumentMeta.ts (added by 11.7, shipped untested).
 *
 * This hook is the only thing that makes the `?lang=en` landing variant look
 * English to a crawler or a link preview. If it silently no-ops, the English
 * page still advertises Spanish title/description/og:locale — a red-line-3
 * failure that is invisible in the UI because the visible copy is correct.
 */
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, cleanup } from '@testing-library/react';
import { useDocumentMeta, type DocumentMetaInput } from '../hooks/useDocumentMeta';

const ES: DocumentMetaInput = {
  title: 'Whetzy — Domina lo que importa',
  description: 'Aprende Python con un motor que te aprende.',
  lang: 'es',
  url: 'https://whetzy.com/landing',
  imageAlt: 'Whetzy',
};

const EN: DocumentMetaInput = {
  title: 'Whetzy — Master what matters',
  description: 'Learn Python with an engine that learns you.',
  lang: 'en',
  url: 'https://whetzy.com/landing?lang=en',
  imageAlt: 'Whetzy',
};

function Probe({ meta }: { meta: DocumentMetaInput }) {
  useDocumentMeta(meta);
  return null;
}

const metaName = (name: string) =>
  document.querySelector(`meta[name="${name}"]`)?.getAttribute('content') ?? null;
const metaProp = (property: string) =>
  document.querySelector(`meta[property="${property}"]`)?.getAttribute('content') ?? null;
const linkRel = (rel: string) =>
  document.querySelector(`link[rel="${rel}"]`)?.getAttribute('href') ?? null;

describe('useDocumentMeta', () => {
  beforeEach(() => {
    document.head.querySelectorAll('meta, link').forEach((el) => el.remove());
    document.title = 'previous title';
    document.documentElement.lang = 'es';
  });

  afterEach(() => {
    cleanup();
  });

  it('sets the title and html lang', () => {
    render(<Probe meta={EN} />);
    expect(document.title).toBe(EN.title);
    expect(document.documentElement.lang).toBe('en');
  });

  it('creates the description meta when none exists', () => {
    render(<Probe meta={EN} />);
    expect(metaName('description')).toBe(EN.description);
  });

  it('reuses an existing description tag instead of duplicating it', () => {
    const existing = document.createElement('meta');
    existing.setAttribute('name', 'description');
    existing.setAttribute('content', 'from index.html');
    document.head.appendChild(existing);

    render(<Probe meta={EN} />);

    expect(document.querySelectorAll('meta[name="description"]')).toHaveLength(1);
    expect(metaName('description')).toBe(EN.description);
  });

  it('sets the Open Graph tags', () => {
    render(<Probe meta={EN} />);
    expect(metaProp('og:title')).toBe(EN.title);
    expect(metaProp('og:description')).toBe(EN.description);
    expect(metaProp('og:url')).toBe(EN.url);
    expect(metaProp('og:image:alt')).toBe(EN.imageAlt);
  });

  it('sets the Twitter tags', () => {
    render(<Probe meta={EN} />);
    expect(metaName('twitter:title')).toBe(EN.title);
    expect(metaName('twitter:description')).toBe(EN.description);
  });

  it('sets the canonical link to the language variant URL', () => {
    render(<Probe meta={EN} />);
    expect(linkRel('canonical')).toBe(EN.url);
  });

  it('reuses an existing canonical link rather than adding a second one', () => {
    const existing = document.createElement('link');
    existing.setAttribute('rel', 'canonical');
    existing.setAttribute('href', 'https://whetzy.com/landing');
    document.head.appendChild(existing);

    render(<Probe meta={EN} />);

    expect(document.querySelectorAll('link[rel="canonical"]')).toHaveLength(1);
    expect(linkRel('canonical')).toBe(EN.url);
  });

  it.each([
    ['es', 'es_ES'],
    ['en', 'en_US'],
  ] as const)('maps lang %s to og:locale %s', (lang, locale) => {
    render(<Probe meta={{ ...EN, lang }} />);
    expect(metaProp('og:locale')).toBe(locale);
  });

  it('restores the previous title and lang on unmount', () => {
    document.title = 'previous title';
    document.documentElement.lang = 'es';
    const { unmount } = render(<Probe meta={EN} />);
    expect(document.title).toBe(EN.title);

    unmount();

    expect(document.title).toBe('previous title');
    expect(document.documentElement.lang).toBe('es');
  });

  it('restores a pre-existing description on unmount', () => {
    const existing = document.createElement('meta');
    existing.setAttribute('name', 'description');
    existing.setAttribute('content', 'from index.html');
    document.head.appendChild(existing);

    const { unmount } = render(<Probe meta={EN} />);
    unmount();

    expect(metaName('description')).toBe('from index.html');
  });

  it('leaves the description alone on unmount when there was none to restore', () => {
    const { unmount } = render(<Probe meta={EN} />);
    unmount();
    // Nothing to restore to — the tag the hook created keeps its value rather
    // than being blanked out, which would be worse than leaving it.
    expect(metaName('description')).toBe(EN.description);
  });

  it('re-applies when the language switches', () => {
    const { rerender } = render(<Probe meta={ES} />);
    expect(metaProp('og:locale')).toBe('es_ES');
    expect(document.title).toBe(ES.title);

    rerender(<Probe meta={EN} />);

    expect(metaProp('og:locale')).toBe('en_US');
    expect(document.title).toBe(EN.title);
    expect(metaName('description')).toBe(EN.description);
    expect(linkRel('canonical')).toBe(EN.url);
    expect(document.documentElement.lang).toBe('en');
  });

  it('never leaves the Spanish title on the English variant', () => {
    render(<Probe meta={EN} />);
    expect(document.title).not.toBe(ES.title);
    expect(metaName('description')).not.toBe(ES.description);
    expect(metaProp('og:locale')).not.toBe('es_ES');
  });
});
