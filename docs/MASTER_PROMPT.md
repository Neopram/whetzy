# Prompt: Fase 4 — DKT + Churn + Pyodide E2E + Duel E2E

> Sesión nueva. Lee este prompt completo antes de ejecutar cualquier comando.
> Postura: escéptica. STATUS.md puede estar desactualizado — la fuente de verdad
> es lo que responde la URL pública, no lo que dice el documento.
> Model routing: Sonnet para todo. No uses Opus en esta sesión.

---

## CONTEXTO — estado verificado al cierre de sesión (r)

URLs en producción (todas verificadas con HTTP real el 2026-09-08):
- **Backend Railway**: `https://api-production-9751.up.railway.app`
- **Frontend CF Pages**: `https://whetzy.pages.dev`
- **Dominio**: `whetzy.com` — LIVE ✅ (IPs 104.21.84.249 / 172.67.199.229, title "Whetzy")

### Estado de fases verificado al cierre de sesión (r)

| Fase | % | Estado |
|------|---|--------|
| 0 | **100%** | ✅ CERRADA |
| 1 | **100%** | ✅ CERRADA — 1253 Q, 70 glosario, currículo gated BKT |
| 2 | **98%** | Groq E2E `provider=groq` ✅; Pyodide no browser-tested |
| 3 | **85%** | Duelos backend ✅ + DuelScreen ✅ + Lottie ✅ + offline badge ✅; Duel E2E browser + Pyodide smoke test pendientes |
| 4 | **8%** | Solo motor base (FSRS/Elo/BKT/bandit) |

### Notas de gotcha (no las redescubras)

| Gotcha | Detalle |
|---|---|
| Backend prod | `https://api-production-9751.up.railway.app` — PostgreSQL real |
| GROQ_MODEL | `qwen/qwen3.8-27b` — `llama-3.3-70b-versatile` NO disponible |
| Quiz start response | `.question.id` — no `.id` top-level |
| Quiz answer | `{session_id, question_id, selected_index, response_time_ms}` |
| DB local | `postgresql+asyncpg://neurium:neurium_dev@localhost:5433/neurium` (Docker via WSL) |
| Alembic | ✅ INICIALIZADO: `backend/alembic/` con 2 revisions (a1b2c3d4e5f6 → b2c3d4e5f6a7). `start.sh` auto-stamp seguro en prod. |
| Duelos schema | Tabla `duels` creada por migration `b2c3d4e5f6a7`. start.sh → alembic upgrade head en cada deploy. |
| ChromaDB/sentence-transformers | Eliminados (OOM Railway free tier). RAG retorna `[]`. |
| Pyodide | 7 preguntas exec en banco (`exec_examples.json`, track01). Motor BKT/Elo rara vez las selecciona (0.6%). |
| Lottie | `@lottiefiles/react-lottie-player` instalado. correct/incorrect/streak.json en `frontend/public/lottie/`. |

---

## PASO 0 — Verificación de estado antes de empezar (OBLIGATORIO)

```bash
# 1. Health check backend prod
curl -s https://api-production-9751.up.railway.app/health

# 2. Railway ha redesplegado con el nuevo start.sh (Alembic)
# El log debe mostrar: "[start] alembic upgrade head..." sin errores
# Verifica en Railway dashboard → Deployments → logs del último deploy

# 3. tsc sin errores locales
cd python/learning-engine/frontend && npx tsc --noEmit

# 4. backend AST OK
cd python/learning-engine/backend && python -c "import app.main"
```

Criterio de continuación: health 200 + tsc 0 errores + AST OK. Si hay errores, arrégralos antes de continuar.

---

## PASO 1 — Pyodide smoke test (pendiente desde Fase 2)

La forma más barata de verificarlo es forzar una pregunta exec via API directamente:

```bash
# Registra un usuario de test
TOKEN=$(curl -s -X POST https://api-production-9751.up.railway.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"pyodide_test@whetzy.dev","username":"pyodide_test","display_name":"Pyodide Test","password":"Test1234!","language":"es"}' \
  | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token','ERR'))")

# Inicia quiz forzando skill con exec questions
curl -s -X POST https://api-production-9751.up.railway.app/api/v1/quiz/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mode":"study","skill_id":"sk010101_exec"}'
```

Si el motor no sirve exec Qs via API, verifica en browser local (localhost:5199):
1. Registra usuario → ESTUDIAR AHORA → responde 10+ preguntas de track01
2. Monitorea F12 → Network → busca `quiz/start` con `type: "fill_blank_exec"`
3. Si aparece: verifica que el input de código se renderiza sin error de consola

**Criterio P-pyodide**: pregunta `fill_blank_exec` aparece en browser + F12 Console limpia.

---

