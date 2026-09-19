import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import '../../styles/gamification.css'

interface Achievement {
  id: string
  name_es: string
  name_en: string
  icon: string
  earned_at?: Date
}

export default function GamificationPanel() {
  const { i18n, t } = useTranslation()
  const lang = i18n.language as 'es' | 'en'

  const [streak] = useState(7)
  const [achievements] = useState<Achievement[]>([
    { id: 'first', name_es: 'Primera', name_en: 'First', icon: '🎯', earned_at: new Date() },
    { id: 'week', name_es: 'Semana', name_en: 'Week', icon: '🔥', earned_at: new Date() },
    { id: 'master', name_es: 'Maestro', name_en: 'Master', icon: '👑', earned_at: new Date() },
    { id: 'league', name_es: 'Liga', name_en: 'League', icon: '⭐' },
    { id: 'tutorial', name_es: 'Tutorial', name_en: 'Tutorial', icon: '📚' },
    { id: 'ai', name_es: 'IA', name_en: 'AI', icon: '🤖' }
  ])

  return (
    <div className="gamification">
      <section className="streak-card">
        <div className="streak-flame">🔥</div>
        <div className="streak-number">{streak}</div>
        <p>{t('gamif.streak', 'Racha de Días')}</p>
      </section>

      <section className="achievements">
        <h2>{t('gamif.achievements', 'Logros')}</h2>
        <div className="badges">
          {achievements.map((a) => (
            <div key={a.id} className={`badge ${a.earned_at ? 'earned' : 'locked'}`}>
              <div className="icon">{a.icon}</div>
              <div className="name">{a[`name_${lang}`]}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="actions">
        <button>⚔️ {t('gamif.duels', 'Duelos')}</button>
        <button>🎪 {t('gamif.challenges', 'Desafíos')}</button>
        <button>📜 {t('gamif.missions', 'Misiones')}</button>
      </section>
    </div>
  )
}
