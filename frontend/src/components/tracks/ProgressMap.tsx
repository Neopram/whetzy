import { useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import type { CurriculumModule } from '../../services/api';
import styles from './ProgressMap.module.css';

interface ProgressMapProps {
  modules: CurriculumModule[];
  lang: 'es' | 'en';
  onSelect: (mod: CurriculumModule) => void;
}

// Zigzag layout: 3 columns
const COLS = 3;
const NODE_R = 28;
const COL_GAP = 100;
const ROW_GAP = 90;
const PAD_X = 50;
const PAD_Y = 50;

function nodePos(i: number): [number, number] {
  const row = Math.floor(i / COLS);
  const col = i % COLS;
  const x = row % 2 === 0 ? PAD_X + col * COL_GAP : PAD_X + (COLS - 1 - col) * COL_GAP;
  const y = PAD_Y + row * ROW_GAP;
  return [x, y];
}

function statusColor(status: CurriculumModule['status'], mastery: number) {
  if (status === 'locked') return 'var(--le-border)';
  if (mastery >= 0.8) return 'var(--le-green)';
  if (mastery >= 0.4) return 'var(--le-brand)';
  return 'var(--le-orange)';
}

function statusBg(status: CurriculumModule['status'], mastery: number) {
  if (status === 'locked') return 'var(--le-border-light)';
  if (mastery >= 0.8) return 'var(--le-green-light)';
  if (mastery >= 0.4) return 'var(--le-brand-light)';
  return 'var(--le-orange-light)';
}

function buildPath(positions: [number, number][]): string {
  if (positions.length < 2) return '';
  const pts = positions.map(([x, y]) => `${x},${y}`).join(' L ');
  return `M ${pts}`;
}

export function ProgressMap({ modules, lang, onSelect }: ProgressMapProps) {
  const { t } = useTranslation();
  const positions = modules.map((_, i) => nodePos(i));
  const totalH = modules.length > 0 ? PAD_Y * 2 + Math.ceil(modules.length / COLS) * ROW_GAP : 200;
  const totalW = PAD_X * 2 + (COLS - 1) * COL_GAP;
  const unlockedCount = modules.filter(m => m.status !== 'locked').length;
  const progressPath = buildPath(positions.slice(0, unlockedCount));
  const fullPath = buildPath(positions);
  const svgRef = useRef<SVGSVGElement>(null);

  const handleKey = useCallback((e: React.KeyboardEvent, mod: CurriculumModule) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(mod); }
  }, [onSelect]);

  return (
    <div className={styles.container}>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${totalW} ${totalH}`}
        className={styles.svg}
        role="list"
        aria-label={t('tracks.skillMap')}
      >
        <path className={styles.trackPath} d={fullPath} />
        {progressPath && (
          <motion.path
            className={styles.trackPathProgress}
            d={progressPath}
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.2, ease: 'easeInOut', delay: 0.3 }}
          />
        )}

        {modules.map((mod, i) => {
          const [cx, cy] = positions[i];
          const mastery = mod.average_mastery ?? 0;
          const locked = mod.status === 'locked';
          const completed = mod.status === 'completed';
          const isCurrent = !locked && !completed && i === unlockedCount - 1;
          const fill = statusColor(mod.status, mastery);
          const bg = statusBg(mod.status, mastery);
          const mastered = (mod.skills ?? []).filter((sk) => sk.mastered).length;
          const label = lang === 'es' ? mod.name_es : mod.name_en;
          const shortLabel = label.length > 12 ? label.slice(0, 11) + '…' : label;
          const circleLen = 2 * Math.PI * (NODE_R - 4);

          return (
            <g
              key={mod.id}
              role="listitem"
              tabIndex={locked ? -1 : 0}
              className={styles.nodeGroup}
              onClick={() => !locked && onSelect(mod)}
              onKeyDown={(e) => !locked && handleKey(e, mod)}
              aria-label={`${label} — ${t('tracks.moduleMastered', { mastered, total: mod.skills?.length ?? 0 })}`}
              aria-disabled={locked}
            >
              {isCurrent && (
                <motion.circle
                  cx={cx} cy={cy} r={NODE_R + 8}
                  fill="none"
                  stroke="var(--le-brand)"
                  strokeWidth={2}
                  strokeOpacity={0.3}
                  animate={{ scale: [1, 1.15, 1], opacity: [0.4, 0.1, 0.4] }}
                  transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                  style={{ transformOrigin: `${cx}px ${cy}px` }}
                />
              )}
              {isCurrent && (
                <circle cx={cx} cy={cy} r={NODE_R + 4} fill="var(--le-brand)" opacity={0.12} />
              )}
              <motion.circle
                cx={cx} cy={cy} r={NODE_R}
                fill={bg}
                stroke={fill}
                strokeWidth={locked ? 2 : 3}
                className={styles.nodeCircle}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: i * 0.05, type: 'spring', stiffness: 300, damping: 20 }}
                style={{ transformOrigin: `${cx}px ${cy}px` }}
              />
              {!locked && mastery > 0 && (
                <motion.circle
                  cx={cx} cy={cy}
                  r={NODE_R - 4}
                  fill="none"
                  stroke={fill}
                  strokeWidth={4}
                  strokeOpacity={0.4}
                  strokeLinecap="round"
                  strokeDasharray={`0 ${circleLen}`}
                  strokeDashoffset={circleLen * 0.25}
                  animate={{ strokeDasharray: `${circleLen * mastery} ${circleLen}` }}
                  transition={{ duration: 0.8, delay: i * 0.05 + 0.4, ease: 'easeOut' }}
                />
              )}
              {locked ? (
                <text x={cx} y={cy} className={styles.nodeIcon} fontSize={16}>&#x1F512;</text>
              ) : completed ? (
                <text x={cx} y={cy} className={styles.nodeIcon} fontSize={18} fill="var(--le-green)">&#x2713;</text>
              ) : (
                <text x={cx} y={cy} className={styles.nodeIcon} fill={fill} fontWeight="900" fontSize={15}>
                  {String(i + 1)}
                </text>
              )}
              {!locked && mastered > 0 && (
                <g transform={`translate(${cx + NODE_R - 6}, ${cy - NODE_R + 6})`}>
                  <circle r={9} fill={fill} />
                  <text className={styles.masteryBadge} fill="#fff">{mastered}</text>
                </g>
              )}
              <text
                x={cx} y={cy + NODE_R + 14}
                className={styles.nodeLabel}
                fill={locked ? 'var(--le-text-muted)' : 'var(--le-text-secondary)'}
              >
                {shortLabel}
              </text>
            </g>
          );
        })}
      </svg>

      <div className={styles.legend}>
        {[
          { color: 'var(--le-green)',  key: 'tracks.legendMastered' },
          { color: 'var(--le-brand)',  key: 'tracks.legendInProgress' },
          { color: 'var(--le-orange)', key: 'tracks.legendStarted' },
          { color: 'var(--le-border)', key: 'tracks.legendLocked' },
        ].map(({ color, key }) => (
          <div key={key} className={styles.legendItem}>
            <div className={styles.legendDot} style={{ background: color }} />
            <span>{t(key)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
