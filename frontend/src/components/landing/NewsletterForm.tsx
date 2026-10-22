import { useId, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import styles from './NewsletterForm.module.css';
import { API_BASE_URL } from '../../services/api';

/* Alta al newsletter (26.10). Habla con el endpoint real, `POST /newsletter/subscribe`
   (doble opt-in: el alta no vale hasta confirmar el correo). El backend responde 202
   igual exista ya la dirección o no, así que aquí «enviado» significa «solicitud
   aceptada», nunca «ya estás suscrito». */

type Status = 'idle' | 'sending' | 'sent' | 'invalid' | 'error';

export function NewsletterForm() {
  const { t, i18n } = useTranslation();
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<Status>('idle');
  const uid = useId();
  const titleId = `${uid}-title`;
  const inputId = `${uid}-email`;
  const msgId = `${uid}-msg`;

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (status === 'sending') return;
    setStatus('sending');
    try {
      const res = await fetch(`${API_BASE_URL}/newsletter/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          language: i18n.language?.startsWith('en') ? 'en' : 'es',
        }),
      });
      if (res.ok) setStatus('sent');
      else setStatus(res.status === 422 ? 'invalid' : 'error');
    } catch {
      setStatus('error');
    }
  }

  const failed = status === 'invalid' || status === 'error';

  return (
    <form className={styles.form} onSubmit={onSubmit} aria-labelledby={titleId} noValidate>
      <h3 id={titleId} className={styles.title}>{t('landing.newsletter.title')}</h3>
      <p className={styles.body}>{t('landing.newsletter.body')}</p>
      {status === 'sent' ? (
        <p role="status" className={styles.sent}>{t('landing.newsletter.sent')}</p>
      ) : (
        <>
          <label htmlFor={inputId} className={styles.label}>{t('landing.newsletter.emailLabel')}</label>
          <div className={styles.row}>
            <input
              id={inputId}
              className={styles.input}
              type="email"
              name="email"
              autoComplete="email"
              inputMode="email"
              required
              value={email}
              onChange={(ev) => setEmail(ev.target.value)}
              aria-invalid={failed ? true : undefined}
              aria-describedby={failed ? msgId : undefined}
            />
            <button type="submit" className={styles.button} disabled={status === 'sending'}>
              {status === 'sending' ? t('landing.newsletter.sending') : t('landing.newsletter.submit')}
            </button>
          </div>
          {failed && (
            <p id={msgId} role="alert" className={styles.error}>
              {t(status === 'invalid' ? 'landing.newsletter.invalid' : 'landing.newsletter.error')}
            </p>
          )}
        </>
      )}
    </form>
  );
}
