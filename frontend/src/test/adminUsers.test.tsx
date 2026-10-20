/**
 * 44.3: pestañas «Usuarios» y «Registro» del panel de administración
 * (docs/PLAN_BACKOFFICE.md B2–B4, B6). Buscar, abrir una ficha y actuar con
 * motivo obligatorio; sin 2FA, el aviso de qué hacer.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { UsersPanel } from '../components/admin/UsersPanel';
import { ActionLogPanel } from '../components/admin/ActionLogPanel';
import { ApiError, adminUsers, type AdminUserDetail } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, adminUsers: { search: vi.fn(), detail: vi.fn(), act: vi.fn(), log: vi.fn() } };
});

const api = adminUsers as unknown as Record<'search' | 'detail' | 'act' | 'log', ReturnType<typeof vi.fn>>;

const DETAIL: AdminUserDetail = {
  id: 'u1',
  account: {
    username: 'anabanana', display_name: 'Ana', email: 'federica@gmail.com', email_verified: false,
    language: 'es', status: 'active', role: 'user', created_at: '2026-10-01T10:00:00Z', last_active: null,
  },
  plan: {
    subscription_tier: null, subscription_status: null, subscription_expires_at: null, subscription_provider: null,
    paddle_subscription_id: null, granted_tier: null, granted_tier_expires_at: null, certification_purchases: [],
  },
  progress: { target_track_id: null, target_certification_id: null, skills_practiced: 3, answers: 42, level: 2, current_streak: 1 },
  security: { recent_events: [] },
  gdpr: { pending: [] },
};

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
  api.search.mockResolvedValue({
    items: [{ id: 'u1', username: 'anabanana', email_masked: 'fe***@gmail.com', created_at: '2026-10-01T10:00:00Z', status: 'active' }],
    page: 1, page_size: 20, total: 1,
  });
  api.detail.mockResolvedValue(DETAIL);
  api.act.mockResolvedValue({ ok: true, action: 'grant_plan', data: {} });
});
afterEach(cleanup);

async function buscarYAbrir() {
  render(<UsersPanel />);
  fireEvent.change(screen.getByLabelText('Buscar por email, usuario o id'), { target: { value: 'fede' } });
  fireEvent.click(screen.getByRole('button', { name: 'Buscar' }));
  expect(await screen.findByText('fe***@gmail.com')).toBeInTheDocument();
  expect(api.search).toHaveBeenCalledWith('fede');
  fireEvent.click(screen.getByRole('button', { name: /anabanana/ }));
  expect(await screen.findByRole('heading', { name: 'Ficha de anabanana' })).toBeInTheDocument();
}

describe('Admin → Usuarios (44.3)', () => {
  it('no busca con menos de 3 caracteres', () => {
    render(<UsersPanel />);
    fireEvent.change(screen.getByLabelText('Buscar por email, usuario o id'), { target: { value: 'fe' } });
    expect(screen.getByRole('button', { name: 'Buscar' })).toBeDisabled();
  });

  it('busca, enmascara en la lista y abre la ficha con el email completo', async () => {
    await buscarYAbrir();
    expect(api.detail).toHaveBeenCalledWith('u1');
    expect(screen.getByText('federica@gmail.com')).toBeInTheDocument();
    expect(screen.getByText('3 habilidades practicadas · 42 respuestas')).toBeInTheDocument();
  });

  it('regalar plan: sin motivo no se confirma; con motivo manda plan, días y motivo', async () => {
    await buscarYAbrir();
    fireEvent.click(screen.getByRole('button', { name: 'Regalar plan' }));
    const confirmar = await screen.findByRole('button', { name: 'Confirmar' });
    expect(confirmar).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Días (1–90)'), { target: { value: '45' } });
    fireEvent.change(screen.getByLabelText('Motivo (obligatorio)'), { target: { value: '  probador del piloto ' } });
    expect(confirmar).toBeEnabled();
    fireEvent.click(confirmar);
    await waitFor(() => expect(api.act).toHaveBeenCalledWith('u1', 'grant_plan', { reason: 'probador del piloto', tier: 'pro', days: 45 }));
    expect(await screen.findByRole('status')).toHaveTextContent('Hecho: Regalar plan.');
    expect(api.detail).toHaveBeenCalledTimes(2); // la ficha se recarga con el cambio
  });

  it('suspender no manda plan ni días', async () => {
    await buscarYAbrir();
    fireEvent.click(screen.getByRole('button', { name: 'Suspender cuenta' }));
    fireEvent.change(await screen.findByLabelText('Motivo (obligatorio)'), { target: { value: 'abuso' } });
    fireEvent.click(screen.getByRole('button', { name: 'Confirmar' }));
    await waitFor(() => expect(api.act).toHaveBeenCalledWith('u1', 'suspend', { reason: 'abuso' }));
  });

  it('sin 2FA explica qué hacer', async () => {
    api.search.mockRejectedValue(new ApiError('2fa_required', 403, '2fa_required'));
    render(<UsersPanel />);
    fireEvent.change(screen.getByLabelText('Buscar por email, usuario o id'), { target: { value: 'fede' } });
    fireEvent.click(screen.getByRole('button', { name: 'Buscar' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('verificación en dos pasos');
  });
});

describe('Admin → Registro (44.3)', () => {
  it('lista quién hizo qué, a quién y por qué', async () => {
    api.log.mockResolvedValue({
      items: [{
        id: 2, created_at: '2026-10-20T04:00:00Z', action: 'grant_plan', reason: 'probador',
        data: { tier: 'pro', days: 30 }, actor_username: 'dueno', target_user_id: 'u1', target_username: 'anabanana',
      }],
      page: 1, page_size: 20, total: 1,
    });
    render(<ActionLogPanel />);
    expect(await screen.findByText('Regaló un plan')).toBeInTheDocument();
    expect(screen.getByText('dueno → anabanana')).toBeInTheDocument();
    expect(screen.getByText('probador')).toBeInTheDocument();
  });

  it('EN: los textos en inglés', async () => {
    await i18n.changeLanguage('en');
    api.log.mockResolvedValue({ items: [], page: 1, page_size: 20, total: 0 });
    render(<ActionLogPanel />);
    expect(await screen.findByText('Nothing in the log yet.')).toBeInTheDocument();
    await i18n.changeLanguage('es');
  });
});
