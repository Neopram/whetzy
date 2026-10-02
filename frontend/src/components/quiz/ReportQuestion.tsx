import { useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { reports, type ReportReason } from '../../services/api';
import styles from './ReportQuestion.module.css';

const REASONS: ReportReason[] = ['wrong_answer', 'typo', 'outdated', 'confusing', 'other'];

type Status = 'closed' | 'open' | 'sending' | 'sent' | 'error';

/**
 * «Reportar un problema» bajo el feedback de una pregunta. El backend lo tenía
 * desde P.6 (`POST /reports/question`) y ninguna pantalla lo usaba: una
 * pregunta con la respuesta mal marcada solo se descubría por casualidad.
 */
export function ReportQuestion({ questionId }: { questionId: string }) {
  const { t } = useTranslation();
  const [status, setStatus] = useState<Status>('closed');
  const [reason, setReason] = useState<ReportReason>('wrong_answer');
  const [notes, setNotes] = useState('');
  const formId = useId();

  async function send(e: React.FormEvent) {
    e.preventDefault();
    setStatus('sending');
    try {
      await reports.question(questionId, reason, notes);
      setStatus('sent');
    } catch {
      setStatus('error');
    }
  }

  if (status === 'sent') {
    return <p className={styles.thanks} role="status">{t('quiz.report.sent')}</p>;
  }

  if (status === 'closed') {
    return (
      <button type="button" className={styles.link} onClick={() => setStatus('open')} aria-controls={formId} aria-expanded={false}>
        {t('quiz.report.button')}
      </button>
    );
  }

  return (
    <form id={formId} className={styles.form} onSubmit={send}>
      <fieldset className={styles.fieldset}>
        <legend className={styles.legend}>{t('quiz.report.title')}</legend>
        {REASONS.map((r) => (
          <label key={r} className={styles.option}>
            <input type="radio" name={`${formId}-reason`} value={r} checked={reason === r} onChange={() => setReason(r)} />
            <span>{t(`quiz.report.reasons.${r}`)}</span>
          </label>
        ))}
      </fieldset>
      <label className={styles.notesLabel}>
        <span>{t('quiz.report.notesLabel')}</span>
        <textarea className={styles.notes} rows={2} maxLength={1000} value={notes} onChange={(e) => setNotes(e.target.value)} />
      </label>
      {status === 'error' && <p className={styles.error} role="alert">{t('quiz.report.error')}</p>}
      <div className={styles.actions}>
        <button type="button" className={styles.secondary} onClick={() => setStatus('closed')}>{t('quiz.report.cancel')}</button>
        <button type="submit" className={styles.primary} disabled={status === 'sending'}>{t('quiz.report.send')}</button>
      </div>
    </form>
  );
}
