# Prompt de auditoría exhaustiva — MASTER_PROMPT completo vs código real

> Ejecutar en sesión NUEVA después de que la sesión de autoría declare cualquier fase "terminada",
> o cuando el MASTER_PROMPT haya acumulado varios turnos de trabajo y quieras saber exactamente
> qué fue real y qué fue solo documentado.
>
> **Postura: fiscal, no testigo.** Tu trabajo es medir la brecha entre lo que el MASTER_PROMPT
> dice que existe y lo que el código demuestra que existe. STATUS.md no es la fuente de verdad —
> es uno de los objetos de auditoría.

---

## CONTEXTO — qué afirma el MASTER_PROMPT

`docs/MASTER_PROMPT.md` describe 8 fases + secciones §3.A–§3.H de requisitos cruzados.
Según `docs/STATUS.md` (última actualización 2026-09-07):

| Fase | % declarado | Área |
|---|---|---|
| 0 | 90% | Rebrand + Auth + Wire + Deploy-ready |
| 1 | 82% | Contenido bilingüe + glosarios + currículo gated |
| 2 | 55% | Tutor AI (Groq) + RAG |
| 3 | 45% | Gamificación + multiplayer + offline + animaciones |
| 4 | 8% | DKT + churn + MLOps |
| 5 | 3% | Pipeline multi-agente + analytics |
| 6 | 5% | Microservicios + observabilidad |
| 7 | 30% | Cloud/K8s/IaC + ASVS + Stripe + i18n + nativo |
| 8 | 70% | Garantía E2E + scorecard |

Tu trabajo: verificar que esos porcentajes son reales leyendo el código, no leyendo STATUS.md.

---

## GOTCHAS DEL ENTORNO (verificados 2026-09-07 — no los redescubras)

| Gotcha | Detalle |
|---|---|
| Python | `python` del sistema (3.12) ya tiene sqlalchemy, aiosqlite, pydantic, pydantic-settings. No crees venv. |
| venv | `python -m venv` **falla** en rutas con espacios ("Banco de preguntas"). No lo necesitas. |
| SQLite en Desktop | **Permission denied.** Usa `%TEMP%` → `C:\Users\feder\AppData\Local\Temp\`. |
| DATABASE_URL | Ruta absoluta, barras normales: `sqlite+aiosqlite:///C:/Users/feder/AppData/Local/Temp/neurium_audit.db` |
| .env | `config.py` lo lee del CWD. Crea `backend/.env` antes de correr el server; bórralo al terminar. |
| Browser preview | El navegador del preview NO alcanza `localhost:8000` — usa `curl` o el proxy Vite (ya configurado en `vite.config.ts`). |
| Service Worker | En dev, SW solo se registra en PROD (`import.meta.env.PROD`). Si ves UI vieja → desregistra SW + limpia caches. |
| `validate_content.py` | ⚠️ **NO EXISTE** en el repo (búsqueda 2026-09-07: 0 resultados). STATUS.md afirma haberlo corrido en varias sesiones. Si sigue sin existir, las afirmaciones de "0 errores" no son reproducibles. |
| fill_blank | Excluido de la selección de quiz (`correct_index IS NOT NULL` filter). Tiene `correct_answer_es/en` en vez de `options`. |
| Limpieza | Borra `backend/.env`, DB de temp y scripts de auditoría al terminar. |

---

## ESTRATEGIA DE AUDITORÍA

Nunca leas STATUS.md como evidencia. Audita en este orden (más barato → más caro):

1. **Existencia de archivos** — `glob` / `grep` en el repo
2. **TypeScript** — `cd frontend && tsc -b --noEmit`
3. **Backend** — AST import analysis + `pytest` si hay tests
4. **HTTP** — `curl` contra el servidor corriendo
5. **Browser** — solo si N1–N4 pasan y el cambio es visual

---

## BLOQUE A — Fase 0: Rebrand + Auth + Wire + Deploy-ready (declarado: 90%)

### A1 — Lo que el MASTER_PROMPT §1 afirma como "ya funciona"

Verifica que TODO esto existe en el código **hoy**:

