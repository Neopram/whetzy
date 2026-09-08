# Whetzy — Orquestador autónomo

> Idempotente. Cualquier sesión que lo lea sabe dónde está el proyecto leyendo
> `docs/AUTONOMOUS_STATE.md`, y sabe dónde dejarlo escribiendo ahí mismo.
>
> **Se ejecuta sin intervención.** Modelo (Sonnet 4.6) y permisos (bypass)
> vienen de `~/.claude/settings.json`. La continuidad la garantiza un scheduled
> task recurrente `whetzy-orch-*` que este mismo archivo mantiene vivo y borra
> cuando termina. No hay nada que el humano deba pulsar entre sesiones.

---

## MISIÓN

Llevar Whetzy a calidad de mercado: 9 fases completas, base de datos y backend
sin defectos conocidos, frontend con diseño de primer nivel, cobertura de tests
real, documentación coherente, cumplimiento verificable de App Store y Play Store.

No cabe en una sesión. Cabe en muchas, si cada una deja el sistema mejor y el
ledger honesto. La siguiente sesión llega sola.

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

El hilo principal corre en **Sonnet 4.6** (lo fija `settings.json`; no lo cambies).
Tú decides el modelo de cada subagente:

| Modelo | Para | Cómo |
|---|---|---|
| **Haiku** | Inventarios, greps masivos, leer 20 archivos, scaffolding repetitivo, formateo | `Agent` + `model: "haiku"` |
| **Sonnet** | Implementar, verificar, integrar, decidir lo reversible | Tú, o `Agent` + `model: "sonnet"` como worker |
| **Opus** | Solo arquitectura irreversible: diseño del modelo DKT, threat model, sistema de diseño, límites de servicio | `Agent` + `model: "opus"`. **Máximo 2 por sesión.** Cada uso va a la bitácora |

Antes de Opus: *¿revertir esto costaría semanas?* Si no, Sonnet.

---

## CONTRATO DE AUTONOMÍA

### Sin preguntar
Escribir, refactorizar, borrar código propio · crear y correr tests · migraciones
Alembic **en local** · `git commit` / `git push` a `master` · instalar dependencias
del proyecto · levantar dev servers y ejercitar la app en el Browser pane ·
reorganizar docs · borrar código muerto **tras** grep que pruebe cero referencias ·
linters, type checkers, formatters y sus fixes · gestionar el scheduled task
`whetzy-orch-*`.

### Detente y escribe en `HUMAN-BLOCKED`
Operaciones destructivas sobre la **DB de producción** · deploy a Railway (manual —
prepáralo y déjalo listo) · claves live de Stripe o cualquier gasto · submisión a
stores · DNS o dominio · datos de usuarios reales · rotar o exponer secretos ·
tocar `~/.claude/settings.json`.

**La regla:** reversible con `git revert` → hazlo. Si no → prepáralo, documéntalo,
sigue con otra cosa. Entre dos diseños razonables: el más simple, a la bitácora,
sigue.

---

## PRE-FLIGHT (solo la primera iteración)

Si algo falla aquí, **arreglarlo es la primera tarea de la sesión** y va al ledger.

### 0. Continuidad — antes que nada
```
mcp__scheduled-tasks__list_scheduled_tasks
→ localiza el task cuyo taskId empieza por "whetzy-orch"
```
- Si tiene `fireAt` (one-shot) o `enabled: false`:
  `update_scheduled_task({ taskId, cronExpression: "23 */6 * * *", enabled: true })`
- Si no existe: `create_scheduled_task` con ese cron y el prompt de
  `C:\Users\feder\.claude\scheduled-tasks\whetzy-orch-20260911-0730\SKILL.md`
- Anota el resultado en `## 6. Cadena de sesiones` del ledger

Esto es lo que hace que un corte por límite de uso no rompa nada: el siguiente
disparo continúa donde el ledger diga. Una sesión que no puede arrancar no gasta;
una que arranca sin trabajo sale en segundos.

### 1-4. Estado del sistema
```powershell
# 1. Repo limpio. Si hay cambios huérfanos de una sesión cortada: revisa, commitea o descarta, anótalo.
git status --short

# 2. Producción responde y coincide con el ledger
$B = "https://api-production-9751.up.railway.app"
Invoke-RestMethod "$B/health"
(Invoke-RestMethod "$B/api/v1/openapi.json").paths.PSObject.Properties.Name.Count

# 3. DB local arriba (si no: docker compose up -d desde la raíz)
docker ps --filter "name=db" --format "{{.Names}} {{.Status}}"

# 4. La suite colecta sin errores de import
Set-Location backend; python -m pytest -q --co 2>&1 | Select-Object -Last 3
```

Después: `Read docs/AUTONOMOUS_STATE.md`. Escéptico — el ledger dice lo que la
sesión anterior *creyó*; producción dice lo que *es*.

