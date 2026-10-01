import { Link, useNavigate } from '@tanstack/react-router';
import { ArrowRight, BookOpen, Flame, RotateCcw } from 'lucide-react';
import { dashboard } from '../fixtures/dashboard';
import { curriculum } from '../fixtures/curriculum';
import { readiness, readinessScore } from '../fixtures/readiness';
import { useSettings } from '../i18n';
import { ReadinessGauge } from '../components/ui/ReadinessGauge';
import { ProgressBar } from '../components/ui/ProgressBar';
import { WButton } from '../components/ui/WButton';
import { WCard } from '../components/ui/WCard';
import { Chip } from '../components/ui/Chip';
import styles from './pages.module.css';
export function Home() {
 const { t, pick } = useSettings(); const navigate = useNavigate();
 const nextSkill = curriculum.modules.flatMap(module => module.skills).find(skill => !skill.lesson_seen);
 const readyCount = readiness.domains.filter(domain => domain.ready).length;
 return <><div className={styles.pageHead}><p className={styles.eyebrow}>{t('today')}</p><h1>{t('preparation')}</h1><p>{t('todayNote')}</p></div>
 <div className={styles.homeGrid}><section className={styles.readinessPanel} aria-label={t('readiness')}><div className={styles.heroHead}><p className={styles.eyebrow}>{t('goal')}</p><h1>PCEP</h1><p>Python Entry-Level Programmer</p><Link className={styles.textLink} to="/preparacion/$trackId" params={{trackId:'track09'}}>{t('examDomains')} <ArrowRight size={15}/></Link></div><div className={styles.gaugeArea}><ReadinessGauge value={readinessScore} ready={readyCount} total={readiness.domains.length}/><p className={styles.threshold}>{t('threshold')}</p></div></section>
 <section className={styles.nextPanel} aria-label={t('nextStep')}><p className={styles.nextTitle}>{t('nextStep')}</p><div className={styles.nextName}><BookOpen size={22}/><span>{nextSkill ? pick(nextSkill) : t('allClear')}</span></div><p>{t('lesson')} · {nextSkill ? pick(nextSkill) : t('allClear')} · {t('minutes')}</p><WButton variant="primary" onClick={() => nextSkill && navigate({to:'/leccion/$skillId',params:{skillId:nextSkill.skill_id}})}>{t('continue')} <ArrowRight size={17}/></WButton></section></div>
 <div className={`${styles.split} ${styles.section}`}><WCard className={styles.smallPanel}><div className={styles.sectionHead}><h2>{t('dueReview')}</h2><RotateCcw size={18} className={styles.muted}/></div>{dashboard.reviews_due ? <><div className={styles.reviewCount}><strong>{dashboard.reviews_due}</strong><span className={styles.muted}>{t('questionsDue')}</span></div><p>{t('reviewDescription')}</p><Link className={styles.textLink} to="/practicar">{t('practiceReview')} <ArrowRight size={15}/></Link></> : <p>{t('allClear')}</p>}</WCard>
 <WCard className={styles.smallPanel}><div className={styles.sectionHead}><h2>{t('streak')}</h2><Flame size={18} className={styles.muted}/></div><div className={styles.streakStats}><div className={styles.streakItem}><strong>{dashboard.current_streak}</strong><span>{t('currentStreak')}</span></div><div className={styles.streakItem}><strong>{dashboard.max_streak}</strong><span>{t('bestStreak')}</span></div><div className={styles.streakItem}><strong>{dashboard.streak_freeze_available}</strong><span>{t('freeze')}</span></div></div></WCard></div>
 <section className={styles.section}><div className={styles.sectionHead}><h2>{t('yourTracks')}</h2><Link to="/rutas" className={styles.textLink}>{t('seeAll')} <ArrowRight size={15}/></Link></div><div className={styles.trackList}>{dashboard.tracks.map(track => <Link key={track.track_id} to="/rutas/$trackId" params={{trackId:track.track_id}} className={styles.trackRow}><span className={styles.trackIcon} aria-hidden="true">{track.icon}</span><span className={styles.trackBody}><strong>{pick(track)}</strong><ProgressBar value={track.average_mastery} label={`${pick(track)} ${t('mastery')}`}/><span className={styles.trackNumbers}><span>{track.skills_mastered}/{track.total_skills} {t('mastered')}</span><b>{Math.round(track.average_mastery * 100)}%</b></span></span><ArrowRight className={styles.trackArrow} size={18}/></Link>)}</div></section>
 <section className={styles.section}><div className={styles.sectionHead}><h2>{t('examDomains')}</h2><Chip tone="attention">{t('goal')}</Chip></div><div className={styles.domainGrid}>{readiness.domains.map(domain => <WCard key={domain.domain_id}><div className={styles.sectionHead}><strong>{pick(domain)}</strong><span className={styles.mono}>{Math.round(domain.p_known_mean * 100)}%</span></div><ProgressBar value={domain.p_known_mean} label={pick(domain)}/><p className={styles.placeholderNote}>{domain.weight_pct}% {t('weight')}</p></WCard>)}</div></section></>;
}
