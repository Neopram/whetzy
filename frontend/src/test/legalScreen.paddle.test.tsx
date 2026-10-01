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
    expect(screen.getAllByText(/Paddle/).length).toBeGreaterThan(0);
  });
});

/**
 * ADR-55 (2026-10-01): lo publicado es la fuente canónica. Las claves de
 * reclamación ante la autoridad, cookies y menores existían en i18n pero
 * ningún componente las pintaba, y la página no decía qué proveedores tratan
 * los datos ni que algunos están fuera del EEE (RGPD art. 13). Se mira la
 * pantalla, no el JSON: el fallo era justo una clave que nadie pintaba.
 */
describe('Política de privacidad — lo que exige el art. 13 RGPD', () => {
  it.each(['es', 'en'])('%s: proveedores, transferencias, reclamación, cookies y menores', async (lang) => {
    await i18n.changeLanguage(lang);
    render(<LegalScreen doc="privacy" />);
    for (const name of ['Railway', 'Cloudflare', 'Groq', 'Resend', 'Sentry']) {
      expect(screen.getByText(new RegExp(name))).toBeTruthy();
    }
    expect(screen.getByText(i18n.t('legal.privacyTransfers'))).toBeTruthy();
    expect(screen.getByText(i18n.t('legal.privacyGdprDesc'))).toBeTruthy();
    expect(screen.getByText(i18n.t('legal.privacyCookies'))).toBeTruthy();
    expect(screen.getByText(i18n.t('legal.privacyCoppaDesc'))).toBeTruthy();
  });
});
