/**
 * La app de Android pide solo lo que usa: red, vibración y avisos. Sin cámara,
 * micrófono ni ubicación (ADR «NO voz, NO OCR»).
 *
 * Mira el manifiesto de la app y el de cada plugin de Capacitor que la app
 * declara en package.json, que son los que Gradle funde en el APK. Los permisos
 * que entran por dependencias transitivas (Firebase, por el plugin de avisos)
 * solo se ven en el APK compilado: esa comprobación va en docs/RUNBOOK.md
 * («App Android de depuración», `aapt2 dump permissions`).
 */
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const FRONT = join(dirname(fileURLToPath(import.meta.url)), '..', '..');

const PROHIBIDOS = [
  'android.permission.CAMERA',
  'android.permission.RECORD_AUDIO',
  'android.permission.ACCESS_FINE_LOCATION',
  'android.permission.ACCESS_COARSE_LOCATION',
  'android.permission.ACCESS_BACKGROUND_LOCATION',
  'android.permission.READ_CONTACTS',
  'android.permission.READ_MEDIA_IMAGES',
  'android.permission.READ_EXTERNAL_STORAGE',
];

// Plugins que existen para eso mismo: si alguno entra, entra su permiso.
const PLUGINS_PROHIBIDOS = /camera|geolocation|microphone|speech|voice|barcode|ocr|contacts/i;

const permisos = (xml: string) =>
  [...xml.matchAll(/<uses-permission[^>]*android:name="([^"]+)"/g)].map((m) => m[1]);

function manifiestos(): Record<string, string> {
  const pkg = JSON.parse(readFileSync(join(FRONT, 'package.json'), 'utf8'));
  const deps = Object.keys({ ...pkg.dependencies, ...pkg.devDependencies });
  const out: Record<string, string> = {
    app: readFileSync(join(FRONT, 'android', 'app', 'src', 'main', 'AndroidManifest.xml'), 'utf8'),
  };
  for (const dep of deps.filter((d) => d.startsWith('@capacitor/'))) {
    const m = join(FRONT, 'node_modules', dep, 'android', 'src', 'main', 'AndroidManifest.xml');
    if (existsSync(m)) out[dep] = readFileSync(m, 'utf8');
  }
  return out;
}

describe('Android: permisos', () => {
  it('ni la app ni sus plugins piden cámara, micrófono ni ubicación', () => {
    const malos = Object.entries(manifiestos()).flatMap(([de, xml]) =>
      permisos(xml).filter((p) => PROHIBIDOS.includes(p)).map((p) => `${de}: ${p}`),
    );
    expect(malos).toEqual([]);
  });

  it('el manifiesto de la app declara solo INTERNET (lo demás lo trae cada plugin)', () => {
    expect(permisos(manifiestos().app)).toEqual(['android.permission.INTERNET']);
  });

  it('ninguna dependencia es un plugin de cámara, voz, ubicación o lectura de imágenes', () => {
    const pkg = JSON.parse(readFileSync(join(FRONT, 'package.json'), 'utf8'));
    const deps = Object.keys({ ...pkg.dependencies, ...pkg.devDependencies });
    expect(deps.filter((d) => PLUGINS_PROHIBIDOS.test(d))).toEqual([]);
  });
});
