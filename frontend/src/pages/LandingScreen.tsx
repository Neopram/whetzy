import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import styles from './LandingScreen.module.css';
import { CATALOG_QUESTIONS, CATALOG_TRACKS } from '../lib/catalog';
import {
  COMPARISON_CHECKED_ON,
  COMPARISON_COMPETITORS,
  COMPARISON_ROWS,
  type ComparisonCell,
} from '../lib/comparison';
import { TUTOR_DAILY_LIMIT_PRO } from '../lib/plans';
import { checkoutHref } from '../lib/paddle';
import { BrandMark } from '../components/common/BrandMark';
import { HeroQuizMock } from '../components/landing/HeroQuizMock';
import { ReadinessBandsMock } from '../components/landing/ReadinessBandsMock';

/* La landing (30.1, 2026-09-24) solo afirma lo que el producto hace hoy:
   cifras de lib/catalog.ts (vigiladas por scripts/check_docs.py), maquetas de
   la app rotuladas como ejemplo (2026-10-15) y una comparativa con fuente y
   fecha. La versión anterior
   traía testimonios con nombre, «1.2M learners», «240+ tracks», precios sin
   aprobar y copia de otro producto (idiomas). Toda la copia vive en i18n. */

type Lang = 'es' | 'en';

const FAQ_KEYS = ['q1', 'q2', 'q3', 'q4', 'q5', 'q6'] as const;

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

