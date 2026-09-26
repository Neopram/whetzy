# Protocolo de verificación — código ↔ documentación ↔ producción

> Documento vivo nº 11 (índice en `README.md`). Nace el 2026-09-18 (sesión **bf**) por
> orden del dueño: *«verificar código vs documentación y actualizar de manera masiva,
> con lujo de detalles, para que los agentes no cometan un solo error»*. Se aplica
> primero como **Serie 20** del ledger y después **de forma permanente** a cada tarea.
> Cuando este protocolo y `ORCHESTRATOR.md` digan cosas distintas sobre *cómo se
> verifica*, manda este; sobre *qué se construye*, manda el ledger.

---

## 0. Por qué existe

El ledger ha arrastrado, documentado por las propias sesiones, afirmaciones que
nadie comprobó: «CI ✓» con ≥ 6 runs en rojo (sesión am), «17.8 cerrada» con una
guardia que moría antes de medir (ar), un frontend de producción tres fases viejo
(12.2), una fila 18.4 en `TODO` con su commit `bec734c` ya en `master` (hoy). Cada
una costó sesiones enteras construyendo sobre arena. El dueño tiene además un cupo
semanal de tokens y una fecha límite de presupuesto: **un error cuesta más que una
verificación**. De ahí las cinco reglas de §1.

---

## 1. Cinco reglas, sin excepciones

1. **Una afirmación = un comando.** Todo número, estado, URL, nombre de fichero o
   comportamiento que aparezca en un documento vivo tiene detrás un comando cuya
   salida lo prueba. Si no lo tiene, o se le pone, o se reescribe como narrativa
   fechada («la sesión X observó…»), o se borra. Un doc no puede afirmar lo que no
   puede demostrar.
2. **Evidencia pegada, no descrita.** «Pasan los tests» no vale; vale la última línea
   de `pytest -q` con el conteo y la fecha. La evidencia va al ledger en la misma
   fila, entre comillas invertidas, con el comando que la produjo.
3. **Verificación adversaria antes del `DONE`.** Nadie cierra su propia tarea. Un
   segundo agente (Haiku, prompt fijo de §7) intenta demostrar que la tarea **no**
   está hecha. Solo si fracasa en demostrarlo, la fila pasa a `DONE`.
4. **Lo que no se puede probar hoy se degrada, no se infla.** CI bloqueado por
   facturación (H.13/H.17) ⇒ la evidencia se llama `CI-LOCAL`, nunca «CI verde».
   Producción sin credenciales de prueba ⇒ «sin verificar en prod», nunca «desplegado».
5. **Nada de producción, nada de gasto, nada irreversible.** Igual que el contrato de
   autonomía de `ORCHESTRATOR.md`: DB de prod, Railway, Stripe live, tiendas, DNS,
   secretos y `~/.claude/settings.json` son del humano. La verificación **lee**
   producción por HTTP público; jamás se registra ni escribe en ella.

---

## 2. Modelos y tokens (ADR-14)

| Rol | Modelo | Regla |
|---|---|---|
| Hilo principal (orquestador) | Sonnet 4.6 (`settings.json`) | Decide, integra, commitea. No lee lo que puede delegar. |
| Workers de lectura | **Haiku 4.5** | Inventarios, diffs doc↔código, greps, verificación adversaria de tareas que no son contenido. No escribe nada que vea el alumno (enmienda a ADR-50, 2026-09-26). |
| Workers de contenido | **Sonnet 5** | Autoría, revisión adversaria y corrección de lecciones, preguntas, distractores y explicaciones, tras la puerta §7 del catálogo y `scripts/content_qa/`. |
| Workers de riesgo | Sonnet 4.6 | Solo si la tarea **escribe** en: `backend/app/core/**`, `backend/app/api/v1/endpoints/auth*.py`, `oauth*`, `billing*`, `entitlements*`, `backend/app/services/engine/**`, `backend/alembic/**`, `backend/app/main.py`, `frontend/src/services/api.ts`, `frontend/src/App.tsx`, cualquier fichero de `legal/`. |
| Opus / Fable | **Prohibidos** en sesiones autónomas | Si una tarea parece necesitarlos, es `HUMAN-BLOCKED`: describe qué decisión irreversible hay y sigue con otra. |

