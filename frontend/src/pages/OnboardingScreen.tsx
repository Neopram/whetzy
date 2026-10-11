import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAppStore } from '../stores/useAppStore'
import { auth, economy } from '../services/api'
import '../styles/onboarding.css'

interface SegmentQuestion {
  id: string
  es: string
  en: string
  options: { es: string; en: string }[]
}

const SEGMENT_QUESTIONS: SegmentQuestion[] = [
  {
    id: 'exp',
    es: '¿Cuál es tu experiencia con programación?',
    en: 'What is your programming experience?',
    options: [
      { es: 'Soy principiante', en: 'I am a beginner' },
      { es: 'Tengo algo de experiencia', en: 'I have some experience' },
      { es: 'Soy profesional', en: 'I am a professional' }
    ]
  },
  {
    id: 'goal',
    es: '¿Cuál es tu objetivo principal?',
    en: 'What is your main goal?',
    options: [
      { es: 'Aprender fundamentos', en: 'Learn fundamentals' },
      { es: 'Conseguir trabajo', en: 'Get a job' },
      { es: 'Avanzar en mi carrera', en: 'Advance my career' },
      { es: 'Preparar una certificación', en: 'Prepare for a certification' },
    ]
  },
  {
    id: 'time',
    es: '¿Cuánto tiempo puedes dedicar por semana?',
    en: 'How much time can you dedicate per week?',
    options: [
      { es: '<3 horas', en: '<3 hours' },
      { es: '3-10 horas', en: '3-10 hours' },
      { es: '>10 horas', en: '>10 hours' }
    ]
  }
]

interface CertTrack { id: string; es: string; en: string }

const CERT_TRACKS: CertTrack[] = [
  { id: 'track08', es: 'AWS Cloud Practitioner (CLF-C02)', en: 'AWS Cloud Practitioner (CLF-C02)' },
  { id: 'track09', es: 'PCEP — Python Nivel Básico', en: 'PCEP — Python Entry-Level' },
  { id: 'track10', es: 'AWS Solutions Architect (SAA-C03)', en: 'AWS Solutions Architect (SAA-C03)' },
  { id: 'track11', es: 'AWS AI Practitioner (AIF-C01)', en: 'AWS AI Practitioner (AIF-C01)' },
  { id: 'track40', es: 'ISC2 CC — Ciberseguridad', en: 'ISC2 CC — Cybersecurity' },
  { id: 'track41', es: 'PCAP — Python Nivel Asociado', en: 'PCAP — Python Associate' },
  { id: 'track43', es: 'AWS ML Engineer (MLA-C01)', en: 'AWS ML Engineer (MLA-C01)' },
  { id: 'track44', es: 'Azure Fundamentals (AZ-900)', en: 'Azure Fundamentals (AZ-900)' },
  { id: 'track45', es: 'Azure AI Fundamentals (AI-901)', en: 'Azure AI Fundamentals (AI-901)' },
]

// goal 0 (learn fundamentals) → Python Basics (track01)
// goal 1 (get a job) / goal 2 (advance career) → Software Engineering (track04)
// goal 3 (certification) → the cert the user picked, or track01 as fallback
export function _placementTrack(goal: number, certTrackId: string | null): string {
  if (goal === 3 && certTrackId) return certTrackId
  if (goal === 1 || goal === 2) return 'track04'
  return 'track01'
}

export default function OnboardingScreen({ onDone }: { onDone: () => void }) {
  const { i18n, t } = useTranslation()
  const setUserLanguage = useAppStore((s) => s.setLanguage)
  const updateUser = useAppStore((s) => s.updateUser)
  const startPlacement = useAppStore((s) => s.startPlacement)
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const [certTrackId, setCertTrackId] = useState<string | null>(null)

  const lang = i18n.language as 'es' | 'en'
  const question = SEGMENT_QUESTIONS[step]
  const isAnswered = step < SEGMENT_QUESTIONS.length && step in answers

  const handleAnswer = (optIndex: number) => {
    setAnswers((prev) => ({ ...prev, [step]: optIndex }))
    setTimeout(() => {
      if (step < SEGMENT_QUESTIONS.length - 1) {
        setStep(step + 1)
      } else {
        setStep(SEGMENT_QUESTIONS.length)
      }
    }, 600)
  }

  // Antes el idioma solo cambiaba la UI local y las respuestas no iban a
  // ninguna parte (34.11). Ahora se guardan en el perfil y deciden el primer
  // paso: quien ya programa va a la prueba de nivel para saltarse lo que sabe.
  const handleLanguageSelect = (selectedLang: 'es' | 'en') => {
    setUserLanguage(selectedLang)
    updateUser({ language: selectedLang })
    void i18n.changeLanguage(selectedLang)
    void auth
      .updateMe({
        language: selectedLang,
        onboarding_experience: answers[0],
        onboarding_goal: answers[1],
        onboarding_weekly_time: answers[2],
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
    if ((answers[0] ?? 0) >= 1) {
      startPlacement(_placementTrack(answers[1] ?? 0, certTrackId))
    }
  }

  // Regular questions
  if (step < SEGMENT_QUESTIONS.length) {
    return (
      <div className="onboarding" data-testid="onboarding">
        <div className="progress">
          <div className="bar" style={{ width: `${(step + 1) / SEGMENT_QUESTIONS.length * 100}%` }}></div>
        </div>

        <div className="question-card">
          <p className="step-indicator">{t('onboarding.question', 'Pregunta')} {step + 1} / {SEGMENT_QUESTIONS.length}</p>
          <h2>{question[lang]}</h2>

          <div className="options">
            {question.options.map((opt, i) => (
              <button
                key={i}
                className="option"
                onClick={() => handleAnswer(i)}
                disabled={isAnswered && answers[step] !== i}
              >
                {opt[lang]}
              </button>
            ))}
          </div>

          {isAnswered && (
            <p className="feedback">{t('onboarding.next', 'Próxima pregunta en 1s...')}</p>
          )}
        </div>
      </div>
    )
  }

  // Cert picker: only shown when goal === 3 and no cert chosen yet
  if ((answers[1] ?? 0) === 3 && certTrackId === null) {
    return (
      <div className="onboarding" data-testid="onboarding">
        <div className="question-card">
          <h2>
            {lang === 'es'
              ? '¿Qué certificación quieres preparar?'
              : 'Which certification do you want to prepare for?'}
          </h2>
          <div className="options">
            {CERT_TRACKS.map((ct) => (
              <button
                key={ct.id}
                className="option"
                data-testid={`cert-${ct.id}`}
                onClick={() => setCertTrackId(ct.id)}
              >
                {ct[lang]}
              </button>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // Language picker
  return (
    <div className="onboarding language-choice" data-testid="onboarding">
      <h2>{t('onboarding.language', 'Elige tu idioma')}</h2>
      <p>{t('onboarding.langDesc', 'Puedes cambiar esto después en Ajustes')}</p>

      <div className="language-buttons">
        <button className="lang-btn" onClick={() => handleLanguageSelect('es')}>
          🇪🇸 Español
        </button>
        <button className="lang-btn" onClick={() => handleLanguageSelect('en')}>
          🇺🇸 English
        </button>
      </div>

    </div>
  )
}
