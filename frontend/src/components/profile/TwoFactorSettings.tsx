import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ApiError, auth } from '../../services/api';
import styles from './TwoFactorSettings.module.css';

type Setup = { qr_svg: string; secret: string; backup_codes: string[] };
type View = 'idle' | 'setup' | 'disable';

/**
 * Verificación en dos pasos (Yo → Ajustes). El backend la tenía sin pantalla y,
 * hasta el 2026-10-02, el login la ignoraba. Activar exige confirmar un código
 * de la app; desactivar, otro (o uno de respaldo).
 */
export function TwoFactorSettings() {
  const { t } = useTranslation();
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [backupLeft, setBackupLeft] = useState(0);
  const [view, setView] = useState<View>('idle');
  const [setup, setSetup] = useState<Setup | null>(null);
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);

  async function refresh() {
    try {
      const s = await auth.twoFactor.status();
      setEnabled(s.enabled);
      setBackupLeft(s.backup_codes_left);
    } catch {
      setEnabled(null);
    }
  }
  useEffect(() => { void refresh(); }, []);

  async function startSetup() {
    setError(null);
    setDone(null);
    setBusy(true);
    try {
      setSetup(await auth.twoFactor.setup());
      setCode('');
      setView('setup');
    } catch {
      setError(t('twoFactor.error'));
    } finally {
      setBusy(false);
    }
  }

  async function confirm(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (view === 'setup') {
        await auth.twoFactor.enable(code);
        setDone(t('twoFactor.enabledDone'));
      } else {
        await auth.twoFactor.disable(code);
        setDone(t('twoFactor.disabledDone'));
      }
      setView('idle');
      setSetup(null);
      setCode('');
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError && err.status === 400 ? t('twoFactor.badCode') : t('twoFactor.error'));
    } finally {
      setBusy(false);
    }
  }

  if (enabled === null) return null;

  return (
    <div className={styles.block}>
      <div className={styles.head}>
        <span className={styles.label}>{t('twoFactor.title')}</span>
        <span className={enabled ? styles.on : styles.off}>{enabled ? t('twoFactor.on') : t('twoFactor.off')}</span>
      </div>
      {enabled && view === 'idle' && (
        <p className={styles.hint}>{t('twoFactor.backupLeft', { count: backupLeft })}</p>
      )}
      {done && <p className={styles.done} role="status">{done}</p>}

      {view === 'idle' && (
        <button
          type="button"
          className={styles.action}
          onClick={() => (enabled ? (setView('disable'), setCode(''), setError(null), setDone(null)) : void startSetup())}
          disabled={busy}
        >
          {enabled ? t('twoFactor.turnOff') : t('twoFactor.turnOn')}
        </button>
      )}

      {view !== 'idle' && (
        <form className={styles.panel} onSubmit={confirm}>
          {view === 'setup' && setup && (
            <>
              <p className={styles.hint}>{t('twoFactor.scan')}</p>
              <img
                className={styles.qr}
                src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(setup.qr_svg)}`}
                alt={t('twoFactor.qrAlt')}
                width={176}
                height={176}
              />
              <p className={styles.hint}>{t('twoFactor.manual')}</p>
              <code className={styles.secret}>{setup.secret}</code>
              <p className={styles.hint}>{t('twoFactor.backupIntro')}</p>
              <ul className={styles.backup} aria-label={t('twoFactor.backupTitle')}>
                {setup.backup_codes.map((c) => <li key={c}><code>{c}</code></li>)}
              </ul>
            </>
          )}
          <label className={styles.field}>
            <span>{view === 'setup' ? t('twoFactor.confirmLabel') : t('twoFactor.disableLabel')}</span>
            <input
              className={styles.input}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\s+/g, ''))}
              autoComplete="one-time-code"
              maxLength={8}
            />
          </label>
          {error && <p className={styles.error} role="alert">{error}</p>}
          <div className={styles.row}>
            <button type="button" className={styles.secondary} onClick={() => { setView('idle'); setSetup(null); setError(null); }}>
              {t('twoFactor.cancel')}
            </button>
            <button type="submit" className={styles.primary} disabled={busy || code.length < 6}>
              {view === 'setup' ? t('twoFactor.confirm') : t('twoFactor.turnOff')}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