**Dieta de contexto** (lo que más tokens ahorra, en orden):

1. `AUTONOMOUS_STATE.md` se lee **por secciones** con `Read` + `offset/limit`:
   `## 0` (invariantes), `## 1` (fases), **solo la serie abierta de menor PRI**, `## 3`
   (HUMAN-BLOCKED) y las **últimas 3 filas** de `## 6`. Nunca el fichero entero.
   La tarea 20.6 lo adelgaza a < 60 KB moviendo la evidencia histórica a
   `docs/archive/LEDGER_HISTORY.md`.
2. `STATUS.md` (62 KB) y `docs/archive/` **no se leen** en sesiones autónomas.
3. Un worker recibe **rutas exactas y el criterio de aceptación**, nunca «lee el repo».
4. Un worker devuelve **≤ 300 palabras + la salida de los comandos**, no prosa.
5. Bloques de contenido: `Workflow` con Sonnet por fichero (escritor, revisor y corrector distintos); el orquestador no lee los
   ficheros producidos, corre las guardias (`pytest tests/content`,
   `check_question_bank.py`, `check_docs.py`) y lee solo los fallos.
6. Ninguna sesión reescribe un documento entero para cambiar tres líneas: `Edit`,
   no `Write`, sobre docs existentes. **En este PC las herramientas `Write`/`Edit`
   pueden fallar con `ENOENT …tmp…` en el árbol del proyecto (Controlled Folder
   Access)**: entonces se escribe en el scratchpad y se copia con `cp` (Git Bash),
   que sí está permitido. `git` también funciona.

---

## 3. Cerrojo de sesión y corte por límite de uso

Precedente: el 2026-09-16 dos sesiones (`as` y `at`) escribieron en la misma copia
de trabajo a la vez; una commiteó el trabajo de la otra y `git log` no distingue quién
hizo qué (`## 6` del ledger).

**Pre-flight 0b (obligatorio, antes de tocar un fichero):**

```
mcp__scheduled-tasks__list_task_runs  →  si hay OTRO run en `running`, sal.
Test-Path .session.lock  →  si existe y su timestamp < 6 h y no es tu sessionId, sal.
Escribe .session.lock = { sessionId, startedAt (ISO), model }.  Bórralo en tu último paso.
```

`.session.lock` está en `.gitignore` (tarea 20.0). Salir significa: **una línea** en
`## 6` («sesión X: cerrojo ocupado por Y, salgo») y terminar. Nada más.

**Corte por límite de uso:** no hay nada que hacer *durante* el corte. La protección
es *antes*: cada tarea cierra con su commit (ledger incluido) y ningún worker escribe
fuera de sus rutas. Así el siguiente disparo del cron (`23 */6 * * *`) encuentra un
árbol limpio o, como mucho, WIP de una sola tarea identificable por `git status`, que
el pre-flight 1 revisa, commitea con `git commit -- <rutas>` o descarta, y anota.

---

## 4. Inventario de afirmaciones: qué se verifica en cada documento

Salida de este paso (tarea 20.1): `docs/archive/verificacion/claims-YYYY-MM-DD.md`,
una tabla `doc | línea | afirmación | comando | resultado | acción`. `archive/` no manda,
es el almacén de evidencia; lo que manda es la corrección aplicada al doc vivo.

