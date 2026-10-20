import { test, expect } from '@playwright/test';
import { registerUser, uniqueUsername } from './helpers';

/**
 * 46.2c: el audio se crea dentro del primer toque y, al encender «Sonidos» en
 * Perfil, suena una muestra en ese mismo toque. Se cuenta con un AudioContext
 * instrumentado: osciladores que arrancan y estado del contexto.
 */
test('Perfil: encender «Sonidos» suena una muestra (46.2c)', async ({ page }) => {
  await page.addInitScript(() => {
    const fx = { contexts: 0, oscStarts: 0, states: [] as string[] };
    (window as unknown as { __fx: typeof fx }).__fx = fx;
    const Orig = window.AudioContext;
    window.AudioContext = class extends Orig {
      constructor(...a: ConstructorParameters<typeof AudioContext>) { super(...a); fx.contexts++; }
      createOscillator() {
        const o = super.createOscillator();
        const start = o.start.bind(o);
        o.start = (...x: [number?]) => { fx.oscStarts++; fx.states.push(this.state); start(...x); };
        return o;
      }
    } as typeof AudioContext;
  });
  await registerUser(page, { username: uniqueUsername('e2e_snd_'), displayName: 'Sonido' });
  const fx = () => page.evaluate(() => (window as unknown as { __fx: { contexts: number; oscStarts: number; states: string[] } }).__fx);

  // `registerUser` acaba recargando: esta página aún no ha visto ningún toque.
  expect((await fx()).contexts).toBe(0);
  // El primer toque (ir a «Yo», el perfil) crea el contexto: sonido encendido por defecto.
  await page.getByRole('button', { name: 'Yo', exact: true }).click();
  expect((await fx()).contexts).toBe(1);
  const sound = page.getByRole('switch', { name: 'Sonidos' });
  await expect(sound).toHaveAttribute('aria-checked', 'true');
  await sound.click(); // apagar: ninguna muestra
  await expect(sound).toHaveAttribute('aria-checked', 'false');
  expect((await fx()).oscStarts).toBe(0);
  await sound.click(); // encender: muestra en el mismo toque
  await expect(sound).toHaveAttribute('aria-checked', 'true');
  const after = await fx();
  expect(after.oscStarts).toBe(2); // C5 → E5, el sonido de un acierto
  expect(after.states.every((s) => s === 'running')).toBe(true);
});
