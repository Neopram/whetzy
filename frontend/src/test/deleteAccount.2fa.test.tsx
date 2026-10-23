/**
 * Revisión de UI del 2026-10-23: con 2FA, `/auth/login` responde 200 con un reto
 * (`mfa_required`) y sin sesión. Borrar cuenta pasaba igual a «confirmar» y el
 * DELETE fallaba después sin explicación. Ahora pide el código, como el login.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { DeleteAccountScreen } from '../pages/DeleteAccountScreen';

type Call = { url: string; method: string; body: string | null };
let calls: Call[] = [];

function json(status: number, body: unknown) {
  return Promise.resolve(new Response(JSON.stringify(body), {
    status, headers: { 'Content-Type': 'application/json' },
  }));
}

beforeEach(async () => {
  await i18n.changeLanguage('es');
  calls = [];
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

function stubFetch(handler: (c: Call) => Promise<Response>) {
  vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const c = { url: String(input), method: init?.method ?? 'GET', body: init?.body ? String(init.body) : null };
    calls.push(c);
    return handler(c);
  }));
}

async function login() {
  render(<DeleteAccountScreen />);
  fireEvent.change(screen.getByLabelText(i18n.t('deleteAccount.email')), { target: { value: 'ana@example.com' } });
  fireEvent.change(screen.getByLabelText(i18n.t('deleteAccount.password')), { target: { value: 'secreto-largo' } });
  fireEvent.click(screen.getByRole('button', { name: i18n.t('deleteAccount.continue') }));
}

describe('Borrar cuenta con 2FA', () => {
  it('si el login pide el segundo factor, pide el código antes de confirmar', async () => {
    stubFetch((c) => {
      if (c.url.endsWith('/auth/login')) return json(200, { mfa_required: true, mfa_token: 'tok-mfa' });
      if (c.url.endsWith('/auth/2fa/login')) return json(200, { access_token: 'a', refresh_token: 'r' });
      if (c.url.endsWith('/auth/me/account')) return json(200, { ok: true });
      return json(404, {});
    });
    await login();

    const code = await screen.findByLabelText(i18n.t('auth.mfaCodeLabel'));
    expect(screen.queryByLabelText(i18n.t('deleteAccount.confirmLabel', { word: i18n.t('deleteAccount.confirmWord') }))).toBeNull();

    fireEvent.change(code, { target: { value: '123456' } });
    fireEvent.click(screen.getByRole('button', { name: i18n.t('deleteAccount.verifyCode') }));

    const confirmWord = i18n.t('deleteAccount.confirmWord');
    expect(await screen.findByLabelText(i18n.t('deleteAccount.confirmLabel', { word: confirmWord }))).toBeInTheDocument();
    const mfa = calls.find((c) => c.url.endsWith('/auth/2fa/login'));
    expect(mfa && JSON.parse(mfa.body ?? '{}')).toMatchObject({ code: '123456', mfa_token: 'tok-mfa' });
  });

  it('un código malo se explica y no avanza', async () => {
    stubFetch((c) => {
      if (c.url.endsWith('/auth/login')) return json(200, { mfa_required: true, mfa_token: 'tok-mfa' });
      if (c.url.endsWith('/auth/2fa/login')) return json(400, { detail: 'invalid_code' });
      return json(404, {});
    });
    await login();
    fireEvent.change(await screen.findByLabelText(i18n.t('auth.mfaCodeLabel')), { target: { value: '000000' } });
    fireEvent.click(screen.getByRole('button', { name: i18n.t('deleteAccount.verifyCode') }));
    expect(await screen.findByText(i18n.t('auth.mfaInvalid'))).toBeInTheDocument();
    expect(screen.getByLabelText(i18n.t('auth.mfaCodeLabel'))).toBeInTheDocument();
  });

  it('un error del servidor no se pinta crudo: credenciales malas dicen eso', async () => {
    stubFetch(() => json(422, { detail: [{ loc: ['body', 'username'], msg: 'field required' }] }));
    await login();
    expect(await screen.findByText(i18n.t('deleteAccount.badCredentials'))).toBeInTheDocument();
    expect(document.body.textContent).not.toContain('[object Object]');
  });

  it('al terminar ofrece volver al inicio', async () => {
    stubFetch((c) => {
      if (c.url.endsWith('/auth/login')) return json(200, { access_token: 'a', refresh_token: 'r' });
      if (c.url.endsWith('/auth/me/account')) return json(200, { ok: true });
      return json(404, {});
    });
    await login();
    const confirmWord = i18n.t('deleteAccount.confirmWord');
    fireEvent.change(await screen.findByLabelText(i18n.t('deleteAccount.confirmLabel', { word: confirmWord })), {
      target: { value: confirmWord },
    });
    fireEvent.click(screen.getByRole('button', { name: i18n.t('deleteAccount.deleteCta') }));
    expect(await screen.findByText(i18n.t('deleteAccount.doneTitle'))).toBeInTheDocument();
    expect(screen.getByRole('link', { name: i18n.t('deleteAccount.goHome') })).toHaveAttribute('href', '/');
    expect(calls.some((c) => c.url.endsWith('/auth/me/account') && c.method === 'DELETE')).toBe(true);
  });
});
