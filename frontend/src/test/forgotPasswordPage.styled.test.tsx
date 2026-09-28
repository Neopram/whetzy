/**
 * ForgotPasswordPage.tsx reuses AuthScreen.module.css but, until this fix,
 * skipped the classes that give AuthScreen its Obsidian look: the raw
 * <input> carried no className at all, and "Volver" was an inline-styled
 * button instead of styles.forgotLink. cssModules.contract.test.ts (34.1)
 * can't catch this — it only checks that a referenced styles.x maps to a
 * real class, not that an element applies one in the first place. This
 * guards the concrete regression: submit the form and check the email
 * input actually carries a CSS-module class (non-empty, non-inline).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { ForgotPasswordPage } from '../pages/ForgotPasswordPage';
import { auth } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, auth: { ...actual.auth, requestPasswordReset: vi.fn() } };
});

const requestPasswordReset = auth.requestPasswordReset as unknown as ReturnType<typeof vi.fn>;

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
});
afterEach(cleanup);

describe('ForgotPasswordPage — estilo Obsidian (34.1)', () => {
  it('el input de correo lleva una clase del CSS module, no sale sin estilo', () => {
    render(<ForgotPasswordPage onBack={() => {}} />);
    const input = screen.getByPlaceholderText('tu@correo.com');
    expect(input.className).not.toBe('');
  });

  it('el botón "Volver" usa una clase del CSS module en vez de estilo inline', () => {
    render(<ForgotPasswordPage onBack={() => {}} />);
    const back = screen.getByRole('button', { name: 'Volver' });
    expect(back.className).not.toBe('');
    expect(back.getAttribute('style')).toBeNull();
  });

  it('tras enviar, la vista "revisa tu correo" también sale con la marca (brand) estilada', async () => {
    requestPasswordReset.mockResolvedValue({ message: 'ok' });
    render(<ForgotPasswordPage onBack={() => {}} />);

    fireEvent.change(screen.getByPlaceholderText('tu@correo.com'), {
      target: { value: 'shots@example.com' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Enviar' }));

    const heading = await screen.findByText('Revisa tu correo');
    expect(heading.className).not.toBe('');
  });
});
