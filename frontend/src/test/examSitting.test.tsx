/**
 * ExamSitting (design/v2, brief-msg2 §F): la vista en curso común a los tres
 * exámenes. La pregunta con ``` sale como bloque de código (antes, texto con
 * las comillas a la vista); la letra de la opción no entra en su nombre
 * accesible; «Marcar» y la cuadrícula llevan el estado de cada pregunta; y
 * entregar con preguntas en blanco pide confirmación.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { useState } from 'react';
import i18n from '../i18n';
import { ExamSitting } from '../components/exam/ExamSitting';
import type { QuestionPublic } from '../services/api';

const q = (id: string, text: string): QuestionPublic => ({
  id, skill_id: 's', type: 'mcq', difficulty_tier: 'easy', question_es: text, question_en: text,
  options_es: ['uno', 'dos'], options_en: ['one', 'two'], correct_answer_es: null, correct_answer_en: null,
} as unknown as QuestionPublic);

const QS = [q('q1', '¿Qué imprime?\n```python\nprint(1)\n```'), q('q2', 'Segunda'), q('q3', 'Tercera')];

function Harness({ onSubmit }: { onSubmit: () => void }) {
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  return (
    <ExamSitting
      title="Simulacro" questions={QS} index={index} onGo={setIndex} answers={answers}
      onChoose={(id, i) => setAnswers((a) => ({ ...a, [id]: i }))}
      secondsLeft={600} grading={false} error={null} onSubmit={onSubmit}
    />
  );
}

beforeEach(async () => { await i18n.changeLanguage('es'); });
afterEach(cleanup);

describe('ExamSitting', () => {
  it('pinta el código como bloque y deja la letra fuera del nombre de la opción', () => {
    render(<Harness onSubmit={() => {}} />);
    expect(screen.getByText('print(1)').closest('pre')).not.toBeNull();
    expect(screen.queryByText(/```/)).not.toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'uno' })).toBeInTheDocument();
  });

  it('marca, salta por la cuadrícula y lleva la cuenta', () => {
    render(<Harness onSubmit={() => {}} />);
    fireEvent.click(screen.getByRole('radio', { name: 'uno' }));
    fireEvent.click(screen.getByRole('button', { name: 'Marcar para revisar' }));
    expect(screen.getByRole('button', { name: 'Marcada para revisar' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText('Respondidas 1/3 · Marcadas 1')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Pregunta 3: sin responder' }));
    expect(screen.getByText('Pregunta 3 de 3')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Pregunta 1: marcada para revisar' })).toBeInTheDocument();

    // Una segunda marca se suma a la primera, no la sustituye.
    fireEvent.click(screen.getByRole('button', { name: 'Marcar para revisar' }));
    expect(screen.getByText('Respondidas 1/3 · Marcadas 2')).toBeInTheDocument();
  });

  it('con preguntas en blanco, entregar pide confirmación; «Seguir respondiendo» no entrega', () => {
    const onSubmit = vi.fn();
    render(<Harness onSubmit={onSubmit} />);
    fireEvent.click(screen.getByRole('button', { name: 'Pregunta 3: sin responder' }));
    fireEvent.click(screen.getByRole('button', { name: 'ENTREGAR' }));
    const dialog = screen.getByRole('alertdialog');
    expect(within(dialog).getByText(/Quedan 3 preguntas sin responder/)).toBeInTheDocument();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Seguir respondiendo' }));
    expect(onSubmit).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'ENTREGAR' }));
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Entregar igualmente' }));
    expect(onSubmit).toHaveBeenCalledOnce();
  });

  it('con todo respondido, entrega sin preguntar', () => {
    const onSubmit = vi.fn();
    render(<Harness onSubmit={onSubmit} />);
    for (let i = 0; i < 3; i++) {
      fireEvent.click(screen.getByRole('radio', { name: 'dos' }));
      if (i < 2) fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
    }
    fireEvent.click(screen.getByRole('button', { name: 'ENTREGAR' }));
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
    expect(onSubmit).toHaveBeenCalledOnce();
  });
});
