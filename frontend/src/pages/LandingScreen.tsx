import { useTranslation } from 'react-i18next'
import '../styles/landing.css'
import { CATALOG_QUESTIONS, CATALOG_TRACKS } from '../lib/catalog'

export default function LandingScreen() {
  const { t } = useTranslation()

  return (
    <div className="landing">
      <section className="hero">
        <h1 className="lnd-hero__h1">{t('landing.title', 'Aprende Python Adaptativo')}</h1>
        <p>{t('landing.subtitle', 'Motor adaptativo + IA en español')}</p>
        
        <div className="stats">
          <div><strong>{CATALOG_QUESTIONS.toLocaleString()}</strong> {t('landing.questions', 'preguntas')}</div>
          <div><strong>{CATALOG_TRACKS}</strong> {t('landing.tracks', 'tracks')}</div>
          <div><strong>100%</strong> {t('landing.bilingual', 'bilingüe')}</div>
        </div>

        <div className="ctas">
          <a href="/auth" className="btn-primary">{t('landing.start', 'Comienza gratis')}</a>
          <a href="/auth" className="btn-secondary">{t('landing.login', 'Inicia sesión')}</a>
        </div>
      </section>

      <section className="features">
        <h2>{t('landing.why', '¿Por qué Whetzy?')}</h2>
        <div className="grid">
          <div className="feature">
            <h3>🧠 {t('landing.f1.title', 'Adaptativo')}</h3>
            <p>{t('landing.f1.body', 'BKT + FSRS: la pregunta justa para ti')}</p>
          </div>
          <div className="feature">
            <h3>🌐 {t('landing.f2.title', 'Español')}</h3>
            <p>{t('landing.f2.body', 'Contenido nativo, no traducido')}</p>
          </div>
          <div className="feature">
            <h3>⚡ {t('landing.f3.title', 'Sin conexión')}</h3>
            <p>{t('landing.f3.body', 'Aprende sin internet')}</p>
          </div>
          <div className="feature">
            <h3>💯 {t('landing.f4.title', 'Honesto')}</h3>
            <p>{t('landing.f4.body', 'Nunca mentimos sobre tu progreso')}</p>
          </div>
        </div>
      </section>

      <section className="pricing">
        <h2>{t('landing.pricing', 'Planes')}</h2>
        <div className="cards">
          <div className="card">{t('landing.planFree', 'Gratuito')} €0</div>
          <div className="card featured">{t('landing.planPro', 'Pro')} €9.99</div>
          <div className="card">{t('landing.planPlus', 'Plus')} €19.99</div>
        </div>
      </section>

      <footer>
        <p>&copy; 2026 Whetzy</p>
      </footer>
    </div>
  )
}
