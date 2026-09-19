import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import '../styles/publicProfile.css'

interface PublicProfile {
  handle: string
  name: string
  bio_es: string
  bio_en: string
  elo: number
  mastery_avg: number
  skills_learned: number
  streak_current: number
  certificates: Array<{ name: string; earned_at: string }>
  projects_completed: Array<{ title_es: string; title_en: string; url: string }>
  joined_at: string
  is_public: boolean
}

export default function PublicProfileScreen({ handle }: { handle: string }) {
  const { i18n, t } = useTranslation()
  const lang = i18n.language as 'es' | 'en'

  const [profile] = useState<PublicProfile>({
    handle,
    name: 'Carlos Pérez',
    bio_es: 'Ingeniero autónomo aprendiendo AWS y Python',
    bio_en: 'Self-taught engineer learning AWS and Python',
    elo: 1840,
    mastery_avg: 78,
    skills_learned: 24,
    streak_current: 12,
    certificates: [
      { name: 'PCEP', earned_at: '2026-09-01' },
      { name: 'AWS SAA-C03', earned_at: '2026-08-15' },
    ],
    projects_completed: [
      { title_es: 'API REST con FastAPI', title_en: 'REST API with FastAPI', url: '/project/001' },
      { title_es: 'Dashboard AWS', title_en: 'AWS Dashboard', url: '/project/002' },
    ],
    joined_at: '2026-01-15',
    is_public: true,
  })

  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    // Simulated fetch: const res = await fetch(`/api/v1/profiles/${handle}`)
    setTimeout(() => setLoading(false), 500)
  }, [handle])

  if (loading) {
    return <div className="public-profile-loading">{t('common.loading', 'Cargando...')}</div>
  }

  if (!profile.is_public) {
    return <div className="public-profile-private">{t('profile.private', 'Este perfil es privado')}</div>
  }

  return (
    <div className="public-profile">
      <div className="profile-header">
        <div className="profile-avatar">
          <div className="avatar-placeholder">{profile.name.charAt(0)}</div>
        </div>
        <div className="profile-info">
          <h1>{profile.name}</h1>
          <p className="handle">@{profile.handle}</p>
          <p className="bio">{profile[`bio_${lang}`]}</p>
          <p className="joined">{t('profile.joined', 'Se unió el')} {new Date(profile.joined_at).toLocaleDateString()}</p>
        </div>
      </div>

      <div className="profile-stats">
        <div className="stat-card">
          <span className="stat-value">{profile.elo}</span>
          <span className="stat-label">{t('profile.elo', 'Elo')}</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{profile.mastery_avg}%</span>
          <span className="stat-label">{t('profile.mastery', 'Dominio')}</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{profile.skills_learned}</span>
          <span className="stat-label">{t('profile.skills', 'Skills')}</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{profile.streak_current}🔥</span>
          <span className="stat-label">{t('profile.streak', 'Racha')}</span>
        </div>
      </div>

      <section className="certificates-section">
        <h2>{t('profile.certs', 'Certificaciones')}</h2>
        {profile.certificates.length === 0 ? (
          <p className="empty">{t('profile.no_certs', 'Sin certificaciones aún')}</p>
        ) : (
          <div className="certs-list">
            {profile.certificates.map((cert, idx) => (
              <div key={idx} className="cert-badge">
                <span className="cert-icon">🏆</span>
                <div className="cert-info">
                  <p className="cert-name">{cert.name}</p>
                  <p className="cert-date">{new Date(cert.earned_at).toLocaleDateString()}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="projects-section">
        <h2>{t('profile.projects', 'Proyectos Completados')}</h2>
        {profile.projects_completed.length === 0 ? (
          <p className="empty">{t('profile.no_projects', 'Sin proyectos aún')}</p>
        ) : (
          <div className="projects-grid">
            {profile.projects_completed.map((proj, idx) => (
              <a key={idx} href={proj.url} className="project-card">
                <h3>{proj[`title_${lang}`]}</h3>
                <span className="arrow">→</span>
              </a>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
