/** `/es/carrera`, `/en/career` (0.14): esta ruta estaba reservada y vacía
 *  desde la fase 0. Whetzy es un proyecto de un solo fundador — no hay
 *  equipo ni vacantes que anunciar, y fabricar una página de "trabaja con
 *  nosotros" sin eso sería justo la clase de afirmación que la línea roja
 *  de este repo prohíbe. En vez de contenido inventado o un hueco en blanco,
 *  se marca `noindex` y se dice la verdad: la recomendación en el PR es no
 *  indexarla hasta que haya algo real que publicar aquí. */
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import styles from './NotAvailablePage.module.css';
import { useNoIndexMeta } from './useNoIndexMeta';

export default function CareerPage({ lang }: { lang: 'es' | 'en' }) {
  const { t, i18n } = useTranslation('marketing');
  useEffect(() => {
    if (i18n.language !== lang) void i18n.changeLanguage(lang);
  }, [lang, i18n]);
  useNoIndexMeta(t('notAvailable.metaTitle'), lang);

  return (
    <main className={styles.page}>
      <h1 className={styles.heading}>{t('notAvailable.heading')}</h1>
      <p className={styles.body}>{t('notAvailable.career')}</p>
      <a className={styles.backLink} href={lang === 'es' ? '/landing' : '/landing?lang=en'}>
        {t('notAvailable.backHome')}
      </a>
    </main>
  );
}
