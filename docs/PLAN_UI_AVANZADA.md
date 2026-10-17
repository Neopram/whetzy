# Plan — Experiencia avanzada: interfaz y experiencia al nivel de Brilliant y Duolingo (serie 46)

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
| 46.6 | **Medición.** PostHog `session-recording` y una encuesta de una pregunta tras el primer quiz, solo bajo el consentimiento ya implementado; re-puntuación de la rúbrica de §0 con una evidencia por celda; captura de la interfaz de Brilliant y Duolingo con URL y fecha → **cierra 40.13** | `frontend/src/lib/analytics*`, `docs/competitive-teardown.md` (sección nueva, sin reescribir las anteriores), `docs/COMPETENCIA.md` §A | tabla criterio a criterio con URL o salida de test por celda; nada «mejor que» sin ella |

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

- **D1 — ADR-62 y el piloto.** Los 30 ítems `interactive` de 40.2 son contenido nuevo. Opciones:
  excepción expresa para el piloto, o firmar ADR-62 con esa excepción, o no. Sin D1, 40.2 se
  queda en los 3 widgets con un ítem de demostración cada uno, no persistido en `content/`.
- **D2 — Mascota o personaje.** Sí o no. Si sí: SVG + Lottie, que ya están en el bundle; **no Rive**
  (dependencia y binarios nuevos, licencia sin verificar).
- **D3 — Sonido por defecto.** Propuesta: apagado (Duolingo lo lleva encendido; aquí el alumno lo
  enciende en Perfil).
- **D4 — `@capacitor/haptics`.** Único paquete nuevo del plan; `package.json` es compartido.

## 5. Lo que este plan no promete

- Igualar el catálogo de matemáticas escolares de Brilliant ni la escala de contenido de Duolingo.
- Una fecha. Cada fila se cierra con evidencia, no con calendario.
- Que la rúbrica de §0 sea la del mercado: es la de este plan, con pesos fijos para poder comparar el
  antes y el después. 46.6 la contrasta con producto medido.
