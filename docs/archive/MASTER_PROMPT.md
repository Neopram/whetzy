# Prompt: Fase 4 — Railway verify + Duel E2E + Pyodide + DKT

> Sesión nueva. Lee este prompt completo antes de ejecutar cualquier comando.
> Postura: escéptica. STATUS.md puede estar desactualizado — fuente de verdad son las HTTP responses.
> Model routing: Sonnet 4.6 para coordinación. Haiku para sub-agentes de búsqueda/lectura (exploración, grep, read). No uses Opus.

---

## CONTEXTO — qué pasó en las sesiones anteriores (no rehacer)

### URLs de producción
- **Backend Railway**: `https://api-production-9751.up.railway.app`
- **Frontend Cloudflare Pages**: `https://whetzy.pages.dev` / `https://whetzy.com`
- **GitHub**: `github.com/Neopram/whetzy` — branch `master`

### Commit más reciente: `2c5b396`
Pushado el 2026-09-08. Contiene:
- Alembic setup completo (`backend/alembic/env.py`, `alembic.ini`)
- Migration inicial `a1b2c3d4e5f6` (15 tablas) → `b2c3d4e5f6a7` (tabla `duels`) — esta es la cadena correcta
- Dockerfile fix: `COPY backend/alembic ./alembic`
- `start.sh` con auto-stamp (si `users` existe sin `alembic_version`, stampa `a1b2c3d4e5f6` y corre `upgrade head` → crea `duels`)
- Duelos backend completo: `app/models/duel.py`, `app/schemas/duel.py`, `app/api/v1/endpoints/duels.py`
- Frontend: `DuelScreen.tsx`, Lottie en `QuizScreen.tsx`, offline badge en `TopBar.tsx`

### Cadena Alembic (VERIFICADA localmente con `alembic heads`)
```
<base> → a1b2c3d4e5f6 (initial_schema) → b2c3d4e5f6a7 (add_duels) [HEAD]
```

### Estado de Railway al cierre
- Railway NO tiene GitHub webhook/auto-deploy. El deploy es MANUAL.
- El token de Railway CLI expiró (UUID de sesión antigua, rechazado por CLI v5.49.4).
- `serviceInstanceRedeploy` via GraphQL se ejecutó pero redesplegó la imagen ANTIGUA.
- La imagen en producción aún tiene 24 rutas sin duelos. Necesita redeploy manual del usuario.

### Gotchas críticos (no redescubrir)
| Gotcha | Detalle |
|---|---|
| `question_id` en quiz | Está en `.question.id`, NO en `.id` top-level |
| GROQ_MODEL | `qwen/qwen3.8-27b` — llama-3.3-70b-versatile NO disponible |
| Railway no auto-despliega | Sin webhook GitHub. Deploy siempre manual via `railway up` o dashboard |
| Token Railway viejo | UUID `6d852a5d-...` no funciona con CLI v5+. Usar dashboard o nuevo token |
| Sandbox Python | Archivos escritos por sesiones ANTERIORES con Write tool pueden ser invisibles a `os.listdir()` en subprocess. Fix: reescribirlos en la sesión actual |
| Alembic versions | Solo 2 archivos deben existir: `a1b2c3d4e5f6_initial_schema.py` y `b2c3d4e5f6a7_add_duels.py`. Cualquier otro es duplicado |
| PostgreSQL local | Puerto 5433 (Docker), user `neurium`, password `neurium_dev`, DB `neurium` |
| Content loader | Solo corre desde `start.sh` en producción. En dev: `DATABASE_URL=... python -m app.services.content_loader` |

---

## PASO 0 — Verificar Railway deploy (con escepticismo)

```powershell
$B = "https://api-production-9751.up.railway.app"

# Si retorna 401 → deploy nuevo está live (ruta existe, auth required)
# Si retorna 404 → deploy viejo aún corriendo
try {
    Invoke-RestMethod "$B/api/v1/duels/my" -Method GET
} catch {
    Write-Host "duels/my HTTP: $($_.Exception.Response.StatusCode.value__)"
}

# Contar rutas (nuevo deploy debe tener 28+, viejo tenía 24)
$openapi = Invoke-RestMethod "$B/api/v1/openapi.json"
Write-Host "Total routes: $($openapi.paths.PSObject.Properties.Name.Count)"
$openapi.paths.PSObject.Properties.Name | Where-Object { $_ -like "*duel*" }
```

