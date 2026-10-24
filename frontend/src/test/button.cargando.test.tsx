/**
 * 34.8 (axe en /_ui, 2026-10-24): con `loading`, el Button común pintaba solo el
 * spinner (aria-hidden) y se quedaba sin nombre accesible (axe button-name,
 * crítico). Lo usan Entrar, Olvidé/Restablecer, Borrar cuenta y la tienda de
 * protectores: mientras se envía, un lector de pantalla oía «botón» y nada más.
 */
import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { Button } from '../components/common/Button';

afterEach(cleanup);

describe('Button cargando', () => {
  it('conserva su nombre accesible y dice que está ocupado', () => {
    render(<Button loading>Entrar</Button>);
    const btn = screen.getByRole('button', { name: 'Entrar' });
    expect(btn).toBeDisabled();
    expect(btn).toHaveAttribute('aria-busy', 'true');
  });

  it('sin cargar, no lleva aria-busy', () => {
    render(<Button>Entrar</Button>);
    expect(screen.getByRole('button', { name: 'Entrar' })).not.toHaveAttribute('aria-busy');
  });
});
