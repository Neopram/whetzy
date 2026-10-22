# Guión — Video Motor (5 min) — Español

## Objetivo
Explicar la tecnología detrás de Whetzy: BKT, FSRS, adaptatividad. Target: técnicos, educadores, reclutadores tech.

## Estructura

### Intro (0:00-0:20)
- **Visual:** Línea de código compilando, terminal con salida limpia
- **Narración:** "¿Cómo logra una plataforma educar a cada usuario de forma diferente? Hoy revelamos el motor."
- **Superposición:** "El Corazón Adaptativo de Whetzy"

### 1. El Problema de la Escala (0:20-0:45)
- **Visual:** Gráfico: 1000 estudiantes, línea horizontal (todos reciben lo mismo)
- **Narración:** "Un profesor tutora a 30 estudiantes. Ve cuándo Maria necesita más práctica en bucles y cuándo Johan está listo para funciones. Pero con 10,000 estudiantes, ¿cómo escala ese juicio?"
- **Transición:** Zoom out a 10,000 estudiantes

### 2. Bayesian Knowledge Tracing (0:45-2:15)
- **Visual:** Animación de ecuación BKT simplificada en la pantalla
  - p_known (probabilidad de dominio)
  - p_guess (probabilidad de adivinar)
  - p_slip (probabilidad de error por distracción)
- **Narración:** "Usamos Bayesian Knowledge Tracing. Para cada habilidad ('funciones en Python'), estimamos: ¿Qué probabilidad hay de que Johan la domina?"
- **Visual:** Grafo de habilidades -> preguntas -> respuestas
- **Narración:** "Cada respuesta nos dice algo: ¿Respondió mal porque no la entiende, o fue un lapsus? Bayesian actualiza la creencia."
- **Ejemplo en pantalla:**
  - "Johan responde Q1 correctamente: p_known sube a 0.65"
  - "Johan responde Q2 mal: ¿Falla genuina? → p_known baja a 0.55"
  - "Johan responde Q3 correctamente: p_known sube a 0.72"

### 3. Espaciado: FSRS (2:15-3:45)
- **Visual:** Curva de olvido tradicional vs. curva FSRS (roja/azul)
- **Narración:** "Conocer algo hoy no significa que lo recuerdes en 3 meses. Ebbinghaus documentó la curva de olvido hace 140 años. FSRS ('Free Spaced Repetition Scheduler') resuelve eso."
- **Animación:** Preguntas que reaparecen a intervalos óptimos
  - "Pregunta respondida correctamente hoy"
  - "Reaparece en 3 días (si difícil) o 10 días (si fácil)"
  - "Cada revisión extiende el intervalo"
- **Narración:** "En lugar de un calendario fijo, calculamos: dado que Johan domina esto al 72%, ¿en cuántos días podría olvidarlo? Programamos la revisión justo antes."
- **Gráfico:** Matriz de intervalos (difficulty vs. stability)

### 4. Selección Adaptativa (3:45-4:30)
- **Visual:** Quiz screen: 3 opciones de preguntas
- **Narración:** "Ahora que sabemos el estado de Johan en cada habilidad, ¿qué pregunta hacemos?"
- **Opciones visibles:**
  - "Opción A: Fácil (95 % de acierto) — Aburrida"
  - "Opción B: Media (~75 % de acierto) — 'Just right'"
  - "Opción C: Difícil (30 % de acierto) — Frustrante"
- **Narración:** "Seleccionamos la que sea desafiante pero no imposible. Eso maximiza aprendizaje. Whetzy busca el 75% de tasa de acierto."

### 5. Verificación: E2E Testing (4:30-4:55)
- **Visual:** Terminal corriendo `pytest tests/content/test_exec_questions.py` — PASS
- **Narración:** "¿Cómo sabemos que funciona? Tests. Cada pregunta ejecutable se valida: ¿El código de prueba realmente rechaza respuestas malas y acepta buenas?"
- **SFX:** Tipeo rápido, test passing chime

### Cierre (4:55-5:00)
- **Visual:** Logo Whetzy + URL
- **Narración:** "Eso es Whetzy. Ciencia en código. Adaptatividad a escala."
- **Superposición:** `whetzy.com` + `YT-ES-MOTOR`

## Notas Técnicas
- **Duración exacta:** 4:58-5:02
- **Resolución:** 1080p 16:9
- **Visual style:** Motion graphics + screenshots reales de la plataforma
- **Código de campaña:** `YT-ES-MOTOR` (final screen)
- **Subtítulos:** ES con ecuaciones/términos técnicos clarificados
- **Audio:** Narración técnica pero accesible, música subtle (sine wave + ambient)