| Documento | Afirmaciones típicas | Cómo se prueban |
|---|---|---|
| `README.md` | Índice de docs vivos; comandos de arranque y verificación; URLs; modelo de deploy | `Test-Path` de cada doc listado; **ejecutar** cada comando del bloque «Verificación»; `Invoke-WebRequest` a cada URL; el modelo de deploy contra H.16 |
| `ARCHITECTURE.md` | Módulos, capas, flujos, tablas | `Get-ChildItem backend/app -Recurse -Filter *.py` vs. los módulos nombrados; `alembic heads` y nº de migraciones; tablas nombradas vs. `backend/app/models/*.py` |
| `API.md` | Endpoints, métodos, auth, cuerpos | `python -c "import json;print(len(json.load(open('openapi.json'))['paths']))"` tras `Invoke-RestMethod $B/api/v1/openapi.json`; diff **bidireccional** rutas doc ↔ OpenAPI = 0; cada gotcha (`.question.id`, JSON en registro) reproducido con una llamada real contra **local** |
| `RUNBOOK.md`, `RELEASE.md` | Comandos de deploy, migración, backup, restore, build nativo | Cada comando se ejecuta en local o se etiqueta «requiere cuenta/humano (H.x)»; ninguno queda sin una de las dos |
| `DECISIONS.md` | ADR vigentes y su reflejo en código | Por ADR, el `grep` o test que demuestra que el código lo cumple (p. ej. ADR-13: existe el provider `apple` y el hook; ADR-11: `check_content_sources.py` PASS; línea roja 5: `check-no-third-party` PASS) |
| `CATALOGO_MAESTRO.md` | Nº de tracks/Q/skills/lecciones/términos (§1); fuentes y licencias (§2.1, §2.2); certs (§3); coste (§6) | `python scripts/check_question_bank.py`; `python scripts/check_docs.py`; **cada URL** de §2.1/§2.2 resuelve (HTTP 200) y **la licencia declarada coincide con el `LICENSE` del repo** (script de 20.5); §6 recalculado con el conteo real |
| `ORCHESTRATOR.md`, `../CLAUDE.md` | Invariantes (HEAD de Alembic, modelo LLM, puertos, URLs), reglas de modelos | `alembic heads`; `grep GROQ_MODEL backend/app/core/config.py`; `docker ps`; coherencia con este protocolo y ADR-14 |
| `competitive-teardown.md` | Pesos §7.1 fijos; serie 30→36→42→43→44; evidencias por dimensión | Los pesos **no se tocan**; cada movimiento de la serie cita una fila del ledger que existe; ninguna dimensión puntúa capacidad sin usuarios (memoria del dueño) |
| `store/*.md` | Permisos, Data Safety, checklist 4.8/3.1.1, IDs de app | `frontend/capacitor.config.*`, `AndroidManifest.xml`, `PrivacyInfo.xcprivacy` vs. lo declarado; ADR-13 vs. checklist |
| `legal/*.md` | Nombre del servicio, planes y precios, procesadores, derechos, edad mínima, ley aplicable | Nombre = «Whetzy» (hoy dice «Learning Engine»); planes = los de `entitlements` y `billing` en código (hoy lista un «English Track $19.99-29.99» que **no existe**); procesadores = servicios reales del código (Railway, Cloudflare, Groq, proveedor de email, Stripe test); todo lo que no coincida se corrige **como error de hecho**; lo que sea criterio jurídico va a la Serie 21 y queda marcado `BORRADOR` |
| `AUTONOMOUS_STATE.md` | Cada fila | §5 de este protocolo |
| `STATUS.md`, `CHANGELOG.md` | Narrativa histórica | **No se reescriben hacia atrás.** Solo se añade una entrada de la verificación con lo encontrado |

---

## 5. Verificación del ledger, fila a fila

Para **cada** fila de `## 2`, en orden de serie:

