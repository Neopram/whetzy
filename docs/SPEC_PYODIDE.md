# Neurium — Spec Técnico: Pyodide (Python ejecutable en navegador)

> Fase 2 del roadmap. Implementar después de que el contenido base (Fase 1) y el
> deploy (Fase 0) estén estables. El diferenciador más fuerte de Neurium contra
> toda la competencia.

---

## 1. Qué es y por qué importa

**Pyodide** es el intérprete CPython compilado a WebAssembly. Corre Python real
directamente en el navegador — sin servidor, sin latencia de red, sin costo de compute.

### Tabla competitiva

| Plataforma | Código ejecutable | Motor adaptativo | Combinación |
|---|---|---|---|
| Codecademy | Sí (lineal) | No | ❌ |
| DataCamp | Sí (lineal) | No | ❌ |
| Boot.dev | Sí (browser) | No | ❌ |
| Neurium sin Pyodide | No — solo MCQ | Sí | Incompleto |
| **Neurium con Pyodide** | **Sí (browser)** | **Sí** | **✅ Único** |

**La diferencia crítica con Boot.dev:** ellos tienen código ejecutable pero path lineal
para todos. Neurium tiene código ejecutable + motor adaptativo que decide qué ejercicio
de código necesitas ahora basándose en tu BKT. Nadie tiene eso.

---

## 2. Tres tipos de ejercicio

### Tipo 1 — `code_output` (predice el resultado)

El usuario ve código y debe **predecir qué produce al ejecutarlo**.
Con Pyodide puede ejecutarlo y confirmar.

```python
# Pregunta
x = [1, 2, 3]
y = x
y.append(4)
print(x)
```

*Concepto evaluado: aliasing de listas (BKT sk010401)*
*El motor registra si el usuario entendió que `y = x` no copia*

### Tipo 2 — `fill_blank_exec` (completa y ejecuta)

El usuario **escribe el código faltante**, lo ejecuta, y ve si produce el output
esperado. El motor verifica por output, no por igualdad de código — hay múltiples
soluciones válidas.

```python
# Completa la función para que devuelva el factorial de n
def factorial(n):
    _______________
    _______________

# Output esperado: factorial(5) → 120
```

*Concepto evaluado: recursión (BKT sk010301)*
*Si el usuario usa iteración en vez de recursión → también correcto, BKT actualiza igualmente*

### Tipo 3 — `fix_bug` (corrige el error)

El usuario ve código **con un bug**, lo ejecuta para ver el error, y lo corrige.
El tutor AI analiza el error específico si el usuario no lo encuentra.

```python
# Este código tiene un bug. Corrígelo.
def average(numbers):
    return sum(numbers) / len(numbers)

result = average([])
print(result)  # Debe manejar lista vacía sin ZeroDivisionError
```

*Concepto evaluado: manejo de excepciones, edge cases (BKT sk010701)*

---

## 3. Flujo de evaluación integrado con el motor

```
Usuario escribe/modifica código en el editor
        ↓
[Pyodide en WebWorker — no bloquea UI]
Ejecuta código con timeout (5s) y sandbox
        ↓
Compara output con expected_output del JSON
        ↓ (si correcto)                    ↓ (si incorrecto)
BKT.update(skill, correct=True)      BKT.update(skill, correct=False)
FSRS.update(card, rating=4)          FSRS.update(card, rating=1)
XP += points                         Tutor AI analiza el error:
Elo sube                               - Error de sintaxis → explica sintaxis
                                       - TypeError → explica tipos
                                       - Lógica → explica el concepto
                                       - Motor programa refuerzo del skill
```

### Integración con `QuizAnswerResponse`

Añadir al schema:

```python
class PyodideResult(BaseModel):
    user_code: str
    actual_output: str
    expected_output: str
    execution_time_ms: int
    error: str | None  # None si ejecutó sin excepción

class QuizAnswerResponse(BaseModel):
    # ... campos existentes ...
    pyodide_result: PyodideResult | None = None
```

---

## 4. Arquitectura técnica

### Frontend — `PyodideRunner.tsx`

```typescript
// Ejecuta en WebWorker para no bloquear la UI
// Timeout de 5 segundos (proceso infinito → terminar)
// Sandbox: sin acceso a red, sin I/O de archivo

interface PyodideRunnerProps {
  starterCode: string;
  expectedOutput: string;
  skillId: string;
  onResult: (result: PyodideResult) => void;
}
```

