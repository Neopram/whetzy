/**
 * Plantilla de lección con formato (39.14, ADR-50d): cada sección lleva un
 * icono, decorativo y por tanto `aria-hidden`, sin reescribir el texto de
 * la lección. El contenido real de `lessonSteps.test.tsx`/`.steps.test.tsx`
 * no cambia: esto solo comprueba el marcado nuevo alrededor.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import '../i18n';
import { LessonScreen } from '../pages/LessonScreen';
import { lessonsApi, type LessonRead } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return { ...actual, lessonsApi: { forSkill: vi.fn() } };
});

const forSkill = lessonsApi.forSkill as unknown as ReturnType<typeof vi.fn>;
afterEach(cleanup);

const sentence = 'Una variable es un nombre que apunta a un valor guardado en memoria del programa. ';
const LESSON: LessonRead = {
  id: 'l1', skill_id: 'sk010101', title_es: 'Variables', title_en: 'Variables',
  body_es: sentence.repeat(10).trim(), body_en: sentence.repeat(10).trim(),
  example_code: 'age = 25\nprint(age)', example_output: '25',
  source: 'Python Docs — https://docs.python.org/3/tutorial/', order: 1,
};

function decorativeIcons() {
  return document.querySelectorAll('[aria-hidden="true"]');
}

describe('LessonScreen — icono accesible por sección (39.14)', () => {
  it('el paso de concepto no reescribe el texto y su icono es decorativo', async () => {
    forSkill.mockResolvedValue([LESSON]);
    await act(async () => { render(<LessonScreen skillId="sk010101" onExit={() => {}} />); });
    await screen.findByRole('progressbar');

    // El texto de la lección sigue verbatim — no se tocó contenido.
    expect(screen.getByText(sentence.trim(), { exact: false })).toBeInTheDocument();

    const icons = [...decorativeIcons()].map((n) => n.textContent);
    expect(icons).toContain('💡');
  });

  it('el paso de ejemplo marca su icono y el de la salida como decorativos', async () => {
    forSkill.mockResolvedValue([LESSON]);
    // Dentro de act: forSkill resuelve en una microtarea y el efecto que
    // engancha el listener de ← / → con el número real de pasos tiene que haber
    // corrido antes de pulsar; si no, con carga, las flechas llegan al listener
    // viejo (sin pasos) y el test falla al azar.
    await act(async () => { render(<LessonScreen skillId="sk010101" onExit={() => {}} />); });
    const bar = await screen.findByRole('progressbar');
    const total = Number(bar.getAttribute('aria-valuemax'));
    for (let i = 1; i < total; i++) fireEvent.keyDown(window, { key: 'ArrowRight' });

    expect(await screen.findByText(/age = 25/)).toBeInTheDocument();
    expect([...decorativeIcons()].map((n) => n.textContent)).toContain('🧪');

    fireEvent.click(await screen.findByRole('button', { name: /Ver la salida|Show the output/ }));
    expect(screen.getByText('25', { selector: 'pre' })).toBeInTheDocument();
    expect([...decorativeIcons()].map((n) => n.textContent)).toContain('📤');
  });

  it('el icono de la fuente no cambia el nombre accesible del enlace', async () => {
    forSkill.mockResolvedValue([LESSON]);
    await act(async () => { render(<LessonScreen skillId="sk010101" onExit={() => {}} />); });
    await screen.findByRole('progressbar');

    expect([...decorativeIcons()].map((n) => n.textContent)).toContain('🔗');
    // Mismo nombre accesible que antes de añadir el icono (lessonScreen.steps.test.tsx).
    expect(screen.getByRole('link', { name: 'Python Docs' })).toHaveAttribute(
      'href', 'https://docs.python.org/3/tutorial/',
    );
  });
});
