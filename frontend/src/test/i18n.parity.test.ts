import { describe, expect, it } from 'vitest';
import en from '../i18n/en/common.json';
import es from '../i18n/es/common.json';

// Arrays are part of the resource shape since the placement test moved its
// questions here (18.15): each question carries an `options` array. They flatten
// by index, so `options.0` .. `options.3` are ordinary keys for parity purposes
// and a language that ships three options where the other ships four fails the
// same way a missing key does.
type Tree = { [k: string]: string | string[] | Tree };

function flatten(tree: Tree, prefix = ''): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [key, value] of Object.entries(tree)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (typeof value === 'string') out[path] = value;
    else if (Array.isArray(value)) value.forEach((v, i) => (out[`${path}.${i}`] = v));
    else Object.assign(out, flatten(value, path));
  }
  return out;
}

const flatEs = flatten(es as Tree);
const flatEn = flatten(en as Tree);

describe('i18n parity (red line 3: nothing ships in one language only)', () => {
  it('every Spanish key has an English counterpart', () => {
    const missing = Object.keys(flatEs).filter((k) => !(k in flatEn));
    expect(missing).toEqual([]);
  });

  it('every English key has a Spanish counterpart', () => {
    const missing = Object.keys(flatEn).filter((k) => !(k in flatEs));
    expect(missing).toEqual([]);
  });

  it('no value is left empty in either language', () => {
    const empty = [
      ...Object.entries(flatEs).filter(([, v]) => !v.trim()).map(([k]) => `es:${k}`),
      ...Object.entries(flatEn).filter(([, v]) => !v.trim()).map(([k]) => `en:${k}`),
    ];
    expect(empty).toEqual([]);
  });

  it('interpolation placeholders match across languages', () => {
    const vars = (s: string) => (s.match(/\{\{(\w+)\}\}/g) ?? []).sort().join(',');
    const mismatched = Object.keys(flatEs)
      .filter((k) => k in flatEn && vars(flatEs[k]) !== vars(flatEn[k]))
      .map((k) => `${k}: es(${vars(flatEs[k])}) vs en(${vars(flatEn[k])})`);
    expect(mismatched).toEqual([]);
  });

  it('the legal and account-deletion screens are fully translated', () => {
    // These two shipped Spanish-only: the privacy policy, the terms of service
    // and the GDPR deletion flow. An English user could not read what they were
    // agreeing to, and had to type the Spanish word "CONFIRMAR" to delete their
    // account. Guarding the namespaces so it cannot silently happen again.
    for (const ns of ['legal', 'deleteAccount']) {
      const esKeys = Object.keys(flatEs).filter((k) => k.startsWith(`${ns}.`));
      const enKeys = Object.keys(flatEn).filter((k) => k.startsWith(`${ns}.`));
      expect(esKeys.length).toBeGreaterThan(0);
      expect(enKeys).toEqual(esKeys);
    }
  });

  it('the deletion confirmation word differs per language', () => {
    // If both languages shared one word, one audience would be typing a foreign
    // string to confirm something irreversible.
    expect(flatEs['deleteAccount.confirmWord']).toBe('CONFIRMAR');
    expect(flatEn['deleteAccount.confirmWord']).toBe('DELETE');
  });
});

// Desde la fase 0 del trabajo en paralelo (docs/SESIONES.md) cada sesion tiene
// su fichero por idioma. La paridad se exige fichero a fichero, y cada fichero
// de rol tiene que estar registrado en el cargador: uno que nadie carga es una
// cadena que el alumno no ve nunca, en ningun idioma.
const esFiles = import.meta.glob<Tree>('../i18n/es/*.json', { eager: true, import: 'default' });
const enFiles = import.meta.glob<Tree>('../i18n/en/*.json', { eager: true, import: 'default' });
const fileName = (p: string) => p.split('/').pop() as string;

describe('i18n parity per file (one file per session, docs/SESIONES.md)', () => {
  it('both languages ship the same files', () => {
    expect(Object.keys(enFiles).map(fileName).sort()).toEqual(Object.keys(esFiles).map(fileName).sort());
  });

  it('every file has the same keys in Spanish and English, none empty', () => {
    const problems: string[] = [];
    for (const [path, esTree] of Object.entries(esFiles)) {
      const name = fileName(path);
      const enTree = enFiles[`../i18n/en/${name}`];
      if (!enTree) continue;
      const fe = flatten(esTree);
      const fn = flatten(enTree);
      for (const k of Object.keys(fe)) if (!(k in fn)) problems.push(`${name}: falta en en: ${k}`);
      for (const k of Object.keys(fn)) if (!(k in fe)) problems.push(`${name}: falta en es: ${k}`);
      for (const [k, v] of [...Object.entries(fe), ...Object.entries(fn)]) {
        if (!v.trim()) problems.push(`${name}: vacio: ${k}`);
      }
    }
    expect(problems).toEqual([]);
  });

  it('every role file is registered in the loader, in both languages', async () => {
    const { default: i18n, ROLE_NAMESPACES } = await import('../i18n');
    for (const ns of ROLE_NAMESPACES) {
      expect(Object.keys(esFiles).map(fileName)).toContain(`${ns}.json`);
      expect(i18n.hasResourceBundle('es', ns)).toBe(true);
      expect(i18n.hasResourceBundle('en', ns)).toBe(true);
    }
  });
});
