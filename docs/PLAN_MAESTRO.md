# Plan maestro de Whetzy

> **Normativo vivo desde el 2026-10-04.** El dueño lo aprobó esa noche y pidió llevarlo «a un detalle
> en que ningún modelo cometa un error». Es el norte del producto y **no repite el ledger**, que sigue
> siendo la fuente de verdad del progreso (ADR-40). **Un plan que no es fila del ledger no es un plan**
> (ADR-48): este documento orienta, y las filas mandan. Las cifras del banco no se copian aquí; salen de
> los scripts de §0.3.
>
> **Base:** `master` `bb1d28d`, con el código idéntico a `05b46b1`. La primera versión se escribió sobre
> `05b46b1` y desde entonces solo cambiaron docs. Las referencias usan la ruta completa desde la raíz del
> repo. **Antes de tocar nada, se vuelven a comprobar**: las líneas se mueven.
>
> **Enmienda del 2026-10-04 (noche):**
> - una verificación adversaria encontró 16 incoherencias en la primera versión;
> - el dueño detectó tres: ADR-60 inexistente, series 41–43 inexistentes y `PADDLE_ENVIRONMENT`;
> - todas están corregidas aquí. El error de fondo era presentar **valores por defecto del código como
>   estado de producción**. Ahora tiene su propia etiqueta (§0.2) y es una trampa de §7.

## Estado de lo que este plan cita y todavía no existe en `master`

