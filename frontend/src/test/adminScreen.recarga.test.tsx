/**
 * Revisión de UI del 2026-10-23, back-office: el botón «Reintentar» del error
 * era `onRetry={() => {}}` (no hacía nada) y el MRR se pedía siempre para
 * `month=2026-09`, así que desde octubre enseñaba un mes viejo.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { AdminScreen } from '../pages/AdminScreen';

let urls: string[] = [];
let failNext = 0;

beforeEach(async () => {
  await i18n.changeLanguage('es');
  urls = [];
  failNext = 0;
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(new Date('2026-10-23T08:00:00Z'));
  vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => {
    urls.push(String(input));
    if (failNext > 0) {
      failNext -= 1;
      return Promise.resolve(new Response('{}', { status: 500 }));
    }
    return Promise.resolve(new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }));
  }));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.useRealTimers(); });

describe('Back-office: reintentar y mes del MRR', () => {
  it('«Reintentar» vuelve a pedir los datos de la pestaña', async () => {
    failNext = 1;
    render(<AdminScreen />);
    const retry = await screen.findByRole('button', { name: i18n.t('common.retry') });
    const before = urls.filter((u) => u.includes('/admin/metrics/users')).length;
    fireEvent.click(retry);
    expect(urls.filter((u) => u.includes('/admin/metrics/users')).length).toBe(before + 1);
  });

  it('el MRR se pide para el mes en curso, no para 2026-09', async () => {
    render(<AdminScreen />);
    fireEvent.click(screen.getByRole('button', { name: i18n.t('admin.tabs.revenue') }));
    await vi.waitFor(() => expect(urls.some((u) => u.includes('/admin/revenue/mrr'))).toBe(true));
    const mrr = urls.find((u) => u.includes('/admin/revenue/mrr')) ?? '';
    expect(mrr).toContain('month=2026-10');
  });
});