// role="img" con «Sí»/«No» de verdad: un aria-label en un <span> sin rol está
// prohibido (axe aria-prohibited-attr) y «✓» no le dice nada a un lector.
function CellMark({ value, lang, notChecked, yes, no }: { value: ComparisonCell; lang: Lang; notChecked: string; yes: string; no: string }) {
  if (value === true) {
    return (
      <span className={styles.cellCheck} role="img" aria-label={yes}>
        <svg className={styles.cellIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      </span>
    );
  }
  if (value === false) {
    return (
      <span className={styles.cellMinus} role="img" aria-label={no}>
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

  const handleLangChange = (newLang: Lang) => {
    setLang(newLang);
    i18n.changeLanguage(newLang);
    document.documentElement.lang = newLang;
    const url = new URL(window.location.href);
    url.searchParams.set('lang', newLang);
    window.history.replaceState({}, '', url.toString());
  };

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
  const plans = (['planFree', 'planPro', 'planProMax'] as const).map((k) => ({
    key: k,
    name: t(`landing.${k}.name`),
    price: t(`landing.${k}.price`),
    note: t(`landing.${k}.note`),
    blurb: t(`landing.${k}.blurb`),
    perks: t(`landing.${k}.perks`, { returnObjects: true, ...counts, tutorLimit: TUTOR_DAILY_LIMIT_PRO }) as string[],
    cta: t(`landing.${k}.cta`),
    featured: k === 'planFree',
    // Pro y Pro Max van al pago (H.29); /checkout pide sesión si no la hay.
    // Creador no se muestra: el marketplace está congelado (D-25) y su plan, oculto (D-7).
    href: k === 'planPro' ? checkoutHref('plus') : k === 'planProMax' ? checkoutHref('pro') : ctaHref,
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
            <span className={styles.logoBadge}><BrandMark height={22} /></span>
            <span className={styles.brandTitle}>Whetzy</span>
          </div>
          <div className={styles.navMenu}>
            <a href="#features" className={styles.navLink}>{t('landing.nav.features')}</a>
            <a href="#how" className={styles.navLink}>{t('landing.nav.how')}</a>
            {showCompare && <a href="#compare" className={styles.navLink}>{t('landing.nav.compare')}</a>}
            <a href="#pricing" className={styles.navLink}>{t('landing.nav.pricing')}</a>
            <a href="#faq" className={styles.navLink}>{t('landing.footerCols.faq')}</a>
          </div>
          <div className={styles.headerActions}>
            <div className={styles.langSelector}>
              <button
                className={`${styles.langBtn} ${lang === 'es' ? styles.active : ''}`}
                onClick={() => handleLangChange('es')}
                title="Español"
                aria-label="Español"
              >
                🇪🇸
              </button>
              <button
                className={`${styles.langBtn} ${lang === 'en' ? styles.active : ''}`}
                onClick={() => handleLangChange('en')}
                title="English"
                aria-label="English"
              >
                🇬🇧
              </button>
            </div>
            <a className={styles.headerCta} href={ctaHref}>
              {hasSession ? t('landing.nav.dashboard') : t('landing.nav.start')}
            </a>
          </div>
        </nav>
      </header>

      <section className={styles.heroSection}>
        <div className={styles.heroContainer}>
          <div className={styles.heroContent}>
            <span className={styles.streakBadge}>
              <span className={styles.badgeDot} aria-hidden="true" />
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

            {/* Cifras de lib/catalog.ts y el objetivo de acierto del selector
                (TARGET_SUCCESS_PROBABILITY = 0.75 en backend/app/services/quiz.py). */}
            <dl className={styles.heroStats}>
              <div><dt>{t('landing.stats.questions')}</dt><dd>{counts.questions}</dd></div>
              <div><dt>{t('landing.stats.tracks')}</dt><dd>{counts.tracks}</dd></div>
              <div><dt>{t('landing.stats.target')}</dt><dd>75 %</dd></div>
            </dl>
          </div>

          <div className={styles.heroVisual}>
            <HeroQuizMock />
          </div>
        </div>
      </section>

      {/* Sin testimonios hasta que haya alumnos reales que los den (H.10). */}
      <section className={styles.betaStrip}>
        <div className={styles.betaInner}>
          <p className={styles.betaText}><strong>{t('landing.beta.title')}</strong> {t('landing.beta.body')}</p>
          <a className={styles.secondaryBtn} href={ctaHref}>{t('landing.beta.cta')}</a>
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

      {/* 35.5: la preparación por dominio, con las bandas de ADR-60 (maqueta
          rotulada como ejemplo, sin porcentaje global). Es lo que ningún preparador observado da en español
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
          <ReadinessBandsMock />
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
                    <td className={styles.tdWhetzy}><CellMark value={row.whetzy} lang={lang} notChecked={notChecked} yes={t('landing.cellYes')} no={t('landing.cellNo')} /></td>
                    {row.others.map((cell, i) => (
                      <td key={COMPARISON_COMPETITORS[i]} className={styles.tdOther}>
                        <CellMark value={cell} lang={lang} notChecked={notChecked} yes={t('landing.cellYes')} no={t('landing.cellNo')} />
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
          <div className={`${styles.plansGrid}`}>
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
                <a className={p.featured ? styles.planCtaFeatured : styles.planCta} href={p.href}>{p.cta}</a>
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
          {(['proof1', 'proof2', 'proof3', 'proof4'] as const).map((k) => (
            <article key={k} className={styles.testimonialCard}>
              <h3 className={styles.cardTitle}>{t(`landing.${k}.title`)}</h3>
              <p className={styles.cardBody}>{t(`landing.${k}.body`)}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="faq" className={styles.faqSection}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionHeading}>{t('landing.faqTitle')}</h2>
        </div>
        {/* <details>: abre y cierra sin JS y su texto ya está en el HTML
            pre-renderizado, que es lo que leen los buscadores. */}
        <div className={styles.faqList}>
          {FAQ_KEYS.map((k) => (
            <details key={k} className={styles.faqItem}>
              <summary className={styles.faqQuestion}>{t(`landing.faq.${k}.q`)}</summary>
              <p className={styles.faqAnswer}>{t(`landing.faq.${k}.a`)}</p>
            </details>
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
        <div className={styles.footerGrid}>
          <div className={styles.footerBrandCol}>
            <span className={styles.brandGroup}>
              <span className={styles.logoBadge}><BrandMark height={20} /></span>
              <span className={styles.footerBrand}>Whetzy</span>
            </span>
            <p className={styles.footerTagline}>{t('landing.footerCols.tagline')}</p>
          </div>
          <nav className={styles.footerCol} aria-label={t('landing.footerCols.product')}>
            <h3 className={styles.footerColTitle}>{t('landing.footerCols.product')}</h3>
            <a href="#features" className={styles.navLink}>{t('landing.nav.features')}</a>
            <a href="#how" className={styles.navLink}>{t('landing.nav.how')}</a>
            <a href="#pricing" className={styles.navLink}>{t('landing.nav.pricing')}</a>
            <a href="#faq" className={styles.navLink}>{t('landing.footerCols.faq')}</a>
          </nav>
          <nav className={styles.footerCol} aria-label={t('landing.footerCols.legal')}>
            <h3 className={styles.footerColTitle}>{t('landing.footerCols.legal')}</h3>
            <a href="/privacy" className={styles.navLink}>{t('landing.privacy')}</a>
            <a href="/terms" className={styles.navLink}>{t('landing.terms')}</a>
            <a href="/refund" className={styles.navLink}>{t('landing.refund')}</a>
          </nav>
        </div>
        <p className={styles.footerCopyright}>{t('landing.footer')}</p>
      </footer>
    </div>
  );
}
