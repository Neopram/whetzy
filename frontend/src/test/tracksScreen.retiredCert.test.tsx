/**
 * Aviso de certificaciones retiradas por su proveedor (39.24/39.25, solo
 * interfaz): insignia en el catálogo y aviso en el detalle para track43
 * (MLA-C01) y track45 (AI-900), nada para una ruta normal.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { TracksScreen } from '../pages/TracksScreen';
import { useAppStore } from '../stores/useAppStore';
import { content as contentApi, exams as examsApi, progress as progressApi } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    content: { tracks: vi.fn() },
    exams: { ...actual.exams, trackBlueprint: vi.fn() },
    progress: { ...actual.progress, curriculum: vi.fn(), dashboard: vi.fn() },
  };
});

const tracks = contentApi.tracks as unknown as ReturnType<typeof vi.fn>;
const trackBlueprint = examsApi.trackBlueprint as unknown as ReturnType<typeof vi.fn>;
const curriculum = progressApi.curriculum as unknown as ReturnType<typeof vi.fn>;
const dashboard = progressApi.dashboard as unknown as ReturnType<typeof vi.fn>;

const NORMAL = {
  id: 'track01', name_es: 'Python', name_en: 'Python', order: 1, icon: '🐍', color: '#000',
  total_questions: 10, is_certification: false, cert_provider: null,
  exam_question_count: null, exam_duration_minutes: null,
};

const RETIRED = {
  id: 'track43', name_es: 'AWS MLA', name_en: 'AWS MLA', order: 43, icon: '🤖', color: '#FF9900',
  total_questions: 300, is_certification: true, cert_provider: 'AWS',
  exam_question_count: 65, exam_duration_minutes: 130,
};

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
  tracks.mockResolvedValue([NORMAL, RETIRED]);
  trackBlueprint.mockRejectedValue(new Error('sin blueprint en este test'));
  curriculum.mockRejectedValue(new Error('sin curriculo en este test'));
  dashboard.mockResolvedValue({ tracks: [] });
  useAppStore.setState({ selectedTrackId: 'track01' });
});
afterEach(cleanup);

describe('TracksScreen — aviso de certificación retirada (39.24/39.25, UI)', () => {
  it('el catálogo marca con insignia solo la ruta retirada', async () => {
    render(<TracksScreen />);
    fireEvent.click(await screen.findByRole('button', { name: /todas las rutas/i }));
    await screen.findByText('AWS MLA');

    const items = screen.getAllByRole('button').filter((b) => /Python|AWS MLA/.test(b.textContent ?? ''));
    const normalItem = items.find((b) => b.textContent?.includes('Python'));
    const retiredItem = items.find((b) => b.textContent?.includes('AWS MLA'));
    expect(normalItem).not.toHaveTextContent(/examen retirado/i);
    expect(retiredItem).toHaveTextContent(/examen retirado/i);
  });

  it('el detalle no avisa para una ruta normal', async () => {
    render(<TracksScreen />);
    await screen.findByText('Python');
    expect(screen.queryByRole('status')).toBeNull();
  });

  it('el detalle avisa con el código y su sustituto para la ruta retirada', async () => {
    useAppStore.setState({ selectedTrackId: 'track43' });
    render(<TracksScreen />);
    const notice = await screen.findByRole('status');
    expect(notice).toHaveTextContent('MLA-C01');
    expect(notice).toHaveTextContent('MLA-C02');
  });

  it('en inglés, el aviso cita AI-900/AI-901 para track45', async () => {
    await i18n.changeLanguage('en');
    tracks.mockResolvedValue([{
      id: 'track45', name_es: 'Azure AI', name_en: 'Azure AI', order: 45, icon: '🤖', color: '#0078D4',
      total_questions: 300, is_certification: true, cert_provider: 'Microsoft',
      exam_question_count: 40, exam_duration_minutes: 85,
    }]);
    useAppStore.setState({ selectedTrackId: 'track45' });
    render(<TracksScreen />);
    const notice = await screen.findByRole('status');
    expect(notice).toHaveTextContent('AI-900');
    expect(notice).toHaveTextContent('AI-901');
  });
});
