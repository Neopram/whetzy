/** Toast: el icono no se lee en voz alta y el mensaje llega entero. */
import { afterEach, describe, expect, it } from 'vitest';
import { act, cleanup, render, screen } from '@testing-library/react';
import { showToast, Toast } from '../components/common/Toast';

afterEach(cleanup);

describe('Toast', () => {
  it('el emoji va aparte con aria-hidden; el texto, en la región viva', () => {
    render(<Toast />);
    act(() => showToast('Algo falló', 'error'));
    const region = screen.getByRole('status');
    expect(region).toHaveTextContent('Algo falló');
    const icon = screen.getByText('❌', { exact: false });
    expect(icon).toHaveAttribute('aria-hidden', 'true');
    expect(icon).not.toBe(region);
  });

  it('info no lleva icono', () => {
    render(<Toast />);
    act(() => showToast('Aviso', 'info'));
    expect(screen.getByRole('status').textContent).toBe('Aviso');
  });
});
