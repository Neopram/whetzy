import { useTranslation } from 'react-i18next';
import type { GlossaryTerm } from '../../services/api';
import styles from './TermCard.module.css';

interface Props {
  term: GlossaryTerm;
  lang: 'es' | 'en';
  onClose: () => void;
}

/**
 * The bilingual pair is the point, not a nicety: someone learning Python in
 * Spanish still has to read English documentation and sit English interviews,
 * so both labels are always shown together, whichever language they are
 * studying in. The definition follows the language they are reading.
 */
export function TermCard({ term, lang, onClose }: Props) {
  const { t } = useTranslation();
  const definition = lang === 'es' ? term.definition_es : term.definition_en;

  return (
    <div className={styles.card} role="dialog" aria-label={term.term_es}>
      <div className={styles.head}>
        <div className={styles.pair}>
          <span className={styles.es}>{term.term_es}</span>
          <span className={styles.arrow}>·</span>
          <span className={styles.en}>{term.term_en}</span>
        </div>
        <button
          type="button"
          className={styles.close}
          onClick={onClose}
          aria-label={t('quiz.close')}
        >
          ✕
        </button>
      </div>
      <p className={styles.definition}>{definition}</p>
      {term.source && <p className={styles.source}>📚 {term.source}</p>}
    </div>
  );
}
