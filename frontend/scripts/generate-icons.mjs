#!/usr/bin/env node
/**
 * Genera todos los PNG de marca a partir de los SVG de design/brand/.
 *
 * Sustituye a scripts/generate_icons.py (2026-10-13), que dibujaba con Pillow
 * una «W» blanca sobre el azul #1CB0F6 retirado en design/v2 y copiaba a mano
 * con rutas de un PC concreto. Aquí la fuente es el SVG del logo y el que
 * rasteriza es Chromium, así que el PNG es el mismo dibujo que ve la web
 * (degradados y brillos incluidos) a cualquier tamaño, sin reescalar un mapa
 * de bits: cada tamaño se dibuja en vectorial a su resolución.
 *
 * Escribe, y solo escribe:
 *   frontend/public/favicon.svg, frontend/public/icons/icon-*.png (PWA),
 *   frontend/public/og-image.png (vista previa al compartir, 1200×630),
 *   frontend/android/app/src/main/res/  mipmap-*  y  drawable*  /splash.png,
 *   frontend/ios/App/App/Assets.xcassets/ (AppIcon y Splash), si existe el proyecto de iOS,
 *   docs/store/icons/  (iOS AppIcon.appiconset y Android, para las tiendas),
 *   design/brand/whetzy-logo-*.png (logos horizontales).
 *
 * Uso, desde frontend/:  node scripts/generate-icons.mjs
 * Chromium: el de Playwright (`npx playwright install chromium`), o el que
 * diga CHROME_PATH si la versión de Playwright no coincide con la instalada.
 */
import { chromium } from '@playwright/test';
import { copyFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const BRAND = join(ROOT, 'design', 'brand');
const RES = join(ROOT, 'frontend', 'android', 'app', 'src', 'main', 'res');
const STORE = join(ROOT, 'docs', 'store', 'icons');
const XCASSETS = join(ROOT, 'frontend', 'ios', 'App', 'App', 'Assets.xcassets');

/** Fondo de la app (--le-bg). El del icono (#0D1525) va dentro de whetzy-app-icon.svg. */
const APP_BG = '#0A0E1A';

const dataUrl = (file, type) =>
  `data:${type};base64,${readFileSync(file).toString('base64')}`;
const brandSvg = (name) => dataUrl(join(BRAND, name), 'image/svg+xml');

// La tipografía de la interfaz (Inter, autoalojada) para que el wordmark salga
// igual en cualquier máquina, en vez de depender de la Arial que haya instalada.
const INTER = dataUrl(
  join(ROOT, 'frontend', 'node_modules', '@fontsource-variable', 'inter', 'files', 'inter-latin-wght-normal.woff2'),
  'font/woff2',
);
const FONT_CSS = `@font-face{font-family:'Inter';src:url(${INTER}) format('woff2');font-weight:100 900;}`;

const APP_ICON = brandSvg('whetzy-app-icon.svg');
const FOREGROUND = brandSvg('whetzy-adaptive-foreground.svg');
const MARK = brandSvg('whetzy-mark.svg');
const MARK_MONO = brandSvg('whetzy-mark-mono.svg');

const written = [];

async function render(page, { width, height, body, out, transparent = false }) {
  await page.setViewportSize({ width, height });
  await page.setContent(
    `<!doctype html><html><head><style>${FONT_CSS}` +
      `html,body{margin:0;width:${width}px;height:${height}px;overflow:hidden;background:transparent}` +
      `img{display:block}</style></head><body>${body}</body></html>`,
  );
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map((i) => i.decode()));
  });
  mkdirSync(dirname(out), { recursive: true });
  await page.screenshot({ path: out, omitBackground: transparent, clip: { x: 0, y: 0, width, height } });
  written.push(relative(ROOT, out));
}

/** Icono cuadrado a sangre; `radius` en % recorta las esquinas en transparente. */
const icon = (src, size, radius = 0) =>
  `<img src="${src}" width="${size}" height="${size}" style="border-radius:${radius}%">`;

const ANDROID = [
  ['mipmap-ldpi', 36],
  ['mipmap-mdpi', 48],
  ['mipmap-hdpi', 72],
  ['mipmap-xhdpi', 96],
  ['mipmap-xxhdpi', 144],
  ['mipmap-xxxhdpi', 192],
];

// Pantallas de arranque de Capacitor: mismo tamaño que las que había.
const SPLASH = [
  ['drawable', 480, 320],
  ['drawable-land-mdpi', 480, 320],
  ['drawable-land-hdpi', 800, 480],
  ['drawable-land-xhdpi', 1280, 720],
  ['drawable-land-xxhdpi', 1600, 960],
  ['drawable-land-xxxhdpi', 1920, 1280],
  ['drawable-port-mdpi', 320, 480],
  ['drawable-port-hdpi', 480, 800],
  ['drawable-port-xhdpi', 720, 1280],
  ['drawable-port-xxhdpi', 960, 1600],
  ['drawable-port-xxxhdpi', 1280, 1920],
];

const wordmark = (size, whet, zy) =>
  `<span style="font-family:Inter;font-weight:700;font-size:${size}px;letter-spacing:-0.02em;line-height:1">` +
  `<span style="color:${whet}">Whet</span><span style="color:${zy}">zy</span></span>`;

function lockup({ bg, mark, whet, zy }) {
  return (
    `<div style="width:1200px;height:300px;background:${bg};display:flex;align-items:center;justify-content:center;gap:36px">` +
    `<img src="${mark}" width="211" height="172">${wordmark(150, whet, zy)}</div>`
  );
}

