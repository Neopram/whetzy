/**
 * 43.6 (ADR-65 D8): el detalle de una ruta enseña la entrada a Proyectos solo
 * si la ruta tiene alguno, y abre la lista filtrada por esa ruta. Antes la
 * única entrada era la de Hoy, con todos los proyectos mezclados.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { TracksScreen } from '../pages/TracksScreen';
import { useAppStore } from '../stores/useAppStore';
import { content as contentApi, exams as examsApi, progress as progressApi, projects as projectsApi } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    content: { tracks: vi.fn() },
    exams: { ...actual.exams, trackBlueprint: vi.fn() },
    progress: { ...actual.progress, curriculum: vi.fn() },
    projects: { ...actual.projects, list: vi.fn() },
  };
});

const m = (f: unknown) => f as ReturnType<typeof vi.fn>;

const TRACK = {
  id: 'track06', name_es: 'SQL', name_en: 'SQL', order: 1, icon: '🗄️', color: '#000',
  total_questions: 10, is_certification: false, cert_provider: null,
  exam_question_count: null, exam_duration_minutes: null,
};

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
  useAppStore.setState({ selectedTrackId: 'track06', projectsTrackId: null, tracksBrowse: false, currentScreen: 'tracks' });
  m(contentApi.tracks).mockResolvedValue([TRACK]);
  m(examsApi.trackBlueprint).mockRejectedValue(new Error('sin blueprint'));
  m(progressApi.curriculum).mockResolvedValue({
    track_id: 'track06', name_es: 'SQL', name_en: 'SQL', icon: '', color: '', mastery_threshold: 0.95, modules: [],
  });
});
afterEach(cleanup);

describe('Rutas → Proyectos (43.6)', () => {
  it('con proyectos, la entrada abre Proyectos filtrado por la ruta', async () => {
    m(projectsApi.list).mockResolvedValue([{ id: 'p1', slug: 'sql-pets' }]);
    render(<TracksScreen />);
    const entry = await screen.findByTestId('track-projects');
    expect(entry.textContent).toContain('1 proyecto guiado');
    expect(projectsApi.list).toHaveBeenCalledWith('track06');
    fireEvent.click(entry);
    expect(useAppStore.getState().currentScreen).toBe('projects');
    expect(useAppStore.getState().projectsTrackId).toBe('track06');
  });

  it('sin proyectos, no hay entrada', async () => {
    m(projectsApi.list).mockResolvedValue([]);
    render(<TracksScreen />);
    await waitFor(() => expect(projectsApi.list).toHaveBeenCalledWith('track06'));
    expect(screen.queryByTestId('track-projects')).toBeNull();
  });

  it('ofrece el playground libre (43.7: sale de Hoy)', async () => {
    m(projectsApi.list).mockResolvedValue([]);
    render(<TracksScreen />);
    fireEvent.click(await screen.findByTestId('track-playground'));
    expect(useAppStore.getState().currentScreen).toBe('playground');
    expect(useAppStore.getState().playgroundSeed).toBeNull();
  });
});
