import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import i18n from '../i18n';
import { ApiError, auth, billing, exams, type UserRead } from '../services/api';
import { loadPaddle, parseCheckoutRequest, type PaddleEvent } from '../lib/paddle';
import { RetiredCertNotice } from '../components/common/RetiredCertNotice';
import { DrawnCheck } from '../components/common/DrawnCheck';
import styles from './CheckoutScreen.module.css';
import { Loading } from '../components/common/Loading';

/**
 * Página de pago (H.29): `/checkout?plan=plus|pro` o
 * `/checkout?plan=certification&track=<id>`.
 *
 * Es una página aparte, fuera de la app, por las cabeceras: el iframe de Paddle
 * no carga bajo el COEP que Pyodide necesita en el resto del sitio (ver
 * `lib/paddle.ts` y `public/_headers`). Es también el «default payment link»
 * que Paddle exige tener configurado.
 *
 * El plan no se da aquí: lo da el webhook firmado de Paddle en el backend. Esta
 * página solo abre el checkout con `custom_data.user_id` y, al terminar, espera
 * a que el backend refleje el pago.
 */

type Phase =
  | 'loading'
  | 'consent'
  | 'invalid'
  | 'unavailable'
  | 'already'
  | 'open'
  | 'closed'
  | 'activating'
  | 'active'
  | 'pending'
  | 'error';

const POLL_MS = 2000;
const POLL_TRIES = 15;

