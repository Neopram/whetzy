import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './i18n/en/common.json';
import es from './i18n/es/common.json';

function detectLanguage(): string {
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
    es: { common: es },
    en: { common: en },
  },
  ns: ['common'],
  defaultNS: 'common',
  lng: detectLanguage(),
  fallbackLng: 'es',
  interpolation: { escapeValue: false },
});

i18n.on('languageChanged', (lng) => {
  try { localStorage.setItem('whetzy_lang', lng); } catch { /* private browsing */ }
});

export default i18n;
