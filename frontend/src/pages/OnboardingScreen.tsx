import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAppStore } from '../stores/useAppStore'
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
      { es: 'Avanzar en mi carrera', en: 'Advance my career' }
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

export default function OnboardingScreen({ onDone }: { onDone: () => void }) {
  const { i18n, t } = useTranslation()
  const setUserLanguage = useAppStore((s) => s.setLanguage)
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [referralCode, setReferralCode] = useState('')

  const lang = i18n.language as 'es' | 'en'
  const question = SEGMENT_QUESTIONS[step]
  const isAnswered = step in answers

  const handleAnswer = (optIndex: number) => {
    setAnswers({ ...answers, [step]: optIndex })
    setTimeout(() => {
      if (step < SEGMENT_QUESTIONS.length - 1) {
        setStep(step + 1)
      } else {
        setStep(SEGMENT_QUESTIONS.length)
      }
    }, 600)
  }

  const handleLanguageSelect = (selectedLang: 'es' | 'en') => {
    setUserLanguage(selectedLang)
    i18n.changeLanguage(selectedLang)
    onDone()
  }

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

      <div className="referral-section">
        <input
          type="text"
          placeholder={t('onboarding.referralCode', 'Código de referido (opcional)')}
          value={referralCode}
          onChange={(e) => setReferralCode(e.target.value)}
        />
      </div>
    </div>
  )
}
