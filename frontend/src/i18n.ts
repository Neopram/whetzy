import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './i18n/en/common.json';
import es from './i18n/es/common.json';

function detectLanguage(): string {
  try {
    const stored = localStorage.getItem('whetzy_lang');
    if (stored === 'en' || stored === 'es') return stored;
  } catch { /* private browsing */ }
  // Node 20 (Cloudflare Pages, .nvmrc) has no global `navigator` during the landing prerender.
  const nav = typeof navigator === 'undefined' ? '' : navigator.language?.slice(0, 2) ?? '';
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
