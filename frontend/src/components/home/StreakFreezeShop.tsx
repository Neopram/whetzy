import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '../common/Button';
import { useApi } from '../../hooks/useApi';
import { ApiError, economy, type StreakFreezeQuote } from '../../services/api';
import { useAppStore } from '../../stores/useAppStore';
import styles from './StreakFreezeShop.module.css';

/** Id por intento de compra. Se reutiliza en los reintentos del mismo intento
 *  (el backend no cobra dos veces el mismo id) y se descarta al terminar. */
function newRequestId(): string {
  const c: Crypto = globalThis.crypto;
  if (typeof c.randomUUID === 'function') return c.randomUUID();
  // Fuera de contexto seguro no hay randomUUID: UUID v4 a mano.
  const b = c.getRandomValues(new Uint8Array(16));
  b[6] = (b[6] & 0x0f) | 0x40;
  b[8] = (b[8] & 0x3f) | 0x80;
  const h = [...b].map((x) => x.toString(16).padStart(2, '0')).join('');
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;
}

type Phase = 'idle' | 'confirm' | 'buying' | 'done' | 'error';

/** Comodines de racha: cuántos tienes, por qué no puedes comprar (si no puedes)
 *  y la compra con créditos en dos toques (35.3). */
export function StreakFreezeShop() {
  const { t } = useTranslation();
  const updateUser = useAppStore((s) => s.updateUser);
  const quote = useApi(() => economy.streakFreeze(), []);
  const [phase, setPhase] = useState<Phase>('idle');
  const [message, setMessage] = useState<string | null>(null);
  const requestId = useRef<string | null>(null);

  const q: StreakFreezeQuote | null = quote.data;
  if (!q) return null; // sin datos (cargando o sin sesión) no se promete nada

  const blockedText = q.blocked_by
    ? t(`home.freezeShop.blocked.${q.blocked_by}`, { price: q.price, balance: q.balance, max: q.max_held, perWeek: q.max_per_week })
    : null;

  async function confirmBuy() {
    requestId.current ??= newRequestId();
    setPhase('buying');
    try {
      const r = await economy.buyStreakFreeze(requestId.current);
      updateUser({ streakFreezeAvailable: r.held });
      requestId.current = null;
      setMessage(t('home.freezeShop.bought', { count: r.held }));
      setPhase('done');
      quote.reload();
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        // Un tope o el saldo: el intento termina, el id no se reutiliza.
        requestId.current = null;
        setMessage(t(`home.freezeShop.blocked.${e.message}`, { price: q!.price, balance: q!.balance, max: q!.max_held, perWeek: q!.max_per_week }));
        quote.reload();
      } else {
        // Red o servidor: se conserva el id, reintentar no cobra dos veces.
        setMessage(t('home.freezeShop.retry'));
      }
      setPhase('error');
    }
  }

  return (
    <div className={styles.shop}>
      <p className={styles.status}>
        {t('home.freezeShop.status', { held: q.held, max: q.max_held, balance: q.balance })}
      </p>

      {phase === 'confirm' || phase === 'buying' ? (
        <div className={styles.confirm} role="group" aria-label={t('home.freezeShop.confirmTitle', { price: q.price })}>
          <p className={styles.confirmText}>{t('home.freezeShop.confirmTitle', { price: q.price })}</p>
          <div className={styles.actions}>
            <Button size="sm" variant="primary" loading={phase === 'buying'} onClick={confirmBuy}>
              {t('home.freezeShop.confirm')}
            </Button>
            <Button size="sm" variant="ghost" disabled={phase === 'buying'} onClick={() => setPhase('idle')}>
              {t('home.freezeShop.cancel')}
            </Button>
          </div>
        </div>
      ) : (
        <Button
          size="sm"
          variant="secondary"
          disabled={!q.can_buy}
          aria-describedby={blockedText ? 'freeze-blocked' : undefined}
          onClick={() => { setMessage(null); setPhase('confirm'); }}
        >
          {t('home.freezeShop.buy', { price: q.price })}
        </Button>
      )}

      {blockedText && phase !== 'confirm' && (
        <p id="freeze-blocked" className={styles.hint}>{blockedText}</p>
      )}
      <p className={styles.live} aria-live="polite">{message}</p>
    </div>
  );
}