| Estado en la fila | Qué se hace | Resultado posible |
|---|---|---|
| `DONE` | (a) el commit citado existe: `git cat-file -t <hash>`; si no cita commit, `git log --all --grep="<ID>"`; (b) **se vuelve a ejecutar** la evidencia del criterio (test, guardia, HTTP local); (c) verificador adversario §7 | Sigue `DONE` con evidencia **fechada de hoy** · o pasa a `REGRESIÓN` (nueva fila PRI 0 con el fallo) · o pasa a `DONE (sin evidencia reproducible)` y se abre tarea para ponérsela |
| `TODO` | ¿Sigue haciendo falta? ¿Ya la hizo otro commit (caso 18.4 / `bec734c`)? ¿Sus dependencias existen? | `TODO` confirmada · o `DONE` con la evidencia del commit que la cerró · o `CADUCADA` (con la razón) |
| `PARCIAL` | Se cuantifica: qué % y qué falta, en una línea | `PARCIAL (n/m: …)` o `DONE` o `TODO` |
| `BLOCKED (x)` | ¿`x` sigue bloqueando? | Se mantiene, o pasa a `TODO` |
| `HUMAN-BLOCKED` | ¿Sigue necesitando al humano? (H.1, H.11, 12.2, 16.17, 17.1x, H.15 parte 1 y 3, H.SEED-glosario ya no) | Se **cierra** con fecha y evidencia, o se mantiene con el texto **acortado** a: bloqueo · qué preparó el agente · qué debe hacer el humano · coste en € |

Reglas de escritura del ledger tras verificar:

- Una fila `DONE` lleva: `DONE — <hash corto> — <comando> → <salida corta> (<fecha>)`.
- La evidencia larga (párrafos, logs) se **mueve** a `docs/archive/LEDGER_HISTORY.md`
  con el ID como ancla, y en la fila queda un puntero (tarea 20.6).
- `## 1. Estado por fase` se recalcula desde las filas, no a ojo: % = DONE / (todas − HUMAN-BLOCKED).
- `## 0` (invariantes) y su fila `Contenido` se tocan **solo** con `check_docs.py` en verde después.

---

## 6. Cambios de código descubiertos durante la verificación

- Un bug de producto encontrado verificando **no se arregla de paso**: se abre fila
  PRI 0 en la serie abierta con la reproducción exacta, y se arregla como tarea
  propia, con test primero.
- Un doc que miente sobre el código se corrige en el doc; un código que contradice
  una decisión (`DECISIONS.md`) se corrige en el código, salvo que la decisión esté
  `PROPUESTA` — entonces se anota y se pregunta en `HUMAN-BLOCKED`.
- Todo commit de verificación: `verify(<ID>): <qué se probó> — <resultado>` y toca
  **solo** los ficheros de esa fila. `git commit -- <rutas>` explícitas, nunca `git add -A`.
- **Un commit en `master` despliega** (H.16), y **solo el dueño fusiona** (ADR-45): la
  sesión acumula sus commits de verificación en su rama y hace **push de la rama**
  (nunca de `master`) al cerrar cada oleada, con las cuatro guardias en verde (`pytest tests/content`,
  `check_question_bank.py`, `check_docs.py`, `npm run build`). Un push de docs
  también reinicia Railway (~60-90 s de 502 para quien esté dentro).

---

## 7. Verificador adversario (obligatorio para cada `DONE`, ADR-20)

Un `Agent` con `model: "haiku"`, `subagent_type: "Explore"` (solo lectura), con este
prompt **literal** (rellenando `<>`):

