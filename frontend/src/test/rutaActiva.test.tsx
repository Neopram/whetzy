/**
 * 43.4 (ADR-65 D5/D6): ruta activa y Hoy filtrado por ella.
 *
 * Antes Hoy pedía `/progress/skills` y `/progress/decaying` sin ruta y el
 * «Estudiar ahora» arrancaba sin `track_id`: mezclaba las skills de todas las
 * rutas. Y no había forma de elegir «mi ruta» fuera del onboarding.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import i18n from '../i18n';
import { HomeScreen } from '../pages/HomeScreen';
import { TracksScreen } from '../pages/TracksScreen';
import { useAppStore } from '../stores/useAppStore';
import { auth, content, exams, gamification, progress as progressApi, type TrackRead } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    auth: { ...actual.auth, updateMe: vi.fn() },
    content: { ...actual.content, tracks: vi.fn() },
    exams: { ...actual.exams, trackBlueprint: vi.fn() },
    progress: {
      ...actual.progress, dashboard: vi.fn(), decaying: vi.fn(), skills: vi.fn(), curriculum: vi.fn(),
    },
    gamification: { ...actual.gamification, missions: vi.fn() },
  };
});

const m = (f: unknown) => f as ReturnType<typeof vi.fn>;

const track = (id: string, name: string): TrackRead => ({
  id, name_es: name, name_en: name, order: 1, icon: '·', color: '#000', total_questions: 10,
  is_certification: false, cert_provider: null, exam_question_count: null, exam_duration_minutes: null,
});

const mastery = (track_id: string, name: string, mastered: number) => ({
  track_id, name_es: name, name_en: name, icon: '·', color: '#000',
  average_mastery: mastered ? 0.5 : 0, skills_mastered: mastered, total_skills: 10,
});

beforeEach(async () => {
  vi.clearAllMocks();
  await i18n.changeLanguage('es');
  useAppStore.setState((s) => ({ user: { ...s.user, language: 'es' }, activeTrackId: 'track13' }));
  m(progressApi.dashboard).mockResolvedValue({
    level: 1, total_xp: 0, current_streak: 0, max_streak: 0, streak_freeze_available: 0,
    last_active: null, reviews_due: 0, total_sessions: 3,
    tracks: [mastery('track13', 'Ciberseguridad', 1), mastery('track01', 'Python Básico', 2)],
  });
  m(progressApi.decaying).mockResolvedValue([]);
  m(progressApi.skills).mockResolvedValue([]);
  m(progressApi.curriculum).mockResolvedValue({ track_id: 'track01', modules: [] });
  m(gamification.missions).mockReturnValue(new Promise(() => {}));
  m(exams.trackBlueprint).mockReturnValue(new Promise(() => {}));
  m(content.tracks).mockResolvedValue([track('track01', 'Python Básico'), track('track13', 'Ciberseguridad')]);
  m(auth.updateMe).mockResolvedValue({});
});
afterEach(cleanup);

describe('Hoy de la ruta activa (D6)', () => {
  it('pide skills y repasos solo de la ruta activa y la nombra arriba', async () => {
    render(<HomeScreen />);
    await waitFor(() => expect(progressApi.skills).toHaveBeenCalledWith('track13'));
    expect(progressApi.decaying).toHaveBeenCalledWith(7, 5, 'track13');
    expect(await screen.findByTestId('home-active-track')).toHaveTextContent('Tu ruta: Ciberseguridad');
    // La activa no se repite en «Otras rutas en curso».
    expect(await screen.findByText('Otras rutas en curso')).toBeTruthy();
    expect(screen.getByText('Python Básico')).toBeTruthy();
    expect(screen.queryAllByText('Ciberseguridad')).toHaveLength(0);
  });

  it('«Estudiar ahora» arranca la sesión en la ruta activa', async () => {
    const startQuiz = vi.fn();
    useAppStore.setState({ startQuiz });
    render(<HomeScreen />);
    fireEvent.click(await screen.findByRole('button', { name: 'ESTUDIAR AHORA' }));
    expect(startQuiz).toHaveBeenCalledWith('study', 10, { trackId: 'track13' });
  });

  it('«Cambiar» abre el catálogo de rutas', async () => {
    render(<HomeScreen />);
    fireEvent.click(await screen.findByRole('button', { name: 'Cambiar' }));
    expect(useAppStore.getState().currentScreen).toBe('tracks');
    expect(useAppStore.getState().tracksBrowse).toBe(true);
  });
});

describe('Hacer esta mi ruta (D5)', () => {
  it('cambia la ruta activa en el servidor y, sin progreso, ofrece su prueba de nivel', async () => {
    const startPlacement = vi.fn();
    useAppStore.setState({ selectedTrackId: 'track01', startPlacement, tracksBrowse: false });
    render(<TracksScreen />);
    fireEvent.click(await screen.findByRole('button', { name: 'Hacer esta mi ruta' }));

    expect(useAppStore.getState().activeTrackId).toBe('track01');
    expect(auth.updateMe).toHaveBeenCalledWith({ target_track_id: 'track01' });
    expect(await screen.findByTestId('track-is-active')).toHaveTextContent('Es tu ruta');
    fireEvent.click(await screen.findByRole('button', { name: 'Hacer la prueba' }));
    expect(startPlacement).toHaveBeenCalledWith('track01');
  });
});
