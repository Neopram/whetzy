import { useTranslation } from 'react-i18next';
import { useDocumentMeta } from '../hooks/useDocumentMeta';
import './LandingScreen.css';

const LANDING_URL = 'https://whetzy.com/landing';

/**
 * The landing has no server-side render, so the `?lang=en` query string is
 * the hreflang-addressable EN variant (see index.html + public/sitemap.xml).
 * It overrides the app's global language for this page only.
 */
function resolveLandingLang(i18nLang: string): 'es' | 'en' {
  try {
    const q = new URLSearchParams(window.location.search).get('lang');
    if (q === 'en' || q === 'es') return q;
  } catch {
    /* window unavailable (SSR/tests) — fall through to i18n language */
  }
  return i18nLang.startsWith('es') ? 'es' : 'en';
}

interface PlanCardProps {
  name: string;
  price: string;
  period: string;
  features: string[];
  cta: string;
  highlighted?: boolean;
  onCta: () => void;
}

function PlanCard({ name, price, period, features, cta, highlighted, onCta }: PlanCardProps) {
  return (
    <div className={`lnd-plan${highlighted ? ' lnd-plan--hi' : ''}`}>
      {highlighted && <div className="lnd-plan__badge">Popular</div>}
      <div className="lnd-plan__name">{name}</div>
      <div className="lnd-plan__price">
        <span className="lnd-plan__amount">{price}</span>
        <span className="lnd-plan__period">/{period}</span>
      </div>
      <ul className="lnd-plan__features">
        {features.map((f) => (
          <li key={f}>✓ {f}</li>
        ))}
      </ul>
      <button className={`lnd-plan__cta${highlighted ? ' lnd-plan__cta--hi' : ''}`} onClick={onCta}>
        {cta}
      </button>
    </div>
  );
}

interface FeatureCardProps {
  icon: string;
  title: string;
  body: string;
}

function FeatureCard({ icon, title, body }: FeatureCardProps) {
  return (
    <div className="lnd-feature">
      <div className="lnd-feature__icon">{icon}</div>
      <h3 className="lnd-feature__title">{title}</h3>
      <p className="lnd-feature__body">{body}</p>
    </div>
  );
}