const OG =
  `<div style="width:1200px;height:630px;background:${APP_BG};position:relative;font-family:Inter;color:#E8ECF1">` +
  `<div style="position:absolute;left:80px;top:96px;display:flex;align-items:center;gap:32px">` +
  `<img src="${APP_ICON}" width="168" height="168" style="border-radius:22%;box-shadow:0 0 0 2px #1A2A4A">` +
  `${wordmark(112, '#FFFFFF', '#00BFFF')}</div>` +
  `<div style="position:absolute;left:80px;right:80px;top:340px">` +
  `<div style="font-size:44px;font-weight:700;line-height:1.2">Aprende Python, IA y ciberseguridad justo en el borde de lo que ya sabes.</div>` +
  `<div style="margin-top:20px;font-size:28px;color:#A9B4C2">Learn Python, AI and cybersecurity right at the edge of what you already know.</div>` +
  `<div style="margin-top:28px;font-size:24px;color:#33CCFF">Certificaciones · Certifications · ES / EN</div></div>` +
  `<div style="position:absolute;left:0;right:0;bottom:0;height:10px;background:linear-gradient(90deg,#00BFFF,#7B68EE 40%,#C71585 70%,#FF1493)"></div>` +
  `</div>`;

const executablePath = process.env.CHROME_PATH || undefined;
const browser = await chromium.launch(executablePath ? { executablePath } : {});
const page = await browser.newPage();

try {
  // Web: favicon vectorial y PWA (192 y 512 son «any maskable»: el símbolo cabe
  // en la zona segura del 80 % y el fondo va a sangre).
  copyFileSync(join(BRAND, 'whetzy-favicon.svg'), join(ROOT, 'frontend', 'public', 'favicon.svg'));
  written.push('frontend/public/favicon.svg');
  for (const size of [72, 96, 128, 144, 152, 192, 384, 512]) {
    await render(page, { width: size, height: size, body: icon(APP_ICON, size), out: join(ROOT, 'frontend', 'public', 'icons', `icon-${size}.png`) });
  }
  await render(page, { width: 1200, height: 630, body: OG, out: join(ROOT, 'frontend', 'public', 'og-image.png') });

  // iOS: opacos y sin esquinas (las redondea el sistema).
  for (const size of [1024, 180, 167, 152, 120, 87, 80, 76, 60, 58, 40, 29, 20]) {
    await render(page, { width: size, height: size, body: icon(APP_ICON, size), out: join(STORE, 'ios', 'AppIcon.appiconset', `Icon-${size}.png`) });
  }
  await render(page, { width: 512, height: 512, body: icon(APP_ICON, 512), out: join(STORE, 'android', 'play-store-512.png') });

  // Android: icono clásico (cuadrado redondeado y redondo) para los lanzadores
  // sin iconos adaptativos, y el primer plano adaptativo a 108 dp (× 1,5 el
  // tamaño del clásico en cada densidad).
  for (const [density, size] of ANDROID) {
    for (const base of [RES, join(STORE, 'android')]) {
      await render(page, { width: size, height: size, body: icon(APP_ICON, size, 22), out: join(base, density, 'ic_launcher.png'), transparent: true });
      await render(page, { width: size, height: size, body: icon(APP_ICON, size, 50), out: join(base, density, 'ic_launcher_round.png'), transparent: true });
    }
    const fg = Math.round(size * 1.5);
    await render(page, { width: fg, height: fg, body: icon(FOREGROUND, fg), out: join(RES, density, 'ic_launcher_foreground.png'), transparent: true });
  }

  for (const [dir, width, height] of SPLASH) {
    const mark = Math.round(Math.min(width, height) * 0.32);
    const body =
      `<div style="width:${width}px;height:${height}px;background:${APP_BG};display:flex;align-items:center;justify-content:center">` +
      `<img src="${MARK}" width="${mark}" height="${Math.round((mark * 110) / 135)}"></div>`;
    await render(page, { width, height, body, out: join(RES, dir, 'splash.png') });
  }

  // Proyecto de Xcode (lo crea `npx cap add ios` con iconos y splash de plantilla
  // de Capacitor): un solo AppIcon de 1024, opaco, y la misma pantalla de arranque
  // que Android a 2732 en las tres escalas que pide Splash.imageset.
  if (existsSync(XCASSETS)) {
    await render(page, { width: 1024, height: 1024, body: icon(APP_ICON, 1024), out: join(XCASSETS, 'AppIcon.appiconset', 'AppIcon-512@2x.png') });
    const side = 2732;
    const mark = Math.round(side * 0.32);
    const body =
      `<div style="width:${side}px;height:${side}px;background:${APP_BG};display:flex;align-items:center;justify-content:center">` +
      `<img src="${MARK}" width="${mark}" height="${Math.round((mark * 110) / 135)}"></div>`;
    for (const name of ['splash-2732x2732.png', 'splash-2732x2732-1.png', 'splash-2732x2732-2.png']) {
      await render(page, { width: side, height: side, body, out: join(XCASSETS, 'Splash.imageset', name) });
    }
  }

  // Logos horizontales para usar fuera de la app (redes, prensa, tiendas).
  await render(page, { width: 1200, height: 300, body: lockup({ bg: APP_BG, mark: MARK, whet: '#FFFFFF', zy: '#00BFFF' }), out: join(BRAND, 'whetzy-logo-dark.png') });
  await render(page, { width: 1200, height: 300, body: lockup({ bg: '#FFFFFF', mark: MARK, whet: '#1A1A2E', zy: '#00BFFF' }), out: join(BRAND, 'whetzy-logo-light.png') });
  await render(page, { width: 1200, height: 300, body: lockup({ bg: '#FFFFFF', mark: MARK_MONO, whet: '#1A1A2E', zy: '#1A1A2E' }), out: join(BRAND, 'whetzy-logo-mono.png') });
} finally {
  await browser.close();
}

console.log(`${written.length} ficheros:\n  ${written.join('\n  ')}`);
