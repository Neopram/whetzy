# Plan — Experiencia avanzada: interfaz y experiencia al nivel de Brilliant y Duolingo (serie 46)

> **Nota del 2026-10-23 (revisión completa de la UI, PR #327).** La línea base del §1 describe `master` del 17 al 20 de
> octubre y ya no es cierta en varios puntos: existen `frontend/src/widgets/` (tres widgets, 40.2), sonido y
> vibración (`lib/feedbackFx.ts`), un solo sistema de tokens (46.4) y la regresión visual (`e2e/visual.spec.ts`,
> 64 capturas). D3 se decidió **encendido** (ADR-67, 46.9). El estado de cada fila lo dice el ledger, no este plan.

> **Normativo-vivo.** Pedido del dueño del 2026-10-17 («plan brutal» de interfaz y experiencia). Lo
> ejecuta la sesión «Progreso del proyecto y oportunidades de mercado» con el prompt de
> `docs/PROMPT_UI_AVANZADA.md`, **después** de la serie 45 (`PLAN_CORREO_ALTA.md`) y sin competir
> con la 44 (`PLAN_BACKOFFICE.md`) por los mismos ficheros a la vez. Las filas nuevas son la
> **serie 46**; las de widgets y tutor ya existen en la **serie 40** (`PLAN_EXPERIENCIA.md`) y se
> reutilizan tal cual: una fila del ledger = un plan (ADR-48).
>
> El número de serie (46) es provisional. La sesión que incorpore este plan lo confirma con
> `grep -n '^### 4' docs/AUTONOMOUS_STATE.md | tail -1`. No cambia ninguna ADR: ADR-52 (modelos),
> ADR-62 (contenido en espera) y ADR-45 (rama + PR) siguen mandando.

## 0. Línea base, medida el 2026-10-17 sobre `master` `3d10daa`

Todo lo de esta sección se comprobó con comandos en esta sesión; donde no, se dice.

**Lo que ya hay y vale:**

- Sistema visual con tokens `--le-*` (`frontend/src/styles/design-tokens.css`, 264 líneas: color,
  tipografía Inter / Bricolage Grotesque / JetBrains Mono, espaciado, radios, sombras, transiciones,
  z-index, tema claro en `:root[data-theme="light"]`). Guía: `docs/design/identidad.md`.
- Port design-v2 con 26 capturas reales (`docs/ui-snapshots/design-v2/`, 2026-10-01).
- axe 0 violaciones en auth, landing, privacy, home, perfil, estadísticas, liga, rutas y feedback del
  quiz (`frontend/e2e/accessibility.spec.ts`).
- El motor **se ve**: «Practicar lo débil · Prob. acierto 63 %» en la pregunta; «Tu mayor palanca» y
  dominios por peso en Preparación (`07-preparacion-390.png`).
- framer-motion con helper compartido (`frontend/src/lib/motion.ts`: `springs`, `correctVariants`,
  `wrongVariants`, `listItemVariants`…) y `MotionConfig reducedMotion="user"` (`App.tsx:560`).
- Presupuestos de peso vigilados: `frontend/scripts/check-bundle.mjs:31-36` (inicial ≤ 300 KB gz por
  chunk y ≤ 350 KB en total; lazy ≤ 1.200 KB).

**Lo que falta o está mal:**

| Hecho | Evidencia |
|---|---|
| `frontend/src/widgets/` no existe; el tipo `interactive` no aparece en `backend/app` ni en `scripts/check_question_bank.py` | `ls frontend/src/widgets` → no existe; `KNOWN_TYPES` cerrado en `check_question_bank.py:100-102`; unión del frontend en `services/api.ts:476-486` |
| Serie 40 a **0/13** | `python scripts/ledger.py series 40` |
| La animación de acierto es un overlay **fijo y centrado** que tapa el código 1,4 s y **no respeta `prefers-reduced-motion`** (el `Player` de Lottie se monta siempre) | `QuizScreen.module.css:409-417` (`position: fixed; inset: 0; z-index: 999`); `QuizScreen.tsx:204-213` y `:841-845`; `06b-quiz-feedback-390.png` |
| El toast «+XP» pisa la barra de progreso; la fuente sale como URL cruda | `06b-quiz-feedback-390.png`; `components/quiz/SourceLine.tsx` |
| Cero vibración y cero sonido | `grep -rni "vibrate\|Haptics\|AudioContext\|new Audio" frontend/src frontend/package.json` → 0 |
| Dos sistemas de tokens: `theme/tokens.css` (`--color-*`) sigue en 10 `.module.css` | `grep -rl "var(--color-" frontend/src --include="*.module.css"`: `DistributionBanner`, `LoadingState`, `TabsNav`, `EmptyState`, `ErrorState`, `MonacoCodeEditor`, `PlaygroundScreen`, `LandingScreen`, `PublicProfileScreen`, `AdminScreen` |
| Sin regresión visual | `grep -rn toHaveScreenshot frontend/e2e` → 0; `scripts/ui-snapshots.mjs` captura sin comparar |
| Sin usuarios medidos; 40.13 (medir la superación) abierta | ledger |
| El ledger está a **60.965 B de 61.440** | `wc -c docs/AUTONOMOUS_STATE.md`; límite en `scripts/check_docs.py:317` |

**Rúbrica de interfaz y experiencia** (pesos fijos de este plan; la de `competitive-teardown.md` §7.1
mide el producto entero y no se toca):

| Dimensión | Peso | Whetzy hoy | Meta | Cómo se mide |
|---|---|---|---|---|
| Sistema visual | 0,15 | 65 | 85 | un solo namespace de tokens; contraste AA verde; capturas |
| Animación y pulido | 0,15 | 35 | 70 | feedback dentro de la tarjeta; reduced-motion respetado; haptics/sonido opt-in |
| Superficie interactiva | 0,20 | 40 | 70 | widgets `interactive` en producción con e2e |
| IA dentro de la experiencia | 0,15 | 55 | 75 | tutor que señala y habla, con fuentes |
| Accesibilidad e i18n | 0,10 | 85 | 90 | axe 0 también en widgets; ES/EN |
| Rendimiento y sensación nativa | 0,10 | 55 | 70 | LCP < 2,5 s 4G; presupuestos; haptics en Capacitor |
| Onboarding y retención | 0,15 | 50 | 75 | primer minuto medido con PostHog |
| **Total** | 1,00 | **≈ 53** | **≥ 75** | |

Las notas de Whetzy son juicio de la sesión sobre evidencia observada, sin usuarios. Las de los
rivales (Duolingo ≈ 89, Brilliant ≈ 87, DataCamp ≈ 72 con la misma rúbrica) son **estimación de
memoria, no medida**; 46.6 las sustituye por una captura con URL y fecha antes de usarlas en público.

## 1. Qué significa «brutal» aquí

Igualar lo visible y superar en lo que Whetzy ya tiene de estructura: cada widget es un ítem del
motor (BKT, FSRS, Elo), cada acción del tutor cita su fuente, todo en ES y EN, accesible y ligero
(líneas rojas del `ORCHESTRATOR.md`). **Ninguna frase de superioridad sale a la landing, a un
listing ni a una doc pública hasta que 46.6 cierre 40.13** (`PLAN_EXPERIENCIA.md` §0).

## 2. Olas y filas

Una fila = un PR ≤ ~400 líneas, base `master`, worktree propio, evidencia pegada. El orden entre
olas es estricto; dentro de una ola, las filas pueden ir en paralelo si no comparten ficheros.

### Ola 0 — Arranque

| Fila | Qué | Ficheros | Criterio de DONE |
|---|---|---|---|
| 46.0 | **Dieta del ledger ≥ 2 KB** y alta de la serie 46. Mover el texto largo de filas `DONE` de series cerradas a `docs/archive/LEDGER_DETALLE_<serie>.md`, dejando en el ledger `ID \| DONE \| commit`; después, filas 46.1–46.6 compactas (≤ 160 B cada una) | `docs/AUTONOMOUS_STATE.md`, `docs/archive/**`, `docs/INVENTARIO_DOCS.md` (una línea por archivo nuevo) | `python scripts/ledger.py check` y `python scripts/check_docs.py` verdes; `wc -c` ≤ 59.400 B; `ledger.py fases --write` ejecutado |

### Ola 1 — Pulido del quiz y primer minuto (visible en una semana)

| Fila | Qué | Ficheros | Criterio de DONE |
|---|---|---|---|
| 46.1 | **Feedback sin tapar.** La animación pasa del overlay fijo a **dentro de la tarjeta de feedback** (≤ 72 px, junto a «¡Correcto!»); con `prefers-reduced-motion` el `Player` **no se monta**; el toast «+XP» deja de pisar la barra de progreso (se ancla al `xpBadge` con `correctVariants` de `lib/motion.ts`); la fuente se muestra como etiqueta corta + «Leer fuente» (ya existe `SourceLine`; truncado por CSS) | `pages/QuizScreen.tsx`, `pages/QuizScreen.module.css`, `components/quiz/SourceLine*`, `components/common/Toast*` | test unitario: con reduced-motion no hay `Player` en el DOM; `accessibility.spec.ts` (feedback) sigue en 0; captura 390 px en `docs/ui-snapshots/46.1/` con README |
| 46.2 | **Haptics y sonido, opt-in.** `navigator.vibrate` en web y `@capacitor/haptics` en nativo para acierto, fallo y racha; sonido **sintetizado** con `AudioContext` (tres tonos cortos; sin ficheros ni licencias); interruptores en Perfil, persistidos como el de «¿Por qué?»; **apagados por defecto** salvo D3 | `lib/feedbackFx.ts` (nuevo), `pages/ProfileScreen.tsx`, `pages/QuizScreen.tsx` (una llamada), `i18n/{es,en}/producto.json`; `frontend/package.json` y lockfile en PR aparte **46.2b** (compartidos) | tests: con el interruptor apagado no se llama a `vibrate` ni se crea `AudioContext`; `check-prerender.mjs` y `check-no-third-party.mjs` verdes; nada en SSR |
| 46.3 | **Estados y primer minuto.** `EmptyState`, `LoadingState`, `ErrorState` migrados a `--le-*` y con una sola familia visual (icono, título, acción); en Home, «Tu mayor palanca» (hoy solo en Preparación) sube a la primera tarjeta; la prueba de nivel se presenta en el onboarding con lo que mide y cuánto dura | `components/common/*State*`, `pages/HomeScreen.tsx`, `pages/OnboardingScreen.tsx`, `producto.json` | e2e: un usuario recién registrado ve «mayor palanca» o «prueba de nivel» sin hacer scroll a 390 px; axe 0 en Home y Onboarding |
| 46.1b | **`events[]` en la respuesta del quiz** (§6.3): `QuizAnswerResponse.events: list[FxEvent]` con nivel, insignia, misión, multiplicador de combo y racha en hito, construido con lo que el servidor ya calcula | `backend/app/schemas/session.py`, `backend/app/services/quiz.py`, `frontend/src/services/api.ts`, `docs/API.md` | tests de §6.3; OpenAPI y `docs/API.md` al día |
| 46.7 | **Resumen de sesión (nivel 3) y ceremonias (nivel 4)** (§6.0, §6.2): nivel, insignia, racha 7/30/100, con «Saltar» y máx. 1 por sesión; el resto, tarjetas en el resumen; ascenso de liga **bloqueado** hasta que el servidor lo aplique | `components/quiz/Ceremony*`, `pages/QuizScreen.tsx`, `producto.json` | e2e: dos eventos de nivel 4 en una sesión → una ceremonia y una tarjeta; `fx_emitted{4,…,skipped}` medido |

### Ola 2 — Widgets interactivos (serie 40, filas existentes)

| Fila | Qué | Ficheros | Criterio de DONE |
|---|---|---|---|
| 40.1 | Tipo `interactive` = `{widget, params, target, checker}`: entra en `KNOWN_TYPES` con validación de esquema; `backend/app/services/widgets/checkers.py` con **los mismos checkers** que el cliente; test que muta un checker y pone en rojo la discrepancia cliente↔servidor; unión `QuestionPublic` ampliada; rama de render en `QuizScreen` | `scripts/check_question_bank.py`, `backend/app/services/widgets/**`, `backend/tests/unit/test_widget_checkers.py`, `frontend/src/services/api.ts` (**solo tras 45.4 en `master`**), `pages/QuizScreen.tsx` | el criterio literal de 40.1 en el ledger |
| 40.2 | **Piloto**: 3 widgets (búsqueda binaria, CIDR, JOIN) en `frontend/src/widgets/{binarySearch,cidr,sqlJoin}/` con contrato `render / serialize / check` y test de contrato por widget; carga perezosa; 10 ítems ES/EN por widget **solo con D1** | `frontend/src/widgets/**`, `check-bundle.mjs` (+ `WIDGET_CHUNK_KB = 30`), `content/questions/**` (si D1) | e2e móvil (390) y escritorio (1280); axe 0; ≤ 30 KB gz por widget; LCP < 2,5 s en 4G simulado; sin piloto verde no hay 40.3 |
| 40.3 / 40.4 | Biblioteca de 15 widgets mapeados a dominios de certificación; widget ↔ código en los dos sentidos (Pyodide, sql.js, Worker JS) | `frontend/src/widgets/**` | criterios literales de 40.3 y 40.4 |

### Ola 3 — Tutor que señala y habla (serie 40)

| Fila | Qué | Ficheros | Criterio de DONE |
|---|---|---|---|
| 40.5 | Acciones estructuradas del tutor (`highlight_line`, `mark_node`, `animate_step`) validadas contra un esquema en el backend; acción fuera de esquema rechazada (test); sin grounding lo dice (línea roja 2) | `backend/app/services/ai/**`, `components/quiz/WhyButton.tsx`, widgets | criterio literal de 40.5 |
| 40.6 | Voz ES/EN: TTS con `speechSynthesis`; STT con Groq Whisper, pulsar para hablar, consentimiento explícito, audio no almacenado (H.49) | `lib/voice.ts` (nuevo), Perfil; **`legal.json` es de S4**: el cambio de la política de privacidad se propone en «Fuera de alcance», no se edita | criterio literal de 40.6 (WER en ES medido con muestras propias; retención de Groq leída con URL) |

### Ola 4 — Sistema visual único, regresión visual y medición

| Fila | Qué | Ficheros | Criterio de DONE |
|---|---|---|---|
| 46.4 | **Un solo sistema de tokens.** Migrar los 10 `.module.css` de `--color-*` a `--le-*`, borrar `theme/tokens.css`, actualizar `docs/design/identidad.md`; ampliar `src/test/tokens.contraste.test.ts` a los pares nuevos (mutarlo en rojo antes de aceptarlo) | los 10 ficheros de §0, `styles/global.css`, `theme/tokens.css`, `docs/design/identidad.md` | `grep -rl "var(--color-" frontend/src` → 0; contraste verde; capturas antes/después en `docs/ui-snapshots/46.4/` |
| 46.5 | **Regresión visual.** `toHaveScreenshot` en 8 pantallas × 390/1280 × ES/EN × oscuro/claro, con máscaras sobre cifras vivas (XP, racha, fechas); corre en el **nivel 2** (`ci_local.sh`), nunca en el hook | `frontend/e2e/visual.spec.ts`, `frontend/e2e/__screenshots__/`, `scripts/ci_local.sh` (compartido: PR aparte y mínimo) | la suite se pone en rojo al cambiar un color de token a propósito y se restaura; tiempo añadido al nivel 2 medido y anotado |
| 46.6 | **Medición.** ~~PostHog `session-recording`~~ (lo impide ADR-68 punto 2: nada de terceros en el cliente; enmienda del 2026-10-21) → embudo de pago propio (`checkout_viewed`/`checkout_opened` por plan, anónimos) y una encuesta de una pregunta tras el primer quiz (tres respuestas cerradas, sin usuario, no sale con GPC/DNT), en `GET /analytics/conversion`; re-puntuación de la rúbrica de §0 con una evidencia por celda; captura de la interfaz de Brilliant y Duolingo con URL y fecha → **cierra 40.13** | `frontend/src/lib/analytics*`, `docs/competitive-teardown.md` (sección nueva, sin reescribir las anteriores), `docs/COMPETENCIA.md` §A | tabla criterio a criterio con URL o salida de test por celda; nada «mejor que» sin ella |

## 3. Reglas anticonflicto (las impone el prompt)

1. **Orden.** La serie 45 se termina y se abre su último PR antes de empezar la 46; solo 46.0 puede ir
   en paralelo, en un worktree aparte. La 44 no se mezcla con la 46 en el mismo worktree ni en la
   misma rama.
2. **Aislamiento.** Un worktree por fila (`wt-46N` o `wt-40N` en el scratchpad de la sesión), rama
   `claude/serie-46-N-<slug>` o `claude/serie-40-N-<slug>`, base `origin/master` recién traído;
   `git merge origin/master` antes de cada push; un PR por fila.
3. **Ficheros vedados mientras la 45 no esté en `master`** (los toca 45.1–45.4):
   `frontend/src/pages/AuthScreen.tsx`, `pages/LandingScreen.tsx`, `App.tsx`, `i18n.ts`,
   `i18n/{es,en}/common.json`, `services/api.ts`, `stores/useAppStore.ts`, `pages/DuelScreen.tsx`,
   `e2e/duel.spec.ts`, `e2e/correoAlta.spec.ts`, `backend/app/api/v1/endpoints/auth.py`,
   `endpoints/oauth.py`, `services/email.py`, `core/cookies.py`, `docs/API.md`,
   `docs/MAPA_PRODUCTO.md`, `docs/RUNBOOK.md`.
4. **i18n.** Las cadenas de la serie van a `producto.json` (namespace de S1, `useTranslation('producto')`),
   nunca a `common.json` mientras haya un PR de la 45 abierto. `legal.json` (S4), `motor.json` (S3),
   `contenido.json` (S2) y `marketing.json` (S6) no se tocan.
5. **Compartidos** (`SESIONES.md` §3): `frontend/package.json` y lockfile, `scripts/ci_local.sh`,
   `.githooks/**` van en PRs propios, mínimos y listados en «Fuera de alcance». El ledger lo edita la
   sesión ejecutora en commits `ledger: …` separados, siempre tras `git merge origin/master`, con
   `ledger.py fases --write`, `ledger.py check` y `check_docs.py` verdes antes del push.
6. **Contenido.** `content/**` no se toca (ADR-62) hasta que el dueño decida D1. Retirar un ítem con
   error de hecho sigue permitido.
7. **Puertas.** Hook de nivel 1 en cada push; nivel 2 en la cola de la sesión; `check-bundle.mjs`,
   `check-prerender.mjs`, `check-no-third-party.mjs`, `lighthouse-app-a11y.mjs` donde apliquen; e2e a
   390 y 1280; capturas ES/EN en `docs/ui-snapshots/<fila>/` con README como el de `design-v2/`.
8. **Sin «mejor que».** Ninguna afirmación de superioridad en landing, listing ni docs públicas hasta
   46.6/40.13 (línea roja 9).

## 4. Decisiones que solo toma el dueño

Se preguntan en un solo mensaje al cerrar 46.3, antes de la ola 2. Ninguna se asume.

**Decididas el 2026-10-19 (ADR-67):** D1 sin excepción (demostración fuera de `content/`); D2 mascota sí, dibujada por
un ilustrador a partir del brief de la fila 46.8, con la guía enmendada; D3 sonido encendido por defecto (fila 46.9); D4 `@capacitor/haptics` sí (fila 46.2b).

- **D1 — ADR-62 y el piloto.** Los 30 ítems `interactive` de 40.2 son contenido nuevo. Opciones:
  excepción expresa para el piloto, o firmar ADR-62 con esa excepción, o no. Sin D1, 40.2 se
  queda en los 3 widgets con un ítem de demostración cada uno, no persistido en `content/`.
- **D2 — Mascota o personaje.** Sí o no. Si sí: SVG + Lottie, que ya están en el bundle; **no Rive**
  (dependencia y binarios nuevos, licencia sin verificar). Sin mascota, 46.1 y 46.7 usan el icono de la racha y el check (§6.4).
- **D3 — Sonido por defecto.** Propuesta: apagado (Duolingo lo lleva encendido; aquí el alumno lo
  enciende en Perfil). **Decidido al revés: encendido** (ADR-67 D3; hecho en 46.9).
- **D4 — `@capacitor/haptics`.** Único paquete nuevo del plan; `package.json` es compartido.

## 5. Lo que este plan no promete

- Igualar el catálogo de matemáticas escolares de Brilliant ni la escala de contenido de Duolingo.
- Una fecha. Cada fila se cierra con evidencia, no con calendario.
- Que la rúbrica de §0 sea la del mercado: es la de este plan, con pesos fijos para poder comparar el
  antes y el después. 46.6 la contrasta con producto medido.

## 6. Sistema de juice: animación, sonido y gamificación con orden (ampliación del 2026-10-18)

### 6.0 Principios (lo que da el «orden impecable»)

1. **Un solo bus de eventos.** Todo momento visual, de movimiento, sonido o vibración sale de
   `feedbackFx.emit(event)` (`frontend/src/lib/feedbackFx.ts`, fila 46.2). Nadie llama a `vibrate`
   ni a `AudioContext` por su cuenta. La verdad viene del servidor: el cliente **no inventa**
   recompensas.
2. **Cinco niveles de intensidad con presupuesto fijo.** Cada evento pertenece a un nivel; el nivel
   fija duración, si bloquea la entrada y si suena.

   | Nivel | Qué | Duración | Bloquea | Sonido | Ejemplos |
   |---|---|---|---|---|---|
   | 0 micro | tocar, enfocar, cambiar pestaña | ≤ 120 ms | no | no | `tapScale` de `lib/motion.ts` |
   | 1 respuesta | acierto / fallo / «no lo sé» | ≤ 400 ms | no | 1 tono | pulso o sacudida de la opción, mascota reacciona, «+XP» vuela al `xpBadge` |
   | 2 hito de sesión | combo 3/7/15 (= ×2/×3/×5 del servidor), misión completada | ≤ 700 ms | no | arpegio | anillo del combo se llena, «×3» salta, barra de misión termina con check dibujado |
   | 3 cierre | fin de sesión | ≤ 2,5 s, saltable | sí | tic-tac + nota | recuento animado de aciertos, precisión, XP; sello de la nota S–F; chips de banda que cambian |
   | 4 ceremonia | subir de nivel, insignia, racha 7/30/100, ascenso de liga | ≤ 3 s, saltable, **máx. 1 por sesión** | sí | fanfarria | pantalla completa con la mascota (celda 2/4 de la hoja) |

3. **Coalescencia.** Si en una respuesta coinciden varios eventos (acierto + combo 7 + misión), se
   emite **uno** por nivel y los de nivel 4 se encolan para después del resumen. Nunca dos
   celebraciones apiladas.
4. **Líneas rojas.** Respeta `prefers-reduced-motion` (nivel 0–2 se reducen a opacidad; 3–4 pasan a
   tarjeta estática), `soundEnabled` y el interruptor de vibración; nada de sonido antes del primer
   gesto del usuario (política de autoplay); sin azar, cofres ni recompensas sorpresa; **sin
   porcentajes del modelo** (`1f7c24ab`): bandas y recuentos; cada momento tiene texto equivalente
   (`aria-live` ya existe en `Toast`).
5. **Medido o no existe.** Cada emisión manda un evento de analítica (`fx_emitted {tier, type,
   skipped}`) y el interruptor de sonido otro. Un nivel que se salta > 60 % de las veces se rebaja.

### 6.1 Paleta de sonido sintetizado (`feedbackFx.ts`, ~2 KB)

Un `AudioContext` perezoso, creado en el primer gesto; ganancia maestra 0,2; ondas `triangle` para
lo positivo y `sine` grave para lo negativo; nunca disonancia como castigo.

| Evento | Diseño |
|---|---|
| correcto | dos notas ascendentes C5→E5, 90 ms cada una |
| fallo | un «thud» sine 180 Hz, 120 ms, decaimiento suave |
| «no lo sé» | silencio (declararlo no se castiga ni se premia) |
| combo ×2 / ×3 / ×5 | arpegio C-E-G con una nota más por nivel (3/4/5 notas, 70 ms) |
| misión completada | campanilla de 3 notas G5-C6-E6 |
| fin de sesión | tic a 12 Hz durante el recuento + nota final según la nota S–F |
| subida de nivel / insignia | fanfarria de 5 notas, 600 ms |
| racha (hito) | ráfaga de ruido filtrado 200 ms («chispa») + nota |

Vibración: correcto 10 ms; fallo 20-40-20 ms; hito 30 ms; ceremonia 50-30-50 ms. `navigator.vibrate`
en web, `@capacitor/haptics` en nativo (D4).

### 6.2 Mapa por pantalla (qué se anima, con qué dato)

- **Quiz (nivel 1–2).** Opción elegida: `correctVariants`/`wrongVariants` ya existentes; mascota en
  la tarjeta de feedback (celda 2 o 3); «+XP» sale de la tarjeta y aterriza en `xpBadge` con
  `springs.bouncy`; anillo SVG alrededor del badge de combo con `pathLength` que se llena hacia
  3/7/15 y etiqueta «×2/×3/×5» que salta al cruzar. Fuente: `res.combo`, `res.xp_earned`.
- **Resumen (nivel 3).** Recuento con `animate()` de framer sobre `correct`, `accuracy`, `xp_earned`;
  la letra de la nota «se estampa» (escala 1,6→1 + sacudida corta); «skills que se movieron»: cada
  chip entra con `listItemVariants` y, si cambió de banda, brilla una vez; créditos como moneda que
  cae solo si `credits_earned > 0`. Botón «Saltar» visible desde el primer frame.
- **Home — misiones (nivel 2).** Al entrar, se compara con la última foto guardada en
  `localStorage` (`whetzy_fx_missions_<userId>_<fecha>`): las barras que avanzaron se llenan con
  `springs.gentle`; la que se completó dibuja un check (`motion.path`, 300 ms) y suena **una vez**;
  el `2/3` del encabezado cuenta hacia arriba. Sin foto previa, nada se celebra.
- **Home — territorio (nivel 2).** Celda que subió de banda desde la última foto: borde pulsa en
  el color de la banda nueva, la mascota asoma por la esquina 600 ms, etiqueta de banda cambia con
  `AnimatePresence`. «Not enough evidence» no se anima: no hay logro.
- **Home — rutas.** `skills_mastered` que cambió: el número cuenta hacia arriba y el icono de la
  ruta hace un `tapScale`. El resto, quieto.
- **Racha (nivel 2 y 4).** Llama del TopBar con 3 tamaños (1–6, 7–29, ≥ 30 días) y brillo
  proporcional; hitos 7/30/100 son ceremonia; comodín usado → escudo que absorbe la llama.
- **Liga.** Entrada escalonada del podio y de las filas; flecha ▲ de zona de ascenso pulsa.
  **La ceremonia de ascenso queda bloqueada** hasta que el servidor aplique ascensos
  (`service.py:55-64` copia la liga anterior): celebrar un ascenso que no ocurre es mentir.
- **Preparación.** Sin arco (D-16/17/19). Las bandas por dominio entran escalonadas y «Tu mayor
  palanca» late una vez al cargar.
- **Pantallas de entrada (auth, onboarding).** Nivel 0 solo.

### 6.3 Cambio mínimo de backend (fila nueva 46.1b)

`QuizAnswerResponse.events: list[FxEvent]` con `FxEvent = {type: 'level_up' | 'badge_earned' |
'mission_completed' | 'combo_multiplier' | 'streak_milestone', payload: dict}`, construido en
`services/quiz.py` con lo que ya calcula: ids de `award_badges` (hoy descartados), nivel antes/después
en `:804`, misiones completadas en esta respuesta, multiplicador cruzado, racha nueva en hito. Sin
esto el cliente solo puede adivinar comparando fotos; con esto el servidor sigue siendo la verdad.
Test: una respuesta que cruza combo 7 trae `combo_multiplier{3}`; una que completa una misión trae
`mission_completed{id}`; ninguna trae dos veces el mismo evento.

### 6.4 Filas (van al ledger vía 46.0; descripción compacta)

| Fila | Qué | Criterio de DONE |
|---|---|---|
| 46.1 | (ya en §2) feedback sin tapar, + mascota en la tarjeta y anillo de combo 3/7/15 | sin `Player` con reduced-motion; e2e: «×3» aparece al 7.º acierto seguido (mock) |
| 46.1b | `events[]` en `QuizAnswerResponse` (6.3) | tests de 6.3; OpenAPI y `docs/API.md` al día |
| 46.2 | `feedbackFx.ts`: bus, 5 niveles, sonido sintetizado, vibración, interruptores (`soundEnabled` ya existe) | sin gesto previo no suena; con interruptor apagado 0 llamadas a `AudioContext`/`vibrate` (test); `check-prerender.mjs` verde |
| 46.3 | (ya en §2) + momentos de Home: misiones, territorio y rutas con foto en `localStorage` | e2e: completar una misión → check dibujado y evento `fx_emitted{2,mission}` una sola vez |
| 46.7 | Resumen de sesión nivel 3 y ceremonias nivel 4 (nivel, insignia, racha 7/30/100), con «Saltar» y máx. 1 por sesión; ascenso de liga **bloqueado** hasta que el servidor lo aplique | e2e: dos eventos de nivel 4 en una sesión → una ceremonia y una tarjeta; `fx_emitted{4,…,skipped}` medido |
| 46.6 | (ya en §2) añade `fx_emitted` y `sound_toggled` a la medición | tabla de tasa de salto por nivel tras la cohorte |

Orden dentro de la ola 1: 46.2 (motor) → 46.1b (backend, en paralelo) → 46.1 → 46.3 → 46.7. La
mascota (D2) entra en 46.1/46.7 solo si el dueño dice sí; sin ella, los mismos momentos usan el
icono de la racha y el check.

## 7. Pase de movimiento por toda la app (ADR-68, 2026-10-20)

### 7.1 Punto de partida, medido en `master` `00e52a5`

- Las pantallas internas ya cambian con una transición de eje compartido: `App.tsx:568`, `AnimatePresence`, ±24 px
  según la dirección, 200 ms. `MotionConfig reducedMotion="user"` la apaga para quien lo pide.
- Movimiento **propio** de verdad solo tienen Hoy (25 `motion.`) y Quiz (8). Tracks, Lección, Playground y Proyecto
  tienen 2–4 usos sueltos. **Las otras 27 pantallas no tienen ninguno.**
- `components/common/Skeleton` existe, pero solo lo usa `/_ui`. Doce pantallas cargan con un texto «Cargando…».
- En `lib/motion.ts` hay variantes escritas que no usa nadie: `correctVariants`, `wrongVariants`, `xpBurstVariants`
  y `pulseVariants`.
- De la comparación del §6 con el código (sesión del 2026-10-20) faltan:
  - la analítica (§6.0, punto 5);
  - el pulso y la sacudida de la opción;
  - el «+XP» que vuela;
  - la llama de racha en 3 tamaños con escudo;
  - los contadores de Hoy y la banda con `AnimatePresence`;
  - la entrada escalonada de Liga y Preparación.

  Del resumen animado se encarga #273, y de la palanca, #272.

**Principio del pase.** Cada movimiento cuenta algo que ha pasado de verdad: un dato del servidor, un cambio
respecto a la última visita o una acción del alumno. Si no cuenta nada, la pantalla se queda quieta a propósito.
Rigen las mismas líneas rojas de §6.0. El orden de cada fila es siempre el mismo:
1. el test en rojo;
2. el cambio;
3. las capturas ES/EN a 390 y 1280 px en `docs/ui-snapshots/<fila>/`;
4. axe 0.

### 7.2 Analítica de efectos (46.6a)

- **Ingesta.** `POST /analytics/client-events`:
  - con sesión iniciada y con el limitador que ya existe;
  - hasta 50 eventos por lote;
  - el esquema es cerrado, y cualquier campo o tipo fuera de él da `422`.
- **Tipos de evento:**

  | Tipo | Propiedades |
  |---|---|
  | `fx_emitted` | `{tier 0–4, type ∈ FxType, sounded, vibrated}` |
  | `fx_skipped` | `{tier 3–4, type}` |
  | `sound_toggled` | `{enabled}` |
  | `haptic_toggled` | `{enabled}` |

- **Privacidad.** Se guarda en `analytics_events` **sin `user_id` ni IP** (ADR-68 punto 3).
- **Cliente.** `lib/fxAnalytics.ts` se suscribe a `onFx()`:
  - agrupa en memoria y envía cada 10 s y en `pagehide` (`fetch` con `keepalive`);
  - no envía nada sin sesión, ni durante el prerender, ni en los tests;
  - el «Saltar» de las ceremonias y del recuento emite `fx_skipped`.
- **Lectura.** `GET /analytics/fx?days=7` (admin) devuelve, por nivel:
  - emitidos, saltados y tasa de salto;
  - `downgrade: true` cuando la tasa pasa del 60 % con n ≥ 30 (la regla de §6.0, punto 5).
- **Hecho cuando:**
  - un test de integración manda un lote mixto y comprueba que las filas no llevan `user_id`;
  - un campo de más da `422`;
  - el cálculo de la tasa queda fijado por un test;
  - un test del cliente comprueba que, sin sesión o con Global Privacy Control o Do Not Track activados en el
    navegador, no hay ningún `fetch`.

### 7.3 Lo que faltaba del §6 (46.10–46.13)

| Fila | Qué | Dato que lo dispara | Hecho cuando |
|---|---|---|---|
| 46.10 | Opción acertada: `correctVariants` (pulso de 1,04, 300 ms). Fallada: `wrongVariants` (sacudida de ±6 px, 3 ciclos, 300 ms). «+XP» vuela de la tarjeta al marcador (`layoutId` compartido, `springs.bouncy`) y el marcador hace `pulseVariants` al llegar | `feedback.correct`, `res.xp_earned` | test: con reduced-motion no hay `x` ni `scale` y solo cambia la opacidad; e2e: «+N XP» acaba dentro de `xpBadge` |
| 46.11 | Llama de la TopBar en 3 tamaños: 1–6 días a 16 px, 7–29 a 20 px con brillo, ≥ 30 a 24 px con brillo y halo. Escudo que la cubre 600 ms el día que se gasta un comodín | `currentStreak`, `streak_freeze_used` del servidor | test de los tres umbrales; sin comodín no hay escudo |
| 46.12 | Hoy: el «2/3» de misiones y `skills_mastered` cuentan desde la última foto con el `CountUp` de #273. La etiqueta de banda cambia con `AnimatePresence` y el icono de la ruta hace `tapScale` | la foto de `homeMoments` | sin foto previa, nada cuenta ni late (test) |
| 46.13 | Liga: podio y filas entran escalonados (`listVariants`) y la ▲ de zona de ascenso late una vez. Preparación: las bandas por dominio entran escalonadas | datos de la pantalla | ninguna ceremonia de ascenso (test, §6.2) |

### 7.4 Transiciones y carga (46.14)

- **Esqueletos.** Las 12 pantallas que cargan con un texto pasan a un `Skeleton` con la forma de lo que viene:
  - **con `aria-busy`** y el texto «Cargando» solo para el lector de pantalla;
  - **sin brillo** con reduced-motion;
  - **sin parpadeo:** si los datos llegan en menos de 150 ms, el esqueleto no llega a pintarse.
- **Páginas sueltas.** Auth, Landing, Verificar, Restablecer y Estado entran con la misma transición de eje que las
  pantallas internas. Hoy cambian de golpe.
- **Hecho cuando:**
  - ninguna pantalla interna muestra un «Cargando…» suelto (guarda que lo busca);
  - un e2e con la red frenada ve el esqueleto y después el contenido, sin saltos de layout (CLS 0 en el tramo medido).

### 7.5 Las 27 pantallas sin movimiento propio (46.15, un PR por bloque)

**Rehecha contra el código el 2026-10-24** (§7.7). Cada promesa de la tabla original se buscó en `frontend/src`.
Columna «Evidencia»: el test unitario (`src/test/…`) y el e2e (`e2e/…`) que lo afirman; «sin test propio» cuando
está en el código y nada lo vigila. Lo que no se hace lleva el motivo; nada se da por hecho sin haberlo visto.

| Bloque | Pantalla | Hecho (y con qué dato) | Evidencia | No se hace, y por qué |
|---|---|---|---|---|
| A. Entrada | Auth | el error del formulario tiembla (nivel 0, sin sonido) y se anuncia; con movimiento reducido no tiembla | `entrada46.test.tsx`, `entrada.spec.ts` · `e840523` | — («enviando» sin cambiar de tamaño: el botón es de ancho completo; sin test propio) |
| | Onboarding | cada paso entra desplazándose; la barra de pasos se llena (transición de `width` en `onboarding.css`) | `entrada46.test.tsx`, `entrada.spec.ts`; la barra, sin test propio | check dibujado en la tarjeta elegida: el toque pasa de paso al instante y el check no llegaría a verse |
| | Prueba de nivel | un punto por pregunta respondida; el nivel, en palabras y sin % (ADR-60), aparece con efecto | `entrada46.test.tsx`, `entrada.spec.ts` · `eb74c7d` | — |
| | Verificar, Restablecer, Olvidé | check dibujado solo cuando el servidor confirma; con movimiento reducido, estático | `entrada46.test.tsx`, `resetPasswordPage.i18n.test.tsx`, `entrada.spec.ts` · Restablecer en `e7abd77` | — |
| B. Aprender | Lección | «Copiado» al copiar el ejemplo; cada paso de la lección entra con desplazamiento (`motion.section key={step}`) | `aprender46.test.tsx`, `aprender.spec.ts` · `8ebc7b8`; el paso, sin test propio | IntersectionObserver por sección: la lección va por pasos, una tarjeta cada vez, y no hay página larga que recorrer |
| | Tracks | la skill que subió de banda desde la última visita late una vez, con su propia foto | `aprender46.test.tsx` (3 casos), `aprender.spec.ts` | — |
| | Playground, Proyecto | «Ejecutar» con estado en curso (Playground); paso aceptado por el servidor → `emit('correct')` y el aviso entra (Proyecto) | `aprender46.test.tsx`, `aprender.spec.ts` | resultados de tests escalonados: el Proyecto recibe un solo veredicto (pasa / no pasa) y el Playground no tiene tests |
| C. Competir | Duelo | el desenlace del servidor entra y cierra la sesión una vez; sin resultado del rival, nada | `competir46.test.tsx`, `competir.spec.ts` · `b1fcd2e` | barra del rival en vivo y anillo de cuenta atrás: los duelos son asíncronos (partida grabada, sin reloj) |
| | Simulacro, Examen de ruta | el reloj late al entrar en los 5 últimos minutos, sin sonido; el veredicto entra y cierra la sesión una vez | `competir46.test.tsx`, `competir.spec.ts` | — (el navegador de preguntas existe: `components/exam/ExamSitting.tsx`, una casilla por pregunta con estado respondida / marcada / pendiente; sin movimiento propio ni test que lo nombre) |
| D. Progreso | Perfil | insignias escalonadas; la nueva desde la última foto brilla una vez | `progreso46.test.tsx`, `progreso.spec.ts` · `b663309` | — |
| | Stats | las barras crecen desde 0; listas escalonadas; las cifras del resumen cuentan al llegar los datos (2026-10-24) | `progreso46.test.tsx` («Cifras que cuentan»), `progreso.spec.ts` | — |
| | Cartera | listas escalonadas; el saldo cuenta cuando cambia (canjear, comprar), no al entrar (2026-10-24) | `progreso46.test.tsx` («Cifras que cuentan») | — |
| | Informe de dominio, Perfil público | rutas, certificados y proyectos escalonados | `progreso46.test.tsx` | — |
| | Certificado público | el sello se dibuja solo si el servidor lo da por válido; revocado, sin sello | `progreso46.test.tsx`, `progreso.spec.ts` | — |
| E. Comprar | Checkout, Marketplace | éxito (check dibujado) solo cuando el servidor confirma; las tarjetas del catálogo entran escalonadas | `comprar46.test.tsx`, `comprar.spec.ts` · `b6ba7e4` | **pendiente**: la opción elegida del selector de plan (`choiceOn`, `CheckoutScreen.tsx`, sale con más de un mensual) se marca pero no se eleva |
| F. Leer | Legal, Evidencia, Estado, Borrar cuenta, Admin, Instructor | **quietas a propósito**: se leen, se deciden o son internas | esqueletos de 46.14 (`esqueletos.spec.ts`, `esqueletos-pantallas.spec.ts`) | — |

### 7.6 Orden sin excepciones (46.16)

- **Tokens.** Las duraciones salen de un solo sitio: `lib/motion.ts` exporta `DUR`, y el presupuesto de `TIER_BUDGET`
  sale de ahí.
- **La guarda `src/test/motionGuard.test.ts` falla si:**
  - desaparece el bloque global de movimiento reducido de `styles/global.css`;
  - App deja de envolver la app en `MotionConfig reducedMotion="user"`;
  - una duración de framer pasa de 0,7 s, o algo se repite sin fin, sin una anotación `fx-budget:` que diga por qué;
  - el presupuesto por nivel deja de coincidir con los tokens.
- **Se comprueba con mutaciones:** cada regla se rompe a propósito, se ve fallar la guarda y se restaura.
- **Enmienda del 2026-10-20, al implementarla:** se descarta pedir un bloque `prefers-reduced-motion` en cada fichero
  con `@keyframes`. El bloque global de `global.css:102` ya apaga todas las animaciones CSS
  (`animation-duration: 0.01ms !important`), así que lo que hay que vigilar es que ese bloque siga ahí.

### 7.7 Orden de ejecución

46.6a → 46.10 → 46.11 → 46.12 → 46.13 → 46.14 → 46.16 → 46.15 (bloques A–E).

- **Por qué la guarda va antes de los bloques:** así los cinco bloques ya nacen dentro de las reglas.
- **Cuándo cerrar:** la serie se cierra al rehacer la tabla de §7.5 contra el código, con capturas.