| Qué | Estado comprobado | Hasta que exista |
|---|---|---|
| **ADR-60**: decisiones del dueño del 2026-10-04 (perfil público opt-in, la cuña, Web3 y reorganización como propuesta, lecciones corta/extensa, login Google + Apple, orden) | **No existe**: `docs/DECISIONS.md` termina en ADR-59 [V] | Las decisiones valen (las tomó el dueño en la sesión coordinadora), pero el número puede cambiar al aplicarse |
| **Series 41** (Oleada S), **42** (Oleada 0 y flujo de estudio) y **43** (partes B–J fusionadas) | **0 filas en el ledger**: `ledger.py series 41|42|43` no devuelve nada [V] | Los IDs de este plan son **propuestos** («(prop.)»); el número real es el que les dé S5 |
| **Migración 56** (perfil público opt-in) | No existe; la 55 (#127) tampoco está fusionada [V] | Orden fijado: 55 = #127, 56 = opt-in |

El texto exacto de ADR-60 y de las series va en la sección «Delta del ledger» del PR que trae esta
enmienda (SESIONES §3). S5 lo aplica después de volver a ejecutar los comandos.

---

## 0. Cómo se usa este documento

### 0.1 Reglas que no se rompen

1. **`master` solo lo fusiona el dueño** (ADR-45). La sesión trabaja en su rama y abre un PR. **Nunca**
   hace push a `master`.
2. **Ficheros compartidos: solo los edita S5** (`docs/SESIONES.md` §3). Son estos:
   - `docs/AUTONOMOUS_STATE.md` (ledger), `docs/STATUS.md`, `docs/CHANGELOG.md`, `docs/DECISIONS.md`;
   - `docs/archive/**`, `CLAUDE.md`, `docs/README.md`;
   - `frontend/package.json`, `frontend/package-lock.json`, `backend/requirements*.txt`, `Dockerfile`;
   - `.github/**`, `.githooks/**`;
   - `scripts/ci_local.sh`, `scripts/ledger.py`, `scripts/check_docs.py`.

   Las demás sesiones **proponen el cambio en su propio PR**: el ledger en «Delta del ledger»
   (`ID | estado nuevo | commit | comando ejecutado | salida real`) y el resto en «Fuera de alcance»,
   con el fichero exacto. S5 vuelve a ejecutar cada comando antes de aplicarlo; si no se reproduce, no
   lo aplica. El #89 sirve para avisar, no sustituye al PR.
   - **`docs/INVENTARIO_DOCS.md`** es de solo-añadir: quien crea un `.md` en `docs/` le añade una línea.
3. **Migraciones de una en una** (SESIONES §5). El PR que trae una migración actualiza las tres líneas
   del HEAD: «HEAD actual» de `CLAUDE.md`, la fila «Alembic HEAD» del ledger y «Current Alembic HEAD»
   de `docs/RUNBOOK.md`. Antes de abrirlo, se avisa en el #89.
   - **Hoy: 55 = `20261004_study_session_current_question`** (#127, S.4) [V].
   - Orden fijado: **56 = perfil público opt-in** (#144 rehecho).
   - Las demás van detrás, en el orden en que se fusionen.
4. **Nunca `create_all`, y nunca borrar ni renombrar tracks o skills sin un mapa de progreso.** Desde la
   54, `content_loader` retira un track con `is_active=false` en vez de borrarlo
   (`backend/app/services/content_loader.py`, retirada de tracks) [V]. Aun así, cambiar un ID deja
   huérfano el progreso que cuelga del ID viejo.
5. **Un PR solo es LISTO con estas cuatro cosas:**
   1. contiene `master`;
   2. nivel 1 en verde (`.githooks/pre-push`);
   3. **`python scripts/check_docs.py` en verde, ejecutado a mano.** El pre-push solo lo corre si el
      push toca `docs/`, `content/`, un `.md`, `ledger.py` o `check_docs.py` (`.githooks/pre-push:183-184`),
      y `scripts/ci_local.sh` **no lo corre nunca** [V]. Así llegó el #145 con `check_docs` en rojo:
      su push solo tocaba código;
   4. nivel 2 en VERDE (`scripts/ci_local.sh --carril <x> --sha <sha>`).
6. **Cada guarda nueva se muta**: se rompe a propósito, se ve en rojo y se restaura (CLAUDE.md,
   «Estilo»). **Un test que falla al azar no puede ser puerta**: se arregla o se saca. Hoy hay uno:
   `frontend/src/test/profileTab.test.tsx` (43.9 prop.).
7. **Después de cada fusión:**
   - Railway en SUCCESS (`list-deployments`);
   - `node scripts/check-deployed.mjs --sha <sha>`, ejecutado desde `frontend/`, en PASS;
   - `/health` 200;
   - una comprobación en producción de lo que cambió.
8. **Textos de interfaz en ES y EN nativos**, con la paridad de `frontend/src/test/i18n.parity.test.ts`
   en verde. Cada rol escribe en su fichero de `frontend/src/i18n/{es,en}/` (SESIONES §6).
9. **Contenido para el alumno:** lo escribe Sonnet desde un fragmento de fuente `reusar`, con revisión
   adversaria y corrector (ADR-59, `docs/PLAN_CONTENIDO.md`). Haiku nunca escribe contenido.

### 0.2 Etiquetas

- **[V]:** comprobado con una herramienta el 2026-10-04 sobre `master` o contra producción (GET
  público, sin autenticar).
- **[def]:** **valor por defecto del código** (`backend/app/core/config.py`). Su valor en producción
  (variables de Railway) **no se ha leído**. **No vale como estado de producción.**
- **[P]:** lo dice un informe o un documento que no se ha vuelto a comprobar.
- **[O]:** propuesta u opinión.

### 0.3 De dónde salen las cifras

| Cifra | Comando |
|---|---|
| Banco, tracks, skills, lecciones, términos | `python scripts/project_snapshot.py` |
| Preguntas pendientes por track | `python scripts/catalog_coverage.py` |
| Estado del backlog | `python scripts/ledger.py stats` / `blocked` / `next` |
| Coherencia entre docs y código | `python scripts/check_docs.py` |

---

## 1. Tesis y métricas norte

**Cuña** (decisión del dueño del 2026-10-04; ADR-60 prop.): preparación de **certificaciones técnicas
en ES y EN**. El marketplace de creadores y el B2B se construyen después, sobre la misma base.

**Métricas norte.** La analítica es **propia**: `backend/app/services/analytics.py` escribe en la tabla
`analytics_events`. No se instala PostHog ni Mixpanel en el navegador; PostHog solo podría entrar como
destino desde el backend, con la privacidad actualizada antes (ADR-50j) [V].
- **Ya existen** las metas D1/D7/D30 y la conversión a 35 días (`PRODUCT_METRIC_TARGETS`,
  `backend/app/services/analytics.py:32-36`; `conversion_d35`, `:312`) [V], con sus referencias de
  ADR-32 y ADR-53 §8.
- **No hay medida real** porque no hay cohorte (H.10).

| Métrica | Definición | Estado |
|---|---|---|
| Activación D0 [O] | % de altas que el mismo día UTC ven ≥ 1 lección y responden ≥ 10 preguntas | **Falta el evento**: no existen `lesson_viewed` ni `answer_submitted` en el código [V]. Se crean sobre `analytics_events` |
| Retención D1/D7/D30 | La que ya calcula `analytics.py` | Existe [V] |
| Conversión | **35 días**, la de `analytics.py` (meta ≥ 0,021, objetivo 0,03) | Existe [V]. No se inventa otra ventana |
| Preparación [O] | % que alcanza «listo para el simulacro» (#133) y aprueba un simulacro | **Falta el evento** `mock_exam_submitted` [V] |

---

## 2. Estado de los actores, flujo a flujo

### 2.1 Alumno

| Paso | Hoy | Hueco | Fila |
|---|---|---|---|
| Alta y verificación | En prod, `POST /api/v1/auth/verify-email` usa `ResetPasswordRequest`, que exige `new_password`: da **422** con `{token}` [V] | #145 lo arregla, pero tiene `check_docs` en rojo: le faltan `VerifyEmailPage` y `/verify-email` en `docs/MAPA_PRODUCTO.md` [V] | 42.1 (prop.) |
| Login social | Solo GitHub y Google (`backend/app/api/v1/endpoints/oauth.py`); el `state` se crea en `:122` y se valida en `:168-180`, se guarda en la BD (`backend/app/models/oauth.py:14`, `OAuthState`) sin cookie y **sin PKCE** [V]; **sin Apple** [V] | PKCE, `state` atado a una cookie, Apple (ADR-13) | 41.14 (prop.) |
| Onboarding | 3 preguntas (`frontend/src/pages/OnboardingScreen.tsx:14-45`). `onboarding_goal` (`backend/app/models/user.py:109`) se guarda y se expone, pero **ninguna lógica lo usa** [V]. **Si el alumno no se declara principiante, el examen de nivel es siempre `track01`**; un principiante no hace examen de nivel (`OnboardingScreen.tsx:93`) [V] | Objetivo → especialidad → examen de nivel de esa especialidad | 42.3 (prop.) |
| Especialidad activa | No hay campo en `User`. `selectedTrackId` vale `'track01'` por defecto (`frontend/src/stores/useAppStore.ts:321`) y **solo se guarda en el `localStorage` del dispositivo** (`:353`, `persist`) [V] | Guardarla en el servidor (migración) | 42.3 (prop.) |
| Estudiar | «Estudiar» llama a `startQuiz('study', 10)` (`frontend/src/pages/HomeScreen.tsx:87`). La lección es puerta real: `_LESSON_GATED_MODES = {"study","review"}` (`backend/app/services/quiz.py:184`) y `needs_lesson` (`:195-198`, `:275-278`) [V]. Si falta la lección, se ve un `QuizError` con botón a la lección (`frontend/src/pages/QuizScreen.tsx:426-436`) [V] | La lección no aparece como paso 1: se llega a ella por una pantalla de error | 42.4 (prop.) |
| Lección | Una por skill (`backend/tests/content/test_lessons.py:196`), **150–300 palabras** por idioma (`:36-37`) [V]. Mediana: **217 palabras en ES y 205 en EN** [V] | Versión extensa a elegir | 42.5 (prop.), oleada C |
| Panel | Igual para todos. La única marca de «primera vez» es `whetzy_onboarded_<id>` en `localStorage` (`frontend/src/App.tsx:185`, `:393`) [V] | Panel por segmento y pistas de primera vez | 42.6, 42.7 (prop.) |
| Simulacro | En todos los planes (ADR-58). `MOCK_EXAM_RESERVED_POOL_ENABLED=False` [def] (`config.py:301`) y **0 preguntas con `pool: "simulacro"` en el banco** [P, verificador] | Umbral «listo» (#133) | 43.10 (prop.) |
| Certificación | 39,99 $ pago único (ADR-49). En prod, `GET /api/v1/billing/paddle/config` devuelve **`enabled: true`, `environment: "production"` y un precio `certification` configurado** [V]. `CERTIFICATION_PAYWALL=False` es [def] (`config.py:285`): su valor real está sin leer | Confirmar si se cobra hoy (§5, n.º 3) | Oleada E |
| Perfil público | `frontend/src/pages/PublicProfileScreen.tsx` muestra datos **inventados** («Carlos Pérez») [V] | #144 rehecho como opt-in | 42.2 (prop.) |

### 2.2 Creador

| Paso | Hoy | Hueco | Fila |
|---|---|---|---|
| Plan Creador | 99,99 $ (ADR-41). `CREATOR_PLAN_REQUIRED=False` [def] (`config.py:266`). En Paddle de producción **no hay precio de Creador**, solo `plus`, `pro` y `certification` [V] | Precio en Paddle y flag | Oleada E |
| Inscripción en un curso de pago | `enroll_student` (`backend/app/api/v1/endpoints/instructor_marketplace.py:200`) dice «Sin pasarela todavía» (`:211`). `enroll_student_in_course` (`backend/app/services/instructor_service.py`) suma `price_cents` a `revenue_cents` y al payout **sin ningún cobro** [V] | Exigir compra confirmada antes de inscribir. **Urgente**: Paddle ya está en producción | 41.6 (prop.) |
| Payout | `process_monthly_payouts` (`backend/app/services/periodic.py:281-312`) **solo pasa a `processing`** las liquidaciones pendientes de ≥ 50 € el día 15; **el pago lo hace el dueño a mano** desde esa lista, sin mover dinero [V]. Lo llaman `periodic_jobs_loop` (cada hora) y el job `run_payouts` (`backend/app/services/job_worker.py:168-175`) [V] | Activar (H.25) | H.25 |

### 2.3 Empresa

| Paso | Hoy | Hueco |
|---|---|---|
| Página | `/es/empresas` y `/en/enterprise` muestran un aviso honesto con `noindex` (#126) [V] | NECESITO de S6: ¿publicar sin precio? |
| Producto | **No existen** organizaciones, asientos ni equipos en modelos ni endpoints; solo el enum de créditos `SPEND_COMPANY_SEAT` [P, verificador] | Oleada H |
| Precio | Hipótesis interna: 99 $ por asiento y año, mínimo 10 (ADR-47) [V] | Pilotos (H.39) |

### 2.4 Dueño / admin

- **`/admin` existe** (`frontend/src/pages/AdminScreen.tsx`) [V], con endpoints `require_admin` [P].
- **Falta:**
  - el admin **de empresa** (oleada H);
  - la moderación del marketplace. Hoy solo se puede reportar, bloquear y desbloquear usuarios
    (`backend/app/api/v1/endpoints/moderation.py`) [P].

---

## 3. Arquitectura

**Hoy:**
- **API:** FastAPI con 2 procesos gunicorn (`backend/scripts/start.sh:42`, `--workers 2`) [V], en Railway, región `iad` (Railway `list-deployments`) [V].
- **Arranque, en este orden:** `alembic upgrade head` → `content_loader` → `bootstrap_owner` → `seed` → gunicorn [V].
- **Tareas de fondo:** cada proceso arranca 6 en su lifespan (`backend/app/main.py`) [P].
  - La cola de trabajos usa `SKIP LOCKED` (#132) [V].
  - `periodic_jobs_loop` y el bucle de referidos se protegen con un advisory lock [P].
  - `account_purge_loop` corre uno por proceso y es idempotente [P].
- **Frontend:** SPA en Cloudflare Pages [V].
- **Rate limiter:** `REDIS_URL` vale por defecto `redis://localhost:6379/0` [def] (`config.py:61`). En
  producción el limitador cae a memoria, uno por proceso [P, según los logs que leyó S5]. Así, el límite
  real es el doble del configurado.
- **Cobro web:** Paddle en `production`, con token `live` y precios `plus`, `pro` y `certification`;
  sin precios anuales (`GET /api/v1/billing/paddle/config`) [V].

**Objetivo** [O]: un monolito modular. Nada de microservicios con cero usuarios.

| Orden | Cambio | Quién | Coste |
|---|---|---|---|
| 1 | **D1:** vaciar `REDIS_URL` en Railway; montar Redis de verdad cuando haya tráfico | Dueño | 0 |
| 2 | **D4:** `alembic upgrade head && python -m app.services.content_loader` como pre-deploy de Railway, y `start.sh` solo arranca gunicorn. Antes, leer la documentación de Railway sobre pre-deploy | Dueño (panel) + S5 (PR) | Menos caída por despliegue |
| 3 | **D2:** entorno `staging` en Railway, ya aprobado en ADR-50p. **Antes de cambiar nada del cobro**, que ya está en producción | Dueño (clic) + S5 (RUNBOOK) | Un entorno |
| 4 | **D3:** worker aparte | — | No hasta que haya trabajos pesados reales |
| 5 | **Copias:** `scripts/db_backup.sh`, `db_restore.sh` y `db_restore_test.sh` (`docs/RUNBOOK.md`, «DB backup / restore»), con ensayo mensual (33.1, DONE). **RPO ≤ 24 h y RTO ≤ 60 min están sin medir** (`docs/RUNBOOK.md:454-455`) [P] | S5 | Medirlos ya: el cobro está activo |

---

## 4. Oleadas

Cada punto dice qué tocar, qué reutilizar, el test (con su mutación) y cuándo está terminado. Lo
marcado **(D)** es una decisión del dueño, y no se implementa sin ella. Los IDs `4x.y` son
**propuestos** (ver la tabla de arriba).

### Oleada A: seguridad y dinero (S1; `backend/app/core/**` es de S5)

**A.1 · 41.4 (prop.) · `/quiz/answer` solo acepta la pregunta servida, y una sola vez.** PR #127.
- `git merge origin/master` y `down_revision = "20261004_tracks_is_active"` ya hechos — la migración
  es la 55, con las tres líneas del HEAD actualizadas (2026-10-05). Pendiente: nivel 2 y quitar el
  borrador.
- Test: responder dos veces la misma pregunta → 409; responder una pregunta que no se sirvió → 409.

**A.2 · 41.5 (prop.) · El tutor no ayuda en un examen ni con preguntas reservadas, y no cobra cupo si no respondió la IA.**
- Dónde:
  - `backend/app/api/v1/endpoints/tutor.py:43-84` comprueba el cupo antes de llamar y lo anota en `:82`;
  - `backend/app/services/ai/tutor.py:112` (`explain_question`).
- Hechos [V]:
  - `Question.pool` vale `"practica"` por defecto (`backend/app/models/content.py:186`) y el banco
    reservado es `"simulacro"`;
  - `MockExamAttempt` está en `backend/app/models/exam.py:24`;
  - `NullProvider.name = "fallback"` (`backend/app/services/ai/provider.py:32-36`);
  - `complete_named` devuelve el nombre del proveedor (`provider.py:134`; se usa en `services/ai/tutor.py:189-191`).
  - Ninguno de los dos ficheros mira `pool` ni `MockExamAttempt`.
- Cambio:
  1. 403 si `question.pool == "simulacro"`.
  2. 403 si hay un `MockExamAttempt` en curso que contiene esa pregunta.
  3. No llamar a `tutor_quota.record` si respondió `"fallback"`.
- Tests en `backend/tests/integration/test_tutor.py`, cada uno mutado.

**A.3 · 41.6 (prop.) · Un curso de pago solo se inscribe con la compra confirmada. Es la prioridad 1 de la oleada.**
- Dónde: `backend/app/api/v1/endpoints/instructor_marketplace.py:200` y `backend/app/services/instructor_service.py` (`enroll_student_in_course`).
- **Ya:** un curso con `price_cents > 0` responde **402**, sin fila de inscripción ni de payout. Un
  curso gratis sigue como hoy.
- **Después:** la inscripción la crea el webhook de Paddle, igual que `certification_purchase` en
  `backend/app/api/v1/endpoints/webhooks.py:121`. Lleva el id de transacción como referencia externa e
  idempotencia por evento. Hace falta un precio en Paddle (oleada E).
- Test: sin compra → 402 y el payout no cambia; curso gratis → 201. Mutación: quitar el 402 → rojo.

**A.4 · 41.14 (prop.) · OAuth con PKCE y `state` atado a una cookie.**
- Cambio:
  - `code_verifier` en `/start`, en una cookie HttpOnly firmada [O] (sin migración);
  - `code_challenge` S256;
  - el callback exige que el `state` de la cookie coincida con el de la query, y manda el `code_verifier`.
- Test en `backend/tests/integration/test_oauth.py`: callback sin cookie → error; `state` cambiado → error.

**A.5 · 41.17 (prop.) · Cupo del tutor por tokens y sin la sesión de BD abierta durante la llamada al LLM.**
- Hechos [P]:
  - `GroqProvider.complete` no lee `usage`;
  - `TutorUsage` solo cuenta explicaciones;
  - `explain()` mantiene la sesión abierta durante la llamada.
- Cambio:
  - el proveedor devuelve también los tokens;
  - columna de tokens en `TutorUsage` (**migración**, en la cola);
  - el límite va en `config.py` (S5);
  - leer, liberar la sesión, llamar al LLM, y abrir otra sesión para anotar.
- **Carrera entre la comprobación del cupo y la llamada** [V]: hoy se comprueba antes de llamar, así
  que dos peticiones a la vez pasan las dos. Arreglo: reservar el cupo antes
  (`UPDATE … WHERE explanations < límite RETURNING`) y devolverlo si el LLM falla.

**A.6 · 41.18 (prop.) · El logout invalida de verdad.**
- Hechos [V]:
  - `logout` (`backend/app/api/v1/endpoints/auth.py:336`) solo audita y borra cookies;
  - `/auth/refresh` (`auth.py:253`) usa un refresh JWT con `jvs`;
  - en `backend/app/core/security.py:316-410` hay refresh opacos con rotación
    (`create_opaque_refresh_token`, `verify_opaque_refresh_token`, `refresh_token_rotation`), **sin usar
    fuera de `security.py`**. Además **tienen un defecto**: `refresh_token_rotation` emite
    `create_access_token(user_id)` **sin `jwt_version`** (`security.py:403`), y `security.py:211`
    rechaza cualquier token cuyo `jvs` no coincida con el del usuario;
  - hoy **no existe** «cerrar sesión en todos»: `jwt_version` solo sube al cambiar la contraseña
    (`auth.py:419`), al restablecerla (`:581`) y al borrar la cuenta.
- Cambio [O]:
  1. Corregir `refresh_token_rotation` para que pase `jwt_version`, con test.
  2. `/auth/refresh` pasa a los refresh opacos.
  3. `logout` revoca el refresh actual.
  4. Endpoint nuevo «cerrar sesión en todos», que sube `jwt_version`.
- Test: el refresh de antes del logout da 401; el de otro dispositivo sigue valiendo.

**La oleada termina cuando:** cada punto tiene su test mutado en rojo, el #127 está fusionado como 55, y
la revisión de COORD no encuentra ninguna ruta que cree dinero o acceso de pago sin cobro.

### Oleada B: flujo de estudio coherente (S1 + S3)

**B.1 · 42.1 (prop.) · `/verify-email`.**
- Sobre el #145: entrada en `docs/MAPA_PRODUCTO.md`, `git merge origin/master`, `check_docs` en verde y nivel 2.
- Prueba en producción: el enlace del correo (`backend/app/services/email.py:483`, `/verify-email?token=`)
  verifica la cuenta.

**B.2 · 42.3 (prop.) · Objetivo → especialidad (o ruta, si se aprueba D-a de la propuesta de los 4 puntos) → examen de nivel de esa especialidad.**
1. **Migración** (en la cola): `User.focus_track_id`, o `focus_path_id` si se aprueban las rutas.
2. **Onboarding:** pide la especialidad, la guarda y llama a `startPlacement(<ese track>)` en lugar de
   `'track01'` (`frontend/src/pages/OnboardingScreen.tsx:93`).
3. **El backend ya acepta cualquier track** (`backend/app/services/placement.py:50-58` filtra por
   `Module.track_id` y excluye `pool = "simulacro"`) [V]. Antes de ofrecer un track, se comprueba que
   tiene preguntas que se pueden responder.
4. **Cambiar de especialidad nunca borra nada:** `uq_user_skill_state` (`backend/app/models/user.py:142`) [V].
5. **Tests:**
   - e2e `frontend/e2e/onboarding.spec.ts`: elegir AZ-900 lleva al examen de nivel de AZ-900;
   - integración: cambiar la especialidad no toca `user_skill_states`.

**B.3 · 42.4 (prop.) · La lección como paso 1 visible.** «Estudiar» (`HomeScreen.tsx:87`) abre la lección
de la skill siguiente si no está vista (`backend/app/services/lesson_gate.py`, `viewed_skill_ids`), en
vez de pasar por el `QuizError` con botón. Test e2e con un alumno nuevo.

**B.4 · Prior de BKT a partir del examen de nivel (S3, (D)).**
- `p_l0 = 0.1` (`backend/app/services/engine/bkt.py:22`) y `p_known = 0.1` (`user.py:152`) [V].
- El examen de nivel **no escribe** `UserSkillState` [P, verificador].
- S3 avisa de que con 1–2 ítems por skill el prior puede ser más ruidoso que el 0,1 fijo.

**La oleada termina cuando** el e2e «alumno nuevo elige AZ-900 → examen de nivel de AZ-900 → lección
antes de la primera pregunta» está en verde en el nivel 2.

### Oleada C: lecciones corta y extensa (COORD contenido + S1 esquema)

Decisión del dueño (ADR-60 prop.): **el alumno elige** entre la versión corta y la extensa, de 15 a 20 minutos.

1. **Esquema.**
   - Campos opcionales `body_long_es` y `body_long_en` en el JSON y en `Lesson`
     (`backend/app/models/content.py:200-224`, **migración**).
   - `_upsert_lesson` (`backend/app/services/content_loader.py:228-247`) los copia con `data.get(...)`.
   - `LessonRead` (`backend/app/schemas/content.py:150-164`) los expone.
   - **No** se crea una segunda lección por skill.
   - **Terreno:** `content_loader`, `models` y `schemas` no figuran en ninguna lista de `SESIONES.md` §4
     → **NECESITO en el #89** para asignarlos (propuesta: S1).
2. **Tests** (`backend/tests/content/test_lessons.py`, terreno de contenido, hoy COORD por ADR-59).
   - La regla de 150–300 palabras sigue para `body_*`.
   - Para `body_long_*`, regla nueva **con el rango que salga del piloto**.
   - Los dos idiomas o ninguno; fuente obligatoria.
3. **Pantalla (S1).** `frontend/src/pages/LessonScreen.tsx` ofrece «Versión corta · ~3 min» y
   «Versión extensa · 15–20 min», y recuerda la preferencia del alumno.
4. **Contenido (COORD).** Piloto de 10 (ADR-59) con la regla de parada de `PLAN_CONTENIDO.md` §4.

**La oleada termina cuando:**
- el piloto pasa (≤ 3/10 con blocker o major);
- su coste queda anotado en `PLAN_CONTENIDO.md` §7;
- el e2e permite elegir versión.

### Oleada D: panel por segmento y pistas de primera vez (S1)

- **Panel** (`frontend/src/pages/HomeScreen.tsx`).
  - La cabecera y «Siguiente paso» dependen de la especialidad y de `onboarding_goal`.
  - El resto se pliega en tarjetas compactas.
- **Pistas.**
  - 3–5 pasos la primera vez, y una ayuda en contexto la primera vez que se abre cada pantalla
    (tutor, repaso, simulacro).
  - Se guardan en el servidor (**migración**) para que no se repitan en otro dispositivo.
  - Accesibles: foco, Esc y texto para lectores de pantalla.
- **La oleada termina cuando:** un test muestra que el panel cambia según el objetivo, y un e2e que las
  pistas salen una vez y no vuelven.

### Oleada E: verificar y completar el cobro, que ya está en producción (dueño + S1/S5)

**Hecho [V]:** Paddle está en `production`, con token `live` y precios `plus`, `pro` y `certification`;
**sin** precios anuales ni de Creador. Existe la página `/checkout` (`frontend/src/App.tsx:241`).
**Hay que actualizar el ledger:** H.29 sigue diciendo «falta alta Paddle y dominio».

**Sin leer** (valores en Railway): `CERTIFICATION_PAYWALL`, `CREATOR_PLAN_REQUIRED`,
`FREE_DAILY_QUOTA_ENABLED` y `ANNUAL_PLAN_ENABLED`. Solo se conocen sus valores por defecto, todos
`False` [def] (`config.py:285`, `:266`, `:290`, `:348`). Que los precios anuales salgan `null` encaja con
`ANNUAL_PLAN_ENABLED` apagado, pero no lo prueba.

**Hay código de Stripe** (`backend/app/api/v1/endpoints/billing.py:67` checkout y `:90` webhook) [V],
pero el cobro es Paddle (H.29). No se construye nada nuevo sobre Stripe.

**Orden:**
1. **El dueño confirma** en Railway los cuatro flags y si ha habido compras reales (§5, n.º 3).
2. **A.3** (cursos de pago sin cobro) antes que nada más.
3. **Staging (D2)** para probar los cambios del cobro.
4. **Precios anuales** (40.9, H.35, **(D)**) y precio de Creador.
5. **Una compra y un reembolso reales**, verificados de punta a punta: webhook → `User.subscription_*`
   y concesión o revocación de la certificación.

**La oleada termina cuando** el punto 5 está comprobado y anotado.

### Oleada F: distribución (dueño + S6 + S1)

- **Beta:** cohorte de 30 personas (H.10).
- **Pitch (S6):** rehacerlo con las cifras de §0.3 y ADR-41/58 (y ADR-60 cuando exista).
- **Tiendas.**
  - Android: `@capacitor/android` y `frontend/android` existen [P].
  - **iOS: no hay `@capacitor/ios` ni carpeta `ios/`** [V].
  - Sign in with Apple no existe [V], y es obligatorio si hay OAuth (ADR-13; guía 4.8 de la App Store
    leída el 2026-10-04 [V]).
  - RevenueCat: hay webhook (`billing.py:149`) [V], pero no hay SDK en el cliente [P].
  - Bloqueado por H.2, H.3 y H.14.
- **La oleada termina cuando** D1/D7 estén medidos con usuarios reales.

### Oleada G: creador

- A.3 cerrado, payouts (H.25), moderación de cursos e instructores fundadores (H.40).
- **La oleada termina cuando** una venta real llega a payout.

### Oleada H: B2B

- Organizaciones, asientos y equipos, con su admin de empresa.
- Pilotos (H.39) y la página `/empresas` (NECESITO de S6).
- **La oleada termina cuando** un piloto con equipo usa el panel.

### Contenido, en paralelo (COORD)

- **Lo pendiente** lo da `catalog_coverage.py`: 4.118 el 2026-10-04, repartidas en
  2.610 + 468 + 1.040 (ver `PLAN_CONTENIDO.md` §1).
- **Orden de `PLAN_CONTENIDO.md` §5.1 y de la fila 37.10:** **MLA-C01** (faltan 131) y **AI-901**
  (faltan 224), las dos certificaciones de la cuña que siguen pendientes.
- **Web3 y la reorganización de los tracks:** propuesta pendiente de las decisiones D-a a D-f (§6).

---

## 5. Cola del dueño, ordenada por lo que desbloquea

| # | Qué | Desbloquea |
|---|---|---|
| 1 | Fusionar lo que esté LISTO, de uno en uno, y probar a mano: login → una respuesta → logout (CSRF, #131) | Todo |
| 2 | D1 (vaciar `REDIS_URL`) y D4 (pre-deploy) | Límites coherentes; despliegues más cortos |
| 3 | **Confirmar en Railway** `CERTIFICATION_PAYWALL`, `CREATOR_PLAN_REQUIRED`, `FREE_DAILY_QUOTA_ENABLED` y `ANNUAL_PLAN_ENABLED`, y decir si ha habido compras reales | Saber si hoy se cobra (oleada E) |
| 4 | D2 staging | Cambios del cobro sin riesgo |
| 5 | Precios anuales y de Creador en Paddle (H.35) | Oleada E completa |
| 6 | Beta de 30 personas (H.10) | Cualquier métrica real |
| 7 | Cuentas de Apple y Google (H.2, H.3) | Tiendas, Sign in with Apple, IAP |
| 8 | Revisión legal (H.20) | Textos legales finales |
| 9 | Payouts (H.25) e instructores (H.40) | Oleada G |
| 10 | Pilotos B2B (H.39) y página `/empresas` | Oleada H |
| 11 | Facturación de GitHub Actions (H.13) | CI en la nube |
| — | Decisiones pendientes: **B.4** (prior de BKT, S3); **C.3 del plan UI/UX** (XP único o separado, y renombrar `Module.level`; S3 recomienda separado y renombrar); **41.10** (CORS para la app nativa); **D-a … D-f** (propuesta de los 4 puntos) | — |

**H.12 (clave de Groq).** Decisión del dueño del 2026-10-04: **la clave se mantiene sin rotar y él
asume el riesgo**, y las ramas `railway/*` no se borran.
- El commit `ba37a0e` (`docs/STATUS.md`) está en la historia de `master`: `compare ba37a0e...master`
  da `behind_by = 0` [V]. Por eso borrar ramas no habría servido de nada.
- La única mitigación real es rotarla.

---

## 6. Después de este plan: los 4 puntos nuevos

La propuesta detallada se entregó al dueño el 2026-10-04 y espera sus decisiones D-a a D-f:
1. reorganización de los tracks con metadatos (área, nivel, prerrequisitos y rutas), sin renombrar IDs;
2. Web3 como especialización de habilidades, en 3 tracks;
3. login con Google y Apple, con PKCE, y una excepción CSRF solo para el callback `form_post` de Apple;
4. acceso con una hoja desplegable en la que el email va primero.

Nada se ejecuta hasta que lleguen esas decisiones. Lo aprobado se escribirá aquí y en filas del ledger.

---

## 7. Trampas comprobadas (para no repetirlas)

- **Un valor por defecto de `config.py` no es el estado de producción.** Este mismo plan lo confundió
  con `PADDLE_ENVIRONMENT`. Hay que leer el endpoint público o pedir el valor al dueño, y marcarlo [def]
  si no se ha leído.
- **Un ID de ADR o de fila que no está en `master` no existe.** Se cita como «(prop.)».
- **`ci_local.sh` no corre `check_docs.py`**, y el pre-push solo lo corre si el push toca docs o
  contenido. Hay que ejecutarlo a mano antes del LISTO.
- **El esquema de `tracks.json` es `name_es/name_en/order/color/icon`**, nunca `title_*`: el cargador
  revienta con otra forma.
- **Una lección por skill y 150–300 palabras:** lo exigen los tests de contenido.
- **`selectedTrackId` solo vive en el `localStorage` del dispositivo**, y por defecto es `track01`.
- **El examen de nivel acepta cualquier track**, pero el onboarding solo lanza `track01`, y solo a quien
  no es principiante.
- **Los refresh opacos existen, no se usan y tienen un defecto** (no pasan `jwt_version`). El refresh
  real es un JWT con `jvs`.
- **La analítica es propia** (`analytics_events`); no hay PostHog en el navegador (ADR-50j).
- **El código de Stripe sigue en el repo**, pero el cobro es Paddle (H.29), que ya está en producción.
- **`REDIS_URL` vale por defecto `localhost`**, y en Railway no hay Redis [P].
- **No hay `@capacitor/ios` ni carpeta `ios/`.**
- **GitHub Actions no tiene runner** (H.13). Un rojo con `runner_id: 0` no es culpa del PR: se comenta
  una vez y no se relanza.
- **Los ficheros compartidos se proponen en el PR** («Delta del ledger» / «Fuera de alcance»), no en el #89.
