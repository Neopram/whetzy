import { describe, expect, it } from 'vitest';
import { BLOG_POSTS, postBySlug, postsByLang } from '../pages/marketing/blogContent';

describe('blogContent — carga content/blog/**/*.md real', () => {
  it('loads exactly the 4 ES + 4 EN posts that exist on disk today', () => {
    expect(postsByLang('es')).toHaveLength(4);
    expect(postsByLang('en')).toHaveLength(4);
    expect(BLOG_POSTS).toHaveLength(8);
  });

  it('every post has all required fields non-empty', () => {
    for (const post of BLOG_POSTS) {
      expect(post.slug).toBeTruthy();
      expect(post.title).toBeTruthy();
      expect(post.date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(post.author).toBeTruthy();
      expect(post.summary).toBeTruthy();
      expect(post.body.length).toBeGreaterThan(100);
    }
  });

  it('every ES slug has a matching EN slug and vice versa (bilingüe nativo, CLAUDE.md)', () => {
    const esSlugs = postsByLang('es').map((p) => p.slug).sort();
    const enSlugs = postsByLang('en').map((p) => p.slug).sort();
    expect(esSlugs).toEqual(enSlugs);
  });

  it('postBySlug finds a known article in each language', () => {
    expect(postBySlug('es', 'math-behind-fsrs')?.title).toContain('matemática');
    expect(postBySlug('en', 'math-behind-fsrs')?.title).toContain('math');
  });

  it('postBySlug returns undefined for an unknown slug', () => {
    expect(postBySlug('es', 'nope')).toBeUndefined();
  });

  it('is sorted newest-first by date', () => {
    const dates = postsByLang('es').map((p) => p.date);
    const sorted = [...dates].sort().reverse();
    expect(dates).toEqual(sorted);
  });

  it('body never contains the frontmatter delimiter', () => {
    for (const post of BLOG_POSTS) {
      expect(post.body.startsWith('---')).toBe(false);
    }
  });
});
