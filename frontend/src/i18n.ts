import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './i18n/en/common.json';
import es from './i18n/es/common.json';
import enContenido from './i18n/en/contenido.json';
import enLegal from './i18n/en/legal.json';
import enMarketing from './i18n/en/marketing.json';
import enMotor from './i18n/en/motor.json';
import enProducto from './i18n/en/producto.json';
import esContenido from './i18n/es/contenido.json';
import esLegal from './i18n/es/legal.json';
import esMarketing from './i18n/es/marketing.json';
import esMotor from './i18n/es/motor.json';
import esProducto from './i18n/es/producto.json';

/** Un namespace por sesion de trabajo en paralelo (docs/SESIONES.md): cada una
 *  escribe solo su fichero y `common` lo edita una sola. Namespaces separados y
 *  no un merge en `common`: dos sesiones con la misma clave se pisarian en
 *  silencio. Se usan con `useTranslation('marketing')` o `t('marketing:clave')`. */
export const ROLE_NAMESPACES = ['producto', 'contenido', 'motor', 'legal', 'marketing'] as const;

/** Idioma al arrancar: lo guardado en `whetzy_lang` (lo elegido en la portada o
 *  en /auth), y si no el navegador. 45.1 (ADR-66 E1) la usa como respaldo de `?lang`. */
export function detectLanguage(): string {
  // No `window` in Node (the landing prerender, scripts/prerender-landing.mjs)
  // regardless of Node version. `navigator` is NOT a safe proxy for that: Node
  // 21+ ships its own global `navigator` with a real `.language` derived from
  // the OS/ICU locale (verified live: Node 22 here resolves it to "en-US"),
  // which silently flipped the prerendered hero to English the moment this
  // sandbox's Node stopped matching `.nvmrc`'s pinned 20.19.0. Always Spanish
  // outside a browser, matching the static shell's `<html lang="es">`.
  if (typeof window === 'undefined') return 'es';
  try {
    const stored = localStorage.getItem('whetzy_lang');
    if (stored === 'en' || stored === 'es') return stored;
  } catch { /* private browsing */ }
  const nav = navigator.language?.slice(0, 2) ?? '';
  return nav === 'en' ? 'en' : 'es';
}

i18n.use(initReactI18next).init({
  resources: {
    es: {
      common: es,
      producto: esProducto,
      contenido: esContenido,
      motor: esMotor,
      legal: esLegal,
      marketing: esMarketing,
    },
    en: {
      common: en,
      producto: enProducto,
      contenido: enContenido,
      motor: enMotor,
      legal: enLegal,
      marketing: enMarketing,
    },
  },
  ns: ['common', ...ROLE_NAMESPACES],
  defaultNS: 'common',
  lng: detectLanguage(),
  fallbackLng: 'es',
  interpolation: { escapeValue: false },
});

i18n.on('languageChanged', (lng) => {
  try { localStorage.setItem('whetzy_lang', lng); } catch { /* private browsing */ }
});

export default i18n;
