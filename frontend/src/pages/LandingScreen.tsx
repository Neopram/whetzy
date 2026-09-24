import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './LandingScreen.module.css';

const features = [
  {
    icon: '⚡',
    title: 'Adaptive Difficulty',
    body: 'The algorithm recalculates your knowledge frontier on every answer. Zero filler questions.',
  },
  {
    icon: '🌐',
    title: 'Native Dual Language',
    body: 'Switch seamlessly between Spanish and English mid-lesson without losing progress or context.',
  },
  {
    icon: '🤖',
    title: '24/7 AI Tutor Core',
    body: 'Instant interactive breakdowns, edge-case hints and tailored explanations when you get stuck.',
  },
];

const steps = [
  { n: '1', title: 'Choose your track', body: 'Select from backend, databases, frontend and devops. A quick placement check locks in your level.' },
  { n: '2', title: 'Train dynamically', body: 'Bite-sized diagnostic quizzes, live code runners and AI corrections adapt dynamically to you.' },
  { n: '3', title: 'Earn verification', body: 'Pass the final mock exam and unlock tamper-proof certificates with granular skill breakdowns.' },
];

export default function LandingScreen() {
  const navigate = useNavigate();
  const [hasSession, setHasSession] = useState(false);

  useEffect(() => {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('whetzy_token');
      setHasSession(Boolean(token));
    } catch {
      setHasSession(false);
    }
  }, []);

  return (
    <div className={styles.page}>
      <header className={styles.nav}>
        <span className={styles.brand}>Whetzy</span>
        <div className={styles.navLinks}>
          <a className={styles.navLink} href="#features">Features</a>
          <a className={styles.navLink} href="#how">Method</a>
          <a className={styles.navLink} href="#certs">Certifications</a>
        </div>
        <div className={styles.navActions}>
          {hasSession ? (
            <button className={styles.ctaPrimary} onClick={() => navigate('/app')}>Go to Dashboard</button>
          ) : (
            <button className={styles.ctaPrimary} onClick={() => navigate('/auth')}>Sign in</button>
          )}
        </div>
      </header>

      <main>
        <section className={styles.hero}>
          <h1 className={styles.heroTitle}>
            Lessons that rewire themselves around your exact knowledge gap.
          </h1>
          <p className={styles.heroSubtitle}>
            Never waste time on what you already mastered. Whetzy blends real-time
            diagnostic evaluation, native English/Spanish tracks and instant AI
            reasoning to get you certified in record time.
          </p>
          <button className={styles.ctaPrimary} onClick={() => navigate('/auth')}>
            Start diagnostic free
          </button>
        </section>

        <section id="features" className={styles.features}>
          {features.map((f) => (
            <article key={f.title} className={styles.featureCard}>
              <span className={styles.featureIcon}>{f.icon}</span>
              <h3 className={styles.featureTitle}>{f.title}</h3>
              <p className={styles.featureBody}>{f.body}</p>
            </article>
          ))}
        </section>

        <section id="how" className={styles.steps}>
          {steps.map((s) => (
            <article key={s.n} className={styles.stepCard}>
              <span className={styles.stepNumber}>{s.n}</span>
              <h3 className={styles.featureTitle}>{s.title}</h3>
              <p className={styles.featureBody}>{s.body}</p>
            </article>
          ))}
        </section>

        <section id="certs" className={styles.finalCta}>
          <h2 className={styles.finalTitle}>Ready to upgrade how you learn?</h2>
          <p className={styles.heroSubtitle}>
            Free to start, cancel anytime.
          </p>
          <button className={styles.ctaPrimary} onClick={() => navigate('/auth')}>
            Get started free
          </button>
        </section>
      </main>

      <footer className={styles.footer}>
        <span>© 2026 Whetzy. All rights reserved.</span>
      </footer>
    </div>
  );
}
