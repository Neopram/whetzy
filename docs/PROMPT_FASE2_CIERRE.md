# Prompt: Auditoría + Cierre de Fase 2 al 100%

> Sesión nueva. Lee este prompt completo antes de ejecutar cualquier comando.
> Postura: escéptica. STATUS.md es lo que auditas, no tu fuente de verdad.
> Model routing obligatorio: Haiku para boilerplate/JSON, Sonnet para implementación,
> nunca Opus en esta sesión (límite de tokens).

---

## CONTEXTO — estado real del proyecto

Repo en: `C:\Users\feder\Desktop\Banco de preguntas\python\learning-engine\`

**Lo que STATUS.md dice que existe (sesiones a–l):**
- Fase 0: 90% — rebrand, auth JWT, quiz adaptativo, gamificación, tutor, seguridad ASVS, Docker+CI
- Fase 1: 100% — 1246 Q (7 tracks, 207 skills, todas ≥6), source 1246/1246, glosario 70 términos, TracksScreen BKT-gated
- Fase 2: ~70% — ChromaDB RAG activo, tutor con inyección RAG, Groq wired (sin key), **Pyodide pendiente según sesión (l)**

**Incógnita crítica:** una sesión paralela afirma haber implementado Pyodide (WebWorker + fill_blank_exec/fix_bug + QuizScreen actualizado). STATUS.md sesión (l) dice "Pyodide pendiente". Tu primera tarea es resolver esa contradicción con evidencia de código, no con suposiciones.

**Dominio comprado:** whetzy.com (Cloudflare). Rebrand Neurium→Whetzy pendiente — hacerlo en esta sesión si el tiempo lo permite, ANTES del deploy, no después.

---

## GOTCHAS DEL ENTORNO (no los redescubras)

| Gotcha | Detalle |
|---|---|
| Python | Sistema (3.12), ya tiene sqlalchemy, aiosqlite, pydantic, pydantic-settings, chromadb, sentence-transformers. No crees venv. |
| SQLite | Desktop = `Permission denied`. Usa `%TEMP%` → `C:\Users\feder\AppData\Local\Temp\`. DATABASE_URL con ruta absoluta y barras normales. |
| .env | `config.py` lee del CWD. Crea `backend/.env` antes de correr el server. |
| Browser preview | No alcanza localhost:8000. Usa `curl` o el proxy Vite `/api` (ya configurado). |
| Service Worker | Solo en PROD. En dev: si ves UI vieja, desregistra SW + limpia caches. |
| `validate_content.py` | ⚠️ NO EXISTE en el repo. STATUS.md afirma haberlo corrido en sesiones (c)–(j). Las afirmaciones de "0 errores" no son reproducibles. Escribe tu propio validador si lo necesitas. |
| ChromaDB | Descarga all-MiniLM-L6-v2 (~90MB) en primera construcción. Persiste en `backend/chroma_db/`. |
| Limpieza | Borra `backend/.env`, DB de temp y scripts de auditoría al terminar. |

---

## PASO 0 — Resolver la contradicción Pyodide (5 min, gratis)

Antes de tocar código, ejecuta:

```bash
# ¿Existe el WebWorker?
ls frontend/public/pyodide-worker.js 2>/dev/null || echo "NO EXISTE"

# ¿Existe el hook?
ls frontend/src/hooks/usePyodide.ts 2>/dev/null || echo "NO EXISTE"

# ¿QuizScreen tiene rama exec?
grep -n "fill_blank_exec\|fix_bug\|code_output\|usePyodide\|PyodideRunner" \
     frontend/src/screens/QuizScreen.tsx 2>/dev/null | head -20

# ¿El backend selecciona exec types?
grep -n "fill_blank_exec\|fix_bug\|exec_type\|pyodide" \
     backend/app/services/quiz.py 2>/dev/null | head -20
```

**Si Pyodide existe en código:** confirma que `tsc -b` compila sin errores y pasa al Paso 1.
**Si Pyodide no existe:** es el ítem más grande de Fase 2 — impleméntalo en el Paso 3.

---

## PASO 1 — Auditoría rápida del núcleo (VERIFY_MASTER_PROMPT Bloques A y K)

### A — ¿El core sigue intacto?

```bash
# TypeScript sin errores
cd frontend && npx tsc -b --noEmit 2>&1 | tail -20

# Backend AST
cd backend && python -c "import app.main; print('AST OK')"

# Archivos críticos existen con implementación real
grep -l "award_badges\|auto_award" backend/app/ -r --include="*.py"
grep -l "elo_rating\|bkt_mastery\|fsrs_stability" backend/app/ -r --include="*.py"
grep -l "RAGIndex\|chroma\|sentence_transformer" backend/app/ -r --include="*.py"
grep -l "GlossaryTerm\|glossary_term" backend/app/ -r --include="*.py"
grep -l "TracksScreen\|curriculum" frontend/src/ -r
```

### K — HTTP E2E completo

```bash
cd backend
# .env con DATABASE_URL a %TEMP%
cat > .env << 'EOF'
ENVIRONMENT=development
DATABASE_URL=sqlite+aiosqlite:///C:/Users/feder/AppData/Local/Temp/neurium_audit.db
SECRET_KEY=audit-key-2026
CHROMA_PERSIST_PATH=C:/Users/feder/AppData/Local/Temp/chroma_audit
EOF