export function LandingScreen() {
  const { i18n } = useTranslation();
  const lang = resolveLandingLang(i18n.language);
  const es = lang === 'es';

  const t = {
    metaTitle:  es ? 'Whetzy — Aprende lo que importa, cuando importa' : 'Whetzy — Master what matters, when it matters',
    metaDesc:   es ? 'Whetzy adapta cada pregunta a tu nivel con IA, repaso espaciado y gamificación — de Python básico a AI Engineer, en español e inglés.' : 'Whetzy adapts every question to your level with AI, spaced repetition and gamification — from basic Python to AI Engineer, in Spanish and English.',
    imageAlt:   es ? 'Whetzy — aprende lo que importa' : 'Whetzy — learn what matters',
    heroTag:    es ? 'Prepárate diferente' : 'Study smarter',
    heroH1:     es ? 'Domina lo que importa,\ncuando importa.' : 'Master what matters,\nwhen it matters.',
    heroSub:    es ? 'Whetzy adapta cada pregunta a tu nivel con IA, repaso espaciado y gamificación — en español e inglés.' : 'Whetzy adapts every question to your level with AI, spaced repetition and gamification — in Spanish and English.',
    heroCta:    es ? 'Empezar gratis' : 'Start for free',
    heroSub2:   es ? 'Sin tarjeta. Sin trampas.' : 'No credit card. No tricks.',
    f1Title:    es ? 'Motor adaptativo' : 'Adaptive engine',
    f1Body:     es ? 'BKT + FSRS + Elo. Cada sesión se calibra en tiempo real para que estudies justo lo que necesitas.' : 'BKT + FSRS + Elo. Every session calibrates in real time so you study exactly what you need.',
    f2Title:    es ? 'Tutor con IA' : 'AI tutor',
    f2Body:     es ? 'Explica cualquier pregunta al instante, con fuente citada y en tu idioma.' : 'Explains any question instantly, with a cited source and in your language.',
    f3Title:    es ? 'Gamificado' : 'Gamified',
    f3Body:     es ? 'Ligas semanales, duelos en tiempo real, rachas y más. Aprender tiene que ser divertido.' : 'Weekly leagues, real-time duels, streaks and more. Learning has to be fun.',
    f4Title:    es ? 'Bilingüe' : 'Bilingual',
    f4Body:     es ? 'Todo el contenido en español e inglés. Cambia de idioma en cualquier momento.' : 'All content in Spanish and English. Switch languages at any time.',
    pricingH2:  es ? 'Elige tu plan' : 'Choose your plan',
    pricingNote:es ? 'Cancela cuando quieras.' : 'Cancel any time.',
    planFree:   es ? 'Gratis' : 'Free',
    planPlus:   es ? 'Plus' : 'Plus',
    planPro:    es ? 'Pro' : 'Pro',
    month:      es ? 'mes' : 'month',
    ctaFree:    es ? 'Empezar gratis' : 'Start free',
    ctaPlus:    es ? 'Suscribirse' : 'Subscribe',
    ctaPro:     es ? 'Suscribirse' : 'Subscribe',
    freeFeats:  es
      ? ['1 track de contenido', 'Quiz adaptativo básico', 'Modo estudio ilimitado', 'Glosario bilingüe']
      : ['1 content track', 'Basic adaptive quiz', 'Unlimited study mode', 'Bilingual glossary'],
    plusFeats:  es
      ? ['Todos los tracks', 'Modo examen y repaso', 'Tutor con IA (explicaciones)', 'Ligas semanales', 'Duelos en tiempo real', 'Sin anuncios']
      : ['All tracks', 'Exam and review modes', 'AI tutor (explanations)', 'Weekly leagues', 'Real-time duels', 'No ads'],
    proFeats:   es
      ? ['Todo lo de Plus', 'Historial de analytics', 'Acceso anticipado a nuevos tracks', 'Soporte prioritario']
      : ['Everything in Plus', 'Analytics history', 'Early access to new tracks', 'Priority support'],
    footerNote: es ? '© 2026 Whetzy. Hecho con ♥ en Europa.' : '© 2026 Whetzy. Made with ♥ in Europe.',
  };

  useDocumentMeta({
    title: t.metaTitle,
    description: t.metaDesc,
    lang,
    url: es ? LANDING_URL : `${LANDING_URL}?lang=en`,
    imageAlt: t.imageAlt,
  });

  function goToAuth() {
    window.location.href = '/';
  }

  return (
    <div className="lnd">
      {/* Nav */}
      <nav className="lnd-nav">
        <span className="lnd-nav__logo">⚡ Whetzy</span>
        <button className="lnd-nav__login" onClick={goToAuth}>
          {es ? 'Entrar' : 'Log in'}
        </button>
      </nav>

      {/* Hero */}
      <section className="lnd-hero">
        <div className="lnd-hero__tag">{t.heroTag}</div>
        <h1 className="lnd-hero__h1">{t.heroH1}</h1>
        <p className="lnd-hero__sub">{t.heroSub}</p>
        <button className="lnd-hero__cta" onClick={goToAuth}>{t.heroCta}</button>
        <p className="lnd-hero__sub2">{t.heroSub2}</p>
      </section>

      {/* Features */}
      <section className="lnd-features">
        <FeatureCard icon="🧠" title={t.f1Title} body={t.f1Body} />
        <FeatureCard icon="🤖" title={t.f2Title} body={t.f2Body} />
        <FeatureCard icon="🏆" title={t.f3Title} body={t.f3Body} />
        <FeatureCard icon="🌍" title={t.f4Title} body={t.f4Body} />
      </section>

      {/* Pricing */}
      <section className="lnd-pricing">
        <h2 className="lnd-pricing__h2">{t.pricingH2}</h2>
        <p className="lnd-pricing__note">{t.pricingNote}</p>
        <div className="lnd-pricing__cards">
          <PlanCard
            name={t.planFree}
            price="0€"
            period={t.month}
            features={t.freeFeats}
            cta={t.ctaFree}
            onCta={goToAuth}
          />
          <PlanCard
            name={t.planPlus}
            price="9,99€"
            period={t.month}
            features={t.plusFeats}
            cta={t.ctaPlus}
            highlighted
            onCta={goToAuth}
          />
          <PlanCard
            name={t.planPro}
            price="19,99€"
            period={t.month}
            features={t.proFeats}
            cta={t.ctaPro}
            onCta={goToAuth}
          />
        </div>
      </section>

      {/* Footer */}
      <footer className="lnd-footer">
        <p>{t.footerNote}</p>
        <div className="lnd-footer__links">
          <a href="/privacy">{es ? 'Privacidad' : 'Privacy'}</a>
          <a href="/terms">{es ? 'Términos' : 'Terms'}</a>
        </div>
      </footer>
    </div>
  );
}
