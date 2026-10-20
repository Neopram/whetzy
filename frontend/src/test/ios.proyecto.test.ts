/**
 * El proyecto de Xcode (`frontend/ios/`, `npx cap add ios`) entra en git como
 * `android/`, para que Codemagic y un Mac partan de lo mismo. Lo que no puede
 * colarse: permisos que la app no usa (ADR «NO voz, NO OCR»), otro bundle id, y
 * rutas de la máquina donde se generó (`cap sync` escribe en Package.swift la
 * ruta real de node_modules; aquí era un enlace y salió `../../../../../nm-shared`).
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const IOS = join(dirname(fileURLToPath(import.meta.url)), '..', '..', 'ios', 'App');
const leer = (p: string) => readFileSync(join(IOS, p), 'utf8');

describe('proyecto de iOS', () => {
  it('Info.plist: nombre, modo oscuro y ninguna clave de cámara, micro, ubicación, fotos o voz', () => {
    const plist = leer('App/Info.plist');
    expect(plist).toMatch(/<key>CFBundleDisplayName<\/key>\s*<string>Whetzy<\/string>/);
    expect(plist).toMatch(/<key>UIUserInterfaceStyle<\/key>\s*<string>Dark<\/string>/);
    const usos = [...plist.matchAll(/<key>(NS\w+UsageDescription)<\/key>/g)].map((m) => m[1]);
    expect(usos).toEqual([]);
  });

  it('el bundle id es app.whetzy en las dos configuraciones', () => {
    const ids = [...leer('App.xcodeproj/project.pbxproj').matchAll(/PRODUCT_BUNDLE_IDENTIFIER = ([^;]+);/g)].map(
      (m) => m[1],
    );
    expect(ids).toEqual(['app.whetzy', 'app.whetzy']);
  });

  it('Package.swift apunta a frontend/node_modules, no a una ruta de la máquina', () => {
    const rutas = [...leer('CapApp-SPM/Package.swift').matchAll(/path: "([^"]+)"/g)].map((m) => m[1]);
    expect(rutas.length).toBeGreaterThan(0);
    for (const r of rutas) expect(r).toMatch(/^\.\.\/\.\.\/\.\.\/node_modules\/@capacitor\//);
  });
});
