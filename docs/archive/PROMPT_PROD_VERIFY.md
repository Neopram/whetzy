# Prompt: Verificación en Producción + Cierre Fase 0 y Fase 2

> Sesión nueva. Lee este prompt completo antes de ejecutar cualquier comando.
> Postura: escéptica. STATUS.md puede estar desactualizado — la fuente de verdad
> es lo que responde la URL pública, no lo que dice el documento.
> Model routing: Sonnet para todo. No uses Opus en esta sesión.

---

## CONTEXTO — estado tras sesión (o): deploy completado

URLs en producción:
- **Backend Railway**: `https://api-production-9751.up.railway.app`
- **Frontend CF Pages**: `https://whetzy.pages.dev`
- **Dominio**: `whetzy.com` — registrado en Cloudflare, DNS propagando al cierre de sesión

Lo que sesión (o) declaró haber hecho:
- PostgreSQL crash-loop resuelto (volumen Railway en `/var/lib/postgresql/data`)
- `content_loader`: 1253 Q + 70 glosario cargados en Postgres prod
- Railway deploy activo, `/health` 200
- CF Pages activo, título "Whetzy" correcto
- Quiz verificado en browser (pregunta real, feedback, XP)
- Groq model: `qwen/qwen3.8-27b` (llama-3.3-70b no disponible en esta cuenta)

Lo que **no se verificó** en sesión (o):
- Groq E2E en prod: ¿el tutor llama a Groq real o sigue usando fallback?
- Pyodide en browser de producción: smoke test pendiente
- `whetzy.com` live: solo "DNS propagando"
- STATUS.md sesión (o) no está escrito

**Objetivo de esta sesión:** cerrar Fase 0 al 100% y Fase 2 al 100% con evidencia HTTP real.

---

## GOTCHAS DEL ENTORNO (no los redescubras)

| Gotcha | Detalle |
|---|---|
| Backend prod | `https://api-production-9751.up.railway.app` — PostgreSQL real, Groq wired |
| GROQ_MODEL | `qwen/qwen3.8-27b` — `llama-3.3-70b-versatile` NO disponible en esta cuenta |
| `whetzy.com` | Cloudflare registrar + DNS + Pages unified. Pages lo configura automáticamente al añadir custom domain. |
| SQLite local | Solo para tests locales. Prod usa Postgres. |
| `validate_content.py` | No existe en el repo. No afirmes haberlo corrido. |
| Pyodide exec Q | Solo 7 preguntas (`fill_blank_exec` en `exec_examples.json`, track01). |
| Alembic | Prod usa `create_all` — riesgo en futuros cambios de schema. Ítem técnico honesto. |
| Registro | `POST /auth/register` acepta **JSON** con `email`, `username`, `password`, `display_name` — no form-encoded. |
| Glosario | `GET /glossary/track01` — el track_id es string `"track01"`, no entero `1`. |
| Quiz answer | Requiere `question_id`, `session_id` (del response de quiz/start), `selected_index`, `response_time_ms`. |
| Quiz start response | Estructura anidada: `{session_id, question: {id, type, ...}}` — el question_id está en `.question.id`, NO en `.id` top-level. |

---

## PASO 0 — Verifica whetzy.com (2 min)

```bash
# DNS lookup — debe resolver a Cloudflare (IPs 104.x.x.x)
Resolve-DnsName whetzy.com -Type A | Select-Object Name, IPAddress

# HTTP check
curl -s -o /dev/null -w "%{http_code}" https://whetzy.com
```

- **Si 200**: whetzy.com está live. Continúa.
- **Si NXDOMAIN / connection refused**: DNS aún propagando. Trabaja con `whetzy.pages.dev` 
  para el resto de los pasos — los criterios son los mismos, solo cambia la URL.

---

## PASO 1 — Verificación de producción: health + contenido (5 min)