export function CheckoutScreen() {
  const { t } = useTranslation();
  const [phase, setPhase] = useState<Phase>('loading');
  const [errorCode, setErrorCode] = useState('');
  const request = useRef(parseCheckoutRequest(window.location.search));
  const user = useRef<UserRead | null>(null);
  const opener = useRef<(() => void) | null>(null);
  const completed = useRef(false);
  const [waiver, setWaiver] = useState(false);
  const [waiverMissing, setWaiverMissing] = useState(false);

  const waitForActivation = useCallback(async () => {
    const req = request.current;
    if (!req) return;
    for (let i = 0; i < POLL_TRIES; i += 1) {
      await new Promise((r) => setTimeout(r, POLL_MS));
      try {
        const done =
          req.plan === 'certification' && req.trackId
            ? (await exams.certificationAccess(req.trackId)).purchased
            : (await auth.me()).is_premium;
        if (done) {
          setPhase('active');
          return;
        }
      } catch {
        // Un fallo puntual de red no cambia nada: el webhook llega igual.
      }
    }
    setPhase('pending');
  }, []);

  const onEvent = useCallback(
    (e: PaddleEvent) => {
      if (e.name === 'checkout.completed') {
        completed.current = true;
        setPhase('activating');
        void waitForActivation();
      } else if (e.name === 'checkout.closed' && !completed.current) {
        setPhase('closed');
      } else if (e.name === 'checkout.error') {
        setErrorCode(e.detail || e.code || '');
        setPhase('error');
      }
    },
    [waitForActivation],
  );

  useEffect(() => {
    const req = request.current;
    if (!req) {
      setPhase('invalid');
      return;
    }
    let cancelled = false;
    (async () => {
      let me: UserRead;
      try {
        me = await auth.me();
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          const back = window.location.pathname + window.location.search;
          window.location.replace(`/auth?next=${encodeURIComponent(back)}`);
          return;
        }
        if (!cancelled) setPhase('error');
        return;
      }
      if (cancelled) return;
      user.current = me;
      void i18n.changeLanguage(me.language);
      document.documentElement.lang = me.language;

      if (req.plan !== 'certification' && me.is_premium) {
        setPhase('already');
        return;
      }
      if (req.plan === 'certification' && req.trackId) {
        // Un track que no existe da 404 aquí y no se llega a cobrar nada.
        const access = await exams.certificationAccess(req.trackId).catch(() => null);
        if (cancelled) return;
        if (!access) {
          setPhase('invalid');
          return;
        }
        if (access.purchased) {
          setPhase('already');
          return;
        }
      }
      const config = await billing.paddleConfig().catch(() => null);
      const priceId = config?.prices[req.plan] ?? null;
      if (!config?.enabled || !config.client_token || !priceId) {
        if (!cancelled) setPhase('unavailable');
        return;
      }
      const paddle = await loadPaddle(config.client_token, config.environment, onEvent).catch(() => null);
      if (cancelled) return;
      if (!paddle) {
        setPhase('error');
        return;
      }
      const customData: Record<string, string> = {
        user_id: me.id,
        // Consentimiento del art. 16.m de la Directiva 2011/83/UE: sin él no se
        // abre el pago, y queda guardado en la transacción de Paddle y en el
        // usuario (`eu_withdrawal_waiver_at`, lo escribe el webhook).
        eu_withdrawal_waiver: 'accepted',
      };
      if (req.trackId) customData.track_id = req.trackId;
      opener.current = () => {
        setPhase('open');
        paddle.Checkout.open({
          items: [{ priceId, quantity: 1 }],
          customer: { email: me.email },
          customData,
          settings: { displayMode: 'overlay', locale: me.language, allowLogout: false },
        });
      };
      setPhase('consent');
    })();
    return () => {
      cancelled = true;
    };
  }, [onEvent]);

  const planName =
    request.current?.plan === 'pro' || request.current?.plan === 'pro_annual'
      ? t('checkout.planPro')
      : request.current?.plan === 'certification'
        ? t('checkout.planCertification')
        : t('checkout.planPlus');

  return (
    <main className={styles.page}>
      <h1 className={styles.title}>{t('checkout.title', { plan: planName })}</h1>
      {request.current?.plan === 'certification' && <RetiredCertNotice trackId={request.current.trackId} />}

      {phase === 'loading' && <Loading label={t('checkout.loading')} shape="line" />}
      {phase === 'consent' && (
        <>
          {request.current?.plan !== 'certification' && <p className={styles.body}>{t('checkout.renewalNotice')}</p>}
          <label className={styles.consent}>
            <input
              type="checkbox"
              checked={waiver}
              onChange={(e) => {
                setWaiver(e.target.checked);
                setWaiverMissing(false);
              }}
            />
            <span>{t('checkout.euWithdrawalWaiver')}</span>
          </label>
          {waiverMissing && <p className={styles.error} role="alert">{t('checkout.euWithdrawalRequired')}</p>}
        </>
      )}
      {phase === 'open' && <p className={styles.body}>{t('checkout.open')}</p>}
      {phase === 'invalid' && <p className={styles.error} role="alert">{t('checkout.invalid')}</p>}
      {phase === 'unavailable' && <p className={styles.body}>{t('checkout.unavailable')}</p>}
      {phase === 'already' && <p className={styles.body}>{t('checkout.already')}</p>}
      {phase === 'closed' && <p className={styles.body}>{t('checkout.closed')}</p>}
      {phase === 'activating' && <p className={styles.body} role="status">{t('checkout.activating')}</p>}
      {/* 46.15 E: el éxito se dibuja cuando el servidor confirma el plan, no
          cuando Paddle dice `checkout.completed` («activando» no lleva check). */}
      {phase === 'active' && <DrawnCheck />}
      {phase === 'active' && <p className={styles.body} role="status">{t('checkout.active', { plan: planName })}</p>}
      {phase === 'pending' && <p className={styles.body} role="status">{t('checkout.pending')}</p>}
      {phase === 'error' && (
        <p className={styles.error} role="alert">
          {t('checkout.error')}
          {errorCode ? ` (${errorCode})` : ''}
        </p>
      )}

      <div className={styles.actions}>
        {phase === 'consent' && (
          <button
            type="button"
            className={styles.primary}
            onClick={() => (waiver ? opener.current?.() : setWaiverMissing(true))}
          >
            {t('checkout.pay')}
          </button>
        )}
        {phase === 'closed' && opener.current && (
          <button type="button" className={styles.primary} onClick={() => opener.current?.()}>
            {t('checkout.reopen')}
          </button>
        )}
        {phase !== 'loading' && phase !== 'consent' && phase !== 'open' && phase !== 'activating' && (
          <a className={phase === 'active' ? styles.primary : styles.secondary} href="/">
            {t('checkout.backToApp')}
          </a>
        )}
      </div>

      <p className={styles.legal}>
        {t('checkout.legal')} <a href="/terms">{t('checkout.terms')}</a> · <a href="/privacy">{t('checkout.privacy')}</a> · <a href="/refund">{t('checkout.refund')}</a>
      </p>
    </main>
  );
}

export default CheckoutScreen;
