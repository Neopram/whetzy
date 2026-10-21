/**
 * 46.14 (docs/PLAN_UI_AVANZADA.md §7.4): las páginas sueltas entran con la
 * transición de eje. `PageEnter` desliza y funde; con `fade={false}` (la
 * landing prerenderizada) solo desliza, para no ocultar nunca el hero del LCP.
 * Con movimiento reducido no hay animación.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { PageEnter } from '../components/common/PageEnter';

const motionPrefs = vi.hoisted(() => ({ reduce: false }));
vi.mock('framer-motion', async (importOriginal) => {
  const actual = await importOriginal<typeof import('framer-motion')>();
  return { ...actual, useReducedMotion: () => motionPrefs.reduce };
});

beforeEach(() => { motionPrefs.reduce = false; });
afterEach(cleanup);

const wrapper = () => screen.getByText('contenido').parentElement as HTMLElement;

describe('PageEnter (46.14)', () => {
  it('entra desde opacidad 0 y 8 px abajo, y marca data-fx="enter"', () => {
    render(<PageEnter><p>contenido</p></PageEnter>);
    expect(wrapper()).toHaveAttribute('data-fx', 'enter');
    expect(wrapper().style.opacity).toBe('0');
    expect(wrapper().style.transform).toContain('translateY(8px)');
  });

  it('con fade={false} no toca la opacidad: el contenido (el LCP) nunca se oculta', () => {
    render(<PageEnter fade={false}><p>contenido</p></PageEnter>);
    expect(wrapper()).toHaveAttribute('data-fx', 'enter');
    expect(wrapper().style.opacity).not.toBe('0');
    expect(wrapper().style.transform).toContain('translateY(8px)');
  });

  it('con movimiento reducido no hay animación: ni atributo ni estado inicial', () => {
    motionPrefs.reduce = true;
    render(<PageEnter><p>contenido</p></PageEnter>);
    expect(wrapper()).not.toHaveAttribute('data-fx');
    expect(wrapper().style.opacity).not.toBe('0');
    expect(wrapper().style.transform || 'none').toMatch(/none|translateY\(0/);
  });
});
