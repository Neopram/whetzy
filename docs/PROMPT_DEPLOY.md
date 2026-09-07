# Prompt: Groq real + Smoke Pyodide + Deploy whetzy.com

> Sesión nueva. Lee este prompt completo antes de ejecutar cualquier comando.
> Postura: escéptica. STATUS.md puede estar desactualizado — la sesión anterior
> afirma haberlo actualizado pero la sección "Deuda técnica" sigue mostrando datos viejos.
> Model routing: Sonnet para todo. No uses Opus ni Haiku en esta sesión.

---

## CONTEXTO — estado declarado tras sesión (m)

Repo: `C:\Users\feder\Desktop\Banco de preguntas\python\learning-engine\`
Dominio comprado: `whetzy.com` en Cloudflare.
Rebrand declarado como completo (Neurium → Whetzy).
Fase 1: 100% cerrada. Fase 2: ~92% (falta Groq real + Pyodide en navegador).
Objetivo de esta sesión: **cerrar Fase 2 al 100% y hacer el primer deploy real.**

---

## GOTCHAS DEL ENTORNO (no los redescubras)

| Gotcha | Detalle |
|---|---|
| Python | Sistema (3.12). No crees venv. |
| SQLite Desktop | Permission denied. Usa `%TEMP%` con ruta absoluta y barras normales. |
| .env | `config.py` lee del CWD. Crea `backend/.env` antes de correr el server. |
| Browser preview | No alcanza localhost. Usa curl o el proxy Vite `/api`. |
| `validate_content.py` | No existe en el repo. Escribe tu propio validador si lo necesitas. |
| ChromaDB | Persiste en `backend/chroma_db/`. Primera build descarga ~90MB. |
| Limpieza | Borra `backend/.env`, DB temp y scripts al terminar. |

---

## PASO 0 — Dos inconsistencias a resolver antes de todo (5 min)

### 0.A — Discrepancia de conteo: 1253 vs 1246

La sesión (m) reportó `content_loader → 1253 Q` pero STATUS.md dice 1246.
Diferencia: 7 preguntas. Origen desconocido. Cuéntalo ahora:

```bash
python -c "
import json, pathlib
total = sum(
    len(json.loads(f.read_text('utf-8')).get('questions', []))
    for f in pathlib.Path('content/questions').rglob('*.json')
)
print(f'Total en archivos: {total}')
"
```

Si el resultado es 1253: hay 7 preguntas nuevas no documentadas en STATUS.md → encuéntralas
(`for f in ... if len(qs) != expected`). Si es 1246: el content_loader de la sesión (m)
contó mal → registra la corrección.

### 0.B — Rebrand verificado

```bash
grep -rn "Neurium\|neurium" frontend/src/ backend/app/ \
     --include="*.tsx" --include="*.ts" --include="*.py" \
     --include="*.css" --include="*.json" 2>/dev/null | grep -v node_modules
```

Si aparecen ocurrencias: aplica los reemplazos ahora. Si es 0: continúa.

---

## PASO 1 — Groq real (≤10 min)

El usuario ya tiene `GROQ_API_KEY` en `backend/.env.example`. Crea el `.env` real:

```bash
# Copia .env.example a .env
cp backend/.env.example backend/.env
# Verifica que GROQ_API_KEY está presente y no es placeholder
grep "GROQ_API_KEY" backend/.env
```

### 1.A — Smoke test directo a la API de Groq

```bash
GROQ_KEY=$(grep GROQ_API_KEY backend/.env | cut -d= -f2)
curl -s https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":"ping"}],"max_tokens":5}' \
  | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('choices',[{}])[0].get('message',{}).get('content','FAIL'))"
```

Si devuelve texto: Groq funciona. Si devuelve FAIL o error 401: la key es inválida.

### 1.B — Tutor con LLM real (E2E)

Arranca el backend con la key real y prueba el tutor:

```bash
# .env ya tiene DATABASE_URL a SQLite en %TEMP% y GROQ_API_KEY real
cd backend
# agrega DATABASE_URL al .env si no está
echo "DATABASE_URL=sqlite+aiosqlite:///C:/Users/feder/AppData/Local/Temp/whetzy_test.db" >> .env
echo "ENVIRONMENT=development" >> .env
echo "SECRET_KEY=test-key-2026" >> .env