```
backend/app/
├── core/security_middleware.py    → ASVS-5.0-L2 headers + rate limit
├── api/v1/auth.py                 → register + login + refresh + /me
├── services/quiz_service.py       → Elo + BKT + FSRS + Thompson
├── services/gamification/         → ligas, misiones, badges + auto-award
├── services/ai/                   → tutor.py + provider.py (Groq + fallback)
├── services/content_loader.py     → loader idempotente
├── services/seed.py               → 5 ligas, 4 misiones, 8 badges

frontend/src/
├── theme.ts                       → initTheme() que setea data-theme en <html>
├── api.ts                         → token persist + auto-refresh
├── hooks/useApi.ts                → 6 screens con datos reales
├── screens/QuizScreen.tsx         → source badge + /tutor/explain button
├── design-tokens.css              → --le-brand:#1CB0F6

raíz/
├── docker-compose.yml             → API + Postgres + Redis
├── .github/workflows/ci.yml       → CI real
├── backend/.env.example
├── README.md
```

Para **cada archivo**: confirma que existe Y que contiene la implementación (no scaffold vacío).
Usa `grep` para los símbolos críticos:
- `ASVS|CSP|security_headers` en `security_middleware.py`
- `elo_rating|bkt_mastery|fsrs_stability` en el modelo de DB
- `--le-brand` en CSS
- `initTheme` en `theme.ts`
- `refresh_token` en `auth.py`
- `auto_award|award_badges` en gamification

**Criterio A1:** cada archivo existe y los símbolos clave están presentes.

### A2 — Lo que el 10% restante de Fase 0 requiere (NO declarado como hecho)

Verifica que esto **NO existe todavía** (para validar el 90% y no inflar):

- `alembic/` en el repo — Alembic migrations (no `create_all`)
- PostgreSQL E2E test — ¿hay algún `pytest` que lance contra Postgres?
- URL pública viva (Railway/Fly.io) — ¿hay un dominio en README o en `.github/`?

**Criterio A2:** si alguno de estos existe, el % de Fase 0 debería ser >90%.
Si ninguno existe, el 90% es correcto.

---

## BLOQUE B — Fase 1: Contenido (declarado: 82%)

### B1 — Preguntas y banco de contenido

```bash
# Cuenta preguntas reales en archivos (fuente de verdad)
python -c "
import json, pathlib, collections
content = pathlib.Path('content/questions')
total = 0
per_track = collections.Counter()
no_source = 0
for f in sorted(content.rglob('*.json')):
    data = json.loads(f.read_text('utf-8'))
    qs = data.get('questions', [])
    track = f.parent.name[:7]
    per_track[track] += len(qs)
    total += len(qs)
    no_source += sum(1 for q in qs if not q.get('source'))
print(f'Total: {total}')
print(f'Meta: 1500 → {total/1500*100:.1f}%')
print(f'Sin source: {no_source}')
for t, n in sorted(per_track.items()): print(f'  {t}: {n}')
"
```

Compara el resultado con lo que dice STATUS.md (1117 Q, desglose por track).
**Cualquier diferencia es un hallazgo.**

### B2 — Glosario (requerido por MASTER_PROMPT Fase 1)

```bash
# ¿Existe el modelo GlossaryTerm?
grep -r "GlossaryTerm\|glossary_term\|GlossaryEntry" backend/app/ --include="*.py" -l
# ¿Existe GlossaryScreen?
find frontend/src -name "GlossaryScreen*" 2>/dev/null
# ¿Hay términos de glosario en content/?
find content/ -name "glossary*" 2>/dev/null
```

Si ninguno devuelve resultados: **glosario = 0%, no construido.**
STATUS.md lo debería reflejar en el % de Fase 1.

### B3 — TracksScreen con desbloqueo BKT

```bash
find frontend/src -name "TracksScreen*" 2>/dev/null
grep -r "TracksScreen\|track.*unlock\|bkt.*unlock" frontend/src/ -l 2>/dev/null
```

Si no existe: **currículo gated por BKT = no construido.**

