export const meta = {
  name: 'reservadas-37-24',
  description: '37.24: banco de simulacro reservado (pool simulacro). Sonnet escribe desde fragmentos literales de fuente oficial, revisor adversario Sonnet por pregunta, corrector Sonnet',
  phases: [
    { title: 'Escribir', detail: 'un escritor por bloque de fragmentos de una skill', model: 'sonnet' },
    { title: 'Revisar', detail: 'revisor adversario por pregunta contra su fragmento', model: 'sonnet' },
    { title: 'Corregir', detail: 'corrector donde haya defectos', model: 'sonnet' },
  ],
}

const RES = '/tmp/claude-0/-home-user-whetzy/f27deaa8-7d94-54bb-9529-68ae8cf55f6a/scratchpad/res'

const Q = {
  type: 'object',
  properties: {
    slot: { type: 'integer' }, fragment_id: { type: 'string' },
    question_es: { type: 'string' }, question_en: { type: 'string' },
    options_es: { type: 'array', items: { type: 'string' }, minItems: 4, maxItems: 4 },
    options_en: { type: 'array', items: { type: 'string' }, minItems: 4, maxItems: 4 },
    correct_index: { type: 'integer', minimum: 0, maximum: 3 },
    explanation_es: { type: 'string' }, explanation_en: { type: 'string' },
    fragment: { type: 'string' },
  },
  required: ['slot', 'fragment_id', 'question_es', 'question_en', 'options_es', 'options_en', 'correct_index', 'explanation_es', 'explanation_en', 'fragment'],
}
const WRITE = { type: 'object', properties: { questions: { type: 'array', items: Q } }, required: ['questions'] }
const REVIEW = { type: 'object', properties: {
  fragment_is_verbatim: { type: 'boolean' }, answer_supported_by_fragment: { type: 'boolean' },
  copies_source_wording: { type: 'boolean' }, duplicates_practice: { type: 'boolean' },
  defects: { type: 'array', items: { type: 'object', properties: {
    severity: { type: 'string', enum: ['blocker', 'major', 'minor'] }, issue: { type: 'string' }, fix: { type: 'string' } },
    required: ['severity', 'issue', 'fix'] } } },
  required: ['fragment_is_verbatim', 'answer_supported_by_fragment', 'copies_source_wording', 'duplicates_practice', 'defects'] }
const CORR = { type: 'object', properties: { discard: { type: 'boolean' }, reason: { type: 'string' }, question: Q }, required: ['discard', 'reason', 'question'] }

