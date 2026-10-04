/** `/es/empresas`, `/en/enterprise` (0.14): reservada y vacía desde la fase
 *  0. Hay una decisión del dueño que ya aprueba vender pilotos B2B
 *  (`docs/DECISIONS.md` ADR-22/ADR-47), pero ningún panel de equipo existe
 *  todavía en el producto (ni backend ni frontend), y el precio por asiento
 *  de esa misma decisión está marcado explícitamente "sin publicar". Una
 *  página pública que prometa un panel que no existe, o que publique un
 *  precio que el dueño no ha autorizado a publicar, sería la clase de
 *  afirmación que la línea roja de este repo prohíbe — así que por ahora se
 *  marca `noindex` con un mensaje honesto, sin CTA de contacto. El `[S6]
 *  NECESITO (dueño)` en el #89 ofrece la alternativa (una página con la
 *  oferta real del piloto, sin precio, con teams@whetzy.com) para quien
 *  decida activarla. */
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import styles from './NotAvailablePage.module.css';
import { useNoIndexMeta } from './useNoIndexMeta';

export default function EnterprisePage({ lang }: { lang: 'es' | 'en' }) {
  const { t, i18n } = useTranslation('marketing');
  useEffect(() => {
    if (i18n.language !== lang) void i18n.changeLanguage(lang);
  }, [lang, i18n]);
  useNoIndexMeta(t('notAvailable.metaTitle'), lang);

  return (
    <main className={styles.page}>
      <h1 className={styles.heading}>{t('notAvailable.heading')}</h1>
      <p className={styles.body}>{t('notAvailable.enterprise')}</p>
      <a className={styles.backLink} href={lang === 'es' ? '/landing' : '/landing?lang=en'}>
        {t('notAvailable.backHome')}
      </a>
    </main>
  );
}