### B4 — Calibración IRT

```bash
grep -r "irt\|IRT\|discrimination\|guessing\|3PL\|2PL\|1PL\|item_response" \
     backend/app/ --include="*.py" -l
```

Nota: el campo `discrimination` existe en el modelo de preguntas (schema), pero ¿se usa en
la lógica de selección? Busca su uso real, no solo la columna.

**Criterio B:** reporta el % real de Fase 1 con evidencia por componente:
- `preguntas_reales / 1500 × 100`
- glosario: existe / no existe
- TracksScreen: existe / no existe
- IRT calibración: implementada / solo campo
- source backfill: N sin source

---

## BLOQUE C — Fase 2: Tutor AI + RAG (declarado: 55%)

### C1 — Tutor (lo que sí existe)

```bash
grep -r "tutor\|explain\|LLMProvider\|GroqProvider" backend/app/ -l
# Verifica que el endpoint existe
grep -r "POST.*tutor\|router.*tutor" backend/app/ -l
```

### C2 — RAG vectorial (lo que NO existe según STATUS.md)

```bash
grep -r "chromadb\|ChromaDB\|sentence_transformers\|SentenceTransformer\|embeddings" \
     backend/ -l 2>/dev/null
grep -r "vector\|retrieval\|rerank" backend/app/ --include="*.py" -l
```

Si ChromaDB no aparece: RAG vectorial = no construido.

### C3 — Memoria del tutor

```bash
grep -r "TutorMemory\|long_term\|episodic\|conversation_history" \
     backend/app/ --include="*.py" -l
```

### C4 — Groq key en entorno

```bash
grep -r "GROQ_API_KEY\|groq_api_key" backend/ --include="*.py" -l
grep "GROQ_API_KEY" backend/.env.example 2>/dev/null || echo "no en .env.example"
```

¿Hay GROQ_API_KEY en `.env.example`? Sin ella el tutor usa el fallback grounded.

**Criterio C:** tutor endpoint existe (✓/✗), RAG (✓/✗), memoria (✓/✗), Groq key configurada (✓/✗).
Calcula % real de Fase 2 con esa evidencia.

---

## BLOQUE D — Fase 3: Gamificación avanzada + Social + Offline (declarado: 45%)

### D1 — Gamificación base (lo que debería existir)

```bash
grep -r "league\|mission\|badge\|award_badge\|XP\|streak" backend/app/ -l
grep -r "League\|Mission\|Badge" frontend/src/ -l
```

### D2 — Lo que el MASTER_PROMPT exige para el 100% de Fase 3

Verifica que estos componentes NO existen (para validar el 45%):

```bash
# Framer Motion en uso real (no solo instalada)
grep -r "framer-motion\|AnimatePresence\|motion\." frontend/src/ -l 2>/dev/null
# Duelos multiplayer (WebSocket)
grep -r "WebSocket\|socket.io\|duel\|duelo\|tournament" backend/app/ -l frontend/src/ -l 2>/dev/null
# Offline sync / IndexedDB (más allá del SW básico)
grep -r "IndexedDB\|idb\|offline.*sync\|sync.*offline\|vector.clock" frontend/src/ -l 2>/dev/null
# Cofres / streak freeze
grep -r "chest\|cofre\|freeze\|streak_freeze\|combo" backend/app/ -l frontend/src/ -l 2>/dev/null
# Medidor ZPD visible
grep -r "ZPD\|zpd\|zone.*proximal\|optimal.*difficulty" frontend/src/ -l 2>/dev/null
# Memory strength / forgetting curve visible
grep -r "memory_strength\|forgetting_curve\|fsrs.*bar\|stability.*bar" frontend/src/ -l 2>/dev/null
```

**Criterio D:** para cada componente, EXISTE o NO EXISTE. Calcula % real.

---

## BLOQUE E — Fases 4, 5, 6: ML avanzado / Pipeline / Microservicios

Para las fases con bajo % declarado (4: 8%, 5: 3%, 6: 5%), confirma que el 8/3/5% sí existe
y que el resto efectivamente no está construido:

