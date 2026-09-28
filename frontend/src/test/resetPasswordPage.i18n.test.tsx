/**
 * 23.1: `ResetPasswordPage.tsx` never called `useTranslation` — hardcoded
 * Spanish, and its two `<input>`s carried no className at all (same
 * unstyled-input bug 34.1 already found and fixed once in the sibling
 * ForgotPasswordPage.tsx).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { ResetPasswordPage } from '../pages/ResetPasswordPage';

beforeEach(() => vi.clearAllMocks());
afterEach(cleanup);

describe('ResetPasswordPage — ES y EN nativos, inputs con clase (23.1)', () => {
  it('ES: validación y botón en español', async () => {
    await i18n.changeLanguage('es');
    render(<ResetPasswordPage token="tok" onSuccess={() => {}} />);
    fireEvent.click(screen.getByRole('button', { name: 'Cambiar' }));
    expect(await screen.findByText(/Mínimo 8 caracteres/)).toBeInTheDocument();
  });

  it('EN: same validation and button in English', async () => {
    await i18n.changeLanguage('en');
    render(<ResetPasswordPage token="tok" onSuccess={() => {}} />);
    expect(screen.getByRole('button', { name: 'Change' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Change' }));
    expect(await screen.findByText(/At least 8 characters/)).toBeInTheDocument();
  });

  it('EN: mismatched passwords say so in English, not a stale Spanish string', async () => {
    await i18n.changeLanguage('en');
    render(<ResetPasswordPage token="tok" onSuccess={() => {}} />);
    fireEvent.change(screen.getByPlaceholderText('New password'), { target: { value: 'longenough1' } });
    fireEvent.change(screen.getByPlaceholderText('Confirm'), { target: { value: 'different1' } });
    fireEvent.click(screen.getByRole('button', { name: 'Change' }));
    expect(await screen.findByText(/Don't match/)).toBeInTheDocument();
    expect(screen.queryByText(/No coinciden/)).not.toBeInTheDocument();
  });

  it('both password inputs carry a CSS-module class, not an unstyled raw input', () => {
    render(<ResetPasswordPage token="tok" onSuccess={() => {}} />);
    const inputs = screen.getAllByDisplayValue('');
    for (const input of inputs) expect(input.className).not.toBe('');
  });
});