```
Tu única misión es demostrar que la tarea <ID> del ledger NO está hecha, o que su
evidencia es falsa, incompleta o no reproducible. No confíes en resúmenes: ejecuta
los comandos. Contexto: criterio de aceptación = «<criterio literal de la fila>».
Evidencia que se te presenta = «<evidencia literal>». Rutas que dice haber tocado =
<rutas>. Repo: C:\Users\feder\Desktop\Banco de preguntas\python\learning-engine.

Haz, en este orden y sin saltarte ninguno:
1. `git show --stat <hash>` — ¿toca esas rutas? ¿Existe el hash?
2. Vuelve a ejecutar cada comando de la evidencia. Pega las últimas 5 líneas de cada uno.
3. Busca la forma más barata de romperlo: un input vacío, el otro idioma, el caso
   límite del criterio, la ruta que el criterio nombra y el commit no toca.
4. Si el criterio nombra un número (Q, %, ms, KB), mídelo tú.
5. Si hay UI, comprueba que la cadena i18n existe en ES **y** EN y que no hay
   fallback silencioso al otro idioma.

Devuelve EXACTAMENTE este formato, ≤ 250 palabras:
VEREDICTO: CONFIRMADA | REFUTADA | NO REPRODUCIBLE
PRUEBAS: <comando → salida corta>, una por línea
FALLO ENCONTRADO: <uno, el más grave, o «ninguno»>
```

Reglas:

- `CONFIRMADA` → el orquestador escribe `DONE` con la evidencia **del verificador**
  (no la del worker) y la fecha.
- `REFUTADA` → la fila vuelve a `TODO` con el fallo pegado; se reasigna; el worker
  original no la verifica nunca.
- `NO REPRODUCIBLE` → `BLOCKED (evidencia)`; se abre tarea para hacerla reproducible.
- Dos refutaciones seguidas del mismo worker en la misma sesión → esa tarea pasa a
  Sonnet aunque no esté en la lista de riesgo.
- El verificador **no escribe** nada en el repo. Si necesita un script, va al scratchpad.

---

## 8. Disciplina de cambio (resumen operativo)

1. Cerrojo (§3) → pre-flight de `ORCHESTRATOR.md` → leer el ledger por secciones (§2).
2. Elegir la fila `TODO` de menor PRI con dependencias `DONE`. Si es de la Serie 20,
   seguir §4-§5; si no, implementar con test primero.
3. Worker (Sonnet si escribe contenido o toca la lista de riesgo; Haiku si solo lee) con rutas exactas y criterio literal.
4. Guardias locales: las del `README.md` §Verificación que apliquen a las rutas tocadas.
5. Verificador adversario §7.
6. Fila del ledger + commit de la tarea (`-- <rutas>`), sin push.
7. Cada 3 `DONE`: scorecard (comandos de `ORCHESTRATOR.md` §CIERRE punto 2) en una fila.
8. Fin de sesión: cuatro guardias en verde → **un** push → borrar `.session.lock` →
   fila en `## 6` con: tareas cerradas, refutaciones, tokens aproximados, siguiente tarea.

---

## 9. CI ciego (H.13 / H.17): qué cuenta como evidencia

Mientras `gh run list` muestre runs que mueren en < 10 s por facturación:

- `scripts/verify_ci_local.ps1` (tarea 20.7) ejecuta **exactamente** los pasos de
  `.github/workflows/ci.yml`, en el mismo orden, con las mismas versiones, y escribe
  `ci-local-<fecha>.log` en el scratchpad. La fila del ledger cita `CI-LOCAL <fecha>
  <exit code>` **y** el run id de Actions que falló, para que nadie lo confunda con CI.
- «CI ✓» / «CI verde» quedan **prohibidos** en el ledger hasta que un run real
  termine en `success`. La regla cero de `ORCHESTRATOR.md` lo recoge.
- Para reducir minutos cuando Actions vuelva: e2e solo en `workflow_dispatch` y
  nightly; backend y frontend en cada push con caché de dependencias (20.7).

---

## 10. Invariantes mecánicas reutilizables

Copiar/pegar; cada una es una guardia que ya existe o que 20.9 añade a `check_docs.py`.