```bash
# Fase 4 — DKT, churn, MLOps
grep -r "DKT\|LSTM\|pytorch\|xgboost\|mlflow\|feast\|evidently\|drift" \
     backend/ -l 2>/dev/null
# Fase 5 — Pipeline multi-agente
grep -r "dagster\|prefect\|great_expectations\|content_pipeline\|generator.*agent" \
     backend/ -l 2>/dev/null
# Fase 6 — Microservicios, gRPC, RabbitMQ
grep -r "grpc\|rabbitmq\|kafka\|jaeger\|opentelemetry\|circuit_breaker\|saga" \
     backend/ -l 2>/dev/null
```

Lo que existe justifica el % base (el motor FSRS/Elo/BKT ya implementado = el 8% de Fase 4).
Lo que no existe confirma que el 92/97/95% restante no está construido.

---

## BLOQUE F — Fase 7: Cloud, Seguridad, Pagos, Nativo (declarado: 30%)

El 30% declarado viene de "Seguridad+Docker+CI reales; K8s/Stripe/nativo no".
Verifica los dos lados:

### F1 — Lo que debería existir (el 30%)

```bash
# Docker Compose
ls backend/docker-compose.yml docker-compose.yml 2>/dev/null
# CI/CD GitHub Actions
ls .github/workflows/ 2>/dev/null
# ASVS security headers
grep -r "X-Content-Type\|Strict-Transport\|Content-Security-Policy" \
     backend/app/ --include="*.py" -l
# Rate limiting
grep -r "rate_limit\|RateLimiter\|slowapi\|limiter" backend/app/ --include="*.py" -l
```

### F2 — Lo que requiere Fase 7 completa y no existe

```bash
# Terraform / K8s / Helm
ls infra/ terraform/ k8s/ helm/ 2>/dev/null || echo "IaC no existe"
# Stripe
grep -r "stripe\|Stripe" backend/ -l 2>/dev/null
# RevenueCat
grep -r "revenuecat\|RevenueCat" backend/ -l 2>/dev/null
# i18next completo
grep -r "i18next\|useTranslation\|i18n" frontend/src/ -l 2>/dev/null
# Capacitor
ls frontend/capacitor.config.ts ios/ android/ 2>/dev/null || echo "Capacitor no configurado"
# Playwright
ls e2e/ playwright.config.ts 2>/dev/null || echo "Playwright no existe"
# Sign in with Apple / Google OAuth
grep -r "apple.*signin\|google.*oauth\|PKCE\|authorization_code" \
     backend/app/ --include="*.py" -l 2>/dev/null
# Argon2id
grep -r "argon2\|Argon2" backend/ -l 2>/dev/null
# Password reset correcto
grep -r "password_reset\|reset_token\|forgot_password" backend/app/ -l 2>/dev/null
# Account deletion (in-app + web)
grep -r "delete.*account\|account.*delete\|DELETE.*users.*me" \
     backend/app/ --include="*.py" -l 2>/dev/null
```

### F3 — §3.A Blockers de tiendas (todos requeridos antes de subir)

Para cada punto, EXISTE o NO:

| Requisito | Buscar |
|---|---|
| Sign in with Apple | `apple_auth\|AppleSignIn\|siwa` |
| Sign in with Google (PKCE) | `google_auth\|GoogleSignIn\|pkce` |
| Borrado de cuenta in-app | `DELETE /api/v1/users/me` endpoint |
| Borrado de cuenta web | `/delete-account` route en frontend |
| Privacy Manifest iOS | `PrivacyInfo.xcprivacy` |
| Consentimiento AI (5.1.2i) | `ai_consent\|AIConsent` |
| Biometría | `biometric\|FaceID\|TouchID\|Keychain` |
| Push notifications nativo | `FCM\|APNs\|VAPID\|push_notification` |

**Criterio F:** el 30% declarado se sostiene si F1 existe y F2/F3 no existe.
Si algo de F2/F3 existe que STATUS.md no mencionó, ajusta el % al alza con evidencia.

---

## BLOQUE G — §3.B Seguridad (requisitos del MASTER_PROMPT)

