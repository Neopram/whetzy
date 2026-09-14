import { Trans, useTranslation } from 'react-i18next';
import styles from './LegalScreen.module.css';

interface Props {
  doc: 'privacy' | 'terms';
}

export function LegalScreen({ doc }: Props) {
  const { t } = useTranslation();
  return (
    <div className={styles.page}>
      <button className={styles.back} onClick={() => history.back()}>← {t('legal.back')}</button>
      {doc === 'privacy' ? <PrivacyContent /> : <TermsContent />}
    </div>
  );
}

function PrivacyContent() {
  const { t } = useTranslation();
  return (
    <article className={styles.article}>
      <h1>{t('legal.privacyTitle')}</h1>
      <p className={styles.updated}>{t('legal.updated')}</p>

      <h2>{t('legal.privacyH1')}</h2>
      <ul>
        <li>{t('legal.privacyL1')}</li>
        <li>{t('legal.privacyL2')}</li>
        <li>{t('legal.privacyL3')}</li>
        <li>{t('legal.privacyL4')}</li>
        <li>{t('legal.privacyL5')}</li>
      </ul>

      <h2>{t('legal.privacyH2')}</h2>
      <ul>
        <li>{t('legal.privacyL6')}</li>
        <li>{t('legal.privacyL7')}</li>
        <li>{t('legal.privacyL8')}</li>
        <li>{t('legal.privacyL9')}</li>
      </ul>

      <h2>{t('legal.privacyH3')}</h2>
      <p><Trans i18nKey="legal.privacyP3" components={{ 1: <strong />, 3: <strong /> }} /></p>

      <h2>{t('legal.privacyH4')}</h2>
      <p><Trans i18nKey="legal.privacyP4" components={{ 1: <strong /> }} /></p>

      <h2>{t('legal.privacyH5')}</h2>
      <ul>
        <li>{t('legal.privacyL10')}</li>
        <li>{t('legal.privacyL11')}</li>
        <li>{t('legal.privacyL12')}</li>
      </ul>
      <p>{t('legal.privacyRights')} <a href="mailto:privacy@whetzy.com">privacy@whetzy.com</a></p>

      <h2>{t('legal.privacyH6')}</h2>
      <p>Whetzy · <a href="mailto:privacy@whetzy.com">privacy@whetzy.com</a></p>
    </article>
  );
}

function TermsContent() {
  const { t } = useTranslation();
  return (
    <article className={styles.article}>
      <h1>{t('legal.termsTitle')}</h1>
      <p className={styles.updated}>{t('legal.updated')}</p>

      <h2>{t('legal.termsH1')}</h2>
      <p>{t('legal.termsP1')}</p>

      <h2>{t('legal.termsH2')}</h2>
      <ul>
        <li>{t('legal.termsL1')}</li>
        <li>{t('legal.termsL2')}</li>
        <li>{t('legal.termsL3')}</li>
      </ul>

      <h2>{t('legal.termsH3')}</h2>
      <p>{t('legal.termsP3')}</p>

      <h2>{t('legal.termsH4')}</h2>
      <p>{t('legal.termsP4')}</p>

      <h2>{t('legal.termsH5')}</h2>
      <p>{t('legal.termsP5')}</p>

      <h2>{t('legal.termsH6')}</h2>
      <p>{t('legal.termsP6')}</p>

      <h2>{t('legal.termsH7')}</h2>
      <p>Whetzy · <a href="mailto:legal@whetzy.com">legal@whetzy.com</a></p>
    </article>
  );
}
