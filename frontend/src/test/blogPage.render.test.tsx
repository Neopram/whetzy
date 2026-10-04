/**
 * `/blog` servía una página en blanco (0.14) a pesar de tener 8 artículos
 * reales en `content/blog/**` desde el PR #93. Comprueba que ahora rinde
 * contenido de verdad, en los dos idiomas, con los metadatos de SEO (E.7)
 * correctos por vista — y que nunca se cuelga entre lista y detalle.
 *
 * Todas las URL pasan `?lang=es` explícito en vez de confiar en el `/blog`
 * desnudo: jsdom responde `navigator.language` en inglés por defecto, y
 * `resolveBlogLang()` cae a eso sin `?lang=` — lo mismo que haría un
 * navegador real con el idioma del sistema en inglés, que es justo el
 * comportamiento que se busca en producción (LandingScreen.tsx hace lo
 * mismo), pero no es lo que esta suite quiere fijar como "caso por
 * defecto".
 */
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import BlogPage from '../pages/marketing/BlogPage';
import { postsByLang } from '../pages/marketing/blogContent';

function setUrl(path: string) {
  window.history.pushState({}, '', path);
}

afterEach(cleanup);

describe('BlogPage — lista (0.14)', () => {
  beforeEach(async () => {
    setUrl('/blog?lang=es');
    await i18n.changeLanguage('es');
  });

  it('ES: renders the list heading and every ES post title, not an empty page', () => {
    render(<BlogPage />);
    expect(screen.getByRole('heading', { name: 'Blog' })).toBeInTheDocument();
    for (const post of postsByLang('es')) {
      expect(screen.getByText(post.title)).toBeInTheDocument();
    }
  });

  it('EN via ?lang=en: renders EN titles, not a mix with ES', () => {
    setUrl('/blog?lang=en');
    render(<BlogPage />);
    for (const post of postsByLang('en')) {
      expect(screen.getByText(post.title)).toBeInTheDocument();
    }
    expect(screen.getByRole('heading', { name: 'Blog' })).toBeInTheDocument();
  });

  it('sets document.title and lang to the list meta, not whatever the previous page left behind', () => {
    document.title = 'something else';
    render(<BlogPage />);
    expect(document.title).toBe('Blog — Whetzy');
    expect(document.documentElement.lang).toBe('es');
  });

  it('sets a canonical link pointing at /blog', () => {
    render(<BlogPage />);
    expect(document.querySelector('link[rel="canonical"]')?.getAttribute('href')).toBe('https://whetzy.com/blog');
  });
});

describe('BlogPage — detalle', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('es');
  });

  it('clicking "read more" shows the full article body, not just the summary', () => {
    setUrl('/blog?lang=es');
    render(<BlogPage />);
    const [first] = postsByLang('es');
    fireEvent.click(screen.getAllByText('Leer artículo')[0]);
    expect(screen.getByRole('heading', { name: first.title })).toBeInTheDocument();
    // El cuerpo real tiene mucho más texto que el resumen de la lista.
    expect(screen.queryByText(first.summary)).not.toBeInTheDocument();
  });

  it('loading /blog?post=<slug> directly opens straight into that article', () => {
    const [first] = postsByLang('es');
    setUrl(`/blog?lang=es&post=${first.slug}`);
    render(<BlogPage />);
    expect(screen.getByRole('heading', { name: first.title })).toBeInTheDocument();
  });

  it('sets document.title and canonical to the article, not the list defaults', () => {
    const [first] = postsByLang('es');
    setUrl(`/blog?lang=es&post=${first.slug}`);
    render(<BlogPage />);
    expect(document.title).toBe(`${first.title} — Whetzy`);
    expect(document.querySelector('link[rel="canonical"]')?.getAttribute('href')).toBe(
      `https://whetzy.com/blog?post=${first.slug}`,
    );
  });

  it('an unknown ?post= shows a not-found message instead of crashing or staying blank', () => {
    setUrl('/blog?lang=es&post=does-not-exist');
    render(<BlogPage />);
    expect(screen.getByText('No encontramos ese artículo.')).toBeInTheDocument();
  });

  it('"back to blog" returns to the list', () => {
    const [first] = postsByLang('es');
    setUrl(`/blog?lang=es&post=${first.slug}`);
    render(<BlogPage />);
    fireEvent.click(screen.getByText('← Volver al blog'));
    expect(screen.getByRole('heading', { name: 'Blog' })).toBeInTheDocument();
  });

  it('browser back (popstate) returns to the list after opening an article', () => {
    setUrl('/blog?lang=es');
    render(<BlogPage />);
    fireEvent.click(screen.getAllByText('Leer artículo')[0]);
    setUrl('/blog?lang=es'); // simulates what history.back() would leave window.location at
    fireEvent(window, new PopStateEvent('popstate'));
    expect(screen.getByRole('heading', { name: 'Blog' })).toBeInTheDocument();
  });
});
