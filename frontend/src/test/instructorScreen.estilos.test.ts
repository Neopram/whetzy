/**
 * Revisión de UI del 2026-10-23: InstructorScreen pintaba con
 * `className="page-container instructor-page"`, clases que no define ningún
 * CSS del frontend: la pantalla salía sin márgenes ni tipografía propia. Su
 * CSS va en un módulo, como el resto (serie 34), y el botón es el común.
 */
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const PAGES = join(__dirname, '..', 'pages');
const SRC = readFileSync(join(PAGES, 'InstructorScreen.tsx'), 'utf8');

describe('InstructorScreen — estilos en su módulo', () => {
  it('no usa clases globales que nadie define', () => {
    expect(SRC).not.toMatch(/className="[^"]*page-container/);
    expect(SRC).not.toMatch(/className="[^"]*instructor-page/);
  });

  it('tiene su .module.css y lo importa', () => {
    expect(existsSync(join(PAGES, 'InstructorScreen.module.css'))).toBe(true);
    expect(SRC).toMatch(/import styles from '\.\/InstructorScreen\.module\.css'/);
  });

  it('el botón de volver es el Button común', () => {
    expect(SRC).toMatch(/from '\.\.\/components\/common\/Button'/);
    expect(SRC).not.toMatch(/<button\b/);
  });
});
