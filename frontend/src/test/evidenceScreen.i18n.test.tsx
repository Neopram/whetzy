/**
 * 34.12: `/evidence` estaba en inglés fijo (`EvidenceScreen.tsx` no usaba
 * `useTranslation`) mientras el resto de la app es ES/EN nativo. Comprueba
 * que la página responde de verdad al idioma, en vez de mostrar siempre el
 * mismo texto — incluidas las notas de competidores, que antes eran
 * español fijo pase lo que pasara con el idioma activo.
 */
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { EvidenceScreen } from '../pages/EvidenceScreen';

afterEach(cleanup);

describe('EvidenceScreen — ES y EN nativos (34.12)', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('es');
  });

  it('ES: título, cabecera y nota de competidor en español', () => {
    render(<EvidenceScreen />);
    expect(screen.getByRole('heading', { name: 'Página de evidencia' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Motor de aprendizaje/ })).toBeInTheDocument();
    expect(screen.getByText(/Solo EN, backend gamificado/)).toBeInTheDocument();
    expect(document.title).toBe('Whetzy — Evidencia');
  });

  it('EN: same page in English, not a mix of the two languages', async () => {
    await i18n.changeLanguage('en');
    render(<EvidenceScreen />);
    expect(screen.getByRole('heading', { name: 'Evidence page' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Learning engine/ })).toBeInTheDocument();
    expect(screen.getByText(/EN only, gamified backend/)).toBeInTheDocument();
    expect(screen.queryByText(/Página de evidencia/)).not.toBeInTheDocument();
    expect(document.title).toBe('Whetzy — Evidence');
  });

  it('ES: interpolates the live catalog numbers into the competitor note, not a stale hardcode', () => {
    render(<EvidenceScreen />);
    // CATALOG_TRACKS/CATALOG_QUESTIONS (lib/catalog.ts) interpolated into
    // evidence.competitors.whetzyNow.notes — a stale hardcode would still
    // say "8 tracks 3419 Q" (the old bug this test guards against).
    expect(screen.getByText(/35 tracks 11416 Q/)).toBeInTheDocument();
  });
});
