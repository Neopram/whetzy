import { useEffect } from 'react';
import i18n, { detectLanguage } from '../i18n';
import { DEFAULT_USER_ID, useAppStore } from '../stores/useAppStore';

type Lang = 'es' | 'en';

/**
 * Idioma de las páginas sueltas (certificado e informe públicos, legales).
 *
 * `?lang=` manda (un enlace compartido en un idioma). Con cuenta, el de la
 * cuenta. Sin cuenta, lo elegido en la portada (`whetzy_lang`) o el del
 * navegador: antes se aplicaba `user.language`, que para un visitante es el
 * 'es' por defecto del store, y la verificación de un certificado salía en
 * español a quien la abría con el navegador en inglés.
 */
export function standaloneLanguage(user: { id: string; language: string }): Lang {
  const q = new URLSearchParams(window.location.search).get('lang');
  if (q === 'es' || q === 'en') return q;
  if (user.id !== DEFAULT_USER_ID) return user.language === 'en' ? 'en' : 'es';
  return detectLanguage() === 'en' ? 'en' : 'es';
}

/** Aplica ese idioma a i18n y a `<html lang>` antes de pintar la página. */
export function useStandaloneLanguage(): Lang {
  const id = useAppStore((s) => s.user.id);
  const language = useAppStore((s) => s.user.language);
  const lang = standaloneLanguage({ id, language });
  useEffect(() => {
    void i18n.changeLanguage(lang);
    document.documentElement.lang = lang;
  }, [lang]);
  return lang;
}
