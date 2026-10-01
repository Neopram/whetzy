/**
 * H.29 (2026-10-01): Paddle cobra en la web desde el #58 y la política que se
 * publica en /privacy (estas claves, no docs/legal) no lo nombraba. El dueño
 * pidió mencionarlo; check_legal_facts [1b] vigila el texto y este test que la
 * pantalla lo pinte.
 */
import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { LegalScreen } from '../pages/LegalScreen';

afterEach(async () => {
  cleanup();
  await i18n.changeLanguage('es');
});

describe('Política de privacidad — procesador de pagos', () => {
  it.each(['es', 'en'])('nombra a Paddle en %s', async (lang) => {
    await i18n.changeLanguage(lang);
    render(<LegalScreen doc="privacy" />);
    expect(screen.getByText(/Paddle/)).toBeTruthy();
  });
});