**Carga de Pyodide:** ~6 MB inicial (cacheable via Service Worker).
Primera carga: ~3-5 segundos. Cargas posteriores: desde caché.

### Tipos de pregunta nuevos en JSON

```json
{
  "id": "q010401099",
  "skill_id": "sk010401",
  "type": "fill_blank_exec",
  "difficulty_tier": "intermediate",
  "question_es": "Completa la función para que retorne una copia independiente de la lista.",
  "question_en": "Complete the function so it returns an independent copy of the list.",
  "starter_code": "def copy_list(lst):\n    return ___",
  "test_cases": [
    {"input": "[1, 2, 3]", "expected_output": "[1, 2, 3]"},
    {"input": "call: original = [1,2,3]; copy = copy_list(original); original.append(4); copy", "expected_output": "[1, 2, 3]"}
  ],
  "explanation_es": "...",
  "explanation_en": "...",
  "source": "CPython docs 3.13 — copy module"
}
```

### Backend — cambios mínimos

El backend **no ejecuta código** — Pyodide corre en el cliente.
Solo recibe el resultado verificado y aplica el motor:

```python
# quiz.py — nuevo campo en AnswerRequest
class AnswerRequest(BaseModel):
    question_id: str
    selected_index: int | None = None   # MCQ/true_false
    user_code: str | None = None        # Pyodide
    actual_output: str | None = None    # resultado en cliente
    time_taken_ms: int
```

La lógica de corrección para `fill_blank_exec` y `fix_bug` se verifica en el **cliente**
(output correcto/incorrecto) y el backend recibe solo el booleano resultado. El código
del usuario se guarda para análisis del tutor AI si la respuesta fue incorrecta.

---

## 5. Sandbox y seguridad

Pyodide en WebWorker proporciona aislamiento automático:
- Sin acceso a DOM fuera del worker
- Sin `fetch` / XMLHttpRequest desde Pyodide (configurable)
- Timeout de 5 segundos vía `worker.terminate()`
- El código del usuario **nunca llega al servidor** — solo el output

Módulos disponibles para los ejercicios (preinstalar en Pyodide):
- `math`, `itertools`, `functools`, `collections`, `typing` — siempre
- `json`, `re`, `pathlib` — para ejercicios de ingeniería
- `numpy` — para ejercicios de AI/ML (carga bajo demanda, ~5 MB extra)

---

## 6. Conexión con bootcamps de certificación

Las certs de AWS, Azure, y Google Cloud tienen **preguntas de código en sus exámenes reales**.
Un bootcamp de certificación en Neurium con Pyodide:

- **AWS:** ejercicios de Python para boto3, Lambda handlers, scripts de automatización
- **Azure ML / AI-102:** ejercicios de código para Azure SDK, llamadas a APIs de AI
- **Google ML Engineer:** NumPy, pandas, scikit-learn snippets ejecutables

Ningún competidor en el espacio de preparación para certs (Whizlabs, ExamTopics,
MeasureUp) tiene código ejecutable. Es un diferenciador directo.

---

## 7. Cronograma de implementación

| Paso | Qué | Modelo |
|---|---|---|
| 7.1 | `PyodideRunner.tsx` con WebWorker + timeout | Sonnet |
| 7.2 | Tipos `fill_blank_exec` y `fix_bug` en el content JSON schema | Haiku |
| 7.3 | Extender `AnswerRequest` + `QuizAnswerResponse` | Sonnet |
| 7.4 | Integración con tutor AI para análisis de errores de código | Sonnet |
| 7.5 | 30 preguntas Pyodide en Track 01 (aliasing, closures, recursión) | Haiku |
| 7.6 | Verificación E2E en navegador | — |

**Criterio de aceptación:** usuario escribe código incorrecto → Pyodide lo ejecuta →
tutor AI explica el error específico → BKT actualiza el dominio → motor planifica refuerzo.

---

## 8. Impacto en el argumento de venta

> "Neurium no te da preguntas sobre código — te hace escribir y ejecutar código real.
> El motor sabe exactamente qué concepto no dominas y te da el ejercicio que necesitas ahora."