**Si duelos = 404**: El deploy no ocurrió. Pedir al usuario:
1. Ir a [railway.app](https://railway.app) → proyecto → servicio → "Deploy" desde commit `2c5b396`
2. O generar token en railway.app/account/tokens y compartirlo para usar `railway up`

**Si duelos = 401**: Railway deployó. Continuar con PASO 1.

---

## PASO 1 — Verificar Alembic en producción

Si el deploy ocurrió, `start.sh` debió:
1. Detectar `users` table sin `alembic_version` → stamp `a1b2c3d4e5f6`
2. Correr `alembic upgrade head` → crear tabla `duels` (revision `b2c3d4e5f6a7`)

Verificar vía endpoint (tabla `duels` existe ↔ endpoint duels responde 401 no 500):
```powershell
# 401 = tabla existe y auth funciona
# 500 = tabla no existe (migration falló)
$code = try { (Invoke-WebRequest "$B/api/v1/duels/my").StatusCode } catch { $_.Exception.Response.StatusCode.value__ }
Write-Host "duels/my: $code  (esperado: 401)"
```

---

## PASO 2 — Duel E2E en producción

Registrar dos usuarios y ejecutar un duelo completo:

```powershell
$B = "https://api-production-9751.up.railway.app"

# Usuario A (challenger)
$A = (Invoke-RestMethod "$B/api/v1/auth/register" -Method POST -ContentType "application/json" -Body '{"username":"challenger_test","email":"chal@test.com","password":"Test1234!"}')
$TOKEN_A = (Invoke-RestMethod "$B/api/v1/auth/login" -Method POST -ContentType "application/json" -Body '{"username":"challenger_test","password":"Test1234!"}').access_token

# Usuario B (opponent)
$null = Invoke-RestMethod "$B/api/v1/auth/register" -Method POST -ContentType "application/json" -Body '{"username":"opponent_test","email":"opp@test.com","password":"Test1234!"}'
$TOKEN_B = (Invoke-RestMethod "$B/api/v1/auth/login" -Method POST -ContentType "application/json" -Body '{"username":"opponent_test","password":"Test1234!"}').access_token

# Crear duelo (A reta a B)
$hA = @{ Authorization = "Bearer $TOKEN_A" }
$duel = Invoke-RestMethod "$B/api/v1/duels/challenge" -Method POST -Headers $hA -ContentType "application/json" -Body '{"opponent_username":"opponent_test"}'
Write-Host "Duel ID: $($duel.duel_id), Questions: $($duel.question_ids.Count)"

# A responde las 5 preguntas
$QIDs = $duel.question_ids
foreach ($qid in $QIDs) {
    $body = "{`"duel_id`":`"$($duel.duel_id)`",`"question_id`":`"$qid`",`"answer`":`"A`"}"
    $r = Invoke-RestMethod "$B/api/v1/duels/answer" -Method POST -Headers $hA -ContentType "application/json" -Body $body
    Write-Host "A answered: correct=$($r.correct)"
}

# B responde las 5 preguntas
$hB = @{ Authorization = "Bearer $TOKEN_B" }
foreach ($qid in $QIDs) {
    $body = "{`"duel_id`":`"$($duel.duel_id)`",`"question_id`":`"$qid`",`"answer`":`"B`"}"
    $r = Invoke-RestMethod "$B/api/v1/duels/answer" -Method POST -Headers $hB -ContentType "application/json" -Body $body
}

# Resultado
$result = Invoke-RestMethod "$B/api/v1/duels/$($duel.duel_id)/result" -Method GET -Headers $hA
$result | ConvertTo-Json -Depth 5
```

Criterio: `status = "completed"`, `winner_id` definido (o null si empate), `challenger_correct` y `opponent_correct` con valores numéricos.

---

## PASO 3 — Pyodide smoke test

Pyodide no se puede testear con curl — requiere browser real. Usar el dev server local.

```powershell
# Arrancar frontend
cd "C:\Users\feder\Desktop\Banco de preguntas\python\learning-engine\frontend"
npm run dev -- --port 5199
```

En browser (localhost:5199):
1. Login con cuenta existente
2. Iniciar quiz → esperar a que aparezca una pregunta de tipo `exec` (7 de 1253 = 0.6%)
3. Si no aparece exec en 10 intentos → documentar en STATUS.md como "probabilidad baja, pendiente"

Alternativa determinista: forzar una pregunta exec vía API:
```powershell
$TOKEN = "..."  # token de usuario local
$hdr = @{ Authorization = "Bearer $TOKEN" }
# Intentar iniciar quiz en modo "skill" que tenga exec questions
for ($i=0; $i -lt 20; $i++) {
    $s = Invoke-RestMethod "http://localhost:8000/api/v1/quiz/start" -Method POST -Headers $hdr -ContentType "application/json" -Body '{}'
    if ($s.question.type -eq "exec") { Write-Host "GOT EXEC! skill=$($s.question.skill_id)"; break }
    # responder para continuar
    Invoke-RestMethod "http://localhost:8000/api/v1/quiz/answer" -Method POST -Headers $hdr -ContentType "application/json" -Body "{`"session_id`":`"$($s.session_id)`",`"question_id`":`"$($s.question.id)`",`"answer`":`"A`"}" | Out-Null
}
```

---

## PASO 4 — DKT architecture (Fase 4 core)

Implementar `backend/app/services/dkt.py`:
- Input: historial de respuestas del usuario (skill_id, correcto, timestamp)
- Output: probabilidad P(correcto) por skill — para reemplazar FSRS con DKT
- Biblioteca: `torch` (ya en requirements si está, si no: añadir `torch==2.3.0+cpu`)
- Modelo: LSTM simple, 1 capa, hidden_size=64, input = (skill_id_embedded, correct)

```python
# Estructura mínima viable
class DKT(nn.Module):
    def __init__(self, n_skills: int, hidden: int = 64):
        super().__init__()
        self.embed = nn.Embedding(n_skills * 2, hidden)  # (skill*2 + correct)
        self.lstm = nn.LSTM(hidden, hidden, batch_first=True)
        self.out = nn.Linear(hidden, n_skills)

    def forward(self, x):  # x: (B, T) int indices
        e = self.embed(x)
        h, _ = self.lstm(e)
        return torch.sigmoid(self.out(h))  # (B, T, n_skills)
```

Integración: `GET /api/v1/progress/skills` debe devolver `dkt_probability` por skill.

---

## PASO 5 — Commit y STATUS.md

Al finalizar cada paso verificado:
```powershell
cd "C:\Users\feder\Desktop\Banco de preguntas\python\learning-engine"
git add -p  # revisar antes de stagear
git commit -m "Fase 4: [descripción específica]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
git push origin master
```

Actualizar `docs/STATUS.md` con evidencia HTTP real (no suposiciones).

---

## Estado esperado al cierre de esta sesión

| Criterio | Verificación |
|---|---|
| P0: Railway con duelos | `GET /api/v1/duels/my` → 401 |
| P1: Duel E2E | `status=completed`, `winner_id` o empate |
| P2: Pyodide | exec question renderiza en browser, o documentado como pendiente |
| P3: DKT MVP | `dkt.py` implementado, importable, unit test pasa |

---

## Recordatorio de arquitectura

```
backend/
  alembic/              ← script_location = "alembic" (en alembic.ini)
    versions/
      20260908_0200_a1b2c3d4e5f6_initial_schema.py  ← base, 15 tablas
      20260908_0201_b2c3d4e5f6a7_add_duels.py        ← HEAD, tabla duels
  app/
    api/v1/endpoints/duels.py   ← challenge, answer, result, my
    models/duel.py              ← Duel model
    schemas/duel.py             ← request/response schemas
    services/dkt.py             ← PENDIENTE (Fase 4)
  scripts/start.sh              ← auto-stamp a1b2c3d4e5f6 + alembic upgrade head
  alembic.ini                   ← sqlalchemy.url vacío (lo llena env.py desde settings)
```
