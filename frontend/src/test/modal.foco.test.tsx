/**
 * Revisión de UI del 2026-10-23: el efecto del modal dependía de `onClose`, y
 * quien lo usa (UsersPanel) le pasa una función nueva en cada render. Al
 * escribir en el modal el efecto se repetía y el foco saltaba al ✕ a cada
 * tecla. Además el diálogo no tenía nombre accesible ni retenía el Tab.
 */
import { useState } from 'react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { Modal } from '../components/common/Modal';

function Harness() {
  const [open, setOpen] = useState(true);
  const [reason, setReason] = useState('');
  return (
    <Modal open={open} onClose={() => { setOpen(false); }} title="Suspender cuenta">
      <label htmlFor="motivo">Motivo</label>
      <input id="motivo" value={reason} onChange={(e) => setReason(e.target.value)} />
      <button type="button">Confirmar</button>
    </Modal>
  );
}

beforeEach(async () => { await i18n.changeLanguage('es'); });
afterEach(cleanup);

describe('Modal — foco estable y diálogo con nombre', () => {
  it('escribir en un campo no le roba el foco aunque onClose cambie en cada render', () => {
    render(<Harness />);
    const input = screen.getByLabelText('Motivo');
    input.focus();
    fireEvent.change(input, { target: { value: 'spam' } });
    fireEvent.change(input, { target: { value: 'spam repetido' } });
    expect(document.activeElement).toBe(input);
  });

  it('el diálogo se llama como su título', () => {
    render(<Harness />);
    expect(screen.getByRole('dialog', { name: 'Suspender cuenta' })).toBeInTheDocument();
  });

  it('Tab desde el último control vuelve al primero (no se escapa del modal)', () => {
    render(<Harness />);
    const last = screen.getByRole('button', { name: 'Confirmar' });
    last.focus();
    fireEvent.keyDown(document, { key: 'Tab' });
    expect(document.activeElement).toBe(screen.getByRole('button', { name: i18n.t('quiz.close') }));
  });
});
