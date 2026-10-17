/**
 * D-19 (dueño, 2026-10-12): el aviso de MLA-C01 (examen sustituido por MLA-C02)
 * sale donde la certificación se elige, se practica o se compra, no solo en
 * Rutas. Y no sale sobre track45, que ya es el AI-901 vigente.
 */
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import i18n from '../i18n';
import { RetiredCertNotice } from '../components/common/RetiredCertNotice';

beforeEach(async () => {
  await i18n.changeLanguage('es');
});
afterEach(cleanup);

describe('RetiredCertNotice (D-19)', () => {
  it('avisa en track43 de que MLA-C01 lo sustituye MLA-C02', () => {
    render(<RetiredCertNotice trackId="track43" />);
    expect(screen.getByTestId('retired-cert-notice')).toHaveTextContent(/MLA-C01.*MLA-C02/);
  });

  it('no avisa sobre track45: su contenido ya es AI-901', () => {
    render(<RetiredCertNotice trackId="track45" />);
    expect(screen.queryByTestId('retired-cert-notice')).not.toBeInTheDocument();
  });

  it.each(['MockExamScreen', 'ReadinessScreen', 'CheckoutScreen'])(
    '%s pinta el aviso',
    (page) => {
      const src = readFileSync(join(process.cwd(), `src/pages/${page}.tsx`), 'utf8');
      expect(src).toContain('<RetiredCertNotice');
    },
  );

  it('el onboarding marca la certificación retirada al elegirla', () => {
    const src = readFileSync(join(process.cwd(), 'src/pages/OnboardingScreen.tsx'), 'utf8');
    expect(src).toContain("retiredCertificationFor(id)");
  });
});
