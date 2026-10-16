/**
 * Serie 34 (coherencia visual), continuación de #214: las acciones de Perfil
 * (suscripción, cerrar sesión) y de Quiz (siguiente, resumen, error y el
 * aviso de salida) pintaban sus botones con clases propias, planas, distintas
 * del `Button` común. Esta guarda falla si alguna vuelve a su clase propia.
 * Quedan fuera los controles que no son acciones: opciones de respuesta,
 * conmutadores, idioma y filas de menú.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const PAGES = join(__dirname, '..', 'pages');
const read = (f: string) => readFileSync(join(PAGES, f), 'utf8');

const HAND_MADE: Record<string, string[]> = {
  ProfileScreen: ['proBtn', 'secondaryBtn', 'dangerBtn', 'signOut'],
  QuizScreen: ['btnNext', 'btnPrimary', 'btnStudy', 'btnGhost', 'btnLeave'],
};

describe('Perfil y Quiz usan el Button común en sus acciones', () => {
  for (const [screen, classes] of Object.entries(HAND_MADE)) {
    it(`${screen}.tsx importa el Button común`, () => {
      expect(read(`${screen}.tsx`)).toContain("from '../components/common/Button'");
    });

    for (const cls of classes) {
      it(`${screen}: sin la clase propia .${cls} (ni en el TSX ni en el CSS)`, () => {
        expect(read(`${screen}.tsx`)).not.toMatch(new RegExp(`styles\\.${cls}\\b`));
        expect(read(`${screen}.module.css`)).not.toMatch(new RegExp(`\\.${cls}\\b`));
      });
    }
  }
});