python -m app.services.content_loader 2>&1 | tail -3
python -m app.services.seed 2>&1 | tail -3

# Arranca en background
uvicorn app.main:app --host 127.0.0.1 --port 8765 &
sleep 4

# Register → quiz → answer → source presente
TOKEN=$(curl -s -X POST http://127.0.0.1:8765/api/v1/auth/register \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=audit2@whetzy.com&password=Audit_2026!" \
  | python -c "import sys,json; print(json.load(sys.stdin).get('access_token','FAIL'))")

QUIZ=$(curl -s -X POST http://127.0.0.1:8765/api/v1/quiz/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"skill_id": "sk010401"}')

echo "source: $(echo $QUIZ | python -c "import sys,json; print(json.load(sys.stdin).get('source','NO_SOURCE'))")"
echo "type:   $(echo $QUIZ | python -c "import sys,json; print(json.load(sys.stdin).get('type','NO_TYPE'))")"

# Glosario
curl -s http://127.0.0.1:8765/api/v1/glossary/1 | \
  python -c "import sys,json; d=json.load(sys.stdin); print(f'glossary: {len(d)} terms')"

# Curriculum gated (debe ser 401 sin token)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8765/api/v1/progress/curriculum?track_id=1)
echo "curriculum sin token: $STATUS (esperado 401)"

pkill -f "uvicorn app.main" 2>/dev/null
```

**Criterio A+K:** tsc 0 errores, content_loader 1246/0 skipped, source presente en respuesta, glosario 10 términos, curriculum 401 sin token.

**Si algo falla:** diagnostica y corrige antes de avanzar. No declares "auditado" sin haber visto la salida.

---

## PASO 2 — Ítem pendiente confirmado: Tutor memory

STATUS.md sesión (l) implementó RAG pero **no la memoria del tutor**. MASTER_PROMPT §2 Fase 2 exige:

- **Memoria corto plazo:** historial de la conversación actual (últimas N interacciones).
- **Memoria largo plazo:** perfil del usuario — skills débiles, patrones de error persistentes.
- **Memoria episódica:** fallos previos — "la tercera vez que fallas esta pregunta, la explicación cambia".

Verifica si existe algo:
```bash
grep -rn "TutorMemory\|long_term\|episodic\|conversation_history\|times_missed" \
     backend/app/services/ai/ --include="*.py"
```

`_times_missed()` ya existe (tests en sesión l lo prueban). Eso es el núcleo de la memoria episódica.
Lo que falta: usar ese dato para **cambiar el estilo de explicación** (no solo el número de intentos).

### Implementar memoria completa del tutor

**Corto plazo (más simple):** el endpoint `/tutor/explain` ya recibe `question_id` y `user_id`.
Añade un campo opcional `conversation_history: list[dict] | None` al request schema.
Si viene historial, inyéctalo en el prompt como contexto de la conversación.

**Largo plazo:** ya tienes `UserSkillState` con `p_known` y `times_missed` (calculado vía query).
En `tutor.py`, antes de construir el prompt:
```python
weak_skills = await get_weak_skills(user_id, threshold=0.4, limit=3)
# inyectar en prompt: "Este usuario tiene dificultades con: X, Y, Z"
```

**Episódica (ya parcialmente implementada):** `times_missed` controla el tono (directo→simple→analogía).
Extiende la lógica: si `times_missed >= 3`, añade un ejemplo de código ejecutable en la explicación.

**Criterio de aceptación (del MASTER_PROMPT):**
> "Fallar 3× la misma pregunta produce explicaciones distintas y progresivamente más simples,
> cada una con cita verificable al material."

Implementa este criterio de forma verificable. Escribe un test que lo demuestre:
```python
# tests/integration/test_tutor_memory.py
async def test_explanation_changes_with_failures():
    # usuario falla 0, 1, 2, 3 veces → explicaciones distintas
    # la de times_missed=3 debe contener un ejemplo de código
```

---

## PASO 3 — Pyodide (si el Paso 0 confirmó que NO existe)

Solo ejecutar si el grep del Paso 0 no encontró `pyodide-worker.js` ni `usePyodide.ts`.

### 3.1 Backend — selección y calificación

En `backend/app/services/quiz.py`, `_select_question`:
```python
EXEC_TYPES = {"fill_blank_exec", "fix_bug", "code_output"}
# incluir exec types en la selección (tienen correct_index null pero se califican por output)
# añadir campo exec_type al filtro
```

En `AnswerRequest`:
```python
class AnswerRequest(BaseModel):
    question_id: str
    selected_index: int | None = None   # MCQ/true_false
    exec_correct: bool | None = None    # Pyodide: cliente verifica, backend confía
    time_taken_ms: int
```

⚠️ **Bandera de seguridad documentada:** `exec_correct` viene del cliente — es explotable.
Documentar en el código con un comentario explícito. La arquitectura Pyodide lo acepta por diseño
(ejecución 100% cliente), pero debe ser explícito, no silencioso. En el futuro: rate-limit por
usuario en respuestas exec + anomaly detection en tasa de acierto.

### 3.2 Frontend — WebWorker

`frontend/public/pyodide-worker.js`:
```javascript
// Carga Pyodide 0.26.2 desde CDN oficial
// Captura stdout en buffer (sys.stdout = io.StringIO())
// Responde {output, error, executionTimeMs}
// Sin acceso a fetch/DOM desde el worker
importScripts("https://cdn.jsdelivr.net/pyodide/v0.26.2/full/pyodide.js");

let pyodide = null;
async function init() {
  pyodide = await loadPyodide();
  await pyodide.runPythonAsync(`
import sys, io
class CaptureOut:
    def __init__(self): self.buf = io.StringIO()
    def write(self, s): self.buf.write(s)
    def flush(self): pass
sys.stdout = CaptureOut()
sys.stderr = CaptureOut()
  `);
}
init();

self.onmessage = async ({ data: { code, id } }) => {
  try {
    await pyodide.runPythonAsync(code);
    const output = pyodide.runPython("sys.stdout.buf.getvalue()");
    pyodide.runPython("sys.stdout.buf.truncate(0); sys.stdout.buf.seek(0)");
    self.postMessage({ id, output, error: null });
  } catch (e) {
    self.postMessage({ id, output: "", error: e.message });
  }
};
```

`frontend/src/hooks/usePyodide.ts`:
```typescript
// Crea Worker una sola vez, timeout 5000ms via AbortController pattern
// Si timeout: worker.terminate(), crea worker fresco en background
// Expone: runCode(code: string): Promise<{output: string, error: string | null}>
```

### 3.3 QuizScreen — rama exec

Añadir al render de QuizScreen, después del bloque MCQ existente:
- `fill_blank_exec`: textarea con código que tiene `___`, botón ▶, output box, 3 intentos
- `fix_bug`: textarea editable con código buggy, mismo flujo
- `code_output`: MCQ existente + botón "▶ Ejecutar para verificar" post-respuesta (no bloquea el submit)

Mantener el flujo MCQ intacto — la rama exec es aditiva, no modifica el código existente.

---

## PASO 4 — Rebrand Neurium → Whetzy

Dominio comprado: `whetzy.com`. El rebrand debe ocurrir ANTES del deploy.

```bash
# Busca todas las ocurrencias de "Neurium" y "neurium" en código fuente
grep -rn "Neurium\|neurium" frontend/src/ backend/app/ \
     --include="*.tsx" --include="*.ts" --include="*.py" --include="*.css" \
     --include="*.json" | grep -v node_modules | grep -v __pycache__
```

Reemplaza en archivos de código (NO en docs/ ni en content/ — el contenido de las preguntas no menciona el nombre de la app):
- `Neurium` → `Whetzy`
- `neurium` → `whetzy`
- `--le-brand: #1CB0F6` → mantener (azul cielo es correcto para Whetzy también)
- Logo: mantener el triángulo neural — es agnóstico al nombre

Actualiza también:
- `README.md` — nombre del proyecto
- `docker-compose.yml` — nombre del servicio si aparece
- `package.json` — campo `name`
- `backend/app/core/config.py` — si hay `APP_NAME` o similar

---

## PASO 5 — Actualizar STATUS.md

Al terminar cada paso, actualiza STATUS.md con los números reales medidos, no los declarados.
Plantilla para la sesión nueva:

```markdown
## Sesión 2026-09-07 (m): Auditoría + Cierre Fase 2 + Rebrand Whetzy

### Auditoría (Bloques A+K)
- tsc: [0 errores / N errores — detalle]
- content_loader: [N ingestadas, N skipped]
- source en respuesta HTTP: [✅ / ❌]
- glosario: [N términos]
- curriculum sin token: [401 / otro]

### Pyodide
- Estado pre-auditoría: [existía / no existía]
- [Si implementado]: archivos nuevos, tsc OK, smoke test navegador
- Bandera de seguridad (exec_correct cliente): [documentada en código sí/no]

### Tutor memory
- Memoria episódica extendida (explicación cambia en fallo 3): [✅ / ❌]
- Test de regresión: [N/N verdes]

### Rebrand
- Whetzy en: [N archivos modificados, lista]
- Logo: [mantenido / actualizado]

### Fase 2 estado real
[Lista ítems con ✅/❌ y evidencia]
```

---

## ENTREGABLE FINAL

1. **Veredicto por paso** (P0–P4): PASA / FALLA con evidencia numérica.
2. **Fase 2 % real** con justificación ítem por ítem.
3. **STATUS.md actualizado** con sesión (m).
4. **Limpieza confirmada:** `backend/.env`, DB temporal, scripts borrados.

---

## REGLAS

- Verifica más barato primero: grep → tsc → pytest → curl → navegador.
- Nunca declares "implementado" sin haber ejecutado el comando.
- Si algo no lo verificaste: escribe "no verificado — [razón]".
- Model routing: Haiku para JSON/boilerplate, Sonnet para implementación y lógica.
- No uses Opus — límite de tokens semanal al 70%.
