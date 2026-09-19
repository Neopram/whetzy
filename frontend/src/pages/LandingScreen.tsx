import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import '../styles/landing.css'

export default function LandingScreen() {
  const { t } = useTranslation()

  return (
    <div className="landing">
      <section className="hero">
        <h1>{t('landing.title', 'Aprende Python Adaptativo')}</h1>
        <p>{t('landing.subtitle', 'Motor adaptativo + IA en español')}</p>
        
        <div className="stats">
          <div><strong>5,715+</strong> preguntas</div>
          <div><strong>18</strong> tracks</div>
          <div><strong>100%</strong> bilingüe</div>
        </div>

        <div className="ctas">
          <Link to="/auth" className="btn-primary">{t('landing.start', 'Comienza gratis')}</Link>
          <Link to="/auth" className="btn-secondary">{t('landing.login', 'Inicia sesión')}</Link>
        </div>
      </section>

      <section className="features">
        <h2>{t('landing.why', '¿Por qué Whetzy?')}</h2>
        <div className="grid">
          <div className="feature">
            <h3>🧠 Adaptativo</h3>
            <p>BKT + FSRS: pregunta perfecta para ti</p>
          </div>
          <div className="feature">
            <h3>🌐 Español</h3>
            <p>Contenido nativo, no traducido</p>
          </div>
          <div className="feature">
            <h3>⚡ Offline</h3>
            <p>Aprende sin internet</p>
          </div>
          <div className="feature">
            <h3>💯 Honesto</h3>
            <p>Nunca mentimos sobre tu progreso</p>
          </div>
        </div>
      </section>

      <section className="pricing">
        <h2>{t('landing.pricing', 'Planes')}</h2>
        <div className="cards">
          <div className="card">Gratuito €0</div>
          <div className="card featured">Pro €9.99</div>
          <div className="card">Plus €19.99</div>
        </div>
      </section>

      <footer>
        <p>&copy; 2026 Whetzy</p>
      </footer>
    </div>
  )
}
