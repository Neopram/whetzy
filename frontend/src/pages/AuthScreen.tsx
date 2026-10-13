import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ApiError, auth, type OAuthProvider, type RegisterPayload } from '../services/api';
import { ForgotPasswordPage } from './ForgotPasswordPage';
import { BrandMark } from '../components/common/BrandMark';
import styles from './AuthScreen.module.css';

// Surface any oauth_error the backend placed in the URL (e.g. email_required).
function getOAuthError(): string | null {
  try {
    const v = new URLSearchParams(window.location.search).get('oauth_error');
    if (!v) return null;
    window.history.replaceState(null, '', window.location.pathname + window.location.hash);
    return v;
  } catch {
    return null;
  }
}

type Mode = 'login' | 'register' | 'forgot';

// Vuelta de OAuth con 2FA activada: el backend dejó el token del segundo paso
// en una cookie HttpOnly y redirige aquí con ?mfa=1 para pedir el código.
function arrivedForMfa(): boolean {
  try {
    const params = new URLSearchParams(window.location.search);
    if (params.get('mfa') !== '1') return false;
    params.delete('mfa');
    const rest = params.toString();
    window.history.replaceState(null, '', window.location.pathname + (rest ? `?${rest}` : '') + window.location.hash);
    return true;
  } catch {
    return false;
  }
}

interface Props {
  onAuthed: () => void;
}

