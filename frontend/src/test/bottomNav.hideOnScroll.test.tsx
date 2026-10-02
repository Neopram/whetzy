/**
 * La barra inferior tapaba siempre el pie de cada pantalla. Ahora se aparta al
 * bajar y vuelve al subir, arriba del todo o con el foco del teclado.
 */
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import '../i18n';
import { BottomNav } from '../components/layout/BottomNav';

function scrollTo(y: number) {
  Object.defineProperty(window, 'scrollY', { value: y, configurable: true });
  window.dispatchEvent(new Event('scroll'));
}
const frame = () => act(() => new Promise<void>((r) => requestAnimationFrame(() => r())));

beforeEach(() => {
  Object.defineProperty(window, 'innerHeight', { value: 800, configurable: true });
  Object.defineProperty(document.documentElement, 'scrollHeight', { value: 4000, configurable: true });
  scrollTo(0);
});
afterEach(cleanup);

const nav = () => screen.getByRole('navigation', { name: 'Main navigation' });

describe('BottomNav — se aparta al leer', () => {
  it('bajar la esconde; subir la devuelve', async () => {
    render(<BottomNav />);
    expect(nav()).not.toHaveAttribute('data-hidden');
    scrollTo(400); await frame();
    expect(nav()).toHaveAttribute('data-hidden', 'true');
    scrollTo(300); await frame();
    expect(nav()).not.toHaveAttribute('data-hidden');
  });

  it('arriba del todo y al final de la página está siempre visible', async () => {
    render(<BottomNav />);
    scrollTo(400); await frame();
    scrollTo(30); await frame();
    expect(nav()).not.toHaveAttribute('data-hidden');
    scrollTo(3200); await frame(); // 800 + 3200 = 4000: final de la página
    expect(nav()).not.toHaveAttribute('data-hidden');
  });

  it('con el foco del teclado dentro no se esconde', async () => {
    render(<BottomNav />);
    scrollTo(400); await frame();
    expect(nav()).toHaveAttribute('data-hidden', 'true');
    fireEvent.focus(screen.getAllByRole('button')[0]);
    expect(nav()).not.toHaveAttribute('data-hidden');
  });
});