python -m app.services.content_loader 2>&1 | tail -3
python -m app.services.seed 2>&1 | tail -3

uvicorn app.main:app --host 127.0.0.1 --port 8770 &
sleep 5

TOKEN=$(curl -s -X POST http://127.0.0.1:8770/api/v1/auth/register \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=groqtest@whetzy.com&password=Groq_2026!" \
  | python -c "import sys,json; print(json.load(sys.stdin).get('access_token','FAIL'))")

# Responde una pregunta incorrecta para activar el tutor
QID=$(curl -s -X POST http://127.0.0.1:8770/api/v1/quiz/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"skill_id":"sk010401"}' \
  | python -c "import sys,json; print(json.load(sys.stdin).get('id','FAIL'))")

# Respuesta incorrecta (índice 99)
curl -s -X POST http://127.0.0.1:8770/api/v1/quiz/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"question_id\":\"$QID\",\"selected_index\":99,\"time_taken_ms\":3000}" > /dev/null

# Llama al tutor — debe usar Groq (provider != "fallback")
TUTOR=$(curl -s -X POST http://127.0.0.1:8770/api/v1/tutor/explain \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"question_id\":\"$QID\"}")

echo "provider: $(echo $TUTOR | python -c "import sys,json; print(json.load(sys.stdin).get('provider','?'))")"
echo "explanation snippet: $(echo $TUTOR | python -c "import sys,json; print(json.load(sys.stdin).get('explanation','')[:120])")"

pkill -f "uvicorn app.main" 2>/dev/null
```

**Criterio P1:** `provider: groq` (no `fallback`), explanation con contenido real (no el texto genérico de fallback).

---

## PASO 2 — Smoke test Pyodide en navegador (único paso que requiere browser)

Pyodide no se puede verificar con curl — necesita el navegador. Arranca el frontend:

```bash
cd frontend && npm run dev
```

Abre el browser en `http://localhost:5173`, regístrate, ve al quiz.
Necesitas una pregunta de tipo `fill_blank_exec` o `fix_bug`. Si el banco no tiene ninguna en producción todavía, crea una de test en un archivo temporal:

```bash
# Verifica si ya hay preguntas exec en el banco
python -c "
import json, pathlib
exec_types = {'fill_blank_exec','fix_bug','code_output'}
found = []
for f in pathlib.Path('content/questions').rglob('*.json'):
    for q in json.loads(f.read_text('utf-8')).get('questions',[]):
        if q.get('type') in exec_types:
            found.append((f.name, q['id'], q['type']))
print(f'Preguntas exec encontradas: {len(found)}')
for x in found[:5]: print(x)
"
```

Si hay 0 preguntas exec: el banco no tiene contenido Pyodide todavía.
Esto no es un bloqueante para el deploy — Pyodide es Fase 2, el deploy es Fase 0.
Documenta el hallazgo y continúa.

Si hay preguntas exec: prueba el flujo en navegador y confirma que Pyodide ejecuta código sin error.

---

## PASO 3 — PostgreSQL E2E con Docker Compose

El deploy necesita Postgres, no SQLite. Verifica que el compose funciona:

```bash
# Verifica que Docker está corriendo
docker --version

# Levanta solo la DB
docker compose up -d db

# Espera que Postgres arranque
sleep 5

# Apunta el backend a Postgres del compose
cd backend
cat > .env << 'EOF'
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/whetzy
SECRET_KEY=test-key-deploy-2026
GROQ_API_KEY=<tu-key-aqui>
CHROMA_PERSIST_PATH=./chroma_db
EOF

python -m app.services.content_loader 2>&1 | tail -5
python -m app.services.seed 2>&1 | tail -3

uvicorn app.main:app --host 127.0.0.1 --port 8771 &
sleep 4

# Registro básico contra Postgres
curl -s -X POST http://127.0.0.1:8771/api/v1/auth/register \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=pgtest@whetzy.com&password=PG_2026!" \
  | python -c "import sys,json; d=json.load(sys.stdin); print('Postgres E2E:', 'OK' if d.get('access_token') else 'FAIL')"

pkill -f "uvicorn app.main" 2>/dev/null
docker compose down
```

**Si falla:** diagnostica y corrige antes de continuar al deploy.
Causa más probable: `asyncpg` no instalado o DATABASE_URL mal formateada.

---

## PASO 4 — Deploy backend a Railway

Railway es la opción más simple para este stack (FastAPI + Postgres + Redis).

### 4.1 — Instala Railway CLI si no existe

```bash
npm install -g @railway/cli 2>/dev/null || echo "ya instalado"
railway --version
```

### 4.2 — Login y proyecto

```bash
railway login
# Crea proyecto nuevo o vincula el existente
railway init
```

### 4.3 — Variables de entorno en Railway

En el dashboard de Railway (railway.app), configura:

```
ENVIRONMENT=production
SECRET_KEY=<genera uno: python -c "import secrets; print(secrets.token_hex(32))">
GROQ_API_KEY=<tu key>
CHROMA_PERSIST_PATH=/app/chroma_db
DATABASE_URL=<Railway te da esto automáticamente al añadir Postgres>
```

Añade el addon **PostgreSQL** desde el dashboard de Railway → tu proyecto → New → Database → PostgreSQL.
Railway inyecta `DATABASE_URL` automáticamente.

### 4.4 — Verifica el Dockerfile para producción

```bash
# El Dockerfile debe existir y estar en el directorio correcto
ls backend/Dockerfile docker-compose.yml

# Verifica que el HEALTHCHECK o /health endpoint existe
grep -n "health\|/health" backend/app/main.py | head -5
```

Si `/health` no existe, añádelo en `backend/app/main.py`:
```python
@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
```

### 4.5 — Deploy

```bash
cd backend
railway up
```

Espera el output. Railway devuelve la URL pública: `https://<proyecto>.up.railway.app`

### 4.6 — Verifica el deploy

```bash
BACKEND_URL="https://<tu-url>.up.railway.app"

# Health check
curl -s $BACKEND_URL/health

# Registro real en producción
curl -s -X POST $BACKEND_URL/api/v1/auth/register \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=prod@whetzy.com&password=Prod_2026!" \
  | python -c "import sys,json; d=json.load(sys.stdin); print('Prod register:', 'OK' if d.get('access_token') else d)"
```

**Criterio P4:** `/health` responde 200, registro en producción funciona contra Postgres real.

---

## PASO 5 — Deploy frontend a Cloudflare Pages

### 5.1 — Build local primero

```bash
cd frontend
# Apunta a la URL del backend en producción
echo "VITE_API_URL=https://<tu-railway-url>.up.railway.app" > .env.production
npm run build 2>&1 | tail -10
ls dist/
```

Si el build falla: corrige antes de conectar Cloudflare.

### 5.2 — Conecta en Cloudflare Dashboard

1. Entra a dash.cloudflare.com → **Pages** → Create a project → Connect to Git
2. Selecciona tu repo de GitHub
3. Configuración de build:
   - Framework preset: **Vite**
   - Build command: `cd frontend && npm run build`
   - Build output directory: `frontend/dist`
   - Root directory: `/` (la raíz del repo)
4. Variables de entorno (en Cloudflare Pages Settings):
   - `VITE_API_URL` = `https://<tu-railway-url>.up.railway.app`
5. Deploy

### 5.3 — Conecta whetzy.com

En Cloudflare Pages → tu proyecto → Custom Domains → Add custom domain → `whetzy.com`
Cloudflare lo configura automáticamente (es tu registrador).

### 5.4 — Configura CORS en el backend

El backend debe aceptar requests desde `https://whetzy.com`:

```python
# backend/app/main.py — en el middleware CORS
origins = [
    "http://localhost:5173",       # dev
    "https://whetzy.com",          # producción
    "https://www.whetzy.com",
    "https://*.pages.dev",         # Cloudflare Pages preview
]
```

Verifica que ya existe:
```bash
grep -n "CORSMiddleware\|origins\|allow_origins" backend/app/main.py
```

### 5.5 — Verifica E2E en producción

Una vez desplegado en whetzy.com:

```bash
# Health check del backend desde la URL pública
curl -s https://whetzy.com/api/v1/health  # a través del proxy Vite si está configurado
# O directamente
curl -s https://<railway-url>.up.railway.app/health

# La PWA debe cargar en https://whetzy.com
# Verifica en browser: registro → quiz → respuesta → source visible
```

**Criterio P5:** `https://whetzy.com` carga la PWA, registro funciona, quiz devuelve pregunta con source.

---

## PASO 6 — /delete-account (bloqueante para Google Play)

Google Play exige que los usuarios puedan eliminar su cuenta desde la web.
Sin esta página, la app no pasa la revisión de Play Store.

### Backend — endpoint

```python
# backend/app/api/v1/users.py (o donde esté el router de usuarios)
@router.delete("/me/account")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Marca para borrado — retención 30 días (GDPR)
    current_user.deletion_requested_at = datetime.utcnow()
    current_user.is_active = False
    await db.commit()
    # En producción: tarea async que borra definitivamente a los 30 días
    return {"message": "Cuenta marcada para eliminación. Se borrará permanentemente en 30 días."}
```

### Frontend — página /delete-account

Página simple en `frontend/src/screens/DeleteAccountScreen.tsx`:
- Campo email + campo "CONFIRMAR" (texto literal)
- Botón "Eliminar mi cuenta y datos"
- Llama a `DELETE /api/v1/users/me/account`
- Muestra confirmación clara de qué datos se borran

Añade la ruta en tu router. Verifica que es accesible sin autenticación (el usuario debe poder
llegar desde un email o un link del store).

**Criterio P6:** `curl -X DELETE https://whetzy.com/api/v1/users/me/account` con token válido
devuelve 200. La página `/delete-account` carga y muestra el formulario.

---

## PASO 7 — Actualiza STATUS.md

Sesión (n) — con los números reales medidos:

```markdown
## Sesión 2026-09-07 (n): Deploy real + Groq + /delete-account

### Conteo resuelto
- Total Q en archivos: [N — resuelve discrepancia 1253 vs 1246]

### Groq real
- curl a Groq API: [OK / FAIL]
- tutor/explain provider: [groq / fallback]

### Pyodide en navegador
- Preguntas exec en banco: [N]
- Smoke test en browser: [PASA / PENDIENTE — 0 preguntas exec en banco]

### PostgreSQL E2E
- docker compose up → content_loader → register: [OK / FAIL]

### Deploy
- Backend Railway URL: https://_____.up.railway.app
- /health en producción: [200 OK]
- Frontend Cloudflare Pages URL: https://whetzy.com
- Registro en producción: [OK]
- Quiz en producción: [OK / PENDIENTE]

### /delete-account
- Endpoint DELETE: [OK / PENDIENTE]
- Página web: [OK / PENDIENTE]

### Fase 0 estado real: [N%]
### Fase 2 estado real: [N%]
```

---

## ENTREGABLE FINAL

1. URL del backend en Railway funcionando: `https://_____.up.railway.app/health`
2. URL del frontend en producción: `https://whetzy.com`
3. E2E real en producción: registro → quiz → source visible
4. Groq funcionando: provider=groq en tutor/explain
5. STATUS.md actualizado con números reales

**Reglas:**
- Deploy primero, features después.
- Si el Paso 3 (Postgres E2E) falla, no avances al Paso 4.
- Si Railway da problemas, usa Fly.io como alternativa: `flyctl launch` desde `backend/`.
- Limpieza al terminar: `backend/.env` (con la key real) no debe quedar en el repo.
  Verifica: `grep -r "GROQ_API_KEY" . --include="*.env" | grep -v example`
