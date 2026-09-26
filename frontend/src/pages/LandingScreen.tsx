import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import styles from './LandingScreen.module.css';
import heroShotEs from '../assets/hero-quiz-es.jpg';
import heroShotEn from '../assets/hero-quiz-en.jpg';
import readinessShotEs from '../assets/readiness-es.jpg';
import readinessShotEn from '../assets/readiness-en.jpg';
import { CATALOG_QUESTIONS, CATALOG_TRACKS } from '../lib/catalog';
import {
  COMPARISON_CHECKED_ON,
  COMPARISON_COMPETITORS,
  COMPARISON_ROWS,
  type ComparisonCell,
} from '../lib/comparison';
import { TUTOR_DAILY_LIMIT_PRO } from '../lib/plans';

/* La landing (30.1, 2026-09-24) solo afirma lo que el producto hace hoy:
   cifras de lib/catalog.ts (vigiladas por scripts/check_docs.py), capturas
   reales de la app y una comparativa con fuente y fecha. La versión anterior
   traía testimonios con nombre, «1.2M learners», «240+ tracks», precios sin
   aprobar y copia de otro producto (idiomas). Toda la copia vive en i18n. */

type Lang = 'es' | 'en';

/** ?lang=en|es manda; si no, el idioma del navegador. En el pre-render (sin
 *  window) sale español, que es lo que se sirve como HTML estático. */
function resolveLandingLang(): Lang {
  if (typeof window === 'undefined') return 'es';
  const q = new URLSearchParams(window.location.search).get('lang');
  if (q === 'es' || q === 'en') return q;
  return (navigator.language || 'es').toLowerCase().startsWith('en') ? 'en' : 'es';
}

const featureIcons = [
  (
      <svg className={styles.featureSvg} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
      </svg>
  ),
  (
      <svg className={styles.featureSvg} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m5 8 6 6" />
        <path d="m4 14 6-6 2-3" />
        <path d="M2 5h12" />
        <path d="M7 2h1" />
        <path d="m22 22-5-10-5 10" />
        <path d="M14 18h6" />
      </svg>
  ),
  (
      <svg className={styles.featureSvg} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 8V4H8" />
        <rect width="16" height="12" x="4" y="8" rx="2" />
        <path d="M2 14h2" />
        <path d="M20 14h2" />
        <path d="M15 13v2" />
        <path d="M9 13v2" />
      </svg>
  ),
];

const stepIcons = [
  (
      <svg className={styles.stepSvg} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
      </svg>
  ),
  (
      <svg className={styles.stepSvg} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
      </svg>
  ),
  (
      <svg className={styles.stepSvg} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6" />
        <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18" />
        <path d="M4 22h16" />
        <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22" />
        <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22" />
        <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z" />
      </svg>
  ),
];

