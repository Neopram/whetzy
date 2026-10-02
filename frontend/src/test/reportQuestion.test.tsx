/**
 * «Reportar un problema» (P.6): el backend existía y ninguna pantalla lo usaba.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { ReportQuestion } from '../components/quiz/ReportQuestion';
import { reports } from '../services/api';

beforeEach(async () => {
  await i18n.changeLanguage('es');
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('ReportQuestion', () => {
  it('manda el motivo elegido y la nota, y da las gracias', async () => {
    const send = vi.spyOn(reports, 'question').mockResolvedValue({ id: 'r', message: 'ok' });
    render(<ReportQuestion questionId="q42" />);

    fireEvent.click(screen.getByRole('button', { name: 'Reportar un problema con esta pregunta' }));
    fireEvent.click(screen.getByRole('radio', { name: 'Está desactualizada' }));
    fireEvent.change(screen.getByRole('textbox', { name: 'Detalle (opcional)' }), { target: { value: 'Python 3.13 lo cambió' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enviar' }));

    expect(await screen.findByText('Gracias: lo revisamos.')).toBeInTheDocument();
    expect(send).toHaveBeenCalledWith('q42', 'outdated', 'Python 3.13 lo cambió');
  });

  it('si falla lo dice y deja reintentar', async () => {
    const send = vi.spyOn(reports, 'question').mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce({ id: 'r', message: 'ok' });
    render(<ReportQuestion questionId="q42" />);
    fireEvent.click(screen.getByRole('button', { name: 'Reportar un problema con esta pregunta' }));
    fireEvent.click(screen.getByRole('button', { name: 'Enviar' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo enviar');
    fireEvent.click(screen.getByRole('button', { name: 'Enviar' }));
    expect(await screen.findByText('Gracias: lo revisamos.')).toBeInTheDocument();
    expect(send).toHaveBeenCalledTimes(2);
  });
});