```powershell
# Banco y docs
python scripts/check_question_bank.py
python scripts/check_docs.py
python scripts/check_content_sources.py            # URLs de fuentes resuelven
# Backend
Set-Location backend; python -m pytest -q; python -m mypy app --strict --ignore-missing-imports; ruff check app tests
python -m alembic heads; python -m alembic check    # una sola head; modelos = migraciones
# Frontend
Set-Location ../frontend; npx tsc -b --force; npx vitest run; npm run build
node scripts/check-no-third-party.mjs               # línea roja 5 sobre dist/
node scripts/check-e2e-target.mjs                   # e2e nunca contra prod
npm run check:deployed                              # lo servido = lo construido (6 checks)
# API ↔ docs (20.3)
python scripts/check_api_docs.py                    # rutas de API.md == OpenAPI, bidireccional
# Repos de fuentes (20.5)
python scripts/check_source_licenses.py             # LICENSE del clon == licencia en §2.2
# Idiomas (23.1)
python scripts/check_i18n_parity.py                 # sin fallback silencioso ES↔EN
# Producción (solo lectura)
$B="https://api-production-9751.up.railway.app"; Invoke-RestMethod "$B/health"; Invoke-RestMethod "$B/health/ready"
(Invoke-RestMethod "$B/api/v1/openapi.json").paths.PSObject.Properties.Name.Count
(Invoke-WebRequest "https://whetzy.com/" -UseBasicParsing).Content -match 'canonical'
```

---

## 11. Errores que ya ocurrieron → regla que los impide

| Ocurrió (sesión) | Regla |
|---|---|
| «CI ✓» en el ledger con Actions en rojo (am, ao) | §9: `CI-LOCAL` o run id `success`; nada más |
| Guardia 17.8 que moría con `UnicodeEncodeError` en la rama de fallo (ar) | Toda guardia nueva se prueba **en los dos sentidos**: con el defecto presente debe fallar |
| Dos sesiones en el mismo árbol (as/at) | §3 cerrojo; `git commit -- <rutas>`; `git log -1` antes de dar por tuyo un commit |
| Track a medias en `master` que rompió el loader en prod (at, track12) | Un bloque = un commit verde con las 3 guardias de contenido; nunca un track parcial |
| Proxy de vite a producción sin commitear (H.15) | `check-e2e-target.mjs` en `pretest:e2e`; e2e jamás contra prod sin humano |
| Clave real en `docs/STATUS.md` (13.1) | `gitleaks` en pre-commit (22.4); ningún valor con forma de secreto en docs |
| Python y las herramientas `Write`/`Edit` no escriben en el árbol por Controlled Folder Access (ar, bf) | Scripts y ficheros se escriben en el scratchpad y se copian con `cp`; `git` sí funciona |
| Fila 18.4 `TODO` con commit `bec734c` en `master` (bf) | §5: cada `TODO` se contrasta con `git log --grep` antes de asignarse |
| Worker que informa «hecho» sin que lo esté (varias) | §7: nadie cierra su propia tarea |
| Sesión programada que intenta levantar dev servers (ar) | El cron elige backend/contenido/tests; UI y capturas solo en sesión interactiva |

---

## 12. Definición de DONE de la Serie 20

La Serie 20 está cerrada cuando, en un mismo commit y con `.session.lock` liberado:

1. `claims-<fecha>.md` en `archive/verificacion/` cubre **todas** las líneas con
   afirmaciones de los 11 docs vivos + `store/` + `legal/` + `CLAUDE.md`, y cada
   una tiene `resultado` y `acción`.
2. Cada fila del ledger tiene estado verificado con fecha de la Serie 20.
3. `check_docs.py`, `check_question_bank.py`, `check_api_docs.py`,
   `check_source_licenses.py` y `verify_ci_local.ps1` terminan con exit 0.
4. `AUTONOMOUS_STATE.md` < 60 KB y `LEDGER_HISTORY.md` contiene lo movido.
5. `## 1. Estado por fase` recalculado desde las filas.
6. `STATUS.md` tiene una entrada «Serie 20 — verificación masiva» con: nº de
   afirmaciones, nº corregidas, nº de regresiones abiertas, nº de HUMAN-BLOCKED cerrados.
7. Ninguna fila dice «CI ✓» sin run id `success`.
