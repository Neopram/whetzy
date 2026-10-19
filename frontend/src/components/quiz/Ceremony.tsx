/**
 * Ceremonias de nivel 4 (46.7, docs/PLAN_UI_AVANZADA.md §6.0 y §6.4): subir de
 * nivel, insignia nueva y racha en hito. Solo lo que el servidor dice que pasó
 * (`QuizAnswerResponse.events`, 46.1b); el cliente no inventa recompensas.
 *
 * Como mucho UNA ceremonia por sesión: si hubo varias, la de más peso se
 * celebra y el resto sale como tarjetas quietas en el resumen. Se puede saltar
 * desde el primer fotograma, se cierra sola a los 3 s y, con movimiento
 * reducido, es una tarjeta estática. El ascenso de liga no está: el servidor
 * no aplica ascensos todavía, y celebrar uno que no ocurre sería mentir.
 */
import { useEffect, useRef } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { Button } from '../common/Button';
import { GameIcon, type GameIconName } from '../common/AppIcon';
import { emit } from '../../lib/feedbackFx';
import { springs } from '../../lib/motion';
import type { ServerFxEvent } from '../../services/api';
import styles from './Ceremony.module.css';

export type CeremonyEvent = Extract<ServerFxEvent, { type: 'level_up' | 'badge_earned' | 'streak_milestone' }>;

// Peso de cada ceremonia: si coinciden, gana la primera de esta lista.
const ORDER: CeremonyEvent['type'][] = ['level_up', 'streak_milestone', 'badge_earned'];

export function isCeremony(e: ServerFxEvent): e is CeremonyEvent {
  return (ORDER as string[]).includes(e.type);
}

/** De todos los hitos de una sesión: la ceremonia (o ninguna) y el resto como tarjetas. */
export function pickCeremony(events: ServerFxEvent[]): { ceremony: CeremonyEvent | null; cards: CeremonyEvent[] } {
  const all = events.filter(isCeremony);
  const sorted = [...all].sort((a, b) => ORDER.indexOf(a.type) - ORDER.indexOf(b.type));
  return { ceremony: sorted[0] ?? null, cards: sorted.slice(1) };
}

const ICON: Record<CeremonyEvent['type'], GameIconName> = {
  level_up: 'corona',
  badge_earned: 'trofeo',
  streak_milestone: 'racha',
};

const FX: Record<CeremonyEvent['type'], 'level_up' | 'badge' | 'streak'> = {
  level_up: 'level_up',
  badge_earned: 'badge',
  streak_milestone: 'streak',
};

export function useCeremonyTitle() {
  const { t } = useTranslation('producto');
  return (e: CeremonyEvent, badgeName?: string) =>
    e.type === 'level_up'
      ? t('fx.ceremony.levelUp', { level: e.payload.level })
      : e.type === 'streak_milestone'
        ? t('fx.ceremony.streak', { count: e.payload.days })
        : badgeName
          ? t('fx.ceremony.badgeNamed', { name: badgeName })
          : t('fx.ceremony.badge');
}

const AUTO_CLOSE_MS = 3000;

export function Ceremony({
  event,
  badgeName,
  onDone,
}: {
  event: CeremonyEvent;
  badgeName?: string;
  onDone: (skipped: boolean) => void;
}) {
  const { t } = useTranslation('producto');
  const title = useCeremonyTitle();
  const reduce = useReducedMotion();
  const done = useRef(false);
  const close = (skipped: boolean) => {
    if (done.current) return;
    done.current = true;
    onDone(skipped);
  };

  useEffect(() => {
    emit({ type: FX[event.type] });
    const id = window.setTimeout(() => close(false), AUTO_CLOSE_MS);
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') close(true); };
    window.addEventListener('keydown', onKey);
    return () => { window.clearTimeout(id); window.removeEventListener('keydown', onKey); };
    // Una vez por ceremonia: `close` y el evento no cambian mientras está abierta.
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className={styles.backdrop} role="dialog" aria-modal="true" aria-labelledby="ceremony-title">
      <motion.div
        className={styles.card}
        initial={reduce ? false : { scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={springs.bouncy}
      >
        <GameIcon name={ICON[event.type]} size={72} />
        <h2 id="ceremony-title" className={styles.title}>{title(event, badgeName)}</h2>
        <Button type="button" full autoFocus onClick={() => close(true)}>
          {t('fx.ceremony.skip')}
        </Button>
      </motion.div>
    </div>
  );
}

/** Las demás de la sesión: tarjetas quietas en el resumen, sin sonido. */
export function CeremonyCards({ cards, badgeNames }: { cards: CeremonyEvent[]; badgeNames: Map<string, string> }) {
  const { t } = useTranslation('producto');
  const title = useCeremonyTitle();
  if (cards.length === 0) return null;
  return (
    <section className={styles.cards} aria-label={t('fx.ceremony.alsoThisSession')}>
      <h2 className={styles.cardsTitle}>{t('fx.ceremony.alsoThisSession')}</h2>
      <ul className={styles.cardList}>
        {cards.map((c, i) => (
          <li key={`${c.type}-${i}`} className={styles.cardItem}>
            <GameIcon name={ICON[c.type]} size={28} />
            <span>{title(c, c.type === 'badge_earned' ? badgeNames.get(c.payload.badge_id) : undefined)}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