---

## EL LOOP

### 1. Seleccionar
Tarea `TODO` de menor `PRI`, desempate por ID. Comprueba `## Dependencias`; si
alguna no está `DONE`, salta a la siguiente. Márcala `DOING` y commitea el ledger
(así un corte deja rastro de qué estaba en curso).

Si algo de `PRI` alto se desbloquea en < 20 min, desbloquéalo primero.

### 2. Paralelizar cuando toque
Si la tarea está en un **grupo paralelo** del ledger y sus hermanas también están
`TODO`, lanza workers — un `Agent` por tarea, **en un solo bloque de tool calls**:

```
Agent({
  subagent_type: "general-purpose",
  model: "sonnet",          // "haiku" si es scaffolding o inventario
  run_in_background: true,
  prompt: "<ID y texto de la tarea>
           <criterio de aceptación literal del ledger>
           <archivos que puede tocar — SOLO esos>
           Devuelve: archivos cambiados, evidencia ejecutable pegada, y estado
           propuesto (DONE/BLOCKED con razón). NO commitees. NO toques el ledger."
})
```

- **Máximo 3 simultáneos**
- Cada worker toca **solo** los archivos de su tarea; la disjunción la garantiza
  el ledger. Si dudas, no paralelices
- Los workers no commitean ni escriben el ledger. Solo tú
- Al volver cada uno: revisa su diff, corre **la suite completa**, y solo entonces
  commitea
- `isolation: "worktree"` solo para refactors amplios sin disjunción garantizada;
  luego `git merge`

### 3. Ejecutar
Leer antes de escribir · tests **en el mismo paso** que el código · correr los
tests · si toca UI, `preview_start` con `backend` / `frontend` (ya en
`.claude/launch.json`), ejercitar, leer consola y red, screenshot

### 4. Verificar
Exactamente la evidencia del criterio de aceptación. Si no se cumple: arregla o
`BLOCKED` con detalle. No avances.

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
**Cada 3 tareas `DONE`**, mide el scorecard (comandos en CIERRE, paso 2) y
commitea la fila — así un corte nunca pierde la medición.

### 7. Volver a 1
**Sin cierre voluntario.** Sigue hasta que el backlog ejecutable se agote o la
plataforma te corte. Un corte no pierde nada: el ledger va commiteado tras cada
tarea y el cron reanuda.

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

Rediseño: mírala en el browser → propón → implementa → screenshot antes/después
en el ledger.

---

## CIERRE — solo cuando el backlog ejecutable se agote

Llegas aquí únicamente si todo está `DONE` o `HUMAN-BLOCKED`. Si la plataforma
te corta antes, no pasa nada: el cron continúa.

**1. Nada sin commitear.**

**2. Medir de verdad** y añadir la fila al scorecard:
```powershell
Set-Location backend
python -m pytest --cov=app --cov-report=term-missing -q 2>&1 | Select-Object -Last 20
python -m mypy app 2>&1 | Select-Object -Last 3
ruff check app 2>&1 | Select-Object -Last 3
Set-Location ../frontend
npx tsc --noEmit 2>&1 | Select-Object -Last 3
npx vitest run --coverage 2>&1 | Select-Object -Last 20
```

**3. Actualizar** `## 1. Estado por fase`. Commitear.

**4. Terminar la cadena:**
`mcp__scheduled-tasks__delete_scheduled_task({ taskId: "<whetzy-orch-…>" })`
Anótalo en `## 6`. La cadena ha terminado porque el trabajo automatizable ha
terminado.

**5. Resumen en el chat**, corto: qué quedó, y **exactamente** qué necesita el
humano de la cola `HUMAN-BLOCKED`, en orden de valor.

---

## VÍA REMOTA — la única forma de no depender de la app abierta

`RemoteTrigger` responde en esta cuenta. Schema sondeado (sesión s): el `create`
exige `session_request` (con `worker` obligatorio) o `job_config` con forma
"ccr". El preflight del servidor falla sin repositorio conectado y entorno.

**Gate humano, una sola vez:** en claude.ai, conectar `Neopram/whetzy` y crear un
entorno. Es `H.7` en el ledger.

**Cuando una sesión lo encuentre resuelto:** termina el schema con 1-2 `create`
de prueba, crea la rutina con este mismo prompt y cron de 6 h, anota el
`trigger_id` en `## 6`, y **borra el task local** para no duplicar. Desde ahí la
cadena corre en la nube, con la app cerrada.

---

## ARRANQUE

```
Continuidad → pre-flight → Read docs/AUTONOMOUS_STATE.md → loop sin cierre
voluntario → cuando no quede nada ejecutable, borrar el task y reportar.
Escéptico con el ledger, honesto con la evidencia, tacaño con Opus.
```
