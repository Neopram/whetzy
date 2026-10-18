/** ADR-60 / D-17: estados cualitativos con su evidencia; los umbrales, internos. */
import { describe, expect, it } from 'vitest';
import { bandForDomain, bandForSkill, examBand, overallBand, MIN_EVIDENCE_ANSWERS } from '../lib/evidenceBand';

describe('bandas de evidencia (ADR-60)', () => {
  it('por debajo de 7 respuestas es «evidencia insuficiente», acierte o no', () => {
    expect(MIN_EVIDENCE_ANSWERS).toBe(7);
    expect(bandForSkill({ attempts: 6, p_known: 0.99, correct_count: 6 })).toBe('insufficient');
    expect(bandForSkill({ attempts: 7, p_known: 0.99, correct_count: 7 })).toBe('strong');
    expect(bandForSkill({ attempts: 20, p_known: 0.6, correct_count: 14 })).toBe('developing');
  });

  it('«Fuerte» no contradice los aciertos que la tarjeta enseña (e2e, 2026-10-18)', () => {
    // Medido en local: 10 respuestas, 4 aciertos y p_known 0,971 — BKT pesa lo
    // último y tres aciertos seguidos tras fallos lo suben de ~0,23 a ~0,97.
    expect(bandForSkill({ attempts: 10, p_known: 0.971, correct_count: 4 })).toBe('developing');
    // El suelo es 7 de cada 10, inclusive.
    expect(bandForSkill({ attempts: 10, p_known: 0.99, correct_count: 6 })).toBe('developing');
    expect(bandForSkill({ attempts: 10, p_known: 0.99, correct_count: 7 })).toBe('strong');
    // Precisión alta no basta sin que el motor la dé por dominada.
    expect(bandForSkill({ attempts: 10, p_known: 0.9, correct_count: 10 })).toBe('developing');
  });

  it('un dominio necesita evidencia además de estar listo', () => {
    expect(bandForDomain({ answers: 3, ready: true })).toBe('insufficient');
    expect(bandForDomain({ ready: true })).toBe('insufficient');
    expect(bandForDomain({ answers: 9, ready: true })).toBe('strong');
    expect(bandForDomain({ answers: 9, ready: false })).toBe('developing');
  });

  it('el estado global solo es «Fuerte» si todo lo es', () => {
    expect(overallBand([])).toBe('insufficient');
    expect(overallBand(['insufficient', 'insufficient'])).toBe('insufficient');
    expect(overallBand(['strong', 'strong'])).toBe('strong');
    expect(overallBand(['strong', 'insufficient'])).toBe('developing');
  });

  it('para un examen, un dominio sin evidencia basta para decirlo', () => {
    expect(examBand(['strong', 'insufficient'])).toBe('insufficient');
    expect(examBand(['strong', 'developing'])).toBe('developing');
    expect(examBand(['strong', 'strong'])).toBe('strong');
  });
});
