import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { profiles, type PublicProfile } from '../services/api'
import '../styles/publicProfile.css'

export default function PublicProfileScreen({ handle }: { handle: string }) {
  const { i18n, t } = useTranslation()
  const lang = i18n.language as 'es' | 'en'

  // `profile` stays null on a 404 and on any other fetch failure alike: a
  // public profile page has nothing useful to say about *why* it can't show
  // one, so "not found" covers both rather than inventing a second state.
  const [profile, setProfile] = useState<PublicProfile | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    setLoading(true)
    profiles
      .get(handle)
      .then((data) => {
        if (active) setProfile(data)
      })
      .catch(() => {
        if (active) setProfile(null)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [handle])

  if (loading) {
    return <div className="public-profile-loading">{t('common.loading', 'Cargando...')}</div>
  }

  if (!profile) {
    return (
      <div className="public-profile-private">
        {t('profile.notFound', 'No existe ningún perfil con ese nombre de usuario')}
      </div>
    )
  }

  return (
    <div className="public-profile">
      <div className="profile-header">
        <div className="profile-avatar">
          <div className="avatar-placeholder">{profile.avatar_emoji}</div>
        </div>
        <div className="profile-info">
          <h1>{profile.display_name}</h1>
          <p className="handle">@{profile.username}</p>
          <p className="joined">
            {t('profile.joined', 'Se unió el')} {new Date(profile.joined_at).toLocaleDateString()}
          </p>
        </div>
      </div>

      <div className="profile-stats">
        <div className="stat-card">
          <span className="stat-value">{profile.skills_mastered}</span>
          <span className="stat-label">{t('profile.skills', 'Habilidades')}</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{profile.current_streak}<span aria-hidden="true">🔥</span></span>
          <span className="stat-label">{t('profile.streak', 'Racha')}</span>
        </div>
      </div>

      <section className="certificates-section">
        <h2>{t('profile.certs', 'Certificaciones')}</h2>
        {profile.certificates.length === 0 ? (
          <p className="empty">{t('profile.no_certs', 'Todavía sin certificaciones')}</p>
        ) : (
          <div className="certs-list">
            {profile.certificates.map((cert) => (
              <div key={cert.code} className="cert-badge">
                <span className="cert-icon" aria-hidden="true">🏆</span>
                <div className="cert-info">
                  <p className="cert-name">{lang === 'es' ? cert.track_name_es : cert.track_name_en}</p>
                  <p className="cert-date">{new Date(cert.issued_at).toLocaleDateString()}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="projects-section">
        <h2>{t('profile.projects', 'Proyectos completados')}</h2>
        {profile.projects_completed.length === 0 ? (
          <p className="empty">{t('profile.no_projects', 'Todavía sin proyectos')}</p>
        ) : (
          <div className="projects-grid">
            {profile.projects_completed.map((proj) => (
              // Sin enlace: `/project/<slug>` no es una ruta de la app y llevaba a
              // un 404 (auditoría de pantallas, 2026-10-16).
              <div key={proj.slug} className="project-card">
                <h3>{lang === 'es' ? proj.name_es : proj.name_en}</h3>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
