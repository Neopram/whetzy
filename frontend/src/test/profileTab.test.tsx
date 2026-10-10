/**
 * ProfileTab del panel de instructor (28.8): antes no llamaba a la API —
 * arrancaba vacío siempre y el envío era un `console.log`. Ahora carga el
 * perfil real al montar y lo guarda de verdad con `PATCH /instructor/profile`.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import '../i18n';
import ProfileTab from '../components/instructor/ProfileTab';
import { instructor } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, instructor: { ...actual.instructor, profile: vi.fn(), updateProfile: vi.fn() } };
});

const profile = instructor.profile as unknown as ReturnType<typeof vi.fn>;
const updateProfile = instructor.updateProfile as unknown as ReturnType<typeof vi.fn>;
afterEach(cleanup);

const PROFILE = {
  display_name: 'Jane Teaches Python', bio: 'Backend for 10 years.',
  avatar_url: 'https://example.com/a.png', website: 'https://example.com',
};

describe('ProfileTab — perfil de instructor real (28.8)', () => {
  it('carga el perfil guardado en los campos del formulario', async () => {
    profile.mockResolvedValue(PROFILE);
    render(<ProfileTab />);

    expect(await screen.findByDisplayValue('Jane Teaches Python')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Backend for 10 years.')).toBeInTheDocument();
    expect(screen.getByDisplayValue('https://example.com/a.png')).toBeInTheDocument();
  });

  it('guarda los cambios con PATCH y muestra la confirmación', async () => {
    profile.mockResolvedValue(PROFILE);
    updateProfile.mockResolvedValue({ ...PROFILE, bio: 'Updated bio.' });
    render(<ProfileTab />);

    const bio = await screen.findByLabelText(/Biografía|Bio/);
    fireEvent.change(bio, { target: { value: 'Updated bio.' } });
    fireEvent.click(screen.getByRole('button', { name: /Guardar|Save/ }));

    await waitFor(() => expect(updateProfile).toHaveBeenCalledWith({ ...PROFILE, bio: 'Updated bio.' }));
    expect(await screen.findByText(/Perfil actualizado|Profile updated/)).toBeInTheDocument();
  });

  it('un fallo al cargar no deja el formulario a medias', async () => {
    profile.mockRejectedValue(new Error('network'));
    render(<ProfileTab />);
    expect(await screen.findByText(/No se ha podido cargar|Could not load/i)).toBeInTheDocument();
  });
});
