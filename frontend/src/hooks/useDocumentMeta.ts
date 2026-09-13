/**
 * Sets <title>/<meta description>/OG/Twitter tags for a standalone, statically
 * served page (e.g. the marketing landing) that has no server-side render.
 *
 * Static defaults for the primary (Spanish) variant already live in index.html
 * so crawlers that don't execute JS still get correct tags. This hook only
 * overrides them client-side when the resolved language differs (e.g. the
 * `?lang=en` hreflang variant), and restores the previous values on unmount.
 */

import { useEffect } from 'react';

export interface DocumentMetaInput {
  title: string;
  description: string;
  lang: 'es' | 'en';
  /** Canonical URL for this exact language variant, e.g. https://whetzy.com/landing?lang=en */
  url: string;
  imageAlt: string;
}

function setMetaByName(name: string, content: string) {
  let el = document.querySelector<HTMLMetaElement>(`meta[name="${name}"]`);
  if (!el) {
    el = document.createElement('meta');
    el.setAttribute('name', name);
    document.head.appendChild(el);
  }
  el.setAttribute('content', content);
}

function setMetaByProperty(property: string, content: string) {
  let el = document.querySelector<HTMLMetaElement>(`meta[property="${property}"]`);
  if (!el) {
    el = document.createElement('meta');
    el.setAttribute('property', property);
    document.head.appendChild(el);
  }
  el.setAttribute('content', content);
}

function setLinkByRel(rel: string, href: string, hreflang?: string) {
  const selector = hreflang ? `link[rel="${rel}"][hreflang="${hreflang}"]` : `link[rel="${rel}"]`;
  let el = document.querySelector<HTMLLinkElement>(selector);
  if (!el) {
    el = document.createElement('link');
    el.setAttribute('rel', rel);
    if (hreflang) el.setAttribute('hreflang', hreflang);
    document.head.appendChild(el);
  }
  el.setAttribute('href', href);
}

/** Applies document-level SEO tags for the current render and restores the prior state on unmount. */
export function useDocumentMeta({ title, description, lang, url, imageAlt }: DocumentMetaInput) {
  useEffect(() => {
    // No-op under SSR/build-time prerendering (scripts/prerender-landing.mjs
    // renders this component with renderToStaticMarkup, which never runs
    // effects anyway, but this guard keeps the hook safe if it's ever used
    // with a render path that does, e.g. renderToString + hydration).
    if (typeof document === 'undefined') return;

    const prevTitle = document.title;
    const prevLang = document.documentElement.lang;
    const prevDescription = document.querySelector('meta[name="description"]')?.getAttribute('content') ?? '';

    document.title = title;
    document.documentElement.lang = lang;
    setMetaByName('description', description);
    setMetaByProperty('og:title', title);
    setMetaByProperty('og:description', description);
    setMetaByProperty('og:url', url);
    setMetaByProperty('og:locale', lang === 'es' ? 'es_ES' : 'en_US');
    setMetaByProperty('og:image:alt', imageAlt);
    setMetaByName('twitter:title', title);
    setMetaByName('twitter:description', description);
    setLinkByRel('canonical', url);

    return () => {
      document.title = prevTitle;
      document.documentElement.lang = prevLang;
      if (prevDescription) setMetaByName('description', prevDescription);
    };
  }, [title, description, lang, url, imageAlt]);
}