const LEVEL = {
  'CLF-C02': 'AWS Certified Cloud Practitioner (fundamentos): conceptos de nube, propuesta de valor, modelo de responsabilidad compartida, seguridad y cumplimiento, qué servicio cubre qué necesidad a alto nivel, facturación y soporte como conceptos.',
  'SAA-C03': 'AWS Certified Solutions Architect – Associate: dado un escenario con requisitos (resiliencia, rendimiento, seguridad, coste), elegir la arquitectura o el servicio adecuado y por qué.',
  'AIF-C01': 'AWS Certified AI Practitioner (fundamentos): conceptos de IA/ML e IA generativa, cuándo usar qué servicio o capacidad (Bedrock, SageMaker, servicios de IA), IA responsable, seguridad y gobernanza, a nivel conceptual.',
  'MLA-C01': 'AWS Certified Machine Learning Engineer – Associate: elegir el servicio o la capacidad adecuada para un escenario de ingeniería de ML (datos, entrenamiento, despliegue, monitorización).',
  'PCEP-30-02': 'PCEP (Python de nivel inicial): semántica del lenguaje, tipos, operadores, control de flujo, colecciones básicas, funciones. Se permiten fragmentos de código cortos (≤ 8 líneas) con «¿qué imprime?» si la respuesta se sigue de la fuente y de la semántica de Python 3.',
  'PCAP-31-03': 'PCAP (Python asociado): módulos y paquetes, excepciones, cadenas, POO (clases, herencia, polimorfismo), generadores, cierres, ficheros. Se permiten fragmentos de código cortos (≤ 10 líneas) con «¿qué imprime?» si la respuesta se sigue de la fuente y de la semántica de Python 3.',
  'CC': 'ISC2 Certified in Cybersecurity (nivel inicial): principios de seguridad, continuidad de negocio, respuesta a incidentes, control de acceso, seguridad de red y operaciones de seguridad, a nivel conceptual. La fuente es NIST: pregunta el concepto, no «según NIST».',
  'SY0-701': 'CompTIA Security+ SY0-701: conceptos generales de seguridad, amenazas y mitigaciones, arquitectura, operaciones y gestión del programa de seguridad, con escenarios. La fuente es NIST: pregunta el concepto, no «según NIST».',
}
const rules = code => `Reglas (Whetzy, ADR-59, CATALOGO_MAESTRO §7). Pregunta para el BANCO RESERVADO DEL SIMULACRO de ${code}: no se usa en práctica, así que debe parecerse a una pregunta del examen real.
- Nivel: ${LEVEL[code]}
- multiple_choice, 4 opciones, UNA correcta, deducible SOLO del fragmento citado (y, en preguntas de código Python, de la semántica del lenguaje).
- REDACCIÓN ORIGINAL en enunciado, opciones y explicación (ES y EN): prohibido copiar más de 8 palabras consecutivas del text del fragmento en cualquier campo salvo "fragment" (los nombres de servicios, funciones o términos técnicos no cuentan; una frase entera sí).
- "fragment" es una cita LITERAL (1-3 frases seguidas) del campo text del fragmento, sin parafrasear ni quitar palabras; debe nombrar su sujeto (no empieces en "It..." ni a mitad de frase). Es evidencia para el revisor; no se publica.
- Distractores plausibles para quien prepara ${code} y claramente falsos según la fuente. Ninguna opción de una sola palabra salvo que sean literales de código. La correcta NO debe ser la opción más larga (igual o más corta que al menos una incorrecta), en ES y en EN. Opciones con la misma forma. Nada de "todas/ninguna de las anteriores".
- NADA de precios, cuotas, límites numéricos, regiones, tipos de instancia concretos, versiones de modelos o de productos, fechas, preview/GA, números de control o de sección, ni sintaxis de API o SDK al detalle.
- No repitas el hecho ni el planteamiento de ninguna pregunta de práctica de la skill (lista "existing" del paquete): el simulacro debe medir, no premiar la memoria.
- Español neutro con tildes (sin voseo), inglés nativo, no traducción literal.
- Explicación ES y EN (2-4 frases): por qué la correcta lo es y por qué fallan las otras, sin afirmar sobre la fuente nada que el fragmento no diga.`

const chunks = args.chunks || args.items.map(s => { const [id, code] = s.split('|'); return { id, code, sk: id.split('-')[0], fromFile: true } })
log(`${chunks.length} bloques${args.pilot ? ' (PILOTO: sin corrector)' : ''}`)

