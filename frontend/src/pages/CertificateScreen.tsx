/**
 * Public certificate verification (17.2).
 *
 * Reached at `/certificate/<code>` by someone who very likely has no account
 * here and did not ask to be sold anything — an employer, a reviewer. So the
 * page does one thing: say whether the certificate is genuine, and show what it
 * claims. No sign-up wall, no redirect to the app, no "create your own" banner
 * on top of somebody else's proof.
 */
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { CertificateCard } from '../components/certificate/CertificateCard';
import { DrawnCheck } from '../components/common/DrawnCheck';
import { certificates, type CertificatePublic } from '../services/api';
import styles from './CertificateScreen.module.css';
import { Loading } from '../components/common/Loading';

interface Props {
  code: string;
}

type State =
  | { status: 'loading' }
  | { status: 'found'; certificate: CertificatePublic }
  | { status: 'missing' };

export function CertificateScreen({ code }: Props) {
  const { t } = useTranslation();
  const [state, setState] = useState<State>({ status: 'loading' });

  useEffect(() => {
    let cancelled = false;
    certificates
      .verify(code)
      .then(certificate => {
        if (!cancelled) setState({ status: 'found', certificate });
      })
      .catch(() => {
        // Any failure reads as "not found". Distinguishing a 404 from a 500
        // here would tell a probing visitor which codes exist.
        if (!cancelled) setState({ status: 'missing' });
      });
    return () => {
      cancelled = true;
    };
  }, [code]);

  if (state.status === 'loading') {
    return (
      <div className={styles.screen}>
        <Loading label={t('loading')} shape="card" />
      </div>
    );
  }

  if (state.status === 'missing') {
    return (
      <div className={styles.screen}>
        <h1 className={styles.title}>{t('certificate.verifyTitle')}</h1>
        <p className={styles.muted} role="alert">
          {t('certificate.notFound')}
        </p>
      </div>
    );
  }

  return (
    <div className={styles.screen}>
      <h1 className={styles.title}>{t('certificate.verifyTitle')}</h1>
      {/* 46.15 D: el sello se dibuja solo si el servidor lo da por válido. */}
      {!state.certificate.revoked && <DrawnCheck />}
      {!state.certificate.revoked && (
        <p className={styles.verified} role="status">
          {t('certificate.verifyIntro')}
        </p>
      )}
      {/* showShare is off: the copy-link affordance is for the holder, not for
          whoever is checking it. */}
      <CertificateCard certificate={state.certificate} showShare={false} />
    </div>
  );
}
