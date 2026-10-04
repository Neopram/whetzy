/** `/blog` (0.14, 26.9): lista + detalle de `content/blog/**`, en vez de la
 *  página vacía que servía esta ruta hasta ahora (reservada en la fase 0).
 *
 *  Sin router de cliente: el idioma y el artículo elegido viven en la query
 *  string (`?lang=en&post=<slug>`), igual que `/landing?lang=en`
 *  (`LandingScreen.tsx`). Cambiar de artículo hace `history.pushState` propio
 *  y escucha `popstate`, así que atrás/adelante del navegador funciona sin
 *  que `App.tsx` tenga que saber nada de esta ruta más allá de montarla. */
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import styles from './BlogPage.module.css';
import { useDocumentMeta } from '../../hooks/useDocumentMeta';
import { postBySlug, postsByLang, type BlogLang } from './blogContent';
import { renderMarkdown } from './blogMarkdown';

function resolveBlogLang(): BlogLang {
  if (typeof window === 'undefined') return 'es';
  const q = new URLSearchParams(window.location.search).get('lang');
  if (q === 'es' || q === 'en') return q;
  return (navigator.language || 'es').toLowerCase().startsWith('en') ? 'en' : 'es';
}

function resolvePost(): string | null {
  if (typeof window === 'undefined') return null;
  return new URLSearchParams(window.location.search).get('post');
}

function canonicalUrl(lang: BlogLang, slug: string | null): string {
  const base = 'https://whetzy.com/blog';
  const params = new URLSearchParams();
  if (slug) params.set('post', slug);
  if (lang === 'en') params.set('lang', 'en');
  const qs = params.toString();
  return qs ? `${base}?${qs}` : base;
}

function pushBlogUrl(lang: BlogLang, slug: string | null) {
  const params = new URLSearchParams();
  if (slug) params.set('post', slug);
  if (lang === 'en') params.set('lang', 'en');
  const qs = params.toString();
  window.history.pushState({}, '', qs ? `/blog?${qs}` : '/blog');
}

function formatDate(date: string, lang: BlogLang): string {
  return new Intl.DateTimeFormat(lang === 'es' ? 'es-ES' : 'en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(new Date(`${date}T00:00:00Z`));
}

export default function BlogPage() {
  const { t, i18n } = useTranslation('marketing');
  const [lang, setLang] = useState<BlogLang>(resolveBlogLang);
  const [slug, setSlug] = useState<string | null>(resolvePost);

  useEffect(() => {
    if (i18n.language !== lang) void i18n.changeLanguage(lang);
  }, [lang, i18n]);

  useEffect(() => {
    const onPopState = () => {
      setLang(resolveBlogLang());
      setSlug(resolvePost());
    };
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  const post = slug ? postBySlug(lang, slug) : null;
  const otherLang: BlogLang = lang === 'es' ? 'en' : 'es';
  const otherLangPost = post ? postBySlug(otherLang, post.slug) : null;

  useDocumentMeta({
    title: post ? `${post.title} — Whetzy` : t('blog.metaTitle'),
    description: post ? post.summary : t('blog.metaDescription'),
    lang,
    url: canonicalUrl(lang, post ? post.slug : null),
    imageAlt: 'Whetzy',
  });

  function openPost(nextSlug: string) {
    setSlug(nextSlug);
    pushBlogUrl(lang, nextSlug);
    window.scrollTo(0, 0);
  }

  function backToList() {
    setSlug(null);
    pushBlogUrl(lang, null);
  }

  function switchLanguage() {
    const next = otherLang;
    setLang(next);
    // Un slug no siempre existe en el otro idioma (bilingüe, mismo slug
    // documentado en content/blog/README.md) — si no existe, se cae a la lista.
    const nextSlug = post && postBySlug(next, post.slug) ? post.slug : null;
    setSlug(nextSlug);
    pushBlogUrl(next, nextSlug);
  }

  if (slug && !post) {
    return (
      <main className={styles.page}>
        <p className={styles.notFound}>{t('blog.notFound')}</p>
        <button type="button" className={styles.backLink} onClick={backToList}>
          {t('blog.back')}
        </button>
      </main>
    );
  }

  if (post) {
    return (
      <main className={styles.page}>
        <button type="button" className={styles.backLink} onClick={backToList}>
          {t('blog.back')}
        </button>
        <article>
          <h1 className={styles.articleTitle}>{post.title}</h1>
          <p className={styles.byLine}>{t('blog.byLine', { author: post.author, date: formatDate(post.date, lang) })}</p>
          <div className={styles.articleBody}>{renderMarkdown(post.body)}</div>
        </article>
        {otherLangPost && (
          <button type="button" className={styles.langSwitch} onClick={switchLanguage}>
            {t('blog.switchLanguage')}
          </button>
        )}
      </main>
    );
  }

  const posts = postsByLang(lang);
  return (
    <main className={styles.page}>
      <h1 className={styles.heading}>{t('blog.heading')}</h1>
      <p className={styles.intro}>{t('blog.intro')}</p>
      {posts.length === 0 ? (
        <p className={styles.empty}>{t('blog.empty')}</p>
      ) : (
        <ul className={styles.list}>
          {posts.map((p) => (
            <li key={p.slug} className={styles.listItem}>
              <h2 className={styles.listTitle}>{p.title}</h2>
              <p className={styles.byLine}>{t('blog.byLine', { author: p.author, date: formatDate(p.date, lang) })}</p>
              <p className={styles.summary}>{p.summary}</p>
              <button type="button" className={styles.readMore} onClick={() => openPost(p.slug)}>
                {t('blog.readMore')}
              </button>
            </li>
          ))}
        </ul>
      )}
      <button type="button" className={styles.langSwitch} onClick={switchLanguage}>
        {t('blog.switchLanguage')}
      </button>
    </main>
  );
}
