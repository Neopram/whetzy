/**
 * axe por ruta (34.8, 2026-10-24): /admin con una cuenta que no es la del dueño
 * enseñaba «No se han podido cargar los datos» y «Reintentar», como si fuera un
 * fallo de red. Un 403 no se arregla reintentando: se dice que el panel es solo
 * del dueño y se ofrece volver.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { AdminScreen } from '../pages/AdminScreen';

let status = 403;

beforeEach(async () => {
  await i18n.changeLanguage('es');
  vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response('{}', { status }))));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

describe('Back-office sin permiso', () => {
  it('con 403 dice que es solo del dueño, sin «Reintentar»', async () => {
    status = 403;
    render(<AdminScreen />);
    expect(await screen.findByText(i18n.t('admin.errors.forbidden'))).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: i18n.t('common.retry') })).toBeNull();
    expect(screen.getByRole('link', { name: i18n.t('admin.errors.backHome') })).toHaveAttribute('href', '/');
  });

  it('con 500 sigue siendo un error que se puede reintentar', async () => {
    status = 500;
    render(<AdminScreen />);
    expect(await screen.findByRole('button', { name: i18n.t('common.retry') })).toBeInTheDocument();
    expect(screen.queryByText(i18n.t('admin.errors.forbidden'))).toBeNull();
  });
});
