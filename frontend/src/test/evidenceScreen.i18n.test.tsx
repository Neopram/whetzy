/**
 * 34.12: `/evidence` estaba en inglés fijo (`EvidenceScreen.tsx` no usaba
 * `useTranslation`) mientras el resto de la app es ES/EN nativo. Comprueba
 * que la página responde de verdad al idioma, en vez de mostrar siempre el
 * mismo texto.
 *
 * 2026-10-15: la tabla con notas propias a competidores se quitó (auditoría de
 * pantallas); la sección 04 enlaza ahora a la comparativa de la portada.
 */
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { CATALOG_TRACKS } from '../lib/catalog';
import { COMPARISON_CHECKED_ON } from '../lib/comparison';
import { EvidenceScreen } from '../pages/EvidenceScreen';

afterEach(cleanup);

describe('EvidenceScreen — ES y EN nativos (34.12)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('es');
  });

  it('ES: título, cabecera y sección de comparativa en español', () => {
    render(<EvidenceScreen />);
    expect(screen.getByRole('heading', { name: 'Página de evidencia' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Motor de aprendizaje/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Ver la comparativa' })).toHaveAttribute('href', '/landing#compare');
    expect(document.title).toBe('Whetzy — Evidencia');
  });

  it('EN: same page in English, not a mix of the two languages', async () => {
    await i18n.changeLanguage('en');
    render(<EvidenceScreen />);
    expect(screen.getByRole('heading', { name: 'Evidence page' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Learning engine/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'See the comparison' })).toBeInTheDocument();
    expect(screen.queryByText(/Página de evidencia/)).not.toBeInTheDocument();
    expect(document.title).toBe('Whetzy — Evidence');
  });

  it('ES: the comparison section gives its check date and scores no one', () => {
    render(<EvidenceScreen />);
    expect(screen.getByText(new RegExp(COMPARISON_CHECKED_ON))).toBeInTheDocument();
    expect(screen.queryByRole('columnheader', { name: /Total/ })).not.toBeInTheDocument();
    // The live catalog number still reaches the page, in «Dónde vamos por detrás».
    expect(screen.getByText(new RegExp(`${CATALOG_TRACKS} tracks`))).toBeInTheDocument();
  });
});
