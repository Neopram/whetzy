/**
 * ADR-60 (2026-10-12): mientras el modelo no esté calibrado, ninguna pantalla
 * enseña el dominio como «84 %». Se dice con bandas (Fuerte / En desarrollo /
 * Evidencia insuficiente) o con hechos contables (skills dominadas, aciertos).
 *
 * #189 lo cumplió en Hoy y Preparación; la auditoría del 2026-10-15 encontró
 * el % en otras siete pantallas (informe público, perfil público, estadísticas,
 * rutas, marketplace, prueba de nivel y quiz). Esta guarda las vigila todas.
 *
 * Sí se permite un % de aciertos sobre preguntas respondidas (`accuracy`), la
 * nota de un examen frente a su aprobado y el peso oficial de un dominio: son
 * cuentas, no estimaciones del modelo.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { describe, expect, it } from 'vitest';

import en from '../i18n/en/common.json';
import es from '../i18n/es/common.json';

const SRC = join(__dirname, '..');

function tsxFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) return tsxFiles(full);
    return name.endsWith('.tsx') && !name.includes('.test.') ? [full] : [];
  });
}

/** Una estimación del modelo pasada a porcentaje en la misma expresión. */
const MODEL_PERCENT =
  /(p_known|average_mastery|mastery_avg|expected_p|ability_estimate|reliability|\bmastery\b)[^;]*(\* ?100|pct\()|pct\((s|sk|tr|m|b|prev)\.(p_known|average_mastery)/;

/** Excepciones con su porqué. QuizScreen conserva la barra de dominio y la
 *  probabilidad esperada solo en desarrollo (`import.meta.env.DEV`). */
const ALLOWED: Record<string, { count: number; mustContain: string }> = {
  'pages/QuizScreen.tsx': { count: 4, mustContain: '!import.meta.env.DEV' },
};

describe('ADR-60: ninguna pantalla enseña el dominio del modelo como %', () => {
  const files = [...tsxFiles(join(SRC, 'pages')), ...tsxFiles(join(SRC, 'components'))];

  it('ve los ficheros que vigila', () => {
    const names = files.map((f) => relative(SRC, f));
    for (const f of ['pages/MasteryReportScreen.tsx', 'pages/StatsScreen.tsx', 'pages/TracksScreen.tsx', 'pages/QuizScreen.tsx']) {
      expect(names).toContain(f);
    }
  });

  it('ninguna expresión convierte una estimación del modelo en %', () => {
    const offenders: string[] = [];
    for (const file of files) {
      const rel = relative(SRC, file).split('\\').join('/');
      const src = readFileSync(file, 'utf8');
      const hits = src.split('\n').flatMap((line, i) =>
        MODEL_PERCENT.test(line) && !line.trim().startsWith('//') ? [`${rel}:${i + 1}: ${line.trim()}`] : [],
      );
      const allowed = ALLOWED[rel];
      if (allowed) {
        expect(src, `${rel} debe seguir con la barra tras ${allowed.mustContain}`).toContain(allowed.mustContain);
        if (hits.length !== allowed.count) offenders.push(...hits);
      } else {
        offenders.push(...hits);
      }
    }
    expect(offenders).toEqual([]);
  });

  it('las claves que mostraban el % ya no lo piden', () => {
    const at = (o: unknown, path: string): string =>
      path.split('.').reduce<unknown>((x, k) => (x as Record<string, unknown>)[k], o) as string;
    const keys = [
      'report.trackMeta',
      'marketplace.mastery_meta',
      'tracks.unlockWith',
      'tracks.moduleMastered',
      'placement.abilityResult',
      'placement.lowReliability',
      // ADR-71 (2026-10-23): el umbral de dominio tampoco se dice como «95 % de
      // probabilidad de conocimiento (BKT)»; es una cifra del modelo.
      'tracks.thresholdNote',
    ];
    for (const lang of [es, en]) {
      for (const k of keys) {
        const v = at(lang, k);
        expect(typeof v, k).toBe('string');
        expect(v, k).not.toMatch(/\{\{(pct|mastery)\}\}|%/);
      }
    }
  });

  it('la prueba de nivel no dibuja una barra con la theta del modelo (ADR-71)', () => {
    // El ancho de la barra «Nivel estimado» salía de theta: un % del modelo en
    // forma de barra. El resultado ya se dice en palabras (`abilityResult`).
    const src = readFileSync(join(SRC, 'pages', 'PlacementScreen.tsx'), 'utf8');
    expect(src).not.toMatch(/thetaAPorcentaje|abilityFill/);
  });

  it('el «75 %» de la landing es el objetivo del selector, no una estimación (ADR-71)', () => {
    // Se permite porque es un parámetro fijo del diseño, no una medida del
    // alumno; pero tiene que seguir siendo verdad.
    const quiz = readFileSync(join(SRC, '..', '..', 'backend', 'app', 'services', 'quiz.py'), 'utf8');
    const landing = readFileSync(join(SRC, 'pages', 'LandingScreen.tsx'), 'utf8');
    expect(quiz).toMatch(/^TARGET_SUCCESS_PROBABILITY = 0\.75$/m);
    expect(landing).toContain('<dd>75 %</dd>');
  });

  it('la prueba de nivel no promete Python en una ruta que no lo es', () => {
    expect(es.placement.introDesc).not.toMatch(/Python/);
    expect(en.placement.introDesc).not.toMatch(/Python/);
  });
});
