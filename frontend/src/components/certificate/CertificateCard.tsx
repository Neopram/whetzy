/**
 * The certificate itself, and the link that proves it (17.2).
 *
 * Shown twice: to the learner who just earned it, and on the public
 * verification page that anyone can open without an account. It is the same
 * component in both places on purpose — if what an employer sees differed from
 * what the holder was shown, one of the two would be a lie.
 */
import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';

import type { CertificatePublic } from '../../services/api';
import styles from './CertificateCard.module.css';

/** Where the certificate lives. Built from the current origin so it is right in
 *  dev, in preview and in production without a build-time constant to forget. */
export function certificateUrl(code: string): string {
  return `${window.location.origin}/certificate/${code}`;
}

interface Props {
  certificate: CertificatePublic;
  /** The holder's own view gets the copy-link affordance; a verifier does not. */
  showShare?: boolean;
}

export function CertificateCard({ certificate, showShare = true }: Props) {
  const { t, i18n } = useTranslation();
  const isSpanish = i18n.language.startsWith('es');
  const [copied, setCopied] = useState(false);

  const trackName = isSpanish ? certificate.track_name_es : certificate.track_name_en;
  const url = certificateUrl(certificate.code);

  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2500);
    } catch {
      // Clipboard access can be refused (insecure context, permissions). The
      // link is on screen and selectable, so there is nothing to recover from
      // and nothing worth interrupting the learner about.
    }
  }, [url]);

  if (certificate.revoked) {
    return (
      <div className={styles.revoked} role="status">
        <h2 className={styles.title}>{t('certificate.title')}</h2>
        <p>{t('certificate.revoked')}</p>
      </div>
    );
  }

  return (
    <section className={styles.card} aria-label={t('certificate.title')}>
      <p className={styles.kicker}>{t('certificate.title')}</p>
      <h2 className={styles.track}>{trackName}</h2>

      <p className={styles.holderLabel}>{t('certificate.holder')}</p>
      <p className={styles.holder}>{certificate.username}</p>

      <dl className={styles.meta}>
        <div className={styles.metaRow}>
          <dt>{t('certificate.score')}</dt>
          <dd>{certificate.score_pct}%</dd>
        </div>
        <div className={styles.metaRow}>
          <dt>{t('certificate.questions', { count: certificate.questions })}</dt>
          <dd />
        </div>
        <div className={styles.metaRow}>
          <dt>{t('certificate.issued')}</dt>
          <dd>
            <time dateTime={certificate.issued_at}>
              {new Date(certificate.issued_at).toLocaleDateString(isSpanish ? 'es' : 'en')}
            </time>
          </dd>
        </div>
      </dl>

      {showShare && (
        <>
          <p className={styles.url}>{url}</p>
          <button className={styles.copy} onClick={() => void copy()}>
            {copied ? t('certificate.copied') : t('certificate.copyLink')}
          </button>
          <p className={styles.hint}>{t('certificate.shareHint')}</p>
        </>
      )}
    </section>
  );
}
