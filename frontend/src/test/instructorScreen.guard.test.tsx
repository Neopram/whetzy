/**
 * 28.3: la pantalla de instructor se protege a sí misma. Sin `canCreateCourses`
 * (que llega del store, desde `can_create_courses` de /auth/me) muestra un aviso
 * y no monta el panel, aunque se llegue por `screen === 'instructor'`.
 */
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import i18n from '../i18n';
import InstructorScreen from '../pages/InstructorScreen';
import { useAppStore } from '../stores/useAppStore';

vi.mock('../components/instructor/InstructorPanel', () => ({
  default: () => <div data-testid="instructor-panel">panel</div>,
}));

beforeEach(async () => {
  await i18n.changeLanguage('es');
  useAppStore.setState({ currentScreen: 'instructor' });
});
afterEach(cleanup);

describe('InstructorScreen', () => {
  it('sin permiso de creador: aviso, sin panel, y vuelta al perfil', () => {
    useAppStore.setState({ user: { ...useAppStore.getState().user, canCreateCourses: false } });
    render(<InstructorScreen />);

    expect(screen.queryByTestId('instructor-panel')).toBeNull();
    expect(screen.getByRole('alert')).toHaveTextContent('solo para creadores de cursos');
    fireEvent.click(screen.getByRole('button', { name: 'Volver al perfil' }));
    expect(useAppStore.getState().currentScreen).toBe('profile');
  });

  it('con permiso de creador: el panel, sin aviso', () => {
    useAppStore.setState({ user: { ...useAppStore.getState().user, canCreateCourses: true } });
    render(<InstructorScreen />);

    expect(screen.getByTestId('instructor-panel')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('el aviso sale también en inglés', async () => {
    await i18n.changeLanguage('en');
    useAppStore.setState({ user: { ...useAppStore.getState().user, canCreateCourses: false } });
    render(<InstructorScreen />);
    expect(screen.getByRole('alert')).toHaveTextContent('course creators only');
  });
});
