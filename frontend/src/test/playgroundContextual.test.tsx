/**
 * 43.7 (ADR-65 D9): el playground se abre desde la lección con su ejemplo, y
 * el fragmento que el alumno deja por skill reaparece la vez siguiente.
 *
 * Antes: el playground era una herramienta suelta en Hoy que siempre abría
 * «Hello, Whetzy!» en Python, sin relación con lo que se estaba estudiando.
 */
import 'fake-indexeddb/auto';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { LessonScreen } from '../pages/LessonScreen';
import { PlaygroundScreen } from '../pages/PlaygroundScreen';
import { useAppStore } from '../stores/useAppStore';
import { lessonsApi, type LessonRead } from '../services/api';
import { clearPlaygroundHistory, getPlaygroundHistory, savePlaygroundEntry } from '../services/playgroundDb';

const runCode = vi.fn();
vi.mock('../hooks/useRuntime', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../hooks/useRuntime')>();
  return { ...actual, useRuntime: () => ({ status: 'ready', runCode }) };
});
vi.mock('../components/quiz/MonacoCodeEditor', () => ({
  MonacoCodeEditor: ({ value, onChange }: { value: string; onChange: (v: string) => void }) => (
    <textarea aria-label="code" value={value} onChange={(e) => onChange(e.target.value)} />
  ),
}));
vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, lessonsApi: { forSkill: vi.fn() } };
});

const m = (f: unknown) => f as ReturnType<typeof vi.fn>;

const lesson = (over: Partial<LessonRead> = {}): LessonRead => ({
  id: 'l1', skill_id: 'sk1', title_es: 'Consultas', title_en: 'Queries',
  body_es: 'Una consulta.', body_en: 'A query.',
  example_code: 'SELECT 42 AS answer;', example_output: '42', code_runtime: 'sql',
  source: 'SQLite docs — https://sqlite.org/lang_select.html', order: 1, ...over,
});

async function toCodeStep() {
  await screen.findByRole('progressbar');
  // El ejemplo va en el último paso.
  for (let i = 0; i < 5; i++) fireEvent.keyDown(window, { key: 'ArrowRight' });
  await screen.findByText(/SELECT 42/);
}

const editor = () => screen.getByLabelText('code') as HTMLTextAreaElement;

beforeEach(async () => {
  vi.clearAllMocks();
  // jsdom no implementa scrollIntoView; el playground lo llama al terminar.
  Element.prototype.scrollIntoView = vi.fn();
  await i18n.changeLanguage('es');
  await clearPlaygroundHistory();
  useAppStore.setState({ playgroundSeed: null, lessonReturn: null, currentScreen: 'lesson' });
});
afterEach(cleanup);

describe('Lección → «Probar este código»', () => {
  it('abre el playground con el ejemplo, su runtime y su skill', async () => {
    m(lessonsApi.forSkill).mockResolvedValue([lesson()]);
    render(<LessonScreen skillId="sk1" onExit={() => {}} />);
    await toCodeStep();
    fireEvent.click(screen.getByRole('button', { name: /Probar este código/ }));
    const s = useAppStore.getState();
    expect(s.currentScreen).toBe('playground');
    expect(s.playgroundSeed).toEqual({ runtime: 'sql', code: 'SELECT 42 AS answer;', skillId: 'sk1' });
  });

  it('al volver del playground, la lección sigue en el paso del ejemplo', async () => {
    m(lessonsApi.forSkill).mockResolvedValue([lesson()]);
    const { unmount } = render(<LessonScreen skillId="sk1" onExit={() => {}} />);
    await toCodeStep();
    const bar = screen.getByRole('progressbar');
    const at = bar.getAttribute('aria-valuenow');
    fireEvent.click(screen.getByRole('button', { name: /Probar este código/ }));
    unmount();
    render(<LessonScreen skillId="sk1" onExit={() => {}} />);
    await screen.findByText(/SELECT 42/);
    expect(screen.getByRole('progressbar').getAttribute('aria-valuenow')).toBe(at);
  });

  it('sin runtime (shell, YAML…) no se ofrece', async () => {
    m(lessonsApi.forSkill).mockResolvedValue([lesson({ example_code: 'ls -la', code_runtime: null })]);
    render(<LessonScreen skillId="sk1" onExit={() => {}} />);
    await screen.findByRole('progressbar');
    for (let i = 0; i < 5; i++) fireEvent.keyDown(window, { key: 'ArrowRight' });
    await screen.findByText(/ls -la/);
    expect(screen.queryByRole('button', { name: /Probar este código/ })).toBeNull();
  });
});

describe('Playground abierto desde una lección', () => {
  it('muestra el ejemplo en su runtime y guarda lo ejecutado con la skill', async () => {
    useAppStore.setState({ playgroundSeed: { runtime: 'sql', code: 'SELECT 42 AS answer;', skillId: 'sk1' } });
    runCode.mockResolvedValue({ output: '42', error: null, timedOut: false });
    render(<PlaygroundScreen />);
    await waitFor(() => expect(editor().value).toBe('SELECT 42 AS answer;'));
    expect(screen.getByRole('button', { name: /SQL/ }).className).toMatch(/tabActive/);
    fireEvent.change(editor(), { target: { value: 'SELECT 7;' } });
    fireEvent.click(screen.getByRole('button', { name: /Ejecutar/ }));
    await waitFor(async () => {
      const [last] = await getPlaygroundHistory('sql', 1);
      expect(last?.code).toBe('SELECT 7;');
      expect(last?.skill_id).toBe('sk1');
    });
  });

  it('el fragmento guardado de la skill reaparece, y se puede volver al ejemplo', async () => {
    await savePlaygroundEntry({
      runtime: 'sql', code: 'SELECT 7;', output: '7', error: null,
      timestamp: new Date().toISOString(), skill_id: 'sk1',
    });
    await savePlaygroundEntry({
      runtime: 'sql', code: 'SELECT otra;', output: '', error: null,
      timestamp: new Date(Date.now() + 1000).toISOString(), skill_id: 'sk2',
    });
    useAppStore.setState({ playgroundSeed: { runtime: 'sql', code: 'SELECT 42 AS answer;', skillId: 'sk1' } });
    render(<PlaygroundScreen />);
    await waitFor(() => expect(editor().value).toBe('SELECT 7;'));
    fireEvent.click(screen.getByRole('button', { name: /Volver al ejemplo/ }));
    expect(editor().value).toBe('SELECT 42 AS answer;');
  });

  it('«Volver» regresa a la lección, no a Hoy', async () => {
    useAppStore.setState({
      playgroundSeed: { runtime: 'sql', code: 'SELECT 1;', skillId: 'sk1' },
      currentScreen: 'playground', previousScreen: 'lesson',
    });
    render(<PlaygroundScreen />);
    fireEvent.click(screen.getByRole('button', { name: 'Volver', exact: true }));
    expect(useAppStore.getState().currentScreen).toBe('lesson');
  });
});
