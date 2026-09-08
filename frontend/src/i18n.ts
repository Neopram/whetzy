import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './i18n/en/common.json';
import es from './i18n/es/common.json';

i18n.use(initReactI18next).init({
  resources: {
    es: { common: es },
    en: { common: en },
  },
  ns: ['common'],
  defaultNS: 'common',
  lng: 'es',
  fallbackLng: 'es',
  interpolation: { escapeValue: false },
});

export default i18n;
