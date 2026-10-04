/** Carga y parsea `content/blog/{es,en}/<slug>.md` (26.9, 0.14).
 *
 *  `content/blog/**` sigue siendo la única fuente (content/blog/README.md);
 *  este fichero solo la lee. El frontmatter es deliberadamente simple (clave:
 *  "valor" entre comillas, una línea por clave) — no es YAML completo, es el
 *  subconjunto exacto que `content/blog/README.md` documenta. Un fichero que
 *  no cumpla ese formato revienta en el build en vez de perderse en
 *  silencio (igual que `catalog.ts` respecto a `tracks.json`).
 */

export type BlogLang = 'es' | 'en';

export interface BlogPost {
  slug: string;
  lang: BlogLang;
  title: string;
  date: string;
  author: string;
  summary: string;
  /** Cuerpo en markdown, sin el frontmatter. */
  body: string;
}

const FRONTMATTER_KEYS = ['title', 'slug', 'date', 'lang', 'author', 'summary'] as const;
type FrontmatterKey = (typeof FRONTMATTER_KEYS)[number];

function parsePost(path: string, raw: string): BlogPost {
  const match = raw.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  if (!match) {
    throw new Error(`[blogContent] ${path}: no tiene frontmatter "---\\n...\\n---"`);
  }
  const [, frontmatter, body] = match;
  const fields: Partial<Record<FrontmatterKey, string>> = {};
  for (const line of frontmatter.split('\n')) {
    if (!line.trim()) continue;
    const kv = line.match(/^([a-z]+):\s*"?([^"]*)"?$/);
    if (!kv) throw new Error(`[blogContent] ${path}: línea de frontmatter inesperada: ${JSON.stringify(line)}`);
    const [, key, value] = kv;
    if ((FRONTMATTER_KEYS as readonly string[]).includes(key)) {
      fields[key as FrontmatterKey] = value;
    }
  }
  for (const key of FRONTMATTER_KEYS) {
    if (!fields[key]) throw new Error(`[blogContent] ${path}: falta "${key}" en el frontmatter`);
  }
  const lang = fields.lang as string;
  if (lang !== 'es' && lang !== 'en') {
    throw new Error(`[blogContent] ${path}: lang "${lang}" no es "es" ni "en"`);
  }
  return {
    slug: fields.slug as string,
    lang,
    title: fields.title as string,
    date: fields.date as string,
    author: fields.author as string,
    summary: fields.summary as string,
    body: body.trim(),
  };
}

// `eager: true` porque son 8 ficheros pequeños y la lista/detalle los necesita
// de entrada, sin otra carga en cadena. `?raw` evita que Vite intente
// procesar el markdown como código.
const rawFiles = import.meta.glob<string>('../../../../content/blog/*/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
});

export const BLOG_POSTS: BlogPost[] = Object.entries(rawFiles)
  .map(([path, raw]) => parsePost(path, raw))
  // Más nuevo primero, y si hay empate en fecha, orden estable por slug.
  .sort((a, b) => (a.date === b.date ? a.slug.localeCompare(b.slug) : b.date.localeCompare(a.date)));

export function postsByLang(lang: BlogLang): BlogPost[] {
  return BLOG_POSTS.filter((p) => p.lang === lang);
}

export function postBySlug(lang: BlogLang, slug: string): BlogPost | undefined {
  return BLOG_POSTS.find((p) => p.lang === lang && p.slug === slug);
}
