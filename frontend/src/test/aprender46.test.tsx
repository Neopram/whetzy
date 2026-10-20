/**
 * 46.15 bloque B (docs/PLAN_UI_AVANZADA.md §7.5): las pantallas de aprender.
 * - Rutas: la skill que subió de banda desde la última visita late una vez, y
 *   su módulo lo avisa aunque esté cerrado. La foto es de Rutas: si fuese la de
 *   Hoy, la pantalla que se abriese primero se comería la subida de la otra.
 * - Lección: el código del ejemplo se copia y dice «Copiado».
 * - Proyecto: cuando el servidor da el paso por bueno, efecto de acierto.
 * Con movimiento reducido no late nada (el «Copiado» sí sale: es texto).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { TracksScreen } from '../pages/TracksScreen';
import { LessonScreen } from '../pages/LessonScreen';
import { ProjectScreen } from '../pages/ProjectScreen';
import { bandMoments } from '../lib/homeMoments';
import { onFx, type FxEvent } from '../lib/feedbackFx';
import { useAppStore } from '../stores/useAppStore';
import {
  content as contentApi, exams as examsApi, lessonsApi, progress as progressApi,
  projects as projectsApi, type LessonRead, type ProjectDetail,
} from '../services/api';

let reduce = false;
vi.mock('framer-motion', async (importOriginal) => {
  const actual = await importOriginal<typeof import('framer-motion')>();
  return { ...actual, useReducedMotion: () => reduce };
});
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
  return {
    ...actual,
    content: { tracks: vi.fn() },
    exams: { ...actual.exams, trackBlueprint: vi.fn() },
    progress: { ...actual.progress, curriculum: vi.fn() },
    lessonsApi: { forSkill: vi.fn() },
    projects: { list: vi.fn(), get: vi.fn(), start: vi.fn(), progress: vi.fn(), submitStep: vi.fn() },
  };
});

const m = (f: unknown) => f as ReturnType<typeof vi.fn>;

beforeEach(async () => {
  vi.clearAllMocks();
  reduce = false;
  localStorage.clear();
  await i18n.changeLanguage('es');
  useAppStore.setState((s) => ({ user: { ...s.user, id: 'u1', language: 'es' }, projectsTrackId: null }));
});
afterEach(cleanup);

describe('foto de bandas por pantalla (46.15 B)', () => {
  it('Rutas tiene su propia foto: no se come la subida que Hoy aún no ha visto', () => {
    bandMoments('u1', [{ id: 'a', band: 'insufficient' }]);
    bandMoments('u1', [{ id: 'a', band: 'insufficient' }], 'tracks');
    expect(bandMoments('u1', [{ id: 'a', band: 'developing' }], 'tracks')).toEqual(['a']);
    expect(bandMoments('u1', [{ id: 'a', band: 'developing' }])).toEqual(['a']);
  });
});

// --- Rutas ---
const TRACK = {
  id: 'track01', name_es: 'Python', name_en: 'Python', order: 1, icon: '🐍', color: '#000',
  total_questions: 10, is_certification: false, cert_provider: null,
  exam_question_count: null, exam_duration_minutes: null,
};
const sk = (id: string, attempts: number) => ({
  skill_id: id, name_es: `Skill ${id}`, name_en: `Skill ${id}`, order: 1,
  p_known: 0.5, mastered: false, attempts, correct_count: Math.round(attempts * 0.6), lesson_seen: true,
});
function curriculum() {
  return {
    track_id: 'track01', name_es: 'Python', name_en: 'Python', icon: '🐍', color: '#000', mastery_threshold: 0.95,
    modules: [{
      id: 'm01', name_es: 'Módulo uno', name_en: 'Module one', order: 1, description_es: '', description_en: '',
      min_mastery_to_unlock: 0.7, level: 1, average_mastery: 0, status: 'available' as const,
      prerequisite_id: null, prerequisite_met: true, skills: [sk('a', 8), sk('b', 2)],
    }],
  };
}

async function openTracks() {
  m(contentApi.tracks).mockResolvedValue([TRACK]);
  m(examsApi.trackBlueprint).mockRejectedValue(new Error('sin blueprint'));
  m(progressApi.curriculum).mockResolvedValue(curriculum());
  m(projectsApi.list).mockResolvedValue([]);
  render(<TracksScreen />);
  return screen.findByRole('button', { expanded: false });
}

describe('Rutas — la skill que subió (46.15 B)', () => {
  it('el módulo lo avisa cerrado y, abierto, la banda de la skill late una vez', async () => {
    // «a» tenía evidencia insuficiente en la foto; ahora, con 8 respuestas, está en desarrollo.
    localStorage.setItem('whetzy_fx_bands_tracks_u1', JSON.stringify({ a: 'insufficient', b: 'insufficient' }));
    const header = await openTracks();
    await waitFor(() => expect(header).toHaveAttribute('data-fx', 'band-up'));
    fireEvent.click(header);
    const chips = await screen.findAllByTestId('skill-band');
    const up = chips.filter((c) => c.getAttribute('data-fx') === 'band-up');
    expect(up).toHaveLength(1);
    expect(up[0].closest('li')).toHaveTextContent('Skill a');
  });

  it('sin foto previa no late nada', async () => {
    const header = await openTracks();
    await waitFor(() => expect(localStorage.getItem('whetzy_fx_bands_tracks_u1')).not.toBeNull());
    expect(header).not.toHaveAttribute('data-fx');
  });

  it('con movimiento reducido no late, aunque haya subido', async () => {
    reduce = true;
    localStorage.setItem('whetzy_fx_bands_tracks_u1', JSON.stringify({ a: 'insufficient' }));
    const header = await openTracks();
    await waitFor(() => expect(localStorage.getItem('whetzy_fx_bands_tracks_u1')).toContain('developing'));
    expect(header).not.toHaveAttribute('data-fx');
  });
});

// --- Lección ---
const LESSON: LessonRead = {
  id: 'l1', skill_id: 'sk010101', title_es: 'Variables', title_en: 'Variables',
  body_es: 'Una variable es un nombre.', body_en: 'A variable is a name.',
  example_code: 'age = 25\nprint(age)', example_output: '25',
  source: 'Python Docs — https://docs.python.org/3/tutorial/', order: 1,
};

describe('Lección — copiar el ejemplo (46.15 B)', () => {
  it('copia el código y dice «Copiado»', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });
    m(lessonsApi.forSkill).mockResolvedValue([LESSON]);
    render(<LessonScreen skillId="sk010101" onExit={() => {}} />);
    await screen.findByRole('progressbar');
    await act(async () => {});
    fireEvent.keyDown(window, { key: 'ArrowRight' });
    fireEvent.click(await screen.findByRole('button', { name: 'Copiar código' }));
    expect(writeText).toHaveBeenCalledWith('age = 25\nprint(age)');
    expect(await screen.findByRole('status')).toHaveTextContent('Copiado');
  });
});

// --- Proyecto ---
const step = (n: number) => ({
  id: `s${n}`, step_number: n, title_es: `Paso ${n}`, title_en: `Step ${n}`,
  instructions_es: '', instructions_en: '', starter_code: `-- empieza ${n}`, test_code: `-- test ${n}`,
});
const project: ProjectDetail = {
  id: 'p1', slug: 'sql-pets', track_id: 'track06', runtime: 'sql', name_es: 'Mascotas', name_en: 'Pets',
  description_es: '', description_en: '', difficulty: 1, source_url: '', source_license: 'MIT', order: 1,
  steps: [step(1), step(2)],
};
const sub = (current_step: number) => ({
  id: 'x', project_id: 'p1', current_step, completed: false, started_at: '', completed_at: null,
  step_code: {}, verified: false,
});

async function runProjectTests(passed: boolean) {
  const seen: FxEvent[] = [];
  const off = onFx((e) => seen.push(e));
  m(projectsApi.list).mockResolvedValue([project]);
  m(projectsApi.get).mockResolvedValue(project);
  m(projectsApi.progress).mockResolvedValue(sub(1));
  runCode.mockResolvedValue({ output: '', error: null, timedOut: false });
  m(projectsApi.submitStep).mockResolvedValue({ ...sub(passed ? 2 : 1), step_passed: passed, error: null, timed_out: false });
  render(<ProjectScreen />);
  fireEvent.click(await screen.findByText('Mascotas'));
  await screen.findByText(/Paso 1: Paso 1/);
  fireEvent.click(screen.getByRole('button', { name: 'Probar' }));
  return { seen, off };
}

describe('Proyecto — paso aceptado (46.15 B)', () => {
  it('el servidor lo acepta: efecto de acierto y el aviso entra', async () => {
    const { seen, off } = await runProjectTests(true);
    const pass = await screen.findByText('✅ ¡Todos los tests pasaron!');
    expect(pass).toHaveAttribute('data-fx', 'pass');
    expect(seen.map((e) => e.type)).toContain('correct');
    off();
  });

  it('el servidor lo rechaza: ni efecto ni aviso', async () => {
    const { seen, off } = await runProjectTests(false);
    await waitFor(() => expect(projectsApi.submitStep).toHaveBeenCalled());
    expect(screen.queryByText('✅ ¡Todos los tests pasaron!')).toBeNull();
    expect(seen.map((e) => e.type)).not.toContain('correct');
    off();
  });
});
