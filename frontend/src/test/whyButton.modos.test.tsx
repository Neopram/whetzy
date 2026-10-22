/**
 * Tutor por modos (ola 2, 2026-10-21; dueño: «A fondo» solo Pro Max).
 * - Al abrir pide «¿Por qué?»; «¿Cómo?» pide ese modo.
 * - «A fondo» sin acceso enseña para qué es Pro Max y no llama al servidor;
 *   con acceso (Pro Max, `tutor_deep_access` de /auth/me) lo pide.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { WhyButton } from '../components/quiz/WhyButton';
import { tutor as tutorApi } from '../services/api';
import { useAppStore } from '../stores/useAppStore';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, tutor: { explain: vi.fn() } };
});

const explain = tutorApi.explain as unknown as ReturnType<typeof vi.fn>;

function setDeep(on: boolean) {
  useAppStore.setState((s) => ({ user: { ...s.user, tutorDeepAccess: on } }));
}

beforeEach(async () => {
  explain.mockReset();
  explain.mockImplementation(async (_q: string, mode: string) => ({
    explanation: `texto ${mode}`, provider: 'x', grounded: true, times_missed: 0, mode,
  }));
  await i18n.changeLanguage('es');
});
afterEach(cleanup);

async function open() {
  render(<WhyButton questionId="q1" isPremium onUpgrade={vi.fn()} />);
  fireEvent.click(screen.getByRole('button', { name: '¿Por qué?', expanded: false }));
  await screen.findByText('texto why');
  return screen.getByRole('group', { name: 'Modo del tutor' });
}

describe('WhyButton — modos', () => {
  it('abre en «¿Por qué?» y «¿Cómo?» pide su modo', async () => {
    setDeep(false);
    const modes = await open();
    expect(explain).toHaveBeenLastCalledWith('q1', 'why');
    fireEvent.click(screen.getAllByRole('button', { name: '¿Cómo?' })[0]);
    await screen.findByText('texto how');
    expect(explain).toHaveBeenLastCalledWith('q1', 'how');
    expect(modes.querySelector('[aria-pressed="true"]')).toHaveTextContent('¿Cómo?');
  });

  it('Pro sin acceso: «A fondo» explica Pro Max y no llama al servidor', async () => {
    setDeep(false);
    await open();
    explain.mockClear();
    fireEvent.click(screen.getByRole('button', { name: /A fondo/ }));
    expect(screen.getByText('«A fondo» es de Pro Max')).toBeInTheDocument();
    expect(explain).not.toHaveBeenCalled();
  });

  it('Pro Max: «A fondo» lo pide', async () => {
    setDeep(true);
    await open();
    fireEvent.click(screen.getByRole('button', { name: 'A fondo' }));
    await screen.findByText('texto deep');
    expect(explain).toHaveBeenLastCalledWith('q1', 'deep');
  });
});
