import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import '../styles/dashboard.css'

interface SkillProgress {
  id: string
  name_es: string
  name_en: string
  p_known: number // BKT mastery 0-1
  next_review: Date
  streak: number
}

export default function HomeScreen() {
  const { i18n, t } = useTranslation()
  const [skills, setSkills] = useState<SkillProgress[]>([
    {
      id: 'sk01',
      name_es: 'Variables y Tipos',
      name_en: 'Variables & Types',
      p_known: 0.72,
      next_review: new Date(Date.now() + 2 * 86400000),
      streak: 7
    },
    {
      id: 'sk02',
      name_es: 'Bucles for/while',
      name_en: 'Loops for/while',
      p_known: 0.45,
      next_review: new Date(Date.now() + 1 * 86400000),
      streak: 3
    },
    {
      id: 'sk03',
      name_es: 'Funciones',
      name_en: 'Functions',
      p_known: 0.89,
      next_review: new Date(Date.now() + 5 * 86400000),
      streak: 12
    },
    {
      id: 'sk04',
      name_es: 'Listas y Dicts',
      name_en: 'Lists & Dicts',
      p_known: 0.56,
      next_review: new Date(Date.now() + 1 * 86400000),
      streak: 2
    }
  ])

  const lang = i18n.language as 'es' | 'en'
  const totalStreak = skills.reduce((sum, s) => sum + s.streak, 0)
  const avgMastery = skills.length > 0 
    ? Math.round((skills.reduce((sum, s) => sum + s.p_known, 0) / skills.length) * 100)
    : 0

  return (
    <div className="dashboard">
      {/* Header: Stats + Level */}
      <div className="header">
        <div className="level-badge">
          <div className="level-number">Elo 1,240</div>
          <div className="level-label">{t('home.level', 'Nivel')}</div>
        </div>

        <div className="stats-row">
          <div className="stat">
            <span className=\"stat-value\">{totalStreak}</span>
            <span className=\"stat-label\">{t('home.streak', 'Racha')}</span>
          </div>
          <div className="stat">
            <span className=\"stat-value\">{avgMastery}%</span>
            <span className=\"stat-label\">{t('home.mastery', 'Dominio')}</span>
          </div>
          <div className="stat">
            <span className=\"stat-value\">{skills.length}</span>
            <span className=\"stat-label\">{t('home.skills', 'Skills')}</span>
          </div>
        </div>
      </div>

      {/* BKT Territory Map */}
      <section className="territory">
        <h2>{t('home.territory', 'Tu Territorio')}</h2>
        <div className=\"territory-grid\">
          {skills.map((skill) => {
            const isDominated = skill.p_known >= 0.75
            const isPartial = skill.p_known >= 0.40
            const statusClass = isDominated ? 'dominated' : isPartial ? 'partial' : 'frontier'
            
            return (
              <div key={skill.id} className={\"territory-node \\"}>
                <div className=\"node-name\">{skill[\"name_\" + lang]}</div>
                <div className=\"node-mastery\">
                  {Math.round(skill.p_known * 100)}%
                </div>
                <div className=\"node-indicator\" style={{
                  width: \\%\
                }}></div>
              </div>
            )
          })}
        </div>
      </section>

      {/* FSRS Schedule */}
      <section className=\"schedule\">
        <h2>{t('home.next_review', 'Próximas Sesiones')}</h2>
        <div className=\"review-list\">
          {skills.sort((a, b) => a.next_review.getTime() - b.next_review.getTime()).map((skill) => (
            <div key={skill.id} className=\"review-item\">
              <div className=\"review-skill\">{skill[\"name_\" + lang]}</div>
              <div className=\"review-date\">
                {skill.next_review.toLocaleDateString(lang === 'es' ? 'es-ES' : 'en-US', {
                  month: 'short',
                  day: 'numeric'
                })}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA: Next question */}
      <div className=\"cta-section\">
        <button className=\"btn-start-quiz\">
          {t('home.start_quiz', 'Próxima Pregunta')} →
        </button>
      </div>
    </div>
  )
}
