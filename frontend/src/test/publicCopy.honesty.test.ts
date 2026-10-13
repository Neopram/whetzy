/**
 * Decisiones del dueño del 2026-10-12 sobre lo que la parte pública promete.
 *
 * - D-6: el certificado de los tracks de aprendizaje es gratis (ADR-49) y el
 *   código no pide plan (`track_exam.py`); la landing decía lo contrario.
 * - D-7: el plan Creador no se enseña mientras no exista el marketplace.
 * - D-8: el cupo «5 lecciones / 30 preguntas» no se promete con
 *   `FREE_DAILY_QUOTA_ENABLED` apagado.
 * - D-13: el motor es propietario (LICENSE); nada público dice «código abierto».
 * - El cobro de Paddle ya está en producción: «el cobro abre pronto» era falso.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import es from '../i18n/es/common.json';
import en from '../i18n/en/common.json';

const LANDING_SRC = readFileSync(join(process.cwd(), 'src/pages/LandingScreen.tsx'), 'utf8');
const EVIDENCE_SRC = readFileSync(join(process.cwd(), 'src/pages/EvidenceScreen.tsx'), 'utf8');

const BUNDLES = { es, en } as const;

function strings(node: unknown): string[] {
  if (typeof node === 'string') return [node];
  if (Array.isArray(node)) return node.flatMap(strings);
  if (node && typeof node === 'object') return Object.values(node).flatMap(strings);
  return [];
}

describe.each(Object.entries(BUNDLES))('copy público honesto (%s)', (_lang, bundle) => {
  const landing = strings(bundle.landing).join('\n');

  it('D-6: el plan gratis no niega el examen final ni el certificado', () => {
    expect(landing).not.toMatch(/sin examen final|no track final exam/i);
    expect(strings(bundle.landing.planFree).join(' ')).toMatch(/certifica/i);
  });

  it('D-6: Pro no vende como suyo el certificado que es gratis', () => {
    expect(strings(bundle.landing.planPro).join(' ')).not.toMatch(/certifica/i);
  });

  it('D-7: no hay plan Creador en la landing', () => {
    expect(Object.keys(bundle.landing)).not.toContain('planCreator');
    expect(LANDING_SRC).not.toContain('planCreator');
  });

  it('D-8: no se promete un cupo diario que no está encendido', () => {
    expect(landing).not.toMatch(/30 preguntas|30 new questions|5 lecciones|5 lessons/i);
  });

  it('D-13: nada público dice que el código es abierto', () => {
    const all = strings(bundle).join('\n');
    expect(all).not.toMatch(/c[óo]digo abierto|open[ -]?source/i);
    expect(EVIDENCE_SRC).not.toContain('https://github.com');
  });

  it('el cobro está abierto: no se anuncia como futuro', () => {
    expect(bundle.landing.pricingNote).not.toMatch(/abre pronto|opens soon/i);
  });
});

describe.each(Object.entries(BUNDLES))('términos honestos (%s)', (_lang, bundle) => {
  it('D-7: los términos no venden un plan Creador que no existe', () => {
    expect(bundle.legal.termsP3plans).not.toMatch(/Creador|Creator/);
  });

  it('el tutor envía datos a Groq: los términos no dicen lo contrario', () => {
    expect(bundle.legal.termsP9).not.toMatch(/No se envían datos personales|No personal data is sent/i);
    expect(bundle.legal.termsP9).toMatch(/Groq/);
  });
});
