import { useTranslation } from 'react-i18next';
import styles from './SourceLine.module.css';

interface Props {
  source: string;
}

/** `Label (https://…)` — the shape the authored bank uses when a source is online. */
const TRAILING_URL = /^(.*?)\s*\((https?:\/\/[^\s)]+)\)\s*$/;

/**
 * A citation the learner can actually follow.
 *
 * Every question in the bank cites a canonical source, but until now the
 * citation was decoration: a string you could read and not reach. Where the
 * source carries a URL it becomes a link, which turns the red line "every
 * question cites its source" into instruction rather than a claim.
 *
 * Sources that are books (Fluent Python, Clean Code) have no canonical URL and
 * stay plain text — pointing those at a shop would be an affiliate link wearing
 * a citation's clothes.
 */
export function SourceLine({ source }: Props) {
  const { t } = useTranslation();
  const match = TRAILING_URL.exec(source);

  if (!match) {
    return <p className={styles.line}>📚 {t('quiz.source')}: {source}</p>;
  }

  const [, label, url] = match;
  return (
    <p className={styles.line}>
      📚 {t('quiz.source')}: {label}{' '}
      <a
        className={styles.link}
        href={url}
        target="_blank"
        rel="noopener noreferrer"
      >
        {t('quiz.readSource')}
      </a>
    </p>
  );
}