export function AuthScreen({ onAuthed }: Props) {
  const [mode, setMode] = useState<Mode>('register');
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [ageConfirmed, setAgeConfirmed] = useState(false);
  const [language, setLanguage] = useState<'es' | 'en'>('es');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(() => {
    const oauthErr = getOAuthError();
    if (oauthErr === 'email_required') return 'El proveedor no compartió un correo verificado.';
    if (oauthErr === 'provider_error') return 'Error al comunicarse con el proveedor de identidad.';
    if (oauthErr === 'account_inactive') return 'Esta cuenta está desactivada.';
    return oauthErr ?? null;
  });

  const { t, i18n: i18nInst } = useTranslation();

  // Segundo paso del login con 2FA (contraseña correcta, falta el código).
  const [mfaStep, setMfaStep] = useState<boolean>(arrivedForMfa);
  const [mfaToken, setMfaToken] = useState<string | undefined>();
  const [code, setCode] = useState('');

  async function handleMfaSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (code.trim().length < 6) return setError(t('auth.mfaInvalid'));
    setLoading(true);
    try {
      await auth.login2fa(code, mfaToken);
      onAuthed();
    } catch (err) {
      const status = err instanceof ApiError ? err.status : null;
      if (status === 429) setError(t('auth.mfaLocked'));
      else if (status === 401) {
        setError(t('auth.mfaExpired'));
        setMfaStep(false);
        setMode('login');
      } else setError(t('auth.mfaInvalid'));
    } finally {
      setLoading(false);
    }
  }

  // Solo se pintan los proveedores que el servidor tiene configurados. Antes
  // salían los dos siempre y en producción respondían 503 al pulsarlos.
  const [providers, setProviders] = useState<OAuthProvider[]>([]);
  useEffect(() => {
    let vivo = true;
    auth
      .oauthProviders()
      .then((r) => { if (vivo) setProviders(r.providers); })
      .catch(() => { /* sin respuesta, sin botones */ });
    return () => { vivo = false; };
  }, []);

  function handleLangChange(lang: 'es' | 'en') {
    setLanguage(lang);
    void i18nInst.changeLanguage(lang);
  }

  // Idioma inicial: ?lang=es|en, o el del navegador. Antes /auth salía siempre
  // en español porque i18n arranca con lng: 'es' (34.11).
  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get('lang');
    const initial = q === 'es' || q === 'en' ? q : (navigator.language || 'es').toLowerCase().startsWith('en') ? 'en' : 'es';
    if (initial !== 'es') handleLangChange(initial);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    // Client-side validation mirrors the backend schema constraints.
    if (mode === 'register') {
      if (displayName.trim().length < 1) return setError(t('auth.errName'));
      if (!/^[a-zA-Z0-9_.-]{3,50}$/.test(username)) return setError(t('auth.errUsername'));
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return setError(t('auth.errEmail'));
    if (password.length < 8) return setError(t('auth.errPassword'));
    if (mode === 'register' && !ageConfirmed) return setError(t('auth.errAge'));

    setLoading(true);
    try {
      if (mode === 'register') {
        const payload: RegisterPayload = {
          email: email.trim(),
          username: username.trim(),
          display_name: displayName.trim(),
          password,
          language,
          age_confirmed: ageConfirmed,
        };
        await auth.register(payload);
      } else {
        const res = await auth.login(email.trim(), password);
        if ('mfa_required' in res) {
          setMfaToken(res.mfa_token);
          setCode('');
          setMfaStep(true);
          return;
        }
      }
      onAuthed();
    } catch (err) {
      setError(err instanceof Error ? err.message : t('auth.errGeneric'));
    } finally {
      setLoading(false);
    }
  }

  if (mode === 'forgot') return <ForgotPasswordPage onBack={() => setMode('login')} />;
  if (mfaStep) {
    return (
      <div className={styles.screen}>
        <form className={styles.form} onSubmit={handleMfaSubmit} aria-labelledby="mfa-title">
          <h1 id="mfa-title" className={styles.brandName}>{t('auth.mfaTitle')}</h1>
          <p className={styles.tagline}>{t('auth.mfaBody')}</p>
          <label className={styles.field}>
            <span className={styles.label}>{t('auth.mfaCodeLabel')}</span>
            <input
              className={styles.input}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\s+/g, ''))}
              inputMode="text"
              autoComplete="one-time-code"
              maxLength={8}
              autoFocus
            />
          </label>
          {error && <p className={styles.error} role="alert">{error}</p>}
          <button className={styles.submit} type="submit" disabled={loading}>
            {loading ? t('auth.loading') : t('auth.mfaCta')}
          </button>
          <button
            type="button"
            className={styles.forgotLink}
            onClick={() => { setMfaStep(false); setMode('login'); setError(null); }}
          >
            {t('auth.mfaBack')}
          </button>
        </form>
      </div>
    );
  }
  return (
    <div className={styles.screen}>
      <div className={styles.brand}>
        <div className={styles.logo}>
          <BrandMark height={40} />
        </div>
        <h1 className={styles.brandName}>Whet<span className={styles.brandAccent}>zy</span></h1>
        <p className={styles.tagline}>{t('auth.tagline')}</p>
      </div>

      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${mode === 'register' ? styles.tabActive : ''}`}
          onClick={() => { setMode('register'); setError(null); }}
          type="button"
        >
          {t('auth.register')}
        </button>
        <button
          className={`${styles.tab} ${mode === 'login' ? styles.tabActive : ''}`}
          onClick={() => { setMode('login'); setError(null); }}
          type="button"
        >
          {t('auth.login')}
        </button>
      </div>

      <form className={styles.form} onSubmit={handleSubmit}>
        {mode === 'register' && (
          <>
            <label className={styles.field}>
              <span className={styles.label}>{t('auth.nameLabel')}</span>
              <input
                className={styles.input}
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder={t('auth.namePlaceholder')}
                autoComplete="name"
              />
            </label>
            <label className={styles.field}>
              <span className={styles.label}>{t('auth.usernameLabel')}</span>
              <input
                className={styles.input}
                value={username}
                onChange={(e) => setUsername(e.target.value.toLowerCase())}
                placeholder={t('auth.usernamePlaceholder')}
                autoComplete="username"
              />
            </label>
          </>
        )}

        <label className={styles.field}>
          <span className={styles.label}>{t('auth.emailLabel')}</span>
          <input
            className={styles.input}
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="tu@correo.com"
            autoComplete="email"
            inputMode="email"
          />
        </label>

        <label className={styles.field}>
          <span className={styles.label}>{t('auth.passwordLabel')}</span>
          <input
            className={styles.input}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={t('auth.passwordPlaceholder')}
            autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
          />
        </label>
        {mode === 'login' && (
          <button type="button" className={styles.forgotLink} onClick={() => setMode('forgot')}>
            {t('auth.forgotPassword')}
          </button>
        )}

        {mode === 'register' && (
          <div className={styles.field}>
            <span className={styles.label}>{t('auth.langLabel')}</span>
            <div className={styles.langToggle}>
              <button
                type="button"
                className={`${styles.langBtn} ${language === 'es' ? styles.langActive : ''}`}
                onClick={() => handleLangChange('es')}
              >
                Español
              </button>
              <button
                type="button"
                className={`${styles.langBtn} ${language === 'en' ? styles.langActive : ''}`}
                onClick={() => handleLangChange('en')}
              >
                English
              </button>
            </div>
          </div>
        )}

        {mode === 'register' && (
          <label className={styles.field} style={{ flexDirection: 'row', alignItems: 'center', gap: '0.5rem' }}>
            <input
              type="checkbox"
              checked={ageConfirmed}
              onChange={(e) => setAgeConfirmed(e.target.checked)}
            />
            <span>{t('auth.ageLabel')}</span>
          </label>
        )}

        {error && <p className={styles.error} role="alert">⚠️ {error}</p>}

        <button className={styles.submit} type="submit" disabled={loading}>
          {loading ? t('auth.loading') : mode === 'register' ? t('auth.registerCta') : t('auth.loginCta')}
        </button>
      </form>

      {providers.length > 0 && (<>
      <div className={styles.orDivider}>
        <span className={styles.orLine} />
        <span className={styles.orText}>{t('auth.orSeparator')}</span>
        <span className={styles.orLine} />
      </div>

      <div className={styles.socialButtons}>
        {providers.includes('github') && (
        <button
          type="button"
          className={styles.socialBtn}
          onClick={() => auth.startOAuth('github')}
          disabled={loading}
          aria-label={t('auth.continueWithGitHub')}
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
          </svg>
          {t('auth.continueWithGitHub')}
        </button>
        )}

        {providers.includes('google') && (
        <button
          type="button"
          className={styles.socialBtn}
          onClick={() => auth.startOAuth('google')}
          disabled={loading}
          aria-label={t('auth.continueWithGoogle')}
        >
          <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" />
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
          </svg>
          {t('auth.continueWithGoogle')}
        </button>
        )}
      </div>
      </>)}

      <p className={styles.legal}>{t('auth.legal')}</p>
    </div>
  );
}

