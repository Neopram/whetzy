import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { profiles, type PublicProfile } from '../services/api'
import styles from './PublicProfileScreen.module.css';
import { GameIcon } from '../components/common/AppIcon';
import { StaggerItem, StaggerList } from '../components/common/Stagger';
import { Loading } from '../components/common/Loading';
import { useNoIndexMeta } from './marketing/useNoIndexMeta';

/** 24.8: mientras no haya un perfil público que enseñar (cargando, inexistente
 *  o sin opt-in) la página lleva `noindex`; con perfil cargado se quita. */
function NoIndex({ title, lang }: { title: string; lang: 'es' | 'en' }) {
  useNoIndexMeta(title, lang)
  return null
}

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
    return (
      <div className={styles.publicProfileLoading}>
        <NoIndex title="Whetzy" lang={lang} />
        <Loading label={t('common.loading', 'Cargando...')} shape="card" />
      </div>
    )
  }

  if (!profile) {
    return (
      <div className={styles.publicProfilePrivate}>
        <NoIndex title="Whetzy" lang={lang} />
        {t('profile.notFound', 'No existe ningún perfil con ese nombre de usuario')}
      </div>
    )
  }

  return (
    <div className={styles.publicProfile}>
      <div className={styles.profileHeader}>
        <div className={styles.profileAvatar}>
          <div className={styles.avatarPlaceholder}>{profile.avatar_emoji}</div>
        </div>
        <div className={styles.profileInfo}>
          <h1>{profile.display_name}</h1>
          <p className={styles.handle}>@{profile.username}</p>
          <p className={styles.joined}>
            {t('profile.joined', 'Se unió el')} {new Date(profile.joined_at).toLocaleDateString()}
          </p>
        </div>
      </div>

      <div className={styles.profileStats}>
        <div className={styles.statCard}>
          <span className={styles.statValue}>{profile.skills_mastered}</span>
          <span className={styles.statLabel}>{t('profile.skills', 'Habilidades')}</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statValue}>{profile.current_streak}<GameIcon name="racha" size={20} /></span>
          <span className={styles.statLabel}>{t('profile.streak', 'Racha')}</span>
        </div>
      </div>

      <section className={styles.certificatesSection}>
        <h2>{t('profile.certs', 'Certificaciones')}</h2>
        {profile.certificates.length === 0 ? (
          <p className={styles.empty}>{t('profile.no_certs', 'Todavía sin certificaciones')}</p>
        ) : (
          <StaggerList as="div" className={styles.certsList} data-testid="public-certs">
            {profile.certificates.map((cert) => (
              <StaggerItem as="div" key={cert.code} className={styles.certBadge}>
                <span className={styles.certIcon}><GameIcon name="trofeo" size={28} /></span>
                <div className={styles.certInfo}>
                  <p className={styles.certName}>{lang === 'es' ? cert.track_name_es : cert.track_name_en}</p>
                  <p className={styles.certDate}>{new Date(cert.issued_at).toLocaleDateString()}</p>
                </div>
              </StaggerItem>
            ))}
          </StaggerList>
        )}
      </section>

      <section className={styles.projectsSection}>
        <h2>{t('profile.projects', 'Proyectos completados')}</h2>
        {profile.projects_completed.length === 0 ? (
          <p className={styles.empty}>{t('profile.no_projects', 'Todavía sin proyectos')}</p>
        ) : (
          <StaggerList as="div" className={styles.projectsGrid} data-testid="public-projects">
            {profile.projects_completed.map((proj) => (
              // Sin enlace: `/project/<slug>` no es una ruta de la app y llevaba a
              // un 404 (auditoría de pantallas, 2026-10-16).
              <StaggerItem as="div" key={proj.slug} className={styles.projectCard}>
                <h3>{lang === 'es' ? proj.name_es : proj.name_en}</h3>
              </StaggerItem>
            ))}
          </StaggerList>
        )}
      </section>
    </div>
  )
}
