/**
 * Catálogo por campos (ola 2, 2026-10-21; decisión del dueño: los cinco campos
 * de la maqueta, que son los grupos del onboarding). El campo se combina con
 * el tipo (Aprender / Certificaciones), cada chip dice cuántas rutas hay, y un
 * campo sin rutas del tipo elegido no se ofrece.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import i18n from '../i18n';
import { TracksScreen } from '../pages/TracksScreen';
import { useAppStore } from '../stores/useAppStore';
import { content as contentApi, progress as progressApi } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    content: { tracks: vi.fn() },
    progress: { ...actual.progress, curriculum: vi.fn(), dashboard: vi.fn() },
  };
});

const tracks = contentApi.tracks as unknown as ReturnType<typeof vi.fn>;
const curriculum = progressApi.curriculum as unknown as ReturnType<typeof vi.fn>;
const dashboard = progressApi.dashboard as unknown as ReturnType<typeof vi.fn>;

function track(id: string, name: string, cert: boolean) {
  return {
    id, name_es: name, name_en: name, order: Number(id.slice(5)), icon: '', color: '#000',
    total_questions: 10, is_certification: cert, cert_provider: cert ? 'X' : null,
    exam_question_count: cert ? 60 : null, exam_duration_minutes: cert ? 90 : null,
  };
}

const ALL = [
  track('track01', 'Python Básico', false),
  track('track13', 'Ciberseguridad', false),
  track('track04', 'Ingeniería de Software', false),
  track('track40', 'ISC2 CC', true),
  track('track42', 'Security+', true),
  track('track08', 'AWS CLF', true),
];

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
  tracks.mockResolvedValue(ALL);
  curriculum.mockRejectedValue(new Error('sin currículo en este test'));
  dashboard.mockResolvedValue({ tracks: [] });
  useAppStore.setState({ selectedTrackId: null, activeTrackId: null, tracksBrowse: true });
});
afterEach(cleanup);

async function openCatalogue() {
  render(<TracksScreen />);
  await screen.findByText('Python Básico');
  return screen.getByRole('group', { name: 'Campo' });
}

const names = () =>
  ['Python Básico', 'Ciberseguridad', 'Ingeniería de Software', 'ISC2 CC', 'Security+', 'AWS CLF'].filter((n) => screen.queryByText(n));

describe('catálogo por campos', () => {
  it('«Seguridad y redes» deja solo sus rutas, de los dos tipos', async () => {
    const fields = await openCatalogue();
    fireEvent.click(within(fields).getByRole('button', { name: /Seguridad y redes/ }));
    expect(within(fields).getByRole('button', { name: /Seguridad y redes/ })).toHaveAttribute('aria-pressed', 'true');
    expect(names()).toEqual(['Ciberseguridad', 'ISC2 CC', 'Security+']);
  });

  it('campo y tipo se combinan: Seguridad + Certificaciones', async () => {
    const fields = await openCatalogue();
    fireEvent.click(within(fields).getByRole('button', { name: /Seguridad y redes/ }));
    fireEvent.click(screen.getByRole('tab', { name: /Certificaciones/ }));
    expect(names()).toEqual(['ISC2 CC', 'Security+']);
  });

  it('con Certificaciones, «Desarrollo de software» no se ofrece (no tiene ninguna)', async () => {
    const fields = await openCatalogue();
    expect(within(fields).getByRole('button', { name: /Desarrollo de software/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('tab', { name: /Certificaciones/ }));
    expect(within(fields).queryByRole('button', { name: /Desarrollo de software/ })).toBeNull();
  });

  it('cada chip lleva su recuento', async () => {
    const fields = await openCatalogue();
    expect(within(fields).getByRole('button', { name: /Todos los campos/ })).toHaveTextContent('6');
    expect(within(fields).getByRole('button', { name: /Seguridad y redes/ })).toHaveTextContent('3');
    expect(within(fields).getByRole('button', { name: /Cloud e infraestructura/ })).toHaveTextContent('1');
    // Con un campo puesto, «Todos los campos» sigue contando todos (no los del campo).
    fireEvent.click(within(fields).getByRole('button', { name: /Seguridad y redes/ }));
    expect(within(fields).getByRole('button', { name: /Todos los campos/ })).toHaveTextContent('6');
  });
});
