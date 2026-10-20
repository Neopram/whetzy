import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAppStore } from '../stores/useAppStore'
import { auth, content, economy, type TrackRead } from '../services/api'
import { readAttribution } from '../lib/attribution'
import { retiredCertificationFor } from '../lib/retiredCertifications'
import { TRACK_GROUPS, relatedCerts } from '../lib/trackGroups'
import '../styles/onboarding.css'
import { TrackIcon } from '../components/common/AppIcon';
import { Loading } from '../components/common/Loading';

/**
 * 43.3 (ADR-65 D2): objetivo → ruta de aprendizaje (agrupadas) → certificación
 * relacionada (opcional) → experiencia → prueba de nivel o «empiezo de cero»
 * → Hoy.
 *
 * Antes: tres preguntas de segmento (experiencia, objetivo, horas), la ruta
 * deducida del objetivo (aprender → Python, trabajo → Ingeniería de Software)
 * y una pregunta de idioma que ya se había contestado al registrarse. Las
 * horas por semana ya no se preguntan aquí.
 */

/** Valores de `onboarding_goal`. 0 y 3 conservan el significado de antes
 *  (aprender fundamentos, preparar una certificación); 4 es «las dos cosas». */
export const GOAL = { learn: 0, certify: 3, both: 4 } as const
type Goal = (typeof GOAL)[keyof typeof GOAL]

type Step = 'goal' | 'track' | 'cert' | 'experience' | 'start'

export default function OnboardingScreen({ onDone }: { onDone: () => void }) {
  const { i18n, t } = useTranslation()
  const startPlacement = useAppStore((s) => s.startPlacement)
  const setScreen = useAppStore((s) => s.setScreen)
  const updateUser = useAppStore((s) => s.updateUser)
  const lang = i18n.language === 'en' ? 'en' : 'es'

  const [step, setStep] = useState<Step>('goal')
  const [goal, setGoal] = useState<Goal | null>(null)
  const [trackId, setTrackId] = useState<string | null>(null)
  const [certId, setCertId] = useState<string | null>(null)
  const [experience, setExperience] = useState<number | null>(null)
  const [tracks, setTracks] = useState<TrackRead[] | null>(null)
  const [tracksFailed, setTracksFailed] = useState(false)

  useEffect(() => {
    let alive = true
    content
      .tracks()
      .then((r) => { if (alive) setTracks(r) })
      .catch(() => { if (alive) setTracksFailed(true) })
    return () => { alive = false }
  }, [])

  const byId = useMemo(() => new Map((tracks ?? []).map((tr) => [tr.id, tr])), [tracks])
  const name = (id: string) => {
    const tr = byId.get(id)
    return tr ? (lang === 'en' ? tr.name_en : tr.name_es) : id
  }
  const certsFor = (id: string) => relatedCerts(id).filter((c) => byId.get(c)?.is_certification)

  const pickTrack = (id: string) => {
    setTrackId(id)
    setStep(goal !== GOAL.learn && certsFor(id).length > 0 ? 'cert' : 'experience')
  }

  const finish = (takeTest: boolean) => {
    if (!trackId) return
    useAppStore.setState({ selectedTrackId: trackId, activeTrackId: trackId })
    updateUser({ onboardingCompleted: true, targetCertificationId: certId })
    void auth
      .updateMe({
        onboarding_goal: goal ?? undefined,
        onboarding_experience: experience ?? undefined,
        target_track_id: trackId,
        target_certification_id: certId ?? undefined,
        onboarding_completed: true,
        // D-23: se lee antes de que el referido de abajo borre `whetzy_ref`.
        signup_attribution: readAttribution(),
      })
      .catch(() => { /* sin red: el onboarding no debe bloquear la entrada */ })
    try {
      const ref = localStorage.getItem('whetzy_ref')
      if (ref) {
        void economy.activateReferral(ref)
          .finally(() => { try { localStorage.removeItem('whetzy_ref') } catch { /* ok */ } })
      }
    } catch { /* private mode: no localStorage */ }
    onDone()
    if (takeTest) startPlacement(trackId)
    else setScreen('home')
  }

  const hasCertStep = goal !== GOAL.learn && trackId !== null && certsFor(trackId).length > 0
  const steps: Step[] = ['goal', 'track', ...(hasCertStep ? ['cert' as Step] : []), 'experience', 'start']
  const position = steps.indexOf(step) + 1

  return (
    <div className="onboarding" data-testid="onboarding">
      <div className="progress">
        <div className="bar" style={{ width: `${(position / steps.length) * 100}%` }}></div>
      </div>
      <div className="question-card">
        <p className="step-indicator">{t('onboarding.step', { n: position, total: steps.length })}</p>

        {step === 'goal' && (
          <>
            <h2>{t('onboarding.goalTitle')}</h2>
            <div className="options">
              {([['learn', GOAL.learn], ['certify', GOAL.certify], ['both', GOAL.both]] as const).map(([key, value]) => (
                <button
                  key={key}
                  className="option"
                  onClick={() => { setGoal(value); setStep('track') }}
                >
                  {t(`onboarding.goal.${key}`)}
                </button>
              ))}
            </div>
          </>
        )}

        {step === 'track' && (
          <>
            <h2>{t('onboarding.trackTitle')}</h2>
            {tracksFailed && <p role="alert">{t('onboarding.tracksFailed')}</p>}
            {!tracks && !tracksFailed && <Loading label={t('common.loading')} shape="line" />}
            {tracks && TRACK_GROUPS.map((g) => {
              const available = g.tracks.filter((id) => byId.has(id))
              if (available.length === 0) return null
              return (
                <section key={g.id} className="track-group" aria-labelledby={`grp-${g.id}`}>
                  <h3 id={`grp-${g.id}`}>{t(`onboarding.groups.${g.id}`)}</h3>
                  <div className="options track-grid">
                    {available.map((id) => (
                      <button key={id} className="option" data-testid={`track-${id}`} onClick={() => pickTrack(id)}>
                        <span aria-hidden="true"><TrackIcon trackId={id} fallback={byId.get(id)?.icon} size={22} /></span> {name(id)}
                      </button>
                    ))}
                  </div>
                </section>
              )
            })}
          </>
        )}

        {step === 'cert' && trackId && (
          <>
            <h2>{t('onboarding.certTitle')}</h2>
            <div className="options">
              {certsFor(trackId).map((id) => (
                <button
                  key={id}
                  className="option"
                  data-testid={`cert-${id}`}
                  onClick={() => { setCertId(id); setStep('experience') }}
                >
                  {name(id)}
                  {retiredCertificationFor(id) && ` · ${t('tracks.certRetiredBadge')}`}
                </button>
              ))}
              <button className="option" onClick={() => { setCertId(null); setStep('experience') }}>
                {t('onboarding.certNone')}
              </button>
            </div>
          </>
        )}

        {step === 'experience' && (
          <>
            <h2>{t('onboarding.expTitle', { track: trackId ? name(trackId) : '' })}</h2>
            <div className="options">
              {[0, 1, 2].map((i) => (
                <button
                  key={i}
                  className="option"
                  onClick={() => { setExperience(i); setStep('start') }}
                >
                  {t(`onboarding.exp.${i}`)}
                </button>
              ))}
            </div>
          </>
        )}

        {step === 'start' && trackId && (
          <>
            <h2>{t('onboarding.startTitle')}</h2>
            <p>{t('onboarding.startDesc', { track: name(trackId) })}</p>
            <div className="options">
              <button className="option" onClick={() => finish(true)}>{t('onboarding.startTest')}</button>
              <button className="option" onClick={() => finish(false)}>{t('onboarding.startZero')}</button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
