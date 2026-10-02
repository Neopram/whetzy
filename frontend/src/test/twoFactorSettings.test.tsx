/**
 * Yo → Ajustes → Verificación en dos pasos (O1.3). La 2FA tenía backend y no
 * pantalla. Activar exige confirmar un código de la app; desactivar, otro.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { TwoFactorSettings } from '../components/profile/TwoFactorSettings';
import { ApiError, auth } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    auth: {
      ...actual.auth,
      twoFactor: { status: vi.fn(), setup: vi.fn(), enable: vi.fn(), disable: vi.fn() },
    },
  };
});

const tf = auth.twoFactor as unknown as Record<'status' | 'setup' | 'enable' | 'disable', ReturnType<typeof vi.fn>>;
const SETUP = {
  qr_uri: 'otpauth://totp/Whetzy:ana?secret=ABC',
  qr_svg: '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
  secret: 'JBSWY3DPEHPK3PXP',
  backup_codes: ['a1b2c3d4', 'e5f6a7b8'],
};

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
});
afterEach(cleanup);

describe('TwoFactorSettings', () => {
  it('desactivada → alta con QR, clave y códigos de respaldo; solo se activa con un código válido', async () => {
    tf.status.mockResolvedValueOnce({ enabled: false, backup_codes_left: 0 });
    tf.setup.mockResolvedValue(SETUP);
    render(<TwoFactorSettings />);
    expect(await screen.findByText('Desactivada')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Activar' }));
    expect(await screen.findByRole('img', { name: 'Código QR para tu app de autenticación' })).toBeInTheDocument();
    expect(screen.getByText(SETUP.secret)).toBeInTheDocument();
    expect(screen.getByRole('list', { name: 'Códigos de respaldo' })).toHaveTextContent('a1b2c3d4');

    const submit = screen.getByRole('button', { name: 'Confirmar y activar' });
    expect(submit).toBeDisabled();
    const input = screen.getByLabelText('Código de 6 dígitos de la app');

    tf.enable.mockRejectedValueOnce(new ApiError('Invalid TOTP code', 400));
    fireEvent.change(input, { target: { value: '000000' } });
    fireEvent.click(submit);
    expect(await screen.findByRole('alert')).toHaveTextContent('Ese código no es válido');
    expect(tf.status).toHaveBeenCalledTimes(1);

    tf.enable.mockResolvedValueOnce({ message: 'ok' });
    tf.status.mockResolvedValueOnce({ enabled: true, backup_codes_left: 10 });
    fireEvent.change(input, { target: { value: '123 456' } });
    fireEvent.click(submit);
    expect(await screen.findByRole('status')).toHaveTextContent('activada');
    expect(tf.enable).toHaveBeenLastCalledWith('123456');
    expect(screen.getByText('Activada')).toBeInTheDocument();
    expect(screen.getByText('Te quedan 10 códigos de respaldo.')).toBeInTheDocument();
    // Los códigos de respaldo no se vuelven a mostrar.
    expect(screen.queryByText('a1b2c3d4')).toBeNull();
  });

  it('activada → desactivar pide un código y no llama al alta', async () => {
    tf.status.mockResolvedValueOnce({ enabled: true, backup_codes_left: 1 });
    render(<TwoFactorSettings />);
    expect(await screen.findByText('Te queda 1 código de respaldo.')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Desactivar' }));
    tf.disable.mockResolvedValueOnce({ enabled: false });
    tf.status.mockResolvedValueOnce({ enabled: false, backup_codes_left: 0 });
    fireEvent.change(screen.getByLabelText('Código de la app o de respaldo'), { target: { value: 'a1b2c3d4' } });
    fireEvent.click(screen.getAllByRole('button', { name: 'Desactivar' }).at(-1)!);
    expect(await screen.findByText('Desactivada')).toBeInTheDocument();
    expect(tf.disable).toHaveBeenCalledWith('a1b2c3d4');
    expect(tf.setup).not.toHaveBeenCalled();
  });

  it('sin sesión o sin backend no pinta nada (no inventa un estado)', async () => {
    tf.status.mockRejectedValueOnce(new ApiError('Unauthorized', 401));
    const { container } = render(<TwoFactorSettings />);
    await vi.waitFor(() => expect(tf.status).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });
});
