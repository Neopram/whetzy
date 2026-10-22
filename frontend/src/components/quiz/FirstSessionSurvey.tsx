import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { analyticsAllowed, trackFirstSessionSurvey } from '../../lib/fxAnalytics';
import type { SurveyAnswer } from '../../services/api';
import styles from './FirstSessionSurvey.module.css';

/**
 * 46.6: una pregunta tras la primera sesión de este navegador. Tres respuestas
 * cerradas, sin texto libre, y se guarda sin usuario (ADR-68 punto 3). Si el
 * navegador pide no ser seguido no se enseña: preguntar para tirar la
 * respuesta sería engañar.
 */
export const SURVEY_KEY = 'whetzy.firstSessionSurvey';
const ANSWERS: SurveyAnswer[] = ['a_lot', 'somewhat', 'not_really'];

function seen(): boolean {
  try {
    return localStorage.getItem(SURVEY_KEY) !== null;
  } catch {
    // Sin almacenamiento no se sabe si ya se preguntó: mejor no repetir.
    return true;
  }
}

function markSeen(): void {
  try {
    localStorage.setItem(SURVEY_KEY, 'done');
  } catch {
    /* sin almacenamiento, nada que recordar */
  }
}

export function FirstSessionSurvey() {
  const { t } = useTranslation('producto');
  const [state, setState] = useState<'ask' | 'thanks' | 'hidden'>(() =>
    !seen() && analyticsAllowed() ? 'ask' : 'hidden',
  );
  if (state === 'hidden') return null;
  if (state === 'thanks') {
    return (
      <p className={styles.thanks} role="status">
        {t('survey.thanks')}
      </p>
    );
  }
  const answer = (a: SurveyAnswer) => {
    trackFirstSessionSurvey(a);
    markSeen();
    setState('thanks');
  };
  return (
    <section className={styles.survey} aria-labelledby="first-session-survey">
      <h2 id="first-session-survey" className={styles.question}>
        {t('survey.question')}
      </h2>
      <div className={styles.answers}>
        {ANSWERS.map((a) => (
          <button key={a} type="button" className={styles.answer} onClick={() => answer(a)}>
            {t(`survey.answers.${a}`)}
          </button>
        ))}
      </div>
      <div className={styles.foot}>
        <span className={styles.note}>{t('survey.anonymous')}</span>
        <button
          type="button"
          className={styles.dismiss}
          onClick={() => {
            markSeen();
            setState('hidden');
          }}
        >
          {t('survey.notNow')}
        </button>
      </div>
    </section>
  );
}
