/**
 * 43.6 (ADR-65 D8): Proyectos guarda el progreso en el servidor. Antes la
 * pantalla nunca llamaba a `start` ni a `submit-step`: el paso y el código
 * vivían en memoria y se perdían al salir.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { ProjectScreen } from '../pages/ProjectScreen';
import { useAppStore } from '../stores/useAppStore';
import { ApiError, projects as projectsApi, type ProjectDetail, type ProjectSubmissionRead } from '../services/api';

const runCode = vi.fn();
vi.mock('../hooks/useRuntime', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../hooks/useRuntime')>();
  return { ...actual, useRuntime: () => ({ status: 'ready', runCode }) };
});
// Monaco no carga en jsdom: un textarea con el mismo contrato.
vi.mock('../components/quiz/MonacoCodeEditor', () => ({
  MonacoCodeEditor: ({ value, onChange }: { value: string; onChange: (v: string) => void }) => (
    <textarea aria-label="code" value={value} onChange={(e) => onChange(e.target.value)} />
  ),
}));
vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    projects: { list: vi.fn(), get: vi.fn(), start: vi.fn(), progress: vi.fn(), submitStep: vi.fn() },
  };
});

const m = (f: unknown) => f as ReturnType<typeof vi.fn>;

const step = (n: number) => ({
  id: `s${n}`, step_number: n, title_es: `Paso ${n}`, title_en: `Step ${n}`,
  instructions_es: '', instructions_en: '', starter_code: `-- empieza ${n}`, test_code: `-- test ${n}`,
});

const project: ProjectDetail = {
  id: 'p1', slug: 'sql-pets', track_id: 'track06', runtime: 'sql', name_es: 'Mascotas', name_en: 'Pets',
  description_es: '', description_en: '', difficulty: 1, source_url: '', source_license: 'MIT', order: 1,
  steps: [step(1), step(2), step(3)],
};

const sub = (over: Partial<ProjectSubmissionRead> = {}): ProjectSubmissionRead => ({
  id: 'x', project_id: 'p1', current_step: 1, completed: false, started_at: '', completed_at: null,
  step_code: {}, verified: false, ...over,
});

async function open() {
  render(<ProjectScreen />);
  fireEvent.click(await screen.findByText('Mascotas'));
  return screen.findByText(/Paso \d: Paso/);
}

describe('Proyectos con progreso en el servidor', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    await i18n.changeLanguage('es');
    useAppStore.setState((s) => ({ user: { ...s.user, language: 'es' }, projectsTrackId: null }));
    m(projectsApi.list).mockResolvedValue([project]);
    m(projectsApi.get).mockResolvedValue(project);
  });
  afterEach(cleanup);

  it('retoma el paso y el código guardados', async () => {
    m(projectsApi.progress).mockResolvedValue(sub({ current_step: 2, step_code: { '1': 'uno', '2': 'a medias' } }));
    await open();
    expect(await screen.findByText('Paso 2: Paso 2')).toBeTruthy();
    expect((screen.getByLabelText('code') as HTMLTextAreaElement).value).toBe('a medias');
    // El 3 no se abre hasta pasar el 2.
    const tab3 = screen.getByRole('button', { name: '3' });
    expect((tab3 as HTMLButtonElement).disabled).toBe(true);
  });

  it('sin progreso, lo empieza', async () => {
    m(projectsApi.progress).mockRejectedValue(new ApiError('not started', 404));
    m(projectsApi.start).mockResolvedValue(sub());
    await open();
    await waitFor(() => expect(projectsApi.start).toHaveBeenCalledWith('sql-pets'));
  });

  it('si otra petición lo empezó a la vez (409), lee el progreso y sigue', async () => {
    // StrictMode en desarrollo, o dos pestañas: las dos ven 404 y las dos empiezan.
    m(projectsApi.progress)
      .mockRejectedValueOnce(new ApiError('not started', 404))
      .mockResolvedValue(sub());
    m(projectsApi.start).mockRejectedValue(new ApiError('already started', 409));
    await open();
    expect(await screen.findByText(/Tu progreso y tu código se guardan/)).toBeTruthy();
    expect(screen.queryByText(/No se pudo guardar el progreso/)).toBeNull();
  });

  it('el veredicto es el del servidor aunque el navegador diga que pasa', async () => {
    m(projectsApi.progress).mockResolvedValue(sub());
    runCode.mockResolvedValue({ output: '(no rows)', error: null, timedOut: false });
    m(projectsApi.submitStep).mockResolvedValue({
      ...sub(), step_passed: false, error: 'no such table: pets', timed_out: false,
    });
    await open();
    fireEvent.change(screen.getByLabelText('code'), { target: { value: 'SELECT 1;' } });
    fireEvent.click(screen.getByRole('button', { name: 'Probar' }));
    await waitFor(() => expect(projectsApi.submitStep).toHaveBeenCalledWith('sql-pets', 1, 'SELECT 1;', true));
    expect(await screen.findByText('no such table: pets')).toBeTruthy();
    expect(screen.queryByText('✅ ¡Todos los tests pasaron!')).toBeNull();
  });

  it('al pasar, avanza al paso que dice el servidor', async () => {
    m(projectsApi.progress).mockResolvedValue(sub());
    runCode.mockResolvedValue({ output: '', error: null, timedOut: false });
    m(projectsApi.submitStep).mockResolvedValue({
      ...sub({ current_step: 2, step_code: { '1': 'SELECT 1;' } }), step_passed: true, error: null, timed_out: false,
    });
    await open();
    fireEvent.click(screen.getByRole('button', { name: 'Probar' }));
    expect(await screen.findByText('✅ ¡Todos los tests pasaron!')).toBeTruthy();
    expect((screen.getByRole('button', { name: '3' }) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole('button', { name: '2' }) as HTMLButtonElement).disabled).toBe(false);
  });

  it('completado sin verificar avisa de que no cuenta como evidencia', async () => {
    m(projectsApi.get).mockResolvedValue({ ...project, runtime: 'python' });
    m(projectsApi.progress).mockResolvedValue(sub({ current_step: 3, completed: true, verified: false }));
    await open();
    expect(await screen.findByText(/no cuenta como evidencia/)).toBeTruthy();
  });

  it('abierta desde una ruta, la lista pide solo los de esa ruta', async () => {
    useAppStore.setState({ projectsTrackId: 'track06' });
    render(<ProjectScreen />);
    await screen.findByText('Mascotas');
    expect(projectsApi.list).toHaveBeenCalledWith('track06');
  });
});