```bash
BACKEND="https://api-production-9751.up.railway.app"

# Health check
curl -s $BACKEND/health | python -c "import sys,json; d=json.load(sys.stdin); print(d)"

# Glosario — track_id es string "track01", no número 1
curl -s "$BACKEND/api/v1/glossary/track01" | \
  python -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d)} términos en glosario track01')"

# Registro real en producción
# ⚠️ El endpoint requiere email, username Y display_name — no solo username
TOKEN=$(curl -s -X POST "$BACKEND/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"verify@whetzy.com","username":"verify_prod","password":"Verify_2026!","display_name":"Verify"}' \
  | python -c "import sys,json; print(json.load(sys.stdin).get('access_token','FAIL'))")
echo "token prefix: ${TOKEN:0:20}..."

# Quiz start con skill real — response: {session_id, question: {id, type, ...}}
QUIZ=$(curl -s -X POST "$BACKEND/api/v1/quiz/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"skill_id":"sk010401"}')
QID=$(echo $QUIZ | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('question',{}).get('id','FAIL'))")
SID=$(echo $QUIZ | python -c "import sys,json; print(json.load(sys.stdin).get('session_id','FAIL'))")
echo "question_id=$QID  session_id=$SID"
```

**Criterio P1:** `/health` OK, glosario 10 términos, token recibido, question_id no FAIL.

---

## PASO 2 — Groq E2E en producción (el que nunca se verificó)

Este es el ítem crítico. El tutor usa fallback o Groq real — hay que saberlo.

```bash
BACKEND="https://api-production-9751.up.railway.app"

# quiz/start devuelve id (question_id) y session_id — ambos necesarios para quiz/answer
QUIZ=$(curl -s -X POST "$BACKEND/api/v1/quiz/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"skill_id":"sk010401"}')
QID=$(echo $QUIZ | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('question',{}).get('id','FAIL'))")
SID=$(echo $QUIZ | python -c "import sys,json; print(json.load(sys.stdin).get('session_id','FAIL'))")
echo "question_id=$QID  session_id=$SID"

# Respuesta incorrecta — requiere question_id, session_id y response_time_ms
# ⚠️ El campo es response_time_ms (no time_taken_ms) y selected_index debe estar en rango válido
curl -s -X POST "$BACKEND/api/v1/quiz/answer" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"question_id\":\"$QID\",\"session_id\":\"$SID\",\"selected_index\":0,\"response_time_ms\":3000}" \
  | python -c "import sys,json; d=json.load(sys.stdin); print('correct:', d.get('is_correct'), '| XP:', d.get('xp_earned'))"

# Llamada al tutor — ¿qué provider devuelve?
TUTOR=$(curl -s -X POST "$BACKEND/api/v1/tutor/explain" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"question_id\":\"$QID\"}")

echo "provider: $(echo $TUTOR | python -c "import sys,json; print(json.load(sys.stdin).get('provider','?'))")"
echo "explanation: $(echo $TUTOR | python -c "import sys,json; print(json.load(sys.stdin).get('explanation','')[:150])")"
```

**Criterio P2:** `provider: groq`, explanation con contenido real (≥50 chars, no el texto genérico de fallback).

### Si provider = "fallback":

La GROQ_API_KEY o el GROQ_MODEL están mal configurados en Railway. Diagnóstico:

1. Entra a Railway dashboard → tu servicio → Variables
2. Verifica que `GROQ_API_KEY` y `GROQ_MODEL=qwen/qwen3.8-27b` están presentes
3. Si falta alguna: añádela y Railway redeploya automáticamente
4. Repite el curl del tutor tras el redeploy

**No avances al Paso 3 sin confirmar provider=groq.** Ese es el cierre de Fase 2.

---

## PASO 3 — Pyodide smoke test en navegador real

Pyodide necesita browser. No se puede verificar con curl.

```bash
# Primero: ¿hay preguntas exec en el banco prod?
BACKEND="https://api-production-9751.up.railway.app"
# Pregunta directa al backend sobre tipos disponibles
curl -s "$BACKEND/api/v1/quiz/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"skill_id":"sk010101"}' \
  | python -c "import sys,json; d=json.load(sys.stdin); print('type:', d.get('type'), '| id:', d.get('id','?')[:15])"
```

Las 7 preguntas exec (`fill_blank_exec`) están en track01. Si la skill asignada al quiz las sirve:

1. Abre `https://whetzy.com` (o `https://whetzy.pages.dev`) en el browser
2. Regístrate → quiz → si aparece una pregunta de tipo `fill_blank_exec`:
   - Verifica que aparece el editor de código con `___`
   - Completa el blank y pulsa ▶
   - El output debe mostrarse sin error de carga de Pyodide