Verifica implementación real vs requisito declarado:

```bash
# Refresh token rotation con detección de reuso
grep -r "token_family\|reuse_detect\|jti.*blacklist\|refresh.*rotate" \
     backend/app/ --include="*.py" -C 3 | head -40

# Sin enumeración de cuentas en password reset
grep -r "password_reset\|reset_password" backend/app/ --include="*.py" -A 5 | \
     grep -i "always\|regardless\|whether\|si existe\|no exist" | head -10

# Argon2id vs bcrypt
grep -r "bcrypt\|argon2\|passlib" backend/app/ --include="*.py" -l

# Almacenamiento seguro en nativo
grep -r "Keychain\|Keystore\|SecureStorage" frontend/src/ -l 2>/dev/null

# PKCE en OAuth
grep -r "code_verifier\|code_challenge\|PKCE" backend/app/ --include="*.py" -l 2>/dev/null
```

**Criterio G:** para cada ítem, IMPLEMENTADO (con línea de código) o PENDIENTE.

---

## BLOQUE H — §3.C UX de registro y conversión

```bash
# Registro diferido (placement test antes de cuenta)
grep -r "deferred.*reg\|placement.*test\|onboard.*guest\|guest.*session" \
     frontend/src/ -l 2>/dev/null
grep -r "placement\|nivelacion\|nivel.*test" frontend/src/ -l 2>/dev/null

# Social buttons primero (Apple/Google arriba)
grep -r "Apple\|GoogleSignIn\|ContinuarCon\|Continue with" \
     frontend/src/ --include="*.tsx" -l 2>/dev/null

# Selectores que cambian el flujo de onboarding
grep -r "learning_goal\|daily_goal\|nivel_declarado\|objetivo\|por.*que.*aprendes" \
     frontend/src/ -l 2>/dev/null

# Progressive disclosure (un campo a la vez en móvil)
grep -r "step.*register\|RegisterStep\|multi.*step.*form" frontend/src/ -l 2>/dev/null
```

---

## BLOQUE I — §3.H Web neurium.app

```bash
# ¿Existe un proyecto Next.js o web separado?
ls frontend-web/ neurium-web/ web/ packages/web/ 2>/dev/null || echo "no existe web separado"

# ¿Hay configuración de Cloudflare?
ls _redirects _headers cloudflare.toml wrangler.toml 2>/dev/null

# ¿Hay página /delete-account?
grep -r "delete.account\|delete_account" frontend/src/ -l 2>/dev/null

# ¿Hay privacy policy y terms con URL pública?
find . -name "privacy*" -o -name "terms*" | grep -v node_modules | grep -v .git
```

---

## BLOQUE J — §3.D/E Contenido ejecutable + Gamificación avanzada

```bash
# Pyodide (Fase 2 — no debe existir aún)
grep -r "pyodide\|Pyodide\|WebWorker.*python\|fill_blank_exec\|fix_bug\|code_output_exec" \
     frontend/ backend/ -l 2>/dev/null

# Boss battles (exámenes de módulo)
grep -r "boss.*battle\|boss_battle\|module.*exam\|mastery.*test" \
     backend/app/ frontend/src/ -l 2>/dev/null

# Social proof ("73% falla esta")
grep -r "fail_rate\|failure_rate\|success_rate\|percent.*fail" \
     backend/app/ frontend/src/ -l 2>/dev/null

# ZPD meter visible en UI
grep -r "ZPD\|zpd_score\|optimal_zone" frontend/src/ -l 2>/dev/null
```

---

## BLOQUE K — Verificación E2E del núcleo (el que nadie debe romper)

El §1 del MASTER_PROMPT afirma que el core funciona. Verifica que sigue funcionando después de
todas las sesiones de contenido:

```bash
# 1. TypeScript sin errores
cd frontend && npx tsc -b --noEmit 2>&1 | tail -20

# 2. Backend AST OK
cd backend && python -m py_compile app/main.py && echo "AST OK"

# 3. HTTP E2E completo (nuevo usuario → quiz → motor)
cd backend
# crea .env con DATABASE_URL a %TEMP%
python -m app.services.content_loader 2>&1 | tail -5
python -m app.services.seed 2>&1 | tail -5
# arranca en background
uvicorn app.main:app --host 127.0.0.1 --port 8765 &
sleep 3

TOKEN=$(curl -s -X POST http://127.0.0.1:8765/api/v1/auth/register \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=audit@neurium.app&password=Audit_2026!" \
  | python -c "import sys,json; print(json.load(sys.stdin).get('access_token','FAIL'))")
echo "Token: ${TOKEN:0:20}..."

QUIZ=$(curl -s -X POST http://127.0.0.1:8765/api/v1/quiz/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"skill_id": "sk010401"}')
echo "Quiz response: $(echo $QUIZ | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('id','NO_ID'), d.get('source','NO_SOURCE')[:50])" )"

pkill -f "uvicorn app.main"
```

**Criterio K:** tsc sin errores; content_loader 0 skipped; register → quiz → source en respuesta;
Elo/BKT/FSRS actualizados y persistidos (re-consulta DB para confirmar).

---

## BLOQUE L — Auditoría de veracidad de STATUS.md

Una vez terminados los bloques A–K, compara los números medidos contra lo que STATUS.md declara:

1. ¿El % por fase es defendible con la evidencia? Lista cada fase con % real vs % declarado.
2. ¿`validate_content.py` existe? Si no: las sesiones (c)–(g) declaran haberlo corrido. ¿Son reproducibles esas afirmaciones?
3. ¿El total de 1117 Q coincide con el conteo real de archivos?
4. ¿Hay módulos en `content/` que STATUS.md no menciona? *(así se encontró track05)*
5. ¿Los backfills de source declarados en sesiones (e)/(g) coinciden con la cobertura real?
6. ¿La afirmación "MVP shippable: ~74%" se sostiene?

**Cualquier discrepancia → corrige STATUS.md con el número real.**

---

## ENTREGABLE

Un scorecard honesto con:

### 1. Tabla resumen por fase

| Fase | % declarado | % real auditado | Delta | Evidencia |
|---|---|---|---|---|
| 0 | 90% | ? | ? | archivos N/N, endpoint N/N |
| 1 | 82% | ? | ? | Q reales, glosario, TracksScreen, IRT |
| ... | | | | |

### 2. Tabla de requisitos §3.A–§3.H

| Requisito | ¿Existe? | Archivo o "pendiente" |
|---|---|---|
| Sign in with Apple | ✗ | pendiente |
| Borrado cuenta in-app | ✗ | pendiente |
| ... | | |

### 3. Lista de hallazgos

Por cada discrepancia entre lo declarado y lo medido:
- Severidad: CRÍTICA (afecta aprobación de stores), ALTA (funcionalidad clave faltante),
  MEDIA (% inflado), BAJA (documentación inexacta).
- Qué dice STATUS.md / MASTER_PROMPT.
- Qué encontraste en el código.
- Corrección propuesta.

### 4. STATUS.md corregido

Con los porcentajes reales y los hallazgos incorporados.

### 5. Lista priorizada de próximos pasos

Ordenada por impacto inmediato (no por fase). Ejemplo:
1. Track 07 expansion (bloquea Fase 1 al 100%)
2. /delete-account endpoint + web page (bloquea Google Play)
3. Alembic migrations (bloquea deploy a Postgres)
4. ...

### 6. Limpieza confirmada

`backend/.env`, DB de auditoría y scripts borrados.

---

## REGLAS DE LA AUDITORÍA

- Verifica el **código**, no la documentación. STATUS.md es el output, no el input.
- Nunca declares "verificado" sin haber ejecutado el comando y visto la salida.
- Si algo no lo verificaste, escribe "no verificado — [razón]".
- Un símbolo `grep` que aparece en un archivo de comentario o test no cuenta como implementado.
- Distingue: "el campo existe en el schema" ≠ "la lógica usa ese campo".
- Si encuentras algo que STATUS.md no menciona (positivo o negativo), es el hallazgo más valioso.
