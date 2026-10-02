/**
 * Admin → Economía → Referidos (ECONOMIA §3.5). Hasta el 2026-10-02 un
 * referido abonado no se podía deshacer: ni endpoint ni pantalla.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { ReferralClawback } from '../components/admin/ReferralClawback';
import { adminEconomy } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, adminEconomy: { referrals: vi.fn(), clawback: vi.fn() } };
});

const referrals = adminEconomy.referrals as unknown as ReturnType<typeof vi.fn>;
const clawback = adminEconomy.clawback as unknown as ReturnType<typeof vi.fn>;

const row = (id: string, status: string) => ({
  id, referrer_id: `ref-${id}-aaaaaaaa`, referred_id: `new-${id}-bbbbbbbb`, status,
  activated_at: null, credited_at: null, created_at: '2026-10-01T00:00:00Z',
});

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
  referrals.mockResolvedValue({
    referrals: [row('1', 'credited'), row('2', 'pending'), row('3', 'clawed_back'), row('4', 'activated')],
  });
});
afterEach(cleanup);

describe('ReferralClawback', () => {
  it('solo lista activados y abonados; el clawback pide confirmación y manda el motivo', async () => {
    clawback.mockResolvedValue({ recovered_credits: 100, unrecovered_credits: 200, milestone_revoked: 'pro_month' });
    render(<ReferralClawback />);
    const buttons = await screen.findAllByRole('button', { name: 'Clawback' });
    expect(buttons).toHaveLength(2);

    fireEvent.change(screen.getAllByLabelText('Motivo')[0], { target: { value: 'refund' } });
    fireEvent.click(buttons[0]);
    expect(clawback).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Confirmar clawback' }));

    expect(await screen.findByRole('status')).toHaveTextContent(
      'Hecho: 100 créditos recuperados, 200 ya gastados. Premio retirado: pro_month.',
    );
    expect(clawback).toHaveBeenCalledWith('1', 'refund');
    expect(referrals).toHaveBeenCalledTimes(2);
  });

  it('cancelar no deshace nada', async () => {
    render(<ReferralClawback />);
    fireEvent.click((await screen.findAllByRole('button', { name: 'Clawback' }))[1]);
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }));
    expect(screen.queryByRole('button', { name: 'Confirmar clawback' })).toBeNull();
    expect(clawback).not.toHaveBeenCalled();
  });
});
