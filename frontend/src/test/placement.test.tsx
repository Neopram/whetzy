/**
 * La prueba de nivel usa el motor del servidor, no una cuenta local.
 *
 * Esta pantalla llevaba diez preguntas escritas en los ficheros de idioma y
 * calculaba el nivel con `ability + (acierto ? 0.05 : -0.03)`. El motor CAT con
 * IRT existia en el backend desde el principio —elige cada item segun lo que ya
 * sabe del alumno, para cuando la estimacion se estabiliza y dice que modulos
 * puede saltarse— y no lo llamaba nadie. Ademas el cliente tenia mal las tres
 * llamadas: `start` sin `track_id`, `answer` con `answer_index` en lugar de
 * `selected_index` y sin tiempo, y `result` contra una ruta que daba 404.
 *
 * La version anterior de este fichero comprobaba propiedades de aquel pool de
 * diez preguntas (que la respuesta correcta no estuviera siempre en la misma
 * posicion, que existiera en los dos idiomas). Ese pool ya no existe: las
 * preguntas salen del banco real, y el sesgo de posicion lo vigila
 * `scripts/check_question_bank.py`. Lo que hay que fijar ahora es que la
 * pantalla **no calcule** y que hable el idioma del usuario.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '../i18n'
import { PlacementScreen } from '../pages/PlacementScreen'
import { placement as placementApi } from '../services/api'
import { useAppStore } from '../stores/useAppStore'

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>()
  return {
    ...actual,
    placement: { start: vi.fn(), answer: vi.fn(), result: vi.fn() },
  }
})

const start = placementApi.start as unknown as ReturnType<typeof vi.fn>
const answer = placementApi.answer as unknown as ReturnType<typeof vi.fn>
const result = placementApi.result as unknown as ReturnType<typeof vi.fn>

function pregunta(id: string) {
  return {
    id,
    skill_id: 'sk010101',
    type: 'mcq' as const,
    difficulty_tier: 'easy' as const,
    question_es: `Enunciado en español ${id}`,
    question_en: `English stem ${id}`,
    options_es: ['uno', 'dos', 'tres'],
    options_en: ['one', 'two', 'three'],
    correct_answer_es: null,
    correct_answer_en: null,
    expected_time_ms: 30000,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  useAppStore.setState((s) => ({ user: { ...s.user, language: 'es' } }))
})
afterEach(cleanup)

async function empezar() {
  render(<PlacementScreen trackId="track01" />)
  await userEvent.click(screen.getByRole('button', { name: /empezar|comenzar|start/i }))
}

describe('prueba de nivel', () => {
  it('arranca la sesion en la ruta elegida', async () => {
    start.mockResolvedValue({
      session_id: 's1', track_id: 'track01', question: pregunta('q1'), questions_answered: 0,
    })

    await empezar()

    // Sin `track_id` el backend no sabe de que pool elegir: era el primer fallo.
    await waitFor(() => expect(start).toHaveBeenCalledWith('track01'))
  })

  it('manda el indice elegido y el tiempo de respuesta', async () => {
    start.mockResolvedValue({
      session_id: 's1', track_id: 'track01', question: pregunta('q1'), questions_answered: 0,
    })
    answer.mockResolvedValue({
      correct: true, ability_estimate: 0.4, ability_se: 0.5,
      questions_answered: 1, finished: false, next_question: pregunta('q2'),
    })

    await empezar()
    await screen.findByText(/Enunciado en español q1/)
    await userEvent.click(screen.getByRole('button', { name: /dos/ }))

    await waitFor(() => expect(answer).toHaveBeenCalled())
    const [sesion, idPregunta, indice, ms] = answer.mock.calls[0]
    expect(sesion).toBe('s1')
    expect(idPregunta).toBe('q1')
    expect(indice).toBe(1)
    expect(typeof ms).toBe('number')
    expect(ms).toBeGreaterThanOrEqual(0)
  })

  it('el nivel que enseña sale del motor, no de una cuenta propia', async () => {
    start.mockResolvedValue({
      session_id: 's1', track_id: 'track01', question: pregunta('q1'), questions_answered: 0,
    })
    answer.mockResolvedValue({
      correct: false, ability_estimate: 1.8, ability_se: 0.3,
      questions_answered: 1, finished: true, next_question: null,
    })
    result.mockResolvedValue({
      session_id: 's1', track_id: 'track01',
      ability_estimate: 1.8, ability_se: 0.3,
      total_questions: 24, correct: 20, accuracy: 0.83, reliability: 0.91,
      skill_mastery: {},
      module_recommendations: [
        {
          module_id: 'm0101', module_name_es: 'Variables', module_name_en: 'Variables',
          accuracy: 0.9, questions_seen: 6, can_skip: true,
        },
        {
          module_id: 'm0102', module_name_es: 'Bucles', module_name_en: 'Loops',
          accuracy: 0.4, questions_seen: 5, can_skip: false,
        },
      ],
    })

    await empezar()
    await screen.findByText(/Enunciado en español q1/)
    await userEvent.click(screen.getByRole('button', { name: /uno/ }))

    // theta 1.8 -> «Advanced» (>= 1.5). La ultima respuesta fue FALLO: si la
    // pantalla siguiera restando por su cuenta, no llegaria a ese tramo.
    // ADR-60: en palabras, sin el 80 % que daba la escala.
    expect(await screen.findByRole('heading', { name: /Advanced|Avanzado/ })).toBeTruthy()
    expect(screen.queryByRole('heading', { name: /%/ })).toBeNull()
    expect(result).toHaveBeenCalledWith('s1')
  })

  it('lista solo los modulos que el motor marca como saltables', async () => {
    start.mockResolvedValue({
      session_id: 's1', track_id: 'track01', question: pregunta('q1'), questions_answered: 0,
    })
    answer.mockResolvedValue({
      correct: true, ability_estimate: 1.5, ability_se: 0.3,
      questions_answered: 1, finished: true, next_question: null,
    })
    result.mockResolvedValue({
      session_id: 's1', track_id: 'track01',
      ability_estimate: 1.5, ability_se: 0.3,
      total_questions: 22, correct: 18, accuracy: 0.82, reliability: 0.88,
      skill_mastery: {},
      module_recommendations: [
        {
          module_id: 'm0101', module_name_es: 'Variables', module_name_en: 'Variables',
          accuracy: 0.9, questions_seen: 6, can_skip: true,
        },
        {
          module_id: 'm0102', module_name_es: 'Bucles', module_name_en: 'Loops',
          accuracy: 0.4, questions_seen: 5, can_skip: false,
        },
      ],
    })

    await empezar()
    await screen.findByText(/Enunciado en español q1/)
    await userEvent.click(screen.getByRole('button', { name: /uno/ }))

    expect(await screen.findByText('Variables')).toBeTruthy()
    expect(screen.queryByText('Bucles')).toBeNull()
  })

  it('avisa cuando la estimacion es poco fiable en vez de darla por buena', async () => {
    start.mockResolvedValue({
      session_id: 's1', track_id: 'track01', question: pregunta('q1'), questions_answered: 0,
    })
    answer.mockResolvedValue({
      correct: true, ability_estimate: 0.2, ability_se: 1.4,
      questions_answered: 1, finished: true, next_question: null,
    })
    result.mockResolvedValue({
      session_id: 's1', track_id: 'track01',
      ability_estimate: 0.2, ability_se: 1.4,
      total_questions: 8, correct: 5, accuracy: 0.62,
      reliability: 0.41, skill_mastery: {}, module_recommendations: [],
    })

    await empezar()
    await screen.findByText(/Enunciado en español q1/)
    await userEvent.click(screen.getByRole('button', { name: /uno/ }))

    expect(await screen.findByText(/unreliable|poco fiable/)).toBeTruthy()
    expect(screen.queryByText(/41/)).toBeNull()
  })

  it('pregunta en el idioma del usuario', async () => {
    useAppStore.setState((s) => ({ user: { ...s.user, language: 'en' } }))
    start.mockResolvedValue({
      session_id: 's1', track_id: 'track01', question: pregunta('q1'), questions_answered: 0,
    })

    await empezar()

    expect(await screen.findByText(/English stem q1/)).toBeTruthy()
    expect(screen.queryByText(/Enunciado en español/)).toBeNull()
    expect(screen.getByRole('button', { name: /two/ })).toBeTruthy()
  })

  it('dice que pasa cuando la ruta no tiene preguntas con opciones', async () => {
    start.mockRejectedValue(new Error('Track track14 has no questions that can be answered'))

    await empezar()

    expect(await screen.findByRole('alert')).toBeTruthy()
  })
})
