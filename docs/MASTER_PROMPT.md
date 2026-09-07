# Prompt: Fase 3 — Gamificación extendida + PWA offline

> Sesión nueva. Lee este prompt completo antes de ejecutar cualquier comando.
> Postura: escéptica. STATUS.md puede estar desactualizado — la fuente de verdad
> es lo que responde la URL pública, no lo que dice el documento.
> Model routing: Sonnet para todo. No uses Opus en esta sesión.

---

## CONTEXTO — estado verificado al cierre de sesión (q)

URLs en producción (todas verificadas con HTTP real el 2026-09-08):
- **Backend Railway**: `https://api-production-9751.up.railway.app`
- **Frontend CF Pages**: `https://whetzy.pages.dev`
- **Dominio**: `whetzy.com` — LIVE ✅ (IPs 104.21.84.249 / 172.67.199.229, title "Whetzy")

### Estado de fases verificado (HTTP real, no STATUS.md)

| Fase | % | Estado |
|------|---|--------|
| 0 | **100%** | ✅ CERRADA — backend + Pages + whetzy.com live |
| 1 | **100%** | ✅ CERRADA — 1253 Q, 70 glosario, currículo gated BKT |
| 2 | **98%** | Groq E2E `provider=groq` ✅; Pyodide no browser-tested (7/1253 exec Q, motor no las seleccionó) |
| 3 | **45%** | Gamificación real (ligas/badges/misiones/XP); falta multiplayer, offline, Lottie |

### Notas de gotcha (no las redescubras)

| Gotcha | Detalle |
|---|---|
| Backend prod | `https://api-production-9751.up.railway.app` — PostgreSQL real |
| GROQ_MODEL | `qwen/qwen3.8-27b` — `llama-3.3-70b-versatile` NO disponible |
| Quiz start response | `{session_id, mode, question: {id, ...}, reviews_due}` — el question_id está en `.question.id`, no en `.id` top-level |
| Quiz answer | Requiere `question_id`, `session_id`, `selected_index`, `response_time_ms` |
| Glosario | `GET /glossary/track01` — track_id = string `"track01"` |
| ChromaDB / sentence-transformers | Eliminados (OOM Railway free tier). RAG retorna `[]`. Groq llama igual, sin contexto RAG. |
| Alembic | **BLOQUEANTE CRÍTICO**: prod usa `create_all`. Antes de cualquier cambio de schema, inicializar Alembic. |
| Pyodide | 7 preguntas exec en banco (exec_examples.json, track01). Motor BKT/Elo las selecciona raramente. |

---

## BLOQUEANTE TÉCNICO ANTES DE EMPEZAR: Alembic

El backend usa `create_all` para inicializar schema en producción. Esto es bloqueante para Fase 3 porque añadirás columnas nuevas (duelos, sync offline).

### PASO 0 — Alembic init + primera migration

```bash
cd python/learning-engine/backend
pip install alembic  # probablemente ya instalado en requirements.txt
```

Verifica que `alembic` está en `requirements.txt`. Si no:
```bash
echo "alembic" >> requirements.txt
```

Inicializa Alembic:
```bash
alembic init alembic
```

Edita `alembic/env.py`:
- Importa los modelos: `from app.models import user, gamification, session, content`
- Set `target_metadata = Base.metadata` (Base de `app.core.database`)
- Set `sqlalchemy.url` desde `config.DATABASE_URL` (o usa la variable de entorno)

Genera la primera migration desde el schema actual:
```bash
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head  # en local con SQLite primero
```

Prueba en Postgres local:
```bash
# En docker-compose: postgres en puerto 5433
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5433/whetzy" alembic upgrade head
```

**Criterio**: `alembic upgrade head` sin errores en Postgres local. Sube el cambio a GitHub. Railway se redeploya — verifica `/health` 200 tras redeploy.

---

## FASE 3 — Gamificación extendida + PWA offline

### PASO 1 — Duelos (multiplayer 1v1 asíncrono)

**Spec mínimo shippable:**
- Un usuario reta a otro por username.
- Ambos responden el mismo quiz de 5 preguntas (mismas Q, orden aleatorio por sesión).
- Cuando ambos terminen: ganador = más respuestas correctas (desempate: tiempo total).
- Notificación en home: "¡Tienes un duelo pendiente!" / "¡Ganaste el duelo contra X!"

**Backend** (nuevo endpoint batch en `backend/app/api/v1/endpoints/`):
```
POST /api/v1/duels/challenge   {opponent_username: str} → duel_id
GET  /api/v1/duels/my          → lista de duelos activos/finalizados
POST /api/v1/duels/{id}/answer {question_id, selected_index, response_time_ms} → feedback parcial
GET  /api/v1/duels/{id}/result → resultado final (solo disponible si ambos completaron)
```

**Schema** (nueva tabla, Alembic migration requerida):
```python
class Duel(Base):
    id: UUID (PK)
    challenger_id: FK User
    opponent_id: FK User
    skill_id: str
    question_ids: JSON (lista de 5 Q IDs)
    challenger_answers: JSON | None
    opponent_answers: JSON | None
    challenger_completed_at: datetime | None
    opponent_completed_at: datetime | None
    winner_id: FK User | None
    status: enum("pending", "in_progress", "completed")
    created_at: datetime
```

