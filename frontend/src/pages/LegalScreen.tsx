import { Trans, useTranslation } from 'react-i18next';
import styles from './LegalScreen.module.css';

interface Props {
  doc: 'privacy' | 'terms' | 'refund';
}

export function LegalScreen({ doc }: Props) {
  const { t } = useTranslation();
  return (
    <div className={styles.page}>
      <button className={styles.back} onClick={() => history.back()}>← {t('legal.back')}</button>
      {doc === 'privacy' ? <PrivacyContent /> : doc === 'refund' ? <RefundContent /> : <TermsContent />}
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
      <p>{t('legal.termsP2')}</p>

      <h2>{t('legal.termsH3')}</h2>
      <p>{t('legal.termsP3plans')}</p>

      <h2>{t('legal.termsH4')}</h2>
      <p>{t('legal.termsP4payments')}</p>

      <h2>{t('legal.termsH5')}</h2>
      <p>{t('legal.termsP5withdrawal')}</p>

      <h2>{t('legal.termsH6')}</h2>
      <p>{t('legal.termsP6renewal')}</p>

      <h2>{t('legal.termsH7')}</h2>
      <ul>
        <li>{t('legal.termsL1')}</li>
        <li>{t('legal.termsL2')}</li>
        <li>{t('legal.termsL3')}</li>
      </ul>

      <h2>{t('legal.termsH8')}</h2>
      <p>{t('legal.termsP8')}</p>

      <h2>{t('legal.termsH9')}</h2>
      <p>{t('legal.termsP9')}</p>

      <h2>{t('legal.termsH10')}</h2>
      <p>{t('legal.termsP10')}</p>

      <h2>{t('legal.termsH11')}</h2>
      <p>{t('legal.termsP11')}</p>

      <h2>{t('legal.termsH12')}</h2>
      <p>{t('legal.termsP12')}</p>

      <h2>{t('legal.termsH13')}</h2>
      <p>Whetzy · <a href="mailto:support@whetzy.com">support@whetzy.com</a></p>
    </article>
  );
}

/** Política de reembolsos (H.29): la que exige Paddle para aprobar el dominio.
 *  El desistimiento repite el de los Términos (§5) para que no diverjan. */
function RefundContent() {
  const { t } = useTranslation();
  return (
    <article className={styles.article}>
      <h1>{t('legal.refundTitle')}</h1>
      <p className={styles.updated}>{t('legal.updated')}</p>

      <h2>{t('legal.refundH1')}</h2>
      <p>{t('legal.refundP1')}</p>

      <h2>{t('legal.refundH2')}</h2>
      <p>{t('legal.refundP2')}</p>

      <h2>{t('legal.refundH3')}</h2>
      <p>{t('legal.termsP5withdrawal')}</p>

      <h2>{t('legal.refundH4')}</h2>
      <p>{t('legal.refundP4')}</p>

      <h2>{t('legal.refundH5')}</h2>
      <p>{t('legal.refundP5')}</p>

      <p>Whetzy · <a href="mailto:support@whetzy.com">support@whetzy.com</a></p>
    </article>
  );
}
