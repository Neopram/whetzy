/**
 * «1 respuestas · 1 aciertos» salía en Tu territorio (Hoy) con una skill de una
 * sola respuesta: `bands.evidence` no tenía plural. Ahora anida `answersCount` y
 * `correctCount` con `count`, así que las llamadas siguen igual
 * (`t('bands.evidence', { answers, correct })`).
 */
import { afterEach, describe, expect, it } from 'vitest';
import i18n from '../i18n';

afterEach(async () => {
  await i18n.changeLanguage('es');
});

describe('bands.evidence concuerda en número', () => {
  it('ES: singular y plural en cada mitad', async () => {
    await i18n.changeLanguage('es');
    expect(i18n.t('bands.evidence', { answers: 1, correct: 1 })).toBe('1 respuesta · 1 acierto');
    expect(i18n.t('bands.evidence', { answers: 5, correct: 0 })).toBe('5 respuestas · 0 aciertos');
    expect(i18n.t('bands.evidence', { answers: 40, correct: 10 })).toBe('40 respuestas · 10 aciertos');
  });

  it('EN: singular y plural en cada mitad', async () => {
    await i18n.changeLanguage('en');
    expect(i18n.t('bands.evidence', { answers: 1, correct: 1 })).toBe('1 answer · 1 correct');
    expect(i18n.t('bands.evidence', { answers: 7, correct: 3 })).toBe('7 answers · 3 correct');
  });
});