**Si no aparece ninguna exec (el motor de selección puede no seleccionarlas):**
Documenta como "no verificado en browser — exec questions en banco, pero el motor
de selección no las presentó en esta sesión". No es un fallo de Pyodide.

**Criterio P3:** una pregunta exec ejecutada sin error de consola (F12 → Console limpia).
Si 0 exec presentadas: "Pyodide no verificado — lógicamente implementado, sin exercice en sesión".

---

## PASO 4 — Verificar whetzy.com como URL principal

Si whetzy.com ya resuelve (Paso 0 = 200):

```bash
# PWA carga desde whetzy.com
curl -s -o /dev/null -w "%{http_code}" https://whetzy.com
curl -s -o /dev/null -w "%{http_code}" https://whetzy.com/api/v1/health 2>/dev/null || echo "proxy no config"

# El <title> debe ser Whetzy (no Neurium, no Vite App)
curl -s https://whetzy.com | python -c "
import sys, re
html = sys.stdin.read()
title = re.search(r'<title>(.*?)</title>', html)
print('title:', title.group(1) if title else 'NO TITLE')
"
```

**Criterio P4:** HTTP 200, title = "Whetzy" (o similar — no "Neurium", no "Vite App").

---

## PASO 5 — Nota técnica honesta: Alembic en producción

El backend usa `create_all` para inicializar el schema en producción.
Esto es seguro para el primer deploy (sin datos de usuarios reales).
Se vuelve problemático cuando añadas columnas en Fase 3+.

Escribe en STATUS.md: **"Alembic migrations pendientes — bloqueante técnico antes de Fase 3"**.
No lo implementes ahora — agota el objetivo de esta sesión primero.

---

## PASO 6 — Actualiza STATUS.md

Sesión (o) — con números reales medidos:

```markdown
## Sesión 2026-09-08 (o): Deploy en vivo + Verificación de producción

### URLs en producción
- Backend: https://api-production-9751.up.railway.app
- Frontend: https://whetzy.pages.dev
- Dominio: https://whetzy.com — [live ✅ / DNS pendiente aún]

### Verificación en producción
- /health: [respuesta real]
- Glosario: [N términos]
- Registro: [OK / FAIL]
- Quiz: [skill_id, type, source presente]
- Tutor provider: [groq / fallback — CRÍTICO]
- Pyodide en browser: [verificado / no verificado — razón]

### PostgreSQL en prod
- content_loader: [1253 Q / otro]
- Seed: [OK]

### Fase 0 estado real: [%]
### Fase 2 estado real: [%]

### Deuda técnica pendiente
- Alembic migrations: BLOQUEANTE antes de Fase 3 (actualmente create_all)
- Pyodide smoke test: [verificado / pendiente navegador]
```

---

## ENTREGABLE FINAL

1. **whetzy.com live**: URL que responde 200 ✅ / DNS pendiente (ETA estimado)
2. **Groq en prod**: `provider=groq` con explanation real ✅ / `provider=fallback` + diagnóstico
3. **Pyodide**: verificado en browser ✅ / no verificado (razón honesta)
4. **STATUS.md actualizado** con sesión (o) y números reales
5. **Fase 0 y Fase 2 % real** con justificación

---

## REGLAS

- Verifica en el orden más barato: curl → browser → logs de Railway
- Nunca declares "verificado" sin haber visto la salida del comando
- Si algo no lo comprobaste: escribe "no verificado — [razón]"
- No implementes features nuevas en esta sesión — solo cierra los abiertos
- Model routing: Sonnet para todo. No Opus.

---

## SIGUIENTE SESIÓN

Cuando esta sesión termine con Fase 0=100% y Fase 2=100%, el siguiente paso natural es:

**Fase 3 — Gamificación extendida + PWA offline**
- Gamificación: ya tiene 45% (ligas, badges, misiones — verificados)
- Falta: multiplayer (duelos), offline-sync (Service Worker + IndexedDB), animaciones Lottie
- Bloqueante técnico a resolver primero: Alembic migrations

El prompt para Fase 3 lo generas al final de esta sesión con los números reales.
