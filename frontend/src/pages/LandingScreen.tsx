import { useEffect, useState } from 'react';
import styles from './LandingScreen.module.css';
import heroPoster from '../assets/hero-video-poster.jpg';

type Cell = boolean | string;

const features = [
  {
    icon: (
      <svg className={styles.featureSvg} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
      </svg>
    ),
    title: 'Adaptive learning',
    body: 'Our engine re-scores every answer in real time and rebuilds your next lesson around the exact gaps it finds.',
    tag: 'Engine v4',
  },
  {
    icon: (
      <svg className={styles.featureSvg} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m5 8 6 6" />
        <path d="m4 14 6-6 2-3" />
        <path d="M2 5h12" />
        <path d="M7 2h1" />
        <path d="m22 22-5-10-5 10" />
        <path d="M14 18h6" />
      </svg>
    ),
    title: 'Truly bilingual',
    body: 'Learn any skill in two languages at the same time. Switch mid-lesson and keep your streak and your context.',
    tag: '28 pairs',
  },
  {
    icon: (
      <svg className={styles.featureSvg} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 8V4H8" />
        <rect width="16" height="12" x="4" y="8" rx="2" />
        <path d="M2 14h2" />
        <path d="M20 14h2" />
        <path d="M15 13v2" />
        <path d="M9 13v2" />
      </svg>
    ),
    title: 'AI tutor, 24/7',
    body: 'Stuck at 2am? Ask for a hint, a rewrite or a full explanation and get an answer that knows your history.',
    tag: 'Unlimited on Pro',
  },
];

const steps = [
  {
    icon: (
      <svg className={styles.stepSvg} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
      </svg>
    ),
    title: 'Choose a skill',
    body: 'Pick from 240+ tracks, from Spanish conversation to Python data work. A 3-minute placement check sets your level.',
  },
  {
    icon: (
      <svg className={styles.stepSvg} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
      </svg>
    ),
    title: 'Learn adaptive',
    body: 'Short daily sessions that shift difficulty as you go. Nothing too easy, nothing that makes you quit.',
  },
  {
    icon: (
      <svg className={styles.stepSvg} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6" />
        <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18" />
        <path d="M4 22h16" />
        <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22" />
        <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22" />
        <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z" />
      </svg>
    ),
    title: 'Get certified',
    body: 'Finish a track and earn a verified certificate with your skill breakdown, ready to share.',
  },
];

const comparison: { label: string; whetzy: Cell; duolingo: Cell; datacamp: Cell; brilliant: Cell }[] = [
  { label: 'Real-time adaptive engine', whetzy: true, duolingo: 'Partial', datacamp: false, brilliant: 'Partial' },
  { label: 'Bilingual lessons', whetzy: true, duolingo: false, datacamp: false, brilliant: false },
  { label: 'AI tutor with full history', whetzy: true, duolingo: 'Limited', datacamp: 'Limited', brilliant: false },
  { label: 'Interactive code exercises', whetzy: true, duolingo: false, datacamp: true, brilliant: true },
  { label: 'Verified certificates', whetzy: true, duolingo: false, datacamp: true, brilliant: false },
  { label: 'Offline practice mode', whetzy: true, duolingo: true, datacamp: false, brilliant: false },
  { label: 'Free tier without ads', whetzy: true, duolingo: false, datacamp: 'Limited', brilliant: false },
];

const plans = [
  {
    name: 'Free',
    price: '$0',
    note: 'forever',
    blurb: 'Everything you need to build the habit.',
    perks: ['1 active track', 'Daily adaptive session', 'Streaks & badges', 'Community answers'],
    cta: 'Start free',
    featured: false,
  },
  {
    name: 'Plus',
    price: '$9.99',
    note: '/month',
    blurb: 'For learners who want to move fast.',
    perks: [
      'Unlimited tracks',
      'Bilingual mode',
      'AI tutor (200 msgs/mo)',
      'Progress analytics',
      'Offline practice',
    ],
    cta: 'Get Plus',
    featured: true,
  },
  {
    name: 'Pro',
    price: '$19.99',
    note: '/month',
    blurb: 'Certification and coaching included.',
    perks: [
      'Everything in Plus',
      'Unlimited AI tutor',
      'Verified certificates',
      'Mock interviews & reviews',
      'Priority support',
    ],
    cta: 'Get Pro',
    featured: false,
  },
];

