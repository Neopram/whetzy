/**
 * 46.15 bloque E (plan §7.5): en el selector de plan del checkout, la opción
 * elegida se eleva; la transición respeta el movimiento reducido (global.css
 * apaga las transiciones). El verificador de 34.9 lo marcó pendiente
 * (2026-10-24). Se lee el CSS: jsdom no calcula estilos de módulos.
 */
import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const css = readFileSync(join(__dirname, '../pages/CheckoutScreen.module.css'), 'utf8');
// La última regla del selector: `.choice,\n.choiceOn {…}` va antes y es la común.
const rule = (sel: string) => [...css.matchAll(new RegExp(`\\n${sel.replace('.', '\\.')}\\s*\\{([^}]*)\\}`, 'g'))].at(-1)?.[1] ?? '';

describe('Checkout — la opción elegida se eleva', () => {
  it('choiceOn sube y lleva sombra de token', () => {
    expect(rule('.choiceOn')).toMatch(/transform:\s*translateY\(-\d+px\)/);
    expect(rule('.choiceOn')).toMatch(/box-shadow:\s*var\(--le-shadow-[a-z]+\)/);
  });

  it('el cambio se anima con una transición (que global.css apaga con movimiento reducido)', () => {
    expect(css).toMatch(/\.choice,\s*\n\.choiceOn\s*\{[^}]*transition:[^}]*transform/);
  });
});
