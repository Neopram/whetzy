/**
 * `/es/empresas` y `/en/enterprise` servían una página en blanco (0.14). No
 * hay panel de equipo en el producto y el precio por asiento está marcado
 * "sin publicar" (ADR-22/ADR-47), así que la página no promete ninguno de
 * los dos — mensaje honesto con `noindex`, igual que CareerPage.
 */
import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import EnterprisePage from '../pages/marketing/EnterprisePage';

afterEach(cleanup);

describe('EnterprisePage — soft 404 honesto (0.14)', () => {
  it('ES: shows a not-available message, not a blank page', async () => {
    await i18n.changeLanguage('es');
    render(<EnterprisePage lang="es" />);
    expect(screen.getByText(/Todavía no tenemos una página propia/)).toBeInTheDocument();
  });

  it('EN: same message in English', async () => {
    await i18n.changeLanguage('en');
    render(<EnterprisePage lang="en" />);
    expect(screen.getByText(/dedicated team page/)).toBeInTheDocument();
  });

  it('never mentions a price (the per-seat figure is unpublished, ADR-22/47)', () => {
    render(<EnterprisePage lang="es" />);
    expect(screen.queryByText(/\$99|99\s*(USD|\$)/)).not.toBeInTheDocument();
  });

  it('sets meta robots=noindex', () => {
    render(<EnterprisePage lang="es" />);
    expect(document.querySelector('meta[name="robots"]')?.getAttribute('content')).toBe('noindex');
  });
});