const testimonials = [
  {
    quote:
      'Three weeks in, the lessons already knew which tenses I kept dropping. It felt less like an app and more like a tutor who takes notes.',
    name: 'Marina Petrescu',
    role: 'Product designer, learning Spanish + SQL',
    initials: 'MP',
  },
  {
    quote:
      'I switched from two separate apps. Doing the technical track in English and Portuguese at once is the thing nobody else does.',
    name: 'Diego Alvarenga',
    role: 'Data analyst, Pro member',
    initials: 'DA',
  },
];

function CellMark({ value }: { value: Cell }) {
  if (value === true) {
    return (
      <span className={styles.cellCheck}>
        <svg className={styles.cellIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      </span>
    );
  }
  if (value === false) {
    return (
      <span className={styles.cellMinus}>
        <svg className={styles.cellIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
      </span>
    );
  }
  return <span className={styles.cellText}>{value}</span>;
}

export default function LandingScreen() {
  const [hasSession, setHasSession] = useState(false);

  useEffect(() => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('whetzy_token');
      setHasSession(Boolean(token));
    } catch {
      setHasSession(false);
    }
  }, []);

  const handleAction = () => {
    // Same navigation style as AuthScreen: full page load, no router needed.
    if (hasSession) {
      window.location.assign('/');
    } else {
      window.location.assign('/auth');
    }
  };

  return (
    <div className={styles.page}>
      {/* HEADER / NAV */}
      <header className={styles.header}>
        <nav className={styles.navContainer}>
          <div className={styles.brandGroup}>
            <span className={styles.logoBadge}>W</span>
            <span className={styles.brandTitle}>Whetzy</span>
          </div>

          <div className={styles.navMenu}>
            <a href="#features" className={styles.navLink}>Features</a>
            <a href="#how" className={styles.navLink}>How it works</a>
            <a href="#compare" className={styles.navLink}>Compare</a>
            <a href="#pricing" className={styles.navLink}>Pricing</a>
          </div>

          <button className={styles.headerCta} onClick={handleAction}>
            {hasSession ? 'Go to Dashboard' : 'Start free'}
          </button>
        </nav>
      </header>

      {/* HERO SECTION */}
      <section className={styles.heroSection}>
        <div className={styles.heroContainer}>
          <div className={styles.heroContent}>
            <span className={styles.streakBadge}>
              <svg className={styles.badgeSvg} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
              </svg>
              14-day streak club · 1.2M learners
            </span>

            {/* data-lcp: marcador estable para el prerender y sus guardas; la clase
                de CSS module lleva hash y no sirve de aguja. */}
            <h1 className={styles.heroHeading} data-lcp="hero">
              Lessons that rewrite themselves around you.
            </h1>

            <p className={styles.heroDescription}>
              Whetzy blends an adaptive engine, bilingual lessons and an AI tutor so every session lands exactly at the edge of what you know.
            </p>

            <div className={styles.heroActions}>
              <button className={styles.primaryBtn} onClick={handleAction}>
                Start free
              </button>
              <a href="#how" className={styles.secondaryBtn}>
                <svg className={styles.playIcon} viewBox="0 0 24 24" fill="currentColor">
                  <polygon points="5 3 19 12 5 21 5 3" />
                </svg>
                See how it works
              </a>
            </div>

            {/* Code Snippet Box */}
            <div className={styles.codeSnippet}>
              <div className={styles.codeSnippetHeader}>
                <span className={styles.dotPink} />
                <span className={styles.dotWhite} />
                <span className={styles.dotMuted} />
                <span className={styles.codeFilename}>adaptive_session.ts</span>
              </div>
              <pre className={styles.codeContent}>
                <span className={styles.codeComment}>// tu respuesta anterior: 82% correcto</span>
                {'\n'}next.difficulty <span className={styles.codeAccent}>+=</span> 0.4
                {'\n'}next.focus <span className={styles.codeAccent}>=</span> <span className={styles.codeString}>"pretérito imperfecto"</span>
                {'\n'}next.language <span className={styles.codeAccent}>=</span> <span className={styles.codeString}>"es"</span> | <span className={styles.codeString}>"en"</span>
              </pre>
            </div>
          </div>

          {/* Video / Tour Card */}
          <div className={styles.heroVisual}>
            <div className={styles.videoCard}>
              <div className={styles.posterWrapper}>
                <img
                  src={heroPoster}
                  alt="Whetzy adaptive lesson interface"
                  className={styles.posterImage}
                  width={1280}
                  height={720}
                />
                <button
                  type="button"
                  className={styles.playOverlay}
                  onClick={handleAction}
                  aria-label="Play product tour"
                >
                  <span className={styles.playCircle}>
                    <svg className={styles.playCircleSvg} viewBox="0 0 24 24" fill="currentColor">
                      <polygon points="6 4 20 12 6 20 6 4" />
                    </svg>
                  </span>
                </button>
              </div>
              <p className={styles.videoCaption}>Product tour · 1:48</p>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURE CARDS */}
      <section id="features" className={styles.featuresSection}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionHeading}>
            Three things that make Whetzy <span className={styles.gradientText}>stick</span>.
          </h2>
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

      {/* HOW IT WORKS */}
      <section id="how" className={styles.howSection}>
        <div className={styles.howContainer}>
          <p className={styles.eyebrow}>How it works</p>
          <h2 className={styles.sectionHeading}>
            From zero to certified in three moves.
          </h2>
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

      {/* COMPARISON TABLE */}
      <section id="compare" className={styles.compareSection}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionHeading}>
            How the adaptive engine compares.
          </h2>
          <p className={styles.sectionSubheading}>
            Based on publicly available features of each platform, October 2026.
          </p>
        </div>
        <div className={styles.tableWrapper}>
          <table className={styles.compareTable}>
            <thead>
              <tr>
                <th className={styles.thCapability}>Capability</th>
                <th className={styles.thWhetzy}>Whetzy</th>
                <th className={styles.thOther}>Duolingo</th>
                <th className={styles.thOther}>DataCamp</th>
                <th className={styles.thOther}>Brilliant</th>
              </tr>
            </thead>
            <tbody>
              {comparison.map((row) => (
                <tr key={row.label} className={styles.tableRow}>
                  <td className={styles.tdLabel}>{row.label}</td>
                  <td className={styles.tdWhetzy}>
                    <CellMark value={row.whetzy} />
                  </td>
                  <td className={styles.tdOther}>
                    <CellMark value={row.duolingo} />
                  </td>
                  <td className={styles.tdOther}>
                    <CellMark value={row.datacamp} />
                  </td>
                  <td className={styles.tdOther}>
                    <CellMark value={row.brilliant} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* PRICING */}
      <section id="pricing" className={styles.pricingSection}>
        <div className={styles.pricingContainer}>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionHeading}>Simple pricing.</h2>
            <p className={styles.sectionSubheading}>
              Cancel anytime. Yearly plans save two months.
            </p>
          </div>
          <div className={styles.plansGrid}>
            {plans.map((p) => (
              <article
                key={p.name}
                className={p.featured ? styles.planCardFeatured : styles.planCard}
              >
                {p.featured && <span className={styles.popularBadge}>Most popular</span>}
                <h3 className={styles.planName}>{p.name}</h3>
                <p className={styles.priceRow}>
                  <span className={styles.priceAmount}>{p.price}</span>
                  <span className={styles.priceNote}>{p.note}</span>
                </p>
                <p className={styles.planBlurb}>{p.blurb}</p>
                <ul className={styles.perksList}>
                  {p.perks.map((perk) => (
                    <li key={perk} className={styles.perkItem}>
                      <svg className={styles.perkCheck} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      <span>{perk}</span>
                    </li>
                  ))}
                </ul>
                <button
                  className={p.featured ? styles.planCtaFeatured : styles.planCta}
                  onClick={handleAction}
                >
                  {p.cta}
                </button>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* TESTIMONIALS */}
      <section className={styles.testimonialsSection}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionHeading}>Learners on Whetzy.</h2>
        </div>
        <div className={styles.testimonialsGrid}>
          {testimonials.map((t) => (
            <figure key={t.name} className={styles.testimonialCard}>
              <blockquote className={styles.testimonialQuote}>
                “{t.quote}”
              </blockquote>
              <figcaption className={styles.authorGroup}>
                <span className={styles.avatarCircle}>{t.initials}</span>
                <div>
                  <span className={styles.authorName}>{t.name}</span>
                  <span className={styles.authorRole}>{t.role}</span>
                </div>
              </figcaption>
            </figure>
          ))}
        </div>
      </section>

      {/* FINAL CTA */}
      <section className={styles.finalCtaSection}>
        <div className={styles.finalCtaBox}>
          <h2 className={styles.finalCtaHeading}>
            Your first adaptive lesson takes five minutes.
          </h2>
          <p className={styles.finalCtaSubheading}>
            No card required. Keep the free plan as long as you like.
          </p>
          <button className={styles.finalCtaBtn} onClick={handleAction}>
            Start free
          </button>
        </div>
      </section>

      {/* FOOTER */}
      <footer className={styles.footer}>
        <div className={styles.footerContainer}>
          <span className={styles.footerBrand}>Whetzy</span>
          <span className={styles.footerCopyright}>© 2026 Whetzy. Learn in two languages.</span>
        </div>
      </footer>
    </div>
  );
}
