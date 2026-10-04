/**
 * `/es/carrera` y `/en/career` servían una página en blanco (0.14). Whetzy
 * no tiene vacantes reales que anunciar, así que la página pasa a un
 * "no disponible todavía" honesto con `noindex`, no contenido inventado.
 */
import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import CareerPage from '../pages/marketing/CareerPage';

afterEach(cleanup);

describe('CareerPage — soft 404 honesto (0.14)', () => {
  it('ES: shows the no-vacancies message, not a blank page', async () => {
    await i18n.changeLanguage('es');
    render(<CareerPage lang="es" />);
    expect(screen.getByText(/no hay vacantes abiertas/)).toBeInTheDocument();
  });

  it('EN: same message in English', async () => {
    await i18n.changeLanguage('en');
    render(<CareerPage lang="en" />);
    expect(screen.getByText(/no open positions/)).toBeInTheDocument();
  });

  it('sets meta robots=noindex so it never gets indexed as a real page', () => {
    render(<CareerPage lang="es" />);
    expect(document.querySelector('meta[name="robots"]')?.getAttribute('content')).toBe('noindex');
  });

  it('restores the previous robots meta on unmount', () => {
    const existing = document.createElement('meta');
    existing.setAttribute('name', 'robots');
    existing.setAttribute('content', 'index, follow');
    document.head.appendChild(existing);

    const { unmount } = render(<CareerPage lang="es" />);
    unmount();

    expect(document.querySelector('meta[name="robots"]')?.getAttribute('content')).toBe('index, follow');
  });

  it('links back to the landing in the right language', () => {
    render(<CareerPage lang="en" />);
    expect(screen.getByRole('link', { name: /Back to whetzy.com/ })).toHaveAttribute('href', '/landing?lang=en');
  });
});