const results = await pipeline(
  chunks,
  async c => {
    const slotsTxt = c.fromFile
      ? `los slots del fichero ${RES}/chunk/${c.id}.json (léelo con Read: campo "slots", cada uno con slot, fragment_id y correct_index)`
      : c.slots.map(s => `slot ${s.slot} -> fragment_id ${s.fragment_id}, correct_index ${s.correct_index}`).join('; ')
    const w = await agent(`Eres el escritor de preguntas de Whetzy. Lee con Read el paquete ${RES}/pack/${c.sk}.json: su skill (name_en, ${c.code}); "existing" son las preguntas de práctica de esa skill (no las repitas) y "fragments" los fragmentos de fuente (id, title, url, heading, text).
Escribe exactamente una pregunta por slot, cada una SOLO a partir de su fragmento asignado y con la respuesta correcta en el índice indicado. Slots: ${slotsTxt}.
Si dos slots comparten fragmento, deben evaluar hechos distintos. Usa solo los fragmentos asignados.
${rules(c.code)}`, { label: `escritor ${c.id}`, phase: 'Escribir', model: 'sonnet', schema: WRITE })
    if (!w) return []
    const seen = new Set()
    return w.questions.filter(q => { if (seen.has(q.slot)) return false; seen.add(q.slot); return true }).map(q => ({ c, q }))
  },
  async items => parallel(items.map(({ c, q }) => async () => {
    const extra = /```|\n\s{2,}\S|print\(/.test(q.question_en + q.question_es) ? 'La pregunta contiene código: ejecútalo con python3 (Bash) y comprueba que la salida coincide con la opción marcada como correcta y con ninguna otra.' : ''
    const review = await agent(`Eres un revisor adversario: buscas fallos, no apruebas por defecto. Pregunta candidata (JSON): ${JSON.stringify(q)}
Lee con Read SOLO el fragmento fuente ${RES}/frag/${q.fragment_id}.txt (cabecera title/url/heading y luego "text:"; si no existe, blocker) y, para la duplicación, el campo "existing" de ${RES}/pack/${c.sk}.json.
Comprueba: (1) "fragment" aparece LITERAL dentro del text; (2) la respuesta correcta se deduce de él y la cita nombra su sujeto; (3) ningún distractor es también correcto o defendible; (4) la pregunta es de la skill del paquete y del nivel de ${c.code} (la skill está en "name_en" del paquete); (5) COPIA: ningún campo salvo "fragment" reproduce más de 8 palabras consecutivas del text (copies_source_wording); (6) DUPLICADO: evalúa el mismo hecho con el mismo planteamiento que alguna de "existing" (duplicates_practice); (7) ambigüedad, error técnico, trivia de precios, cuotas, regiones, versiones, números de control o sintaxis, correcta delatada por longitud o forma, opciones de una palabra, ES con voseo o sin tildes, EN no nativo, explicación que afirme sobre la fuente algo que no dice. ${extra}
Severidad: blocker = respuesta incorrecta, dos correctas o no respaldada; major = ambigüedad seria, distractor defendible, error técnico, cita no literal o sin sujeto, fuera de la skill o del nivel, copia de redacción, duplicado de práctica; minor = estilo o redacción.
${rules(c.code)}`, { label: `revisor ${c.sk}.${q.slot}`, phase: 'Revisar', model: 'sonnet', schema: REVIEW })
    if (!review) return { sk: c.sk, track: c.track, code: c.code, q, review: null, corrected: null }
    if (args.pilot || !review.defects.length) return { sk: c.sk, track: c.track, code: c.code, q, review, corrected: null }
    const corrected = await agent(`Eres el corrector. Pregunta original (JSON): ${JSON.stringify(q)}
Defectos del revisor: ${JSON.stringify(review.defects)}
Lee con Read SOLO el fragmento fuente ${RES}/frag/${q.fragment_id}.txt y el campo "existing" de ${RES}/pack/${c.sk}.json.
Corrige TODOS los defectos manteniendo slot, fragment_id y correct_index. "fragment" debe seguir siendo cita literal del text; los demás campos, redacción propia (nunca más de 8 palabras consecutivas del text). Si la pregunta tiene código, ejecútalo con python3 para confirmar la correcta. Devuelve SIEMPRE la pregunta completa en "question". Si no se puede arreglar sin cambiar la pregunta entera o la fuente no la respalda, discard=true con la razón (y en "question" la original).
${rules(c.code)}`, { label: `corrector ${c.sk}.${q.slot}`, phase: 'Corregir', model: 'sonnet', schema: CORR })
    return { sk: c.sk, track: c.track, code: c.code, q, review, corrected }
  }))
)
return results.flat().filter(Boolean)
