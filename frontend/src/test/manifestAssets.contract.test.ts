/**
 * `manifest.json` (0.5) listaba 8 iconos y 2 capturas que nunca llegaron
 * al repo: `/icons/icon-*.png` y `/screenshots/*.png` 404-eaban. Chrome
 * no ofrece instalar la PWA sin un icono 192/512 valido, y el
 * `apple-touch-icon` de `index.html` apuntaba al mismo fichero inexistente.
 *
 * Guarda: cada ruta que `manifest.json` declara tiene que existir de verdad
 * bajo `public/`, para que esto no se repita en silencio.
 */
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const PUBLIC_DIR = join(__dirname, '../../public');
const MANIFEST_PATH = join(PUBLIC_DIR, 'manifest.json');

interface ManifestAsset {
  src: string;
}

interface Manifest {
  icons: ManifestAsset[];
  screenshots?: ManifestAsset[];
}

function readManifest(): Manifest {
  return JSON.parse(readFileSync(MANIFEST_PATH, 'utf-8')) as Manifest;
}

describe('contrato manifest.json ↔ ficheros reales', () => {
  const manifest = readManifest();

  it('tiene al menos un icono 192x192 y uno 512x512 (instalabilidad)', () => {
    const sizes = new Set(manifest.icons.map((i) => (i as ManifestAsset & { sizes: string }).sizes));
    expect(sizes.has('192x192')).toBe(true);
    expect(sizes.has('512x512')).toBe(true);
  });

  it('cada icono declarado existe en public/', () => {
    const missing = manifest.icons
      .map((icon) => icon.src)
      .filter((src) => !existsSync(join(PUBLIC_DIR, src.replace(/^\//, ''))));
    expect(missing).toEqual([]);
  });

  it('cada captura declarada (si hay) existe en public/', () => {
    const missing = (manifest.screenshots ?? [])
      .map((shot) => shot.src)
      .filter((src) => !existsSync(join(PUBLIC_DIR, src.replace(/^\//, ''))));
    expect(missing).toEqual([]);
  });

  it('el apple-touch-icon de index.html existe en public/', () => {
    const html = readFileSync(join(__dirname, '../../index.html'), 'utf-8');
    const match = html.match(/rel="apple-touch-icon"\s+href="([^"]+)"/);
    expect(match).not.toBeNull();
    const href = match![1];
    expect(existsSync(join(PUBLIC_DIR, href.replace(/^\//, '')))).toBe(true);
  });
});
