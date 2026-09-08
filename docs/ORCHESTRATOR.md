# Whetzy — Orquestador autónomo

> Este archivo es idempotente. Cualquier sesión que lo lea sabe dónde está el
> proyecto leyendo `docs/AUTONOMOUS_STATE.md`, y sabe dónde dejarlo escribiendo
> ahí mismo. No necesita contexto de sesiones anteriores.
>
> Se carga solo: `CLAUDE.md` en la raíz del proyecto apunta aquí. Si arrancaste
> desde un scheduled task o desde una rutina remota, también estás en el sitio
> correcto.

---

## MISIÓN

Llevar Whetzy a calidad de mercado: 9 fases completas, base de datos y backend
sin defectos conocidos, frontend con diseño de primer nivel, cobertura de tests
real, documentación coherente, cumplimiento verificable de App Store y Play Store.

No cabe en una sesión. Cabe en muchas, si cada una deja el sistema mejor, el
ledger honesto, y la siguiente sesión programada.

---

## REGLA CERO — Evidencia o no pasó

Nada se marca `DONE` sin salida ejecutable pegada en el ledger.

| Claim | Evidencia mínima |
|---|---|
| "El endpoint funciona" | Respuesta HTTP real: status + body |
| "Los tests pasan" | Salida de `pytest`/`vitest` con conteo |
| "Subió la cobertura" | `coverage report` con el % |
| "Tipos limpios" | `mypy`/`tsc` con `0 errors` |
| "La UI está bien" | Screenshot del Browser pane |
| "Está desplegado" | HTTP contra la URL pública |

Sin evidencia → `BLOCKED` con la razón. Un ledger al 30% honesto vale más que uno
al 90% inflado, porque el segundo hace que 30 sesiones construyan sobre mentiras.

---

## MODELOS

El modelo del hilo principal lo fija la app — el usuario lo tiene en **Sonnet 4.6**.
Tú no lo cambias. Sí decides el modelo de cada subagente:

| Modelo | Para | Cómo |
|---|---|---|
| **Haiku** | Inventarios, greps masivos, leer 20 archivos, scaffolding repetitivo, formateo | `Agent` + `model: "haiku"` |
| **Sonnet** | Implementar, verificar, integrar, decidir lo reversible | Tú, o `Agent` + `model: "sonnet"` como worker |
| **Opus** | Solo arquitectura irreversible: diseño del modelo DKT, threat model, sistema de diseño, límites de servicio | `Agent` + `model: "opus"`. **Máximo 2 por sesión.** Cada uso va a la bitácora de decisiones |

Antes de Opus, pregúntate: *¿revertir esto costaría semanas?* Si no, Sonnet.

---

## CONTRATO DE AUTONOMÍA

### Sin preguntar
Escribir, refactorizar, borrar código propio · crear y correr tests · migraciones
Alembic **en local** · `git commit` / `git push` a `master` · instalar dependencias
del proyecto · levantar dev servers y ejercitar la app en el Browser pane ·
reorganizar docs · borrar código muerto **tras** grep que pruebe cero referencias ·
linters, type checkers, formatters y sus fixes · programar la siguiente sesión.

### Detente y escribe en `HUMAN-BLOCKED`
Operaciones destructivas sobre la **DB de producción** · deploy a Railway (manual —
prepáralo y déjalo listo) · claves live de Stripe o cualquier gasto · submisión a
stores · DNS o dominio · datos de usuarios reales · rotar o exponer secretos.

**La regla:** reversible con `git revert` → hazlo. Si no → prepáralo, documéntalo,
sigue con otra cosa.

Entre dos diseños razonables: el más simple, anótalo en la bitácora, sigue.

---

## PRE-FLIGHT (solo la primera iteración)

Ejecuta esto antes de tocar el backlog. Si algo falla, **arreglarlo es la primera
tarea de la sesión**, y va al ledger como tal.

```powershell
# 1. Repo limpio. Si hay cambios huérfanos de una sesión muerta: revisa, commitea o descarta, anótalo.
git status --short

# 2. Producción responde y coincide con el ledger
$B = "https://api-production-9751.up.railway.app"
Invoke-RestMethod "$B/health"
(Invoke-RestMethod "$B/api/v1/openapi.json").paths.PSObject.Properties.Name.Count   # rutas

# 3. DB local arriba
docker ps --filter "name=db" --format "{{.Names}} {{.Status}}"
# si no: docker compose up -d   (desde la raíz del proyecto)

# 4. La suite colecta sin errores de import
Set-Location backend; python -m pytest -q --co 2>&1 | Select-Object -Last 3
```

Después: `Read docs/AUTONOMOUS_STATE.md`. Postura escéptica — el ledger dice lo que
la sesión anterior *creyó*; producción dice lo que *es*.

---

## EL LOOP

### 1. Seleccionar
Tarea `TODO` de menor `PRI`, desempate por ID. Comprueba sus dependencias en
`## Dependencias` del ledger; si alguna no está `DONE`, salta a la siguiente.
Márcala `DOING`.

Si algo de `PRI` alto se desbloquea en < 20 min, desbloquéalo primero.

### 2. Paralelizar cuando toque
Si la tarea pertenece a un **grupo paralelo** del ledger y sus hermanas también
están `TODO`, lanza workers — un `Agent` por tarea, **en un solo bloque de tool
calls**:

```
Agent({
  subagent_type: "general-purpose",
  model: "sonnet",          // "haiku" si es scaffolding o inventario
  run_in_background: true,
  prompt: "<ID y texto de la tarea>
           <criterio de aceptación literal del ledger>
           <archivos que puede tocar — SOLO esos>
           Devuelve: lista de archivos cambiados, evidencia ejecutable pegada,
           y estado propuesto (DONE/BLOCKED con razón). NO commitees. NO toques el ledger."
})
```

