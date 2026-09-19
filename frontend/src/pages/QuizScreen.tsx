import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import '../styles/quiz.css'

interface QuizQuestion {
  id: string
  text_es: string
  text_en: string
  type: 'mcq' | 'fill_blank' | 'exec'
  options?: { text_es: string; text_en: string }[]
  answer_index: number
  explanation_es: string
  explanation_en: string
  p_known: number
  source?: string
}

export default function QuizScreen() {
  const { i18n, t } = useTranslation()
  const lang = i18n.language as 'es' | 'en'
  
  const [currentIdx, setCurrentIdx] = useState(0)
  const [answered, setAnswered] = useState(false)
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null)
  const [showExplanation, setShowExplanation] = useState(false)
  const [bktValue, setBktValue] = useState(0.5)

  const questions: QuizQuestion[] = [
    {
      id: 'q1',
      text_es: '¿Cuál es la salida de print(2 ** 3)?',
      text_en: 'What is the output of print(2 ** 3)?',
      type: 'mcq',
      options: [
        { text_es: '6', text_en: '6' },
        { text_es: '8', text_en: '8' },
        { text_es: '9', text_en: '9' },
        { text_es: '5', text_en: '5' }
      ],
      answer_index: 1,
      explanation_es: '** es el operador exponencial. 2³ = 8.',
      explanation_en: '** is the exponent operator. 2³ = 8.',
      p_known: 0.72,
      source: 'Python 3.12 docs'
    },
    {
      id: 'q2',
      text_es: 'Completa: x = ______ abre la lista vacía',
      text_en: 'Fill in: x = ______ opens an empty list',
      type: 'fill_blank',
      options: [
        { text_es: '[]', text_en: '[]' },
        { text_es: '{}', text_en: '{}' },
        { text_es: '()', text_en: '()' }
      ],
      answer_index: 0,
      explanation_es: '[] crea una lista vacía. {} es un dict, () es una tupla.',
      explanation_en: '[] creates an empty list. {} is a dict, () is a tuple.',
      p_known: 0.89,
      source: 'Python basics'
    }
  ]

  const q = questions[currentIdx]
  const isCorrect = selectedAnswer === q.answer_index

  useEffect(() => {
    setBktValue(q.p_known)
  }, [currentIdx, q.p_known])

  const handleAnswer = (idx: number) => {
    if (!answered) {
      setSelectedAnswer(idx)
      setAnswered(true)
    }
  }

  const handleNext = () => {
    if (currentIdx < questions.length - 1) {
      setCurrentIdx(currentIdx + 1)
      setAnswered(false)
      setSelectedAnswer(null)
      setShowExplanation(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (answered && (e.key === 'ArrowRight' || e.key === 'Enter')) {
      handleNext()
    }
  }

  return (
    <div className="quiz" onKeyDown={handleKeyDown} tabIndex={0}>
      <div className="quiz-header">
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${(currentIdx + 1) / questions.length * 100}%` }}></div>
        </div>
        <p className="progress-text">{currentIdx + 1} / {questions.length}</p>
      </div>

      <div className="bkt-section">
        <label>{t('quiz.mastery', 'Dominio Estimado')}</label>
        <div className="bkt-bar">
          <div className="bkt-fill" style={{ width: `${bktValue * 100}%` }}></div>
        </div>
        <p className="bkt-value">{Math.round(bktValue * 100)}%</p>
      </div>

      <div className="question-card">
        <h2>{q[`text_${lang}`]}</h2>

        <div className="options">
          {q.options?.map((opt, i) => (
            <button
              key={i}
              className={`option ${selectedAnswer === i ? 'selected' : ''} ${answered && selectedAnswer === i ? (isCorrect ? 'correct' : 'wrong') : ''}`}
              onClick={() => handleAnswer(i)}
              disabled={answered && selectedAnswer !== i}
            >
              {opt[`text_${lang}`]}
            </button>
          ))}
        </div>

        {answered && (
          <div className={`feedback ${isCorrect ? 'correct' : 'wrong'}`}>
            {isCorrect ? '✓ ' + t('quiz.correct', 'Correcto') : '✗ ' + t('quiz.wrong', 'Incorrecto')}
          </div>
        )}

        {answered && (
          <button className="btn-explain" onClick={() => setShowExplanation(!showExplanation)}>
            {t('quiz.why', '¿Por qué?')} {showExplanation ? '▾' : '▸'}
          </button>
        )}

        {showExplanation && (
          <div className="explanation">
            <p>{q[`explanation_${lang}`]}</p>
            {q.source && <small>{t('quiz.source', 'Fuente')}: {q.source}</small>}
          </div>
        )}

        {answered && (
          <button className="btn-next" onClick={handleNext}>
            {currentIdx < questions.length - 1 ? t('quiz.next', 'Siguiente') : t('quiz.finish', 'Terminar')} →
          </button>
        )}
      </div>
    </div>
  )
}