## PASO 2 — Duel E2E en browser (pendiente de sesión r)

El backend de duelos está completo. Falta verificar el flujo completo con 2 usuarios:

1. En localhost:5199, regístrate como `user_a` (ya lo tienes de sesión r: `testuser01`)
2. Registra `user_b` (segundo browser/incógnito)
3. Desde `user_a`: tab ⚔️ → "Retar" → username `user_b` → confirmar
4. Verifica: `POST /duels/challenge` → 201, `duel_id` en respuesta
5. En `user_b`: tab ⚔️ → aparece el duelo → responde las 5 preguntas
6. En `user_a`: responde las 5 preguntas
7. `GET /duels/{duel_id}/result` → `status: "completed"`, `winner_id` correcto

**Criterio P-duel**: flujo completo challenge→answer→result verificado en browser.

---

## PASO 3 — DKT (Deep Knowledge Tracing) — núcleo de Fase 4

El motor actual usa BKT (Hidden Markov). DKT reemplaza/complementa con una LSTM que aprende
secuencias de interacciones.

### Spec mínimo (Python puro, sin entrenamiento en tiempo real)

**Modelo preentrenado** (`backend/app/services/engine/dkt.py`):
- LSTM simple (PyTorch/sklearn) preentrenada offline sobre datos sintéticos.
- Input: secuencia `[(skill_id, correct)]` por usuario.
- Output: `p_correct[skill_id]` para el siguiente ítem.
- Fallback limpio a BKT si PyTorch no disponible.

**Integración**:
- `UserSkillState` mantiene un campo JSON `dkt_hidden_state` (estado oculto serializado).
- En `quiz.py` → `submit_answer`: actualizar DKT state + BKT (híbrido).
- Usar `p_correct` de DKT como señal adicional en selección de skill (promedio con BKT `p_known`).

**Sin entrenamiento real** (fuera de scope ahora):
- Usa pesos iniciales (Xavier uniform) o pesos aleatorios fijos.
- El objetivo es tener la arquitectura lista para reemplazar pesos cuando haya datos reales.
- Criterio: no crash, `p_correct` en [0, 1], fallback a BKT si falla.

**Criterio P-dkt**: `POST /quiz/answer` devuelve campo `dkt_p_correct: float | null` en la respuesta. Valor en [0, 1].

---

## PASO 4 — Churn predictor

### Spec mínimo (regresión logística sin ML externo)

**Features** (calculables desde la DB sin joins complejos):
- `days_since_last_active`: días desde `user.last_active`.
- `sessions_last_7d`: conteo de `StudySession` en los últimos 7 días.
- `avg_accuracy_last_10`: accuracy promedio de las últimas 10 respuestas.
- `streak_current`: racha actual.

**Modelo** (`backend/app/services/ml/churn.py`):
- Regresión logística con coeficientes fijos (heurística validada, no entrenada).
- `churn_risk: float` (0 = safe, 1 = at risk).
- Si `churn_risk > 0.7`: flag al dashboard.

**Dashboard** (`GET /api/v1/progress/dashboard`):
- Añadir campo `churn_risk: float | null` (null si no hay suficientes datos).
- **Schema change → Alembic migration requerida** si añades columna a `users`.
  Alternativa: calcular en runtime sin columna nueva.

**Criterio P-churn**: `GET /progress/dashboard` devuelve `churn_risk` en [0, 1].

---

## PASO 5 — Actualiza STATUS.md

Formato para sesión (s):
```markdown
## Sesión 2026-09-08 (s): Fase 4 — DKT + Churn + Pyodide E2E + Duel E2E

### PASO 0 — Verificación estado
...

### Pyodide smoke test
...

### Duel E2E
...

### DKT
...

### Churn
...

### Fase 4 % real: [%]
```

---

## ENTREGABLE FINAL DE ESTA SESIÓN

1. **Pyodide**: pregunta `fill_blank_exec` en browser sin error de consola ✅ / no verificado
2. **Duel E2E**: challenge → answer × 2 usuarios → result correcto ✅ / parcial
3. **DKT arquitectura**: `dkt_p_correct` en `/quiz/answer` response ✅ / no
4. **Churn predictor**: `churn_risk` en `/progress/dashboard` ✅ / no
5. **STATUS.md actualizado** con sesión (s) y % real
6. **Prompt para Fase 5** al cierre

---

## REGLAS

- Verifica en el orden más barato: curl → browser → logs
- Nunca declares "verificado" sin haber visto la salida del comando
- Si algo no lo comprobaste: escribe "no verificado — [razón]"
- Alembic PRIMERO para cualquier cambio de schema
- Model routing: Sonnet para todo. No Opus.
- `start.sh` ya tiene auto-stamp + alembic upgrade head — no romperlo
