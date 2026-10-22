/**
 * Landing, ola 2 (2026-10-21):
 * - las banderas de idioma son SVG: los emoji de bandera no existen en Windows
 *   y allí se veían como letras sueltas;
 * - el selector dice cuál está activo (`aria-pressed`);
 * - el JSON-LD de schema.org sale en el HTML con los precios de `plans.ts`
 *   y sin valoraciones ni recuento de usuarios.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, beforeEach } from 'vitest';
import i18n from '../i18n';
import LandingScreen from '../pages/LandingScreen';
import { PRO_MAX_MONTHLY_USD, PRO_MONTHLY_USD } from '../lib/plans';
import { landingJsonLd, serializeJsonLd } from '../lib/structuredData';

// Regional indicator symbols: los dos que forman cualquier emoji de bandera.
const FLAG_EMOJI = /[\u{1F1E6}-\u{1F1FF}]{2}/u;

beforeEach(async () => {
  await i18n.changeLanguage('es');
  window.history.replaceState(null, '', '/landing');
});

describe('selector de idioma', () => {
  it('sin emoji de bandera: dos SVG, uno por idioma', () => {
    const { container } = render(<LandingScreen />);
    expect(container.innerHTML).not.toMatch(FLAG_EMOJI);
    expect(container.querySelector('button[aria-label="Español"] svg[data-flag="es"]')).not.toBeNull();
    expect(container.querySelector('button[aria-label="English"] svg[data-flag="en"]')).not.toBeNull();
  });

  it('marca el idioma activo y cambia al pulsar', () => {
    render(<LandingScreen />);
    expect(screen.getByRole('button', { name: 'Español' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: 'English' })).toHaveAttribute('aria-pressed', 'false');
    fireEvent.click(screen.getByRole('button', { name: 'English' }));
    expect(screen.getByRole('button', { name: 'English' })).toHaveAttribute('aria-pressed', 'true');
  });
});

describe('datos estructurados', () => {
  it('van en el HTML estático (el pre-render los lleva) y se pueden leer', () => {
    const html = renderToStaticMarkup(<LandingScreen />);
    const m = html.match(/<script type="application\/ld\+json">(.*?)<\/script>/s);
    expect(m).not.toBeNull();
    const data = JSON.parse(m![1]) as { '@graph': Array<Record<string, unknown>> };
    const app = data['@graph'].find((n) => n['@type'] === 'SoftwareApplication')!;
    const prices = (app.offers as Array<{ price: string }>).map((o) => o.price);
    expect(prices).toEqual(['0.00', PRO_MONTHLY_USD.toFixed(2), PRO_MAX_MONTHLY_USD.toFixed(2)]);
  });

  it.each(['es', 'en'] as const)('sin valoraciones ni recuentos inventados (%s)', (lang) => {
    const text = JSON.stringify(landingJsonLd(lang));
    expect(text).not.toMatch(/aggregateRating|ratingValue|reviewCount|userInteractionCount/);
    expect(text).not.toMatch(/99\.99/); // Creador: precio no publicado en la landing (D-7)
  });

  it('un «<» en los textos no puede cerrar el <script>', () => {
    expect(serializeJsonLd({ x: '</script><b>' })).not.toContain('<');
  });
});
