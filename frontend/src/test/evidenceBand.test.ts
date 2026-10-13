/** ADR-60 / D-17: estados cualitativos con su evidencia; los umbrales, internos. */
import { describe, expect, it } from 'vitest';
import { bandForDomain, bandForSkill, examBand, overallBand, MIN_EVIDENCE_ANSWERS } from '../lib/evidenceBand';

describe('bandas de evidencia (ADR-60)', () => {
  it('por debajo de 7 respuestas es «evidencia insuficiente», acierte o no', () => {
    expect(MIN_EVIDENCE_ANSWERS).toBe(7);
    expect(bandForSkill({ attempts: 6, p_known: 0.99 })).toBe('insufficient');
    expect(bandForSkill({ attempts: 7, p_known: 0.99 })).toBe('strong');
    expect(bandForSkill({ attempts: 20, p_known: 0.6 })).toBe('developing');
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
