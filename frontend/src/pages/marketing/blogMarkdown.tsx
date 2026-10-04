/** Markdown → React, para el subconjunto exacto que usan los artículos de
 *  `content/blog/**` (26.9, 0.14): encabezados `##`, párrafos, **negrita**,
 *  *cursiva*, `código en línea`, bloques ```con lenguaje```, listas `- item`,
 *  enlaces `[texto](url)`, tablas `| a | b |` y la regla horizontal `---`.
 *
 *  No es un parser de markdown general — no intenta serlo. Los 8 artículos
 *  actuales son el contrato; `blogMarkdown.render.test.tsx` fija ese
 *  subconjunto con fixtures, no con el markdown real (que puede cambiar de
 *  contenido sin tocar el parser).
 */
import type { ReactNode } from 'react';

let keyCounter = 0;
function nextKey(prefix: string): string {
  keyCounter += 1;
  return `${prefix}-${keyCounter}`;
}

/** Negrita, cursiva, código en línea y enlaces dentro de una línea de texto. */
export function renderInline(text: string): ReactNode[] {
  const out: ReactNode[] = [];
  // Un solo paso con alternancia: code | bold | italic | link, el resto es texto.
  const pattern = /`([^`]+)`|\*\*([^*]+)\*\*|\*([^*]+)\*|\[([^\]]+)\]\(([^)]+)\)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = pattern.exec(text))) {
    if (m.index > last) out.push(text.slice(last, m.index));
    const [, code, bold, italic, linkText, linkHref] = m;
    if (code !== undefined) out.push(<code key={nextKey('code')}>{code}</code>);
    else if (bold !== undefined) out.push(<strong key={nextKey('b')}>{bold}</strong>);
    else if (italic !== undefined) out.push(<em key={nextKey('i')}>{italic}</em>);
    else if (linkText !== undefined) {
      const external = /^https?:\/\//.test(linkHref);
      out.push(
        <a key={nextKey('a')} href={linkHref} {...(external ? { target: '_blank', rel: 'noreferrer' } : {})}>
          {linkText}
        </a>,
      );
    }
    last = pattern.lastIndex;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

function renderTable(lines: string[]): ReactNode {
  const rows = lines.map((line) =>
    line
      .trim()
      .replace(/^\|/, '')
      .replace(/\|$/, '')
      .split('|')
      .map((cell) => cell.trim()),
  );
  const [header, , ...body] = rows; // rows[1] is the |---|---| separator
  return (
    <table key={nextKey('table')}>
      <thead>
        <tr>
          {header.map((cell, i) => (
            <th key={i}>{renderInline(cell)}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {body.map((row) => (
          <tr key={nextKey('tr')}>
            {row.map((cell, i) => (
              <td key={i}>{renderInline(cell)}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

const isTableSeparator = (line: string) => /^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?$/.test(line.trim());
const isTableRow = (line: string) => line.trim().startsWith('|');

/** Convierte el cuerpo markdown de un artículo (sin frontmatter) en nodos React. */
export function renderMarkdown(markdown: string): ReactNode[] {
  const lines = markdown.split('\n');
  const blocks: ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (!line.trim()) {
      i += 1;
      continue;
    }

    if (line.trim() === '---') {
      blocks.push(<hr key={nextKey('hr')} />);
      i += 1;
      continue;
    }

    const heading = line.match(/^(#{2,3})\s+(.*)$/);
    if (heading) {
      const [, hashes, text] = heading;
      const Tag = hashes.length === 2 ? 'h2' : 'h3';
      blocks.push(<Tag key={nextKey(Tag)}>{renderInline(text)}</Tag>);
      i += 1;
      continue;
    }

    if (line.startsWith('```')) {
      const lang = line.slice(3).trim();
      const codeLines: string[] = [];
      i += 1;
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i]);
        i += 1;
      }
      i += 1; // closing fence
      blocks.push(
        <pre key={nextKey('pre')}>
          <code data-lang={lang || undefined}>{codeLines.join('\n')}</code>
        </pre>,
      );
      continue;
    }

    if (isTableRow(line) && isTableSeparator(lines[i + 1] ?? '')) {
      const tableLines: string[] = [line];
      i += 1;
      while (i < lines.length && isTableRow(lines[i])) {
        tableLines.push(lines[i]);
        i += 1;
      }
      blocks.push(renderTable(tableLines));
      continue;
    }

    if (/^[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^[-*]\s+/, ''));
        i += 1;
      }
      blocks.push(
        <ul key={nextKey('ul')}>
          {items.map((item) => (
            <li key={nextKey('li')}>{renderInline(item)}</li>
          ))}
        </ul>,
      );
      continue;
    }

    if (line.startsWith('>')) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].startsWith('>')) {
        quoteLines.push(lines[i].replace(/^>\s?/, ''));
        i += 1;
      }
      blocks.push(<blockquote key={nextKey('bq')}>{renderInline(quoteLines.join(' '))}</blockquote>);
      continue;
    }

    // Párrafo: junta líneas seguidas hasta la próxima línea en blanco o bloque especial.
    const paraLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() &&
      lines[i].trim() !== '---' &&
      !lines[i].match(/^#{2,3}\s/) &&
      !lines[i].startsWith('```') &&
      !/^[-*]\s+/.test(lines[i]) &&
      !lines[i].startsWith('>') &&
      !isTableRow(lines[i])
    ) {
      paraLines.push(lines[i]);
      i += 1;
    }
    if (paraLines.length) blocks.push(<p key={nextKey('p')}>{renderInline(paraLines.join(' '))}</p>);
    else i += 1; // never loop forever on an unrecognised line
  }

  return blocks;
}