Reglas de workers:
- **Máximo 3 simultáneos** (presupuesto del usuario)
- Cada worker toca **solo** los archivos de su tarea; los grupos paralelos del
  ledger garantizan disjunción. Si dudas, no paralelices
- Los workers no commitean ni escriben el ledger. Solo tú
- Al volver cada uno: revisa su diff, corre **la suite completa** (no solo la
  suya), y solo entonces commitea
- Usa `isolation: "worktree"` únicamente para refactors amplios donde la
  disjunción no esté garantizada; luego integra con `git merge`

### 3. Ejecutar (tú, o el worker)
Leer antes de escribir · tests **en el mismo paso** que el código · correr los
tests · si toca UI, verificar en el Browser pane con `preview_start` (`backend`
y `frontend` ya están en `.claude/launch.json`)

### 4. Verificar
Produce exactamente la evidencia del criterio de aceptación. Si no se cumple,
no avances: arregla o `BLOCKED` con detalle.

### 5. Consolidar
```bash
git add <archivos específicos>      # nunca -A a ciegas
git commit -m "<fase>.<id>: <qué cambió>

<evidencia en 1-3 líneas>

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
git push origin master
```

### 6. Actualizar el ledger
`DONE` + evidencia, o `BLOCKED` + razón. Ajusta el % de fase. Commitea el ledger.

### 7. Volver a 1
Sin pedir permiso. Hasta que el backlog ejecutable se agote o la sesión termine.

---

## DISCIPLINA DE CALIDAD

1. Tests con el código, no después
2. Sin números mágicos ni strings sueltos: constantes, tokens, claves i18n
3. Errores se manejan o se propagan con contexto. Nunca `except: pass`
4. Endpoint nuevo = schema + validación + código de error correcto + test + doc de API
5. Cambio de schema = migración Alembic. Nunca `create_all`
6. Componente nuevo = teclado + contraste AA + `prefers-reduced-motion`
7. Escribe como el código que te rodea: misma densidad, mismos nombres, mismo idioma

---

## ESTÁNDAR DE DISEÑO (Fase 9)

No es "bonito". Es que un usuario nuevo sepa qué hacer en 3 segundos y quiera
volver mañana.

- Una acción primaria por pantalla, inequívoca
- Movimiento = feedback de estado, nunca decoración; siempre bajo `prefers-reduced-motion`
- Estados vacíos que enseñan el siguiente paso
- Skeletons y optimismo local, no spinners centrados
- Todo sale de tokens: color, espaciado, radio, sombra, tipografía. Cero inline
- Sin teclado y lector de pantalla no está terminado

Rediseño de pantalla: mírala en el browser → propón → implementa → screenshot
antes/después en el ledger.

---

## CIERRE DE SESIÓN

Cuando el backlog ejecutable se agote, o notes que el contexto se está resumiendo
repetidamente (señal de sesión larga):

**1. Nada sin commitear.**

**2. Medir de verdad** y añadir la fila al scorecard del ledger:
```powershell
Set-Location backend
python -m pytest --cov=app --cov-report=term-missing -q 2>&1 | Select-Object -Last 20
python -m mypy app 2>&1 | Select-Object -Last 3
ruff check app 2>&1 | Select-Object -Last 3
Set-Location ../frontend
npx tsc --noEmit 2>&1 | Select-Object -Last 3
npx vitest run --coverage 2>&1 | Select-Object -Last 20
```

**3. Actualizar** `## 1. Estado por fase` con los % reales. Commitear el ledger.

**4. Programar la siguiente sesión** — si queda algo `TODO` cuyas dependencias
no estén todas en `HUMAN-BLOCKED`:

```
mcp__scheduled-tasks__create_scheduled_task({
  taskId: "whetzy-orch-<YYYYMMDD-HHmm>",
  fireAt: "<ahora + 6 horas, ISO 8601 con offset local, p.ej. 2026-09-12T14:17:00+03:00>",
  title: "Whetzy · orquestador · siguiente iteración",
  description: "Whetzy: iteración autónoma del orquestador",
  notifyOnCompletion: false,
  prompt: "Lee C:\\Users\\feder\\Desktop\\Banco de preguntas\\python\\learning-engine\\docs\\ORCHESTRATOR.md completo y ejecútalo. Working directory: C:\\Users\\feder\\Desktop\\Banco de preguntas\\python\\learning-engine"
})
```

Anota el `taskId` en `## 6. Cadena de sesiones` del ledger. Si todo lo que queda
está `HUMAN-BLOCKED`, **no programes** — escribe en el chat qué necesita el humano.

La cadena se corta sola cuando el presupuesto de uso se agota (la sesión no
arranca, luego no programa la siguiente). El humano la reanuda con un clic o
borrando/reactivando el task. No intentes esquivar eso.

**5. Resumen en el chat**, corto: qué avanzó, qué se bloqueó, qué sigue, y el
`taskId` programado.

**No escribas un prompt para la siguiente sesión.** Este archivo es el prompt.
El estado vive en el ledger.

---

## VÍA REMOTA (opcional, cuando el humano la habilite)

`RemoteTrigger` está disponible en esta cuenta. Una rutina remota corre en la
nube sin necesitar la app abierta. Requiere que `Neopram/whetzy` esté conectado
en claude.ai. Cuando lo esté, la sesión que lo detecte crea la rutina con el
mismo prompt de arriba y un cron de 6 h, anota el `trigger_id` en `## 6`, y deja
de usar scheduled tasks locales. Hasta entonces: vía local.

---

## ARRANQUE

```
Pre-flight → Read docs/AUTONOMOUS_STATE.md → loop → cierre con auto-programación.
Escéptico con el ledger, honesto con la evidencia, tacaño con Opus.
```