function CellMark({ value, lang, notChecked }: { value: ComparisonCell; lang: Lang; notChecked: string }) {
  if (value === true) {
    return (
      <span className={styles.cellCheck} aria-label="✓">
        <svg className={styles.cellIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      </span>
    );
  }
  if (value === false) {
    return (
      <span className={styles.cellMinus} aria-label="—">
        <svg className={styles.cellIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
      </span>
    );
  }
  if (value === null) return <span className={styles.cellText}>{notChecked}</span>;
  return <span className={styles.cellText}>{value[lang]}</span>;
}

export default function LandingScreen() {
  const { t, i18n } = useTranslation();
  const [lang, setLang] = useState<Lang>('es');
  const [hasSession, setHasSession] = useState(false);

  useEffect(() => {
    const l = resolveLandingLang();
    setLang(l);
    if (i18n.language !== l) void i18n.changeLanguage(l);
    document.documentElement.lang = l;
    try {
      setHasSession(document.cookie.split(';').some((c) => c.trim().startsWith('whetzy_logged_in=')));
    } catch {
      setHasSession(false);
    }
  }, [i18n]);

  useEffect(() => {
    document.title = t('landing.metaTitle');
  }, [t, lang]);

  // Las CTA son enlaces, no botones con onClick: navegan aunque el JS aún no
  // haya cargado (la landing se sirve pre-renderizada) y son lo que un lector
  // de pantalla espera de algo que lleva a otra página.
  const ctaHref = hasSession ? '/' : '/auth';
  const nf = new Intl.NumberFormat(lang === 'es' ? 'es-ES' : 'en-US');
  const counts = { tracks: CATALOG_TRACKS, questions: nf.format(CATALOG_QUESTIONS) };
  const features = (['f1', 'f2', 'f3'] as const).map((k, i) => ({
    icon: featureIcons[i],
    title: t(`landing.${k}.title`),
    body: t(`landing.${k}.body`),
    tag: t(`landing.${k}.tag`),
  }));
  const steps = (['s1', 's2', 's3'] as const).map((k, i) => ({
    icon: stepIcons[i],
    title: t(`landing.${k}.title`),
    body: t(`landing.${k}.body`),
  }));
  const plans = (['planFree', 'planPro', 'planProMax', 'planCreator'] as const).map((k) => ({
    key: k,
    name: t(`landing.${k}.name`),
    price: t(`landing.${k}.price`),
    note: t(`landing.${k}.note`),
    blurb: t(`landing.${k}.blurb`),
    perks: t(`landing.${k}.perks`, { returnObjects: true, ...counts, tutorLimit: TUTOR_DAILY_LIMIT_PRO }) as string[],
    cta: t(`landing.${k}.cta`),
    featured: k === 'planFree',
  }));
  const showCompare = COMPARISON_ROWS.length > 0;
  const checkedOn = COMPARISON_CHECKED_ON
    ? new Date(`${COMPARISON_CHECKED_ON}T00:00:00Z`).toLocaleDateString(lang === 'es' ? 'es-ES' : 'en-US', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' })
    : '';
  const notChecked = lang === 'es' ? 'No comprobado' : 'Not checked';

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <nav className={styles.navContainer}>
          <div className={styles.brandGroup}>
            <span className={styles.logoBadge}>W</span>
            <span className={styles.brandTitle}>Whetzy</span>
          </div>
          <div className={styles.navMenu}>
            <a href="#features" className={styles.navLink}>{t('landing.nav.features')}</a>
            <a href="#how" className={styles.navLink}>{t('landing.nav.how')}</a>
            {showCompare && <a href="#compare" className={styles.navLink}>{t('landing.nav.compare')}</a>}
            <a href="#pricing" className={styles.navLink}>{t('landing.nav.pricing')}</a>
          </div>
          <a className={styles.headerCta} href={ctaHref}>
            {hasSession ? t('landing.nav.dashboard') : t('landing.nav.start')}
          </a>
        </nav>
      </header>

      <section className={styles.heroSection}>
        <div className={styles.heroContainer}>
          <div className={styles.heroContent}>
            <span className={styles.streakBadge}>
              <svg className={styles.badgeSvg} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
              </svg>
              {t('landing.badge', counts)}
            </span>

            {/* data-lcp: marcador estable para el prerender y sus guardas; la clase
                de CSS module lleva hash y no sirve de aguja. */}
            <h1 className={styles.heroHeading} data-lcp="hero">
              {t('landing.heroTitle')}
            </h1>

            <p className={styles.heroDescription}>{t('landing.heroBody')}</p>

            <div className={styles.heroActions}>
              <a className={styles.primaryBtn} href={ctaHref}>{t('landing.heroCta')}</a>
              <a href="#how" className={styles.secondaryBtn}>{t('landing.heroSecondary')}</a>
            </div>

            <div className={styles.codeSnippet} aria-hidden="true">
              <div className={styles.codeSnippetHeader}>
                <span className={styles.dotPink} />
                <span className={styles.dotWhite} />
                <span className={styles.dotMuted} />
                <span className={styles.codeFilename}>scheduler.py</span>
              </div>
              <pre className={styles.codeContent}>
                <span className={styles.codeComment}>{t('landing.codeComment')}</span>
                {'\n'}p_known[<span className={styles.codeString}>"for_loops"</span>] <span className={styles.codeAccent}>=</span> 0.62 → 0.71
                {'\n'}next_q <span className={styles.codeAccent}>=</span> pick(target_p_correct<span className={styles.codeAccent}>=</span>0.75)
                {'\n'}review <span className={styles.codeAccent}>=</span> fsrs.due(<span className={styles.codeString}>"strings"</span>)
              </pre>
            </div>
          </div>

          <div className={styles.heroVisual}>
            <figure className={styles.shotCard}>
              <img
                src={lang === 'en' ? heroShotEn : heroShotEs}
                alt={t('landing.heroShotAlt')}
                className={styles.shotImage}
                width={780}
                height={1688}
              />
              <figcaption className={styles.videoCaption}>{t('landing.heroShotCaption')}</figcaption>
            </figure>
          </div>
        </div>
      </section>

      <section id="features" className={styles.featuresSection}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionHeading}>{t('landing.featuresTitle')}</h2>
        </div>
        <div className={styles.featuresGrid}>
          {features.map((f) => (
            <article key={f.title} className={styles.featureCard}>
              <div className={styles.cardHeader}>
                <span className={styles.featureIconWrapper}>{f.icon}</span>
                <span className={styles.tagBadge}>{f.tag}</span>
              </div>
              <h3 className={styles.cardTitle}>{f.title}</h3>
              <p className={styles.cardBody}>{f.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="how" className={styles.howSection}>
        <div className={styles.howContainer}>
          <p className={styles.eyebrow}>{t('landing.howEyebrow')}</p>
          <h2 className={styles.sectionHeading}>{t('landing.howTitle')}</h2>
          <ol className={styles.stepsGrid}>
            {steps.map((s, i) => (
              <li key={s.title} className={styles.stepCard}>
                <div className={styles.stepHeader}>
                  <span className={styles.stepNumber}>{i + 1}</span>
                  <span className={styles.stepIconWrapper}>{s.icon}</span>
                </div>
                <h3 className={styles.cardTitle}>{s.title}</h3>
                <p className={styles.cardBody}>{s.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* 35.5: la preparación por dominio, con una captura real (cuenta nueva,
          CLF-C02). Es lo que ningún preparador observado da en español
          (COMPETENCIA.md §A.2). */}
      <section id="readiness" className={styles.readinessSection}>
        <div className={styles.readinessGrid}>
          <div>
            <p className={styles.eyebrow}>{t('landing.readiness.eyebrow')}</p>
            <h2 className={styles.sectionHeading}>{t('landing.readiness.title')}</h2>
            <p className={styles.sectionSubheading}>{t('landing.readiness.body')}</p>
            <ul className={styles.perksList}>
              {[t('landing.readiness.p1'), t('landing.readiness.p2'), t('landing.readiness.p3'), t('landing.readiness.p4')].map((pt) => (
                <li key={pt} className={styles.perkItem}>
                  <svg className={styles.perkCheck} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" aria-hidden="true">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>{pt}</span>
                </li>
              ))}
            </ul>
          </div>
          <figure className={styles.shotCard}>
            <img
              src={lang === 'en' ? readinessShotEn : readinessShotEs}
              alt={t('landing.readiness.alt')}
              className={styles.shotImage}
              width={780}
              height={1688}
              loading="lazy"
              decoding="async"
            />
            <figcaption className={styles.videoCaption}>{t('landing.readiness.caption')}</figcaption>
          </figure>
        </div>
      </section>

      {showCompare && (
        <section id="compare" className={styles.compareSection}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionHeading}>{t('landing.compareTitle')}</h2>
            <p className={styles.sectionSubheading}>{t('landing.compareNote', { date: checkedOn })}</p>
          </div>
          <div className={styles.tableWrapper}>
            <table className={styles.compareTable}>
              <thead>
                <tr>
                  <th className={styles.thCapability} />
                  <th className={styles.thWhetzy}>Whetzy</th>
                  {COMPARISON_COMPETITORS.map((c) => (
                    <th key={c} className={styles.thOther}>{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {COMPARISON_ROWS.map((row) => (
                  <tr key={row.label.en} className={styles.tableRow}>
                    <td className={styles.tdLabel}>{row.label[lang]}</td>
                    <td className={styles.tdWhetzy}><CellMark value={row.whetzy} lang={lang} notChecked={notChecked} /></td>
                    {row.others.map((cell, i) => (
                      <td key={COMPARISON_COMPETITORS[i]} className={styles.tdOther}>
                        <CellMark value={cell} lang={lang} notChecked={notChecked} />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section id="pricing" className={styles.pricingSection}>
        <div className={styles.pricingContainer}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionHeading}>{t('landing.pricingTitle')}</h2>
            <p className={styles.sectionSubheading}>{t('landing.pricingNote')}</p>
          </div>
          <div className={`${styles.plansGrid} ${styles.plansGridFour}`}>
            {plans.map((p) => (
              <article key={p.key} className={p.featured ? styles.planCardFeatured : styles.planCard}>
                <h3 className={styles.planName}>{p.name}</h3>
                <p className={styles.priceRow}>
                  <span className={styles.priceAmount}>{p.price}</span>
                  {p.note && <span className={styles.priceNote}>{p.note}</span>}
                </p>
                <p className={styles.planBlurb}>{p.blurb}</p>
                <ul className={styles.perksList}>
                  {p.perks.map((perk) => (
                    <li key={perk} className={styles.perkItem}>
                      <svg className={styles.perkCheck} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" aria-hidden="true">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      <span>{perk}</span>
                    </li>
                  ))}
                </ul>
                <a className={p.featured ? styles.planCtaFeatured : styles.planCta} href={ctaHref}>{p.cta}</a>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className={styles.testimonialsSection}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionHeading}>{t('landing.proofTitle')}</h2>
        </div>
        <div className={styles.testimonialsGrid}>
          {(['proof1', 'proof2'] as const).map((k) => (
            <article key={k} className={styles.testimonialCard}>
              <h3 className={styles.cardTitle}>{t(`landing.${k}.title`)}</h3>
              <p className={styles.cardBody}>{t(`landing.${k}.body`)}</p>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.finalCtaSection}>
        <div className={styles.finalCtaBox}>
          <h2 className={styles.finalCtaHeading}>{t('landing.finalTitle')}</h2>
          <p className={styles.finalCtaSubheading}>{t('landing.finalBody')}</p>
          <a className={styles.finalCtaBtn} href={ctaHref}>{t('landing.finalCta')}</a>
        </div>
      </section>

      <footer className={styles.footer}>
        <div className={styles.footerContainer}>
          <span className={styles.footerBrand}>Whetzy</span>
          <span className={styles.footerCopyright}>
            {t('landing.footer')} · <a href="/privacy" className={styles.navLink}>{t('landing.privacy')}</a> · <a href="/terms" className={styles.navLink}>{t('landing.terms')}</a>
          </span>
        </div>
      </footer>
    </div>
  );
}
