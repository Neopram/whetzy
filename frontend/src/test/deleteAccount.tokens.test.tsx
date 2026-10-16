/**
 * Serie 34 (coherencia visual), primer bloque: `DeleteAccountScreen` pintaba con
 * 26 `style={}` en línea, tres con colores fijos (sombra y caja de aviso) que no
 * cambiaban en modo claro, y sus `<label>` no estaban asociadas a los campos:
 * un lector de pantalla no decía qué se escribía en cada uno.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { DeleteAccountScreen } from '../pages/DeleteAccountScreen';

const SRC = readFileSync(join(__dirname, '..', 'pages', 'DeleteAccountScreen.tsx'), 'utf8');

beforeEach(async () => {
  await i18n.changeLanguage('es');
});
afterEach(cleanup);

describe('Borrar cuenta — tokens y campos con nombre', () => {
  it('no pinta con estilos en línea ni colores fijos', () => {
    expect(SRC).not.toMatch(/style=\{/);
    expect(SRC).not.toMatch(/rgba?\(|#[0-9a-fA-F]{3,8}\b/);
  });

  it('cada campo tiene su etiqueta asociada', () => {
    render(<DeleteAccountScreen />);
    expect(screen.getByLabelText(i18n.t('deleteAccount.email'))).toHaveAttribute('type', 'email');
    expect(screen.getByLabelText(i18n.t('deleteAccount.password'))).toHaveAttribute('type', 'password');
  });

  it('el botón de continuar es el botón común', () => {
    render(<DeleteAccountScreen />);
    const btn = screen.getByRole('button', { name: i18n.t('deleteAccount.continue') });
    expect(btn).toHaveAttribute('type', 'submit');
  });
});
