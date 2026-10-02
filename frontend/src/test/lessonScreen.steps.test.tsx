/**
 * Lección por pasos (design/v2): el cuerpo se reparte en tarjetas, ← / →
 * avanzan, la salida del ejemplo se ve solo al pedirla y el último paso
 * lleva a practicar. La fuente sale en todos los pasos.
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

describe('LessonScreen — pasos', () => {
  it('recorre los pasos con las flechas y termina en practicar', async () => {
    forSkill.mockResolvedValue([LESSON]);
    const onStartQuiz = vi.fn();
    render(<LessonScreen skillId="sk010101" onExit={() => {}} onStartQuiz={onStartQuiz} />);

    const bar = await screen.findByRole('progressbar');
    // El atajo ← / → se engancha en un useEffect, que corre después de pintar:
    // sin esperar, con carga la primera flecha se perdía (1 de cada 2 corridas).
    await act(async () => {});
    const total = Number(bar.getAttribute('aria-valuemax'));
    expect(total).toBeGreaterThanOrEqual(3);
    expect(screen.getByRole('link', { name: 'Python Docs' })).toHaveAttribute('href', 'https://docs.python.org/3/tutorial/');

    for (let i = 1; i < total; i++) fireEvent.keyDown(window, { key: 'ArrowRight' });
    expect(bar).toHaveAttribute('aria-valuenow', String(total));

    // Último paso: el ejemplo, con la salida tapada hasta pedirla (find*: la
    // tarjeta anterior sale animada antes de que entre la nueva).
    expect(await screen.findByText(/age = 25/)).toBeInTheDocument();
    expect(screen.queryByText('25', { selector: 'pre' })).not.toBeInTheDocument();
    fireEvent.click(await screen.findByRole('button', { name: /Ver la salida|Show the output/ }));
    expect(screen.getByText('25', { selector: 'pre' })).toBeInTheDocument();

    fireEvent.keyDown(window, { key: 'ArrowLeft' });
    expect(bar).toHaveAttribute('aria-valuenow', String(total - 1));
    fireEvent.keyDown(window, { key: 'ArrowRight' });

    fireEvent.click(screen.getByRole('button', { name: /Practicar ahora|Practise now/ }));
    expect(onStartQuiz).toHaveBeenCalledOnce();
  });
});
