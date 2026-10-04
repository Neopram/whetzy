import { describe, expect, it } from 'vitest';
import { render } from '@testing-library/react';
import { renderMarkdown } from '../pages/marketing/blogMarkdown';

function html(markdown: string): string {
  const { container } = render(<>{renderMarkdown(markdown)}</>);
  return container.innerHTML;
}

describe('blogMarkdown — subconjunto usado por content/blog/**', () => {
  it('renders a paragraph with bold, italic and inline code', () => {
    const out = html('A **bold** word, an *italic* one, and `inline code`.');
    expect(out).toBe('<p>A <strong>bold</strong> word, an <em>italic</em> one, and <code>inline code</code>.</p>');
  });

  it('renders an h2', () => {
    expect(html('## A heading')).toBe('<h2>A heading</h2>');
  });

  it('renders an h3', () => {
    expect(html('### A subheading')).toBe('<h3>A subheading</h3>');
  });

  it('renders a link, external links get target=_blank', () => {
    const out = html('See [the docs](https://example.com/docs) for more.');
    expect(out).toBe(
      '<p>See <a href="https://example.com/docs" target="_blank" rel="noreferrer">the docs</a> for more.</p>',
    );
  });

  it('renders a relative link without target=_blank', () => {
    const out = html('See [this page](/other).');
    expect(out).toBe('<p>See <a href="/other">this page</a>.</p>');
  });

  it('renders a fenced code block with a language tag', () => {
    const out = html('```python\nprint(1)\n```');
    expect(out).toBe('<pre><code data-lang="python">print(1)</code></pre>');
  });

  it('renders a fenced code block with no language', () => {
    const out = html('```\nplain\n```');
    expect(out).toBe('<pre><code>plain</code></pre>');
  });

  it('renders a bullet list', () => {
    const out = html('- one\n- two\n- three');
    expect(out).toBe('<ul><li>one</li><li>two</li><li>three</li></ul>');
  });

  it('renders a horizontal rule', () => {
    expect(html('---')).toBe('<hr>');
  });

  it('renders a table', () => {
    const out = html('| a | b |\n|---|---|\n| 1 | 2 |');
    expect(out).toBe(
      '<table><thead><tr><th>a</th><th>b</th></tr></thead><tbody><tr><td>1</td><td>2</td></tr></tbody></table>',
    );
  });

  it('renders two paragraphs separated by a blank line as two <p>', () => {
    const out = html('First paragraph.\n\nSecond paragraph.');
    expect(out).toBe('<p>First paragraph.</p><p>Second paragraph.</p>');
  });

  it('joins wrapped lines of the same paragraph with a space', () => {
    const out = html('Line one\nline two still the same paragraph.');
    expect(out).toBe('<p>Line one line two still the same paragraph.</p>');
  });

  it('renders a blockquote', () => {
    const out = html('> quoted text');
    expect(out).toBe('<blockquote>quoted text</blockquote>');
  });

  it('never infinite-loops on an empty string', () => {
    expect(html('')).toBe('');
  });

  it('renders a realistic mixed article body without throwing', () => {
    const body = [
      '## Section one',
      '',
      'A paragraph with **bold** and a [link](https://whetzy.com).',
      '',
      '```python',
      'x = 1',
      '```',
      '',
      '- item one',
      '- item two',
      '',
      '---',
      '',
      '*A closing italic line.*',
    ].join('\n');
    const out = html(body);
    expect(out).toContain('<h2>Section one</h2>');
    expect(out).toContain('<pre><code data-lang="python">x = 1</code></pre>');
    expect(out).toContain('<ul><li>item one</li><li>item two</li></ul>');
    expect(out).toContain('<hr>');
    expect(out).toContain('<em>A closing italic line.</em>');
  });
});
