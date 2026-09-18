import { describe, expect, it } from 'vitest';
import { PLACEMENT_POOL } from '../pages/PlacementScreen';
import en from '../i18n/en/common.json';
import es from '../i18n/es/common.json';

// Two defects this file exists for, both found in 18.15:
//
//  1. All ten questions had `correctIndex: 0`. Nothing shuffles the options, so
//     pressing the first button ten times scored 100 % and placed the learner at
//     the top level, skipping the curriculum. A placement estimate that a
//     guessing habit can max out is not measuring knowledge (red line 1).
//  2. The stems and options were hardcoded Spanish, and the level shown at the
//     end ('Avanzado', 'Basico') was a Spanish literal interpolated into a
//     translated sentence - so an English learner sat a Spanish test and read
//     'Level: Avanzado' (red line 3).

type QuestionBank = Record<string, { text: string; options: string[] }>;

const esQuestions = es.placement.questions as QuestionBank;
const enQuestions = en.placement.questions as QuestionBank;

describe('placement test', () => {
  it('spreads the correct answer across positions', () => {
    const positions = new Set(PLACEMENT_POOL.map((q) => q.correctIndex));
    expect(positions.size).toBeGreaterThanOrEqual(3);
  });

  it('cannot be passed by always pressing the same button', () => {
    for (let button = 0; button < 4; button++) {
      const hits = PLACEMENT_POOL.filter((q) => q.correctIndex === button).length;
      const pct = (hits / PLACEMENT_POOL.length) * 100;
      // 70 % is the threshold that unlocks skipping modules, so staying under
      // it is the property that matters, not evenness for its own sake.
      expect(pct).toBeLessThan(70);
    }
  });

  it('asks every question in both languages', () => {
    for (const { id } of PLACEMENT_POOL) {
      expect(esQuestions[id], `missing Spanish question ${id}`).toBeDefined();
      expect(enQuestions[id], `missing English question ${id}`).toBeDefined();
      expect(esQuestions[id].text.length).toBeGreaterThan(0);
      expect(enQuestions[id].text.length).toBeGreaterThan(0);
    }
  });

  it('offers the same options in the same order in both languages', () => {
    // `correctIndex` is a single number used for both languages, so the two
    // option lists must line up or the English learner is graded against the
    // Spanish key.
    for (const { id } of PLACEMENT_POOL) {
      expect(enQuestions[id].options).toHaveLength(esQuestions[id].options.length);
      expect(esQuestions[id].options).toHaveLength(4);
    }
  });

  it('points correctIndex at an option that exists', () => {
    for (const { id, correctIndex } of PLACEMENT_POOL) {
      expect(correctIndex).toBeGreaterThanOrEqual(0);
      expect(correctIndex).toBeLessThan(esQuestions[id].options.length);
    }
  });

  it('names every level in both languages', () => {
    const esLevels = Object.keys(es.placement.levels);
    const enLevels = Object.keys(en.placement.levels);
    expect(esLevels.sort()).toEqual(enLevels.sort());
    expect(esLevels).toContain('advanced');
    expect(esLevels).toContain('beginner');
  });
});