**Frontend** (`DuelScreen.tsx`):
- Tab en bottom-nav (ícono ⚔️).
- Lista de duelos + botón "Retar a alguien".
- Quiz de duelo = QuizScreen adaptado (sin adaptación BKT, mismas Q fijas).
- Pantalla de resultado: avatar ganador, XP ganado (+50 si ganas, +10 si pierdes).

**Criterio P1**: `POST /duel/challenge` → 201, `GET /duel/{id}/result` → ganador correcto tras simular dos respuestas distintas.

---

### PASO 2 — PWA offline (Service Worker + IndexedDB sync)

**Spec mínimo shippable:**
- El usuario puede hacer quiz sin conexión.
- Las respuestas se guardan en IndexedDB local.
- Al reconectar, se envían al backend (sync background).
- Indicador visual en TopBar: "Sin conexión — sincronizando..." / "Sincronizado ✅".

**Service Worker** (`frontend/public/sw.js` — ya existe, ampliar):
- Cache-first para assets estáticos (JS, CSS, fonts).
- Network-first con fallback cache para `/api/v1/quiz/start` y `/api/v1/quiz/answer`.
- Background sync API (`SyncManager`) para respuestas offline.

**IndexedDB** (`frontend/src/services/offlineQueue.ts`):
```typescript
interface PendingAnswer {
  id: string;            // UUID local
  questionId: string;
  sessionId: string;
  selectedIndex: number;
  responseTimeMs: number;
  timestamp: number;
}
```

**Sync logic** (`frontend/src/hooks/useOfflineSync.ts`):
- `navigator.onLine` listener → al reconectar, `POST /quiz/answer` batch.
- `BackgroundSync` API si disponible (Chrome).

**Criterio P2**: desconectar red (DevTools → offline) → responder una pregunta → reconectar → verificar en backend que la respuesta llegó.

---

### PASO 3 — Animaciones Lottie

**Spec mínimo**: feedback inmediato en QuizScreen con Lottie.

Instalar en frontend:
```bash
cd frontend && npm install @lottiefiles/react-lottie-player
```

Animaciones a añadir:
- Respuesta correcta: checkmark verde (✅) — `public/lottie/correct.json`
- Respuesta incorrecta: X roja (❌) — `public/lottie/incorrect.json`
- Racha ×3: fuego (🔥) — `public/lottie/streak.json`
- Subida de liga: confetti — `public/lottie/league-up.json`

Usar animaciones de Lottie Files (licencia libre, por ejemplo de `lottiefiles.com/featured`).

Integrar en `QuizScreen.tsx`:
```tsx
import { Player } from '@lottiefiles/react-lottie-player';

// Tras recibir feedback:
{feedback.is_correct && <Player src="/lottie/correct.json" autoplay loop={false} style={{width: 120}} />}
```

**Criterio P3**: animación visible en browser al responder correcto/incorrecto.

---

### PASO 4 — Pyodide smoke test (pendiente desde Fase 2)

Para forzar una pregunta exec sin esperar al motor aleatorio:

**Backend** — endpoint temporal de debug (solo en ENVIRONMENT=development):
```python
# quiz.py: añadir opción de forzar tipo
POST /api/v1/quiz/start {"skill_id": "sk010101", "force_type": "fill_blank_exec"}
```

O alternativamente: abre `whetzy.pages.dev` en browser real, regístrate, responde 20-30 preguntas en track01 skills básicas hasta que el motor presente una exec.

**Criterio P4**: una pregunta `fill_blank_exec` ejecutada en browser real sin error de consola (F12 → Console limpia).

---

## PASO 5 — Actualiza STATUS.md

Formato para sesión (r):
```markdown
## Sesión 2026-09-08 (r): Fase 3 — [lo que se haya completado]

### Alembic
- Init + primera migration: [OK / pendiente]
- Upgrade head en Postgres local: [OK / error]
- Railway redeploy: [OK / pendiente]

### Duelos
- Backend endpoints: [OK / parcial / no]
- Schema migration: [OK / pendiente]
- Frontend DuelScreen: [OK / parcial / no]
- E2E: [OK / no]

### PWA Offline
- Service Worker ampliado: [OK / no]
- IndexedDB queue: [OK / no]
- Sync al reconectar: [OK / no]

### Lottie
- Animaciones integradas: [OK / no]

### Pyodide
- Smoke test browser: [verificado / no — razón]

### Fase 3 % real: [%]
```

---

## ENTREGABLE FINAL DE ESTA SESIÓN

1. **Alembic funcional**: `alembic upgrade head` en Postgres sin errores ✅ / pendiente
2. **Duelos MVP**: challenge + answer + result E2E ✅ / parcial
3. **PWA offline**: quiz offline → sync al reconectar ✅ / parcial
4. **Lottie**: animación en QuizScreen ✅ / no
5. **Pyodide**: smoke test en browser ✅ / no verificado
6. **STATUS.md actualizado** con sesión (r) y % real de Fase 3
7. **Prompt para Fase 4** al cierre

---

## REGLAS

- Verifica en el orden más barato: curl → browser → logs
- Nunca declares "verificado" sin haber visto la salida del comando
- Si algo no lo comprobaste: escribe "no verificado — [razón]"
- Alembic PRIMERO — ningún cambio de schema sin migration
- Model routing: Sonnet para todo. No Opus.
