/**
 * Alta al newsletter en el pie de la landing (26.10): habla con el endpoint real
 * (`POST {API_BASE_URL}/newsletter/subscribe`), tiene nombre accesible y estados de
 * enviado y error, y sus textos salen en ES y EN.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import i18n from '../i18n';
import LandingScreen from '../pages/LandingScreen';
import { NewsletterForm } from '../components/landing/NewsletterForm';
import { API_BASE_URL } from '../services/api';

const fetchMock = vi.fn();

beforeEach(async () => {
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
  await i18n.changeLanguage('es');
  window.history.replaceState(null, '', '/landing');
});
afterEach(() => vi.unstubAllGlobals());

const respond = (status: number) =>
  fetchMock.mockResolvedValue({ ok: status >= 200 && status < 300, status } as Response);

describe('montaje en la landing', () => {
  it('el pie lleva el formulario, con nombre accesible', () => {
    const { container } = render(<LandingScreen />);
    const form = screen.getByRole('form', { name: 'Newsletter' });
    expect(container.querySelector('footer')).toContainElement(form);
    expect(screen.getByLabelText('Tu correo electrónico')).toHaveAttribute('type', 'email');
  });
});

describe.each(['es', 'en'] as const)('formulario (%s)', (lang) => {
  const label = () => screen.getByLabelText(lang === 'es' ? 'Tu correo electrónico' : 'Your email address');
  const submit = () => screen.getByRole('button', { name: lang === 'es' ? 'Suscribirme' : 'Subscribe' });
  const setup = async () => {
    await i18n.changeLanguage(lang);
    return render(<NewsletterForm />);
  };

  it('envía al endpoint real con el correo y el idioma, y muestra «enviado»', async () => {
    respond(202);
    await setup();
    fireEvent.change(label(), { target: { value: ' ana@example.com ' } });
    fireEvent.click(submit());

    await waitFor(() => expect(screen.getByRole('status')).toBeInTheDocument());
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(`${API_BASE_URL}/newsletter/subscribe`);
    expect(init.method).toBe('POST');
    expect(JSON.parse(init.body as string)).toEqual({ email: 'ana@example.com', language: lang });
    expect(screen.getByRole('status')).toHaveTextContent(lang === 'es' ? /confirmar la suscripción/ : /confirm your subscription/);
    expect(screen.queryByRole('button', { name: lang === 'es' ? 'Suscribirme' : 'Subscribe' })).toBeNull();
  });

  it('un 422 del servidor dice que el correo no vale y deja reintentar', async () => {
    respond(422);
    await setup();
    fireEvent.change(label(), { target: { value: 'no-es-un-correo' } });
    fireEvent.click(submit());

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(lang === 'es' ? 'Escribe un correo electrónico válido.' : 'Enter a valid email address.');
    expect(label()).toHaveAttribute('aria-invalid', 'true');
    expect(submit()).toBeEnabled();
  });

  it('un 500 o un fallo de red muestran el error genérico', async () => {
    respond(500);
    await setup();
    fireEvent.change(label(), { target: { value: 'ana@example.com' } });
    fireEvent.click(submit());
    expect(await screen.findByRole('alert')).toHaveTextContent(lang === 'es' ? /No hemos podido/ : /couldn't register/);

    fetchMock.mockRejectedValue(new TypeError('network'));
    fireEvent.click(submit());
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(await screen.findByRole('alert')).toHaveTextContent(lang === 'es' ? /No hemos podido/ : /couldn't register/);
  });
});
