import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ApiError,
  adminUsers,
  type AdminUserAction,
  type AdminUserDetail,
  type AdminUserListItem,
} from '../../services/api';
import { Button } from '../common/Button';
import { Modal } from '../common/Modal';
import styles from './UsersPanel.module.css';

/**
 * Admin → Usuarios (44.3, docs/PLAN_BACKOFFICE.md B2–B4): buscar, abrir la
 * ficha y actuar sobre la cuenta. Cada acción pide un motivo y queda en el
 * registro (pestaña «Registro»). Sin la verificación en dos pasos el backend
 * responde `2fa_required` y aquí se explica qué hacer.
 */

const ACTIONS: AdminUserAction[] = ['resend_verification', 'close_sessions', 'unlock', 'grant_plan', 'suspend', 'reactivate'];

function errorKey(err: unknown): string {
  if (err instanceof ApiError && err.message === '2fa_required') return 'admin.users.errors.twoFactor';
  if (err instanceof ApiError && err.status === 404) return 'admin.users.errors.notFound';
  return 'admin.users.errors.generic';
}

export function UsersPanel() {
  const { t, i18n } = useTranslation();
  const [q, setQ] = useState('');
  const [results, setResults] = useState<AdminUserListItem[] | null>(null);
  const [total, setTotal] = useState(0);
  const [detail, setDetail] = useState<AdminUserDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState<AdminUserAction | null>(null);
  const [reason, setReason] = useState('');
  const [tier, setTier] = useState<'plus' | 'pro'>('pro');
  const [days, setDays] = useState(30);

  const date = (iso: string | null) => (iso ? new Date(iso).toLocaleDateString(i18n.language) : '—');

  async function search(e: React.FormEvent) {
    e.preventDefault();
    if (q.trim().length < 3) return;
    setBusy(true);
    setError(null);
    setDetail(null);
    try {
      const page = await adminUsers.search(q.trim());
      setResults(page.items);
      setTotal(page.total);
    } catch (err) {
      setError(t(errorKey(err)));
    } finally {
      setBusy(false);
    }
  }

  async function open(id: string) {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      setDetail(await adminUsers.detail(id));
    } catch (err) {
      setError(t(errorKey(err)));
    } finally {
      setBusy(false);
    }
  }

  async function confirm() {
    if (!detail || !pending || !reason.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await adminUsers.act(detail.id, pending, {
        reason: reason.trim(),
        ...(pending === 'grant_plan' ? { tier, days } : {}),
      });
      setNotice(t('admin.users.done', { action: t(`admin.users.actions.${pending}`) }));
      setPending(null);
      setReason('');
      setDetail(await adminUsers.detail(detail.id));
    } catch (err) {
      setError(t(errorKey(err)));
    } finally {
      setBusy(false);
    }
  }

  const copyEmail = () => {
    if (detail) void navigator.clipboard?.writeText(detail.account.email).catch(() => {});
  };

  return (
    <div className={styles.panel}>
      <form className={styles.search} onSubmit={search} role="search">
        <label htmlFor="admin-user-q" className={styles.label}>{t('admin.users.searchLabel')}</label>
        <div className={styles.searchRow}>
          <input
            id="admin-user-q"
            className={styles.input}
            value={q}
            onChange={(e) => setQ(e.target.value)}
            minLength={3}
            placeholder={t('admin.users.searchPlaceholder')}
          />
          <Button type="submit" disabled={busy || q.trim().length < 3}>{t('admin.users.search')}</Button>
        </div>
        <p className={styles.hint}>{t('admin.users.searchHint')}</p>
      </form>

      {error && <p className={styles.error} role="alert">{error}</p>}
      {notice && <p className={styles.notice} role="status">{notice}</p>}

      {results && !detail && (
        <section aria-label={t('admin.users.results', { count: total })}>
          <h3 className={styles.h3}>{t('admin.users.results', { count: total })}</h3>
          {results.length === 0 ? (
            <p className={styles.hint}>{t('admin.users.empty')}</p>
          ) : (
            <ul className={styles.list}>
              {results.map((u) => (
                <li key={u.id}>
                  <button type="button" className={styles.row} onClick={() => void open(u.id)}>
                    <span className={styles.username}>{u.username}</span>
                    <span className={styles.muted}>{u.email_masked}</span>
                    <span className={styles.muted}>{date(u.created_at)}</span>
                    <span className={u.status === 'active' ? styles.ok : styles.warn}>{t(`admin.users.status.${u.status}`)}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {detail && (
        <article className={styles.detail} aria-label={t('admin.users.detailTitle', { username: detail.account.username })}>
          <div className={styles.detailHead}>
            <h3 className={styles.h3}>{t('admin.users.detailTitle', { username: detail.account.username })}</h3>
            <Button type="button" variant="ghost" size="sm" onClick={() => setDetail(null)}>{t('admin.users.back')}</Button>
          </div>

          <dl className={styles.grid}>
            <dt>{t('admin.users.fields.email')}</dt>
            <dd className={styles.email}>
              <span>{detail.account.email}</span>
              <button type="button" className={styles.link} onClick={copyEmail}>{t('admin.users.copyEmail')}</button>
            </dd>
            <dt>{t('admin.users.fields.status')}</dt><dd>{t(`admin.users.status.${detail.account.status}`)}</dd>
            <dt>{t('admin.users.fields.verified')}</dt><dd>{detail.account.email_verified ? t('admin.users.yes') : t('admin.users.no')}</dd>
            <dt>{t('admin.users.fields.created')}</dt><dd>{date(detail.account.created_at)}</dd>
            <dt>{t('admin.users.fields.lastActive')}</dt><dd>{date(detail.account.last_active)}</dd>
            <dt>{t('admin.users.fields.plan')}</dt>
            <dd>{detail.plan.subscription_tier ?? '—'}{detail.plan.granted_tier && ` · ${t('admin.users.granted', { tier: detail.plan.granted_tier, until: date(detail.plan.granted_tier_expires_at) })}`}</dd>
            <dt>{t('admin.users.fields.progress')}</dt>
            <dd>{t('admin.users.progress', { skills: detail.progress.skills_practiced, answers: detail.progress.answers })}</dd>
            <dt>{t('admin.users.fields.gdpr')}</dt>
            <dd>{detail.gdpr.pending.length ? detail.gdpr.pending.map((g) => g.type).join(', ') : '—'}</dd>
          </dl>

          {detail.security.recent_events.length > 0 && (
            <>
              <h4 className={styles.h4}>{t('admin.users.fields.security')}</h4>
              <ul className={styles.events}>
                {detail.security.recent_events.map((e, i) => (
                  <li key={i}>{date(e.timestamp)} · {e.action} · {e.result}</li>
                ))}
              </ul>
            </>
          )}

          <h4 className={styles.h4}>{t('admin.users.actionsTitle')}</h4>
          <div className={styles.actions}>
            {ACTIONS.map((a) => (
              <Button key={a} type="button" variant={a === 'suspend' ? 'danger' : 'secondary'} size="sm" onClick={() => setPending(a)} disabled={busy}>
                {t(`admin.users.actions.${a}`)}
              </Button>
            ))}
          </div>
        </article>
      )}

      <Modal
        open={pending !== null}
        onClose={() => { setPending(null); setReason(''); }}
        title={pending ? t(`admin.users.actions.${pending}`) : ''}
        footer={
          <Button type="button" onClick={() => void confirm()} disabled={busy || !reason.trim()}>
            {t('admin.users.confirm')}
          </Button>
        }
      >
        {pending === 'grant_plan' && (
          <div className={styles.grantRow}>
            <label className={styles.label}>
              {t('admin.users.tier')}
              <select className={styles.control} value={tier} onChange={(e) => setTier(e.target.value as 'plus' | 'pro')}>
                <option value="plus">Plus</option>
                <option value="pro">Pro</option>
              </select>
            </label>
            <label className={styles.label}>
              {t('admin.users.days')}
              <input className={styles.control} type="number" min={1} max={90} value={days} onChange={(e) => setDays(Number(e.target.value))} />
            </label>
          </div>
        )}
        <label className={styles.label} htmlFor="admin-action-reason">{t('admin.users.reason')}</label>
        <textarea
          id="admin-action-reason"
          className={styles.control}
          rows={3}
          maxLength={500}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
        <p className={styles.hint}>{t('admin.users.reasonHint')}</p>
      </Modal>
    </div>
  );
}
