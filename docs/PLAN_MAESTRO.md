# Plan maestro de Whetzy

> **Normativo vivo desde el 2026-10-04** (aprobado por el dueño esa noche, con la orden de llevarlo
> «a un detalle en que ningún modelo cometa un error»). Es el norte del producto: **no repite el
> ledger**, que sigue siendo la fuente de verdad del progreso (ADR-40). Cada punto apunta a una fila,
> un ADR o un PR. Las cifras del banco no se copian aquí: salen de los scripts de §0.3.
>
> Las referencias `fichero:línea` son de `master` `05b46b1` (2026-10-04). **Antes de tocar
> nada, se vuelven a comprobar**: las líneas se mueven.

## 0. Cómo se usa este documento

### 0.1 Reglas que no se rompen

1. **`master` solo lo fusiona el dueño** (ADR-45). Una sesión trabaja en su rama, abre un PR y nunca
   hace push a `master`.
2. **Ficheros compartidos: solo S5** (`docs/SESIONES.md` §3). Son el ledger, `DECISIONS.md`,
   `STATUS.md`, `CHANGELOG.md`, `CLAUDE.md`, `README.md`, `package.json`, `requirements*.txt`,
   `.github/**`, `.githooks/**`, `ci_local.sh`, `ledger.py` y `check_docs.py`. Quien necesite un
   cambio ahí escribe el texto exacto en el #89 y lo aplica S5.
3. **Migraciones de una en una** (SESIONES §5). El PR con migración actualiza las tres líneas del
   HEAD: `CLAUDE.md`, la fila «Alembic HEAD» del ledger y `RUNBOOK.md`. Antes de abrirlo se avisa en
   el #89.
   - Hoy: **54 = `20261004_tracks_is_active`**.
   - Cola fijada: **55 = #127** (S.4), **56 = perfil público opt-in** (#144 rehecho).
   - Las demás van detrás, en el orden en que se fusionen.
4. **Nunca `create_all`; nunca borrar ni renombrar tracks o skills sin un mapa de progreso.** Desde la
   54, `content_loader` retira un track con `is_active=false` en vez de borrarlo, pero cambiar un ID
   deja huérfano el progreso que cuelga del ID viejo.
5. **Un PR solo es LISTO con estas cuatro cosas:**
   - contiene `master`;
   - nivel 1 verde (pre-push);
   - **`python scripts/check_docs.py` verde a mano**: `ci_local.sh` **no** lo corre [comprobado]. Así
     llegó el #145 con docs rotas;
   - nivel 2 VERDE (`scripts/ci_local.sh --carril <x> --sha <sha>`).
6. **Cada guarda nueva se muta**: se rompe a propósito, se ve en rojo y se restaura (CLAUDE.md,
   «Estilo»). **Un test que falla al azar no puede ser puerta**: se arregla o se saca. Hoy hay uno:
   `profileTab.test.tsx` (43.9).
7. **Después de cada fusión:**
   - Railway en SUCCESS (`list-deployments`);
   - `node scripts/check-deployed.mjs --sha <sha>` desde `frontend/` en PASS;
   - `/health` 200;
   - una comprobación de la función en producción.
8. **Todo texto de interfaz va en ES y EN nativos**, con la paridad de `frontend/src/test/i18n.parity.test.ts`
   en verde. Cada rol escribe en su fichero de `frontend/src/i18n/{es,en}/` (SESIONES §6).
9. **Contenido para el alumno:** lo escribe Sonnet desde un fragmento de fuente `reusar`, con revisión
   adversaria y corrector (ADR-59, `PLAN_CONTENIDO.md`). Haiku nunca escribe contenido.

### 0.2 Etiquetas

- **[V]:** comprobado con una herramienta sobre `master` el 2026-10-04.
- **[P]:** lo dice un informe o un documento que no se ha vuelto a comprobar.
- **[O]:** propuesta u opinión.

### 0.3 De dónde salen las cifras

| Cifra | Comando |
|---|---|
| Banco, tracks, skills, lecciones, términos | `python scripts/project_snapshot.py` |
| Preguntas pendientes por track | `python scripts/catalog_coverage.py` |
| Estado del backlog | `python scripts/ledger.py stats` / `blocked` / `next` |
| Coherencia docs ↔ código | `python scripts/check_docs.py` |

---

## 1. Tesis y métricas norte

**Cuña (ADR-60, confirmada por el dueño el 2026-10-04):** preparación de **certificaciones técnicas
en ES y EN**. El marketplace de creadores y el B2B se construyen después, sobre la misma base.

**Métricas norte** [O]. Hoy no hay ninguna medida porque no hay cohorte (H.10). Se instrumentan con
PostHog (ADR-50j). Cada una tiene que tener su evento antes de la oleada F:

| Métrica | Definición exacta | Evento |
|---|---|---|
| Activación D0 | % de altas que el mismo día UTC ven ≥ 1 lección y responden ≥ 10 preguntas | `lesson_viewed`, `answer_submitted` |
| Retención D7 | % de altas con ≥ 1 respuesta el día 7 (± 0) | `answer_submitted` |
| Conversión 30 d | % de altas con plan de pago o compra de certificación en 30 días | webhook de Paddle |
| Preparación | % que alcanza «listo para el simulacro» (#133) y aprueba un simulacro | `mock_exam_submitted` |

---

## 2. Estado de los actores, flujo a flujo

### 2.1 Alumno

| Paso | Hoy | Hueco | Fila |
|---|---|---|---|
| Alta y verificación | `POST /auth/verify-email` exige `new_password` y da **422** con `{token}` en prod [V] | #145 lo arregla, pero llega con `check_docs` en rojo (falta `MAPA_PRODUCTO.md`) [V] | 42.1 |
| Login social | Solo GitHub y Google (`oauth.py`); `state` en BD (`OAuthState`, `models/oauth.py:14`), sin cookie y **sin PKCE** [V]; **sin Apple** [V] | PKCE, `state` en cookie, Apple (ADR-13) | 41.14, punto nuevo 4 |
| Onboarding | 3 preguntas (`OnboardingScreen.tsx:14-45`). `onboarding_goal` (`user.py:109`) **no lo lee nada**. El examen de nivel es **siempre `track01`** (`OnboardingScreen.tsx:93`) [V] | Objetivo → especialidad → nivel de ese track | 42.3 |
| Especialidad activa | **No hay campo en `User`**: `selectedTrackId` vive solo en el store del cliente, con valor por defecto `'track01'` (`useAppStore.ts:321`) [V] | Persistirla (migración) | 42.3 |
| Estudiar | `startQuiz('study', 10)` (`HomeScreen.tsx:87`). La lección es puerta real: `_LESSON_GATED_MODES = {"study","review"}` (`quiz.py:184`), `needs_lesson` (`quiz.py:195-198`, `:275-278`) [V] | La lección no se ve como paso 1 | 42.4 |
| Lección | Una por skill (`test_at_most_one_lesson_per_skill`, `test_lessons.py:196`), **150–300 palabras** por idioma (`test_lessons.py:36-37`) [V]; mediana 217 [V] | Versión extensa a elección | 42.5 / oleada C |
| Panel | Igual para todos; no hay ninguna marca de «primera vez» salvo `whetzy_onboarded_<id>` en `localStorage` (`App.tsx:185`, `:393`) [V] | Panel por segmento, pistas de primera vez | 42.6, 42.7 |
| Simulacro | En todos los planes (ADR-58); banco reservado apagado (`MOCK_EXAM_RESERVED_POOL_ENABLED=False`, `config.py:301`) [V] | Umbral «listo» (#133) | 43.10 |
| Certificación | 39,99 $ pago único; `CERTIFICATION_PAYWALL=False` (`config.py:285`) [V]. El webhook de Paddle concede y revoca por reembolso [P] | Abrir el cobro | Oleada E |
| Perfil público | Datos **inventados** en `PublicProfileScreen.tsx` [V] | #144 rehecho como opt-in | 42.2 |

### 2.2 Creador

| Paso | Hoy | Hueco | Fila |
|---|---|---|---|
| Plan Creador | 99,99 $ (ADR-41); `CREATOR_PLAN_REQUIRED=False` (`config.py:266`) [V] | Abrir el cobro | Oleada E |
| Inscripción en un curso de pago | `enroll_student` (`instructor_marketplace.py:200`) dice «Sin pasarela todavía» (`:211`). `enroll_student_in_course` suma `price_cents` al payout **sin cobro** [V] | Compra confirmada antes de inscribir | 41.6 |
| Payout | Job `run_payouts` → `process_monthly_payouts` (`job_worker.py:168-169`) [V]. No hay flag global; cómo se impide hoy un pago real está **sin comprobar** | Activar | H.25 |

### 2.3 Empresa

| Paso | Hoy | Hueco |
|---|---|---|
| Página | `/es/empresas` y `/en/enterprise`: aviso honesto con `noindex` (#126) [V] | NECESITO de S6 (¿publicar sin precio?) |
| Producto | **No existen** organizaciones, asientos ni equipos en modelos ni endpoints [P, grep de un informe] | Oleada H |
| Precio | Hipótesis interna: 99 $ por asiento y año, mínimo 10 (ADR-47) [V] | Pilotos H.39 |

### 2.4 Dueño / admin

- **`/admin` existe** (`AdminScreen.tsx`) [V], con endpoints `require_admin` [P].
- **Falta:**
  - el admin de empresa (oleada H);
  - la moderación del marketplace: hoy solo hay reportar y bloquear usuarios (`moderation.py`) [P].

---

## 3. Arquitectura

**Hoy** [V]:
- **API:** FastAPI con 2 procesos gunicorn (`start.sh:42`, `--workers 2`) en Railway (región iad).
- **Arranque**, en este orden: `alembic upgrade head` → `content_loader` → `bootstrap_owner` → `seed` → gunicorn.
- **Tareas de fondo:** cada proceso arranca seis en su lifespan (`main.py`). La cola de trabajos usa `SKIP LOCKED` (#132); los bucles periódicos se protegen con un advisory lock [P].
- **Frontend:** la SPA está en Cloudflare Pages.
- **Rate limiter:** `REDIS_URL` vale por defecto `redis://localhost:6379/0` (`config.py:61`) [V]; en Railway eso no existe y el limitador cae a memoria por proceso [P, logs que leyó S5].

**Objetivo** [O]: un monolito modular. Nada de microservicios con cero usuarios.

| Orden | Cambio | Quién | Coste |
|---|---|---|---|
| 1 | **D1:** vaciar `REDIS_URL` en Railway; Redis real cuando haya tráfico | Dueño | 0 |
| 2 | **D4:** `alembic upgrade head && python -m app.services.content_loader` como pre-deploy de Railway; `start.sh` solo arranca gunicorn. Antes de cambiarlo, leer la documentación de Railway sobre pre-deploy | Dueño (panel) + S5 (PR) | Menos caída por despliegue |
| 3 | **D2:** entorno `staging` en Railway, ya aprobado en ADR-50p, **antes de abrir el cobro** | Dueño (clic) + S5 (RUNBOOK) | Un entorno |
| 4 | **D3:** worker aparte | — | No hasta que haya trabajos pesados reales |
| 5 | Copias: `scripts/db_backup.sh`, `db_restore.sh`, `db_restore_test.sh` (RUNBOOK «DB backup / restore»); ensayo mensual (33.1 DONE). **RPO ≤ 24 h y RTO ≤ 60 min están sin medir** [P] | S5 | Medirlos antes de la oleada E |

---

## 4. Oleadas

Cada punto lleva: qué tocar, qué reutilizar, el test (con su mutación) y cuándo está terminado. Lo
marcado **(D)** es una decisión del dueño, y no se implementa sin ella.

### Oleada A: seguridad y dinero (S1; `backend/app/core/**` es de S5)

**A.1 · 41.4 · `/quiz/answer` solo para la pregunta servida, una vez.** PR #127, en borrador.
- La migración `20261004_study_session_current_question` tiene hoy `down_revision =
  "20261002_newsletter_subscribers"` [V]. **Tiene que ser `"20261004_tracks_is_active"`** y pasar a
  ser la 55, con las tres líneas del HEAD.
- Pasos: `git merge origin/master`, arreglar `down_revision`, nivel 2, sacarlo de borrador.
- Test: responder dos veces la misma pregunta → 409; responder una pregunta no servida → 409.

**A.2 · 41.5 · El tutor no ayuda en un examen ni con preguntas reservadas, y no cobra si no hubo IA.**
- Dónde:
  - `endpoints/tutor.py:43-84`: el cupo se comprueba antes y se anota en `:82`;
  - `services/ai/tutor.py:112` (`explain_question`).
- Hechos [V]:
  - `Question.pool` vale `"practica"` por defecto (`content.py:186`); el banco reservado es `"simulacro"`;
  - `MockExamAttempt` está en `models/exam.py:24`;
  - `NullProvider.name = "fallback"` (`provider.py:32-36`).
- Cambio:
  1. Rechazar con 403 si `question.pool == "simulacro"`.
  2. Rechazar con 403 si el usuario tiene un `MockExamAttempt` en curso que contiene esa pregunta.
  3. No llamar a `tutor_quota.record` si el proveedor que respondió es `"fallback"`, usando
     `complete_named`, que devuelve el nombre del proveedor [P].
- Tests en `tests/integration/test_tutor.py`, cada uno mutado:
  - 403 por pregunta reservada;
  - 403 por examen en curso;
  - el cupo no cambia con `NullProvider`.

**A.3 · 41.6 · Un curso de pago solo se inscribe con la compra confirmada.**
- Dónde:
  - `instructor_marketplace.py:200` (endpoint);
  - `instructor_service.py`, en `enroll_student_in_course` (suma al payout).
- **Ahora, sin pasarela abierta:**
  - un curso con `price_cents > 0` responde 402 en `enroll` (sin fila de inscripción ni de payout);
  - un curso gratis sigue igual.
- **Después, con el cobro abierto:** la inscripción la crea el webhook de Paddle (como `certification_purchase`
  en `webhooks.py`), con el id de transacción como referencia externa e idempotencia por evento.
- Test: 402 sin compra y payout sin cambios; curso gratis → 201.
- Muta: quita el 402 → rojo.

**A.4 · 41.14 · OAuth con PKCE y `state` atado a una cookie.**
- Dónde:
  - `oauth.py`: el `state` se crea en `:122` y se valida en `:168-180`;
  - modelo `OAuthState` (`models/oauth.py:14`).
- Cambio:
  - `code_verifier` aleatorio en `/start`, guardado en el `OAuthState` (columna nueva → **migración**,
    detrás de la 56) **o** en una cookie HttpOnly firmada, sin migración. **[O] Recomiendo la cookie.**
  - `code_challenge` S256 en la URL del proveedor;
  - el callback exige que el `state` de la cookie coincida con el de la query y manda el `code_verifier`.
- Test en `tests/integration/test_oauth.py`: callback sin cookie → error; `state` cambiado → error.

**A.5 · 41.17 · Cupo del tutor por tokens; la sesión de BD no se queda abierta durante la llamada al LLM.**
- Hechos [P]:
  - `GroqProvider.complete` no lee `usage`;
  - `TutorUsage` solo cuenta explicaciones;
  - `explain()` mantiene la sesión durante la llamada.
- Cambio:
  - el proveedor devuelve el texto y los tokens;
  - columna `tokens` en `TutorUsage` (**migración**, en cola);
  - el límite diario por tokens va en `config.py` (S5);
  - cargar los datos, cerrar o liberar la sesión, llamar al LLM y abrir otra sesión para anotar.
- **Además, la carrera de comprobar el cupo antes de la llamada** [V]: reservar el cupo antes de llamar
  (`UPDATE … WHERE explanations < límite RETURNING`) y devolverlo si el LLM falla.

**A.6 · 41.18 · El logout invalida de verdad.**
- Hechos [V]:
  - `logout` (`auth.py:336`) solo audita y borra cookies;
  - `/auth/refresh` (`auth.py:253`) usa un refresh JWT con `jvs`;
  - en `security.py:317-410` hay refresh opacos con rotación (`create_opaque_refresh_token`,
    `verify_opaque_refresh_token`, `refresh_token_rotation`), **sin usar desde ningún endpoint**;
  - existe `RefreshToken.revoked` (`models/auth.py:53`).
- Cambio [O]:
  1. `/auth/refresh` pasa a los refresh opacos, que ya existen y se pueden revocar uno a uno.
  2. `logout` revoca el refresh actual.
  3. «Cerrar sesión en todos» sube `jwt_version`.
- Test: el refresh de antes del logout da 401; el de otro dispositivo sigue valiendo.

**Sale cuando:** cada punto tiene su test mutado en rojo, el #127 está fusionado como 55, y
`grep` de rutas que crean dinero sin cobro da 0 (revisión de COORD).

### Oleada B: flujo de estudio coherente (S1 + S3)

**B.1 · 42.1 · `/verify-email`.**
- Pasos sobre el #145: añadir `VerifyEmailPage` y `/verify-email` a `docs/MAPA_PRODUCTO.md`,
  `git merge origin/master`, `check_docs` verde y nivel 2.
- Prueba en prod: el enlace del correo (`email.py:483`, `/verify-email?token=`) verifica la cuenta.

**B.2 · 42.3 · Objetivo → especialidad → examen de nivel de esa especialidad.**
1. **Migración** (en cola): `User.focus_track_id` (FK a `tracks.id`, nullable).
2. Onboarding:
   - una pantalla más con el catálogo, filtrada por el objetivo (sin certificación → tracks de
     fundamentos; con certificación → las 11);
   - guarda `focus_track_id`;
   - lanza `startPlacement(<ese track>)` en lugar de `'track01'` (`OnboardingScreen.tsx:93`).
3. **El backend ya acepta cualquier track** en el examen de nivel (`placement.py:53-58`, filtra por
   `Module.track_id`) [V]. Un track sin preguntas respondibles no tiene examen de nivel: se comprueba
   con una consulta, por track, antes de ofrecerlo.
4. **Cambiar de especialidad nunca borra nada:** el progreso es por skill
   (`UniqueConstraint("user_id","skill_id")`, `user.py:142`) [V].
5. Tests:
   - e2e `frontend/e2e/onboarding.spec.ts`: elegir AZ-900 → el examen de nivel es de AZ-900;
   - integración: cambiar `focus_track_id` no toca `user_skill_states`.

**B.3 · 42.4 · La lección como paso 1 visible.** «Estudiar» (`HomeScreen.tsx:87`) lleva a la lección de
la skill siguiente si no está vista (`lesson_gate.viewed_skill_ids`), en vez de al quiz vacío con
`needs_lesson`. Test e2e de un alumno nuevo.

**B.4 · Prior de BKT desde el examen de nivel (S3, (D)).**
- Hoy: `p_l0 = 0.1` (`bkt.py:22`) y `p_known` vale 0.1 por defecto (`user.py:152`); el examen de nivel no escribe
  `UserSkillState` [P, S3].
- S3 avisa del riesgo: con 1–2 ítems por skill, el prior puede ser más ruidoso que el 0.1 fijo.
- Necesita la decisión del dueño (en el #89).

**Sale cuando:** el e2e «alumno nuevo elige AZ-900 → examen de nivel de AZ-900 → lección antes de la
primera pregunta» está en verde en el nivel 2.

### Oleada C: lecciones corta y extensa (COORD contenido + S1 esquema)

Decisión del dueño (ADR-60): **el alumno elige** entre la versión corta y la extensa, de 15 a 20 minutos.

1. **Esquema (S1), sin romper lo que hay:**
   - campos opcionales `body_long_es` y `body_long_en` en el JSON y en `Lesson` (`content.py:200-224`,
     **migración**);
   - `_upsert_lesson` (`content_loader.py:228-247`) los copia con `data.get(...)`;
   - `LessonRead` (`schemas/content.py:150-164`) los expone.
   - **No** se crea una segunda lección por skill: `test_at_most_one_lesson_per_skill` lo prohíbe.
2. **Tests (`backend/tests/content/test_lessons.py`):**
   - la regla de 150–300 palabras se queda para `body_*`;
   - regla nueva para `body_long_*`, con un rango de palabras ≈ 15–20 min de lectura más ejercicios.
     **El número exacto sale del piloto** y se escribe en el test con su razón;
   - los dos idiomas o ninguno;
   - fuente obligatoria.
3. **Pantalla (S1):** `LessonScreen.tsx` ofrece «Versión corta · ~3 min» / «Versión extensa · 15–20 min» cuando
   existe la larga. Se guarda la preferencia.
4. **Contenido (COORD):** piloto de 10 desde la fuente (ADR-59), con la regla de parada de
   `PLAN_CONTENIDO.md` §4. Después, track a track, en el orden de la cuña.

**Sale cuando:** el piloto pasa (≤ 3/10 blocker/major), su coste queda anotado en `PLAN_CONTENIDO.md`
§7 y el e2e permite elegir versión.

### Oleada D: panel por segmento y pistas de primera vez (S1)

- **Panel:** `HomeScreen.tsx` (secciones en orden: cabecera, preparación + siguiente paso, repaso,
  racha, rutas, misiones) [P].
  - La cabecera y «Siguiente paso» dependen de `focus_track_id` y de `onboarding_goal`:
    - certificación → preparación del examen y días hasta la fecha objetivo;
    - fundamentos → ruta.
  - Las demás secciones se pliegan en tarjetas compactas.
- **Pistas:** 3–5 pasos la primera vez, más una ayuda en contexto la primera vez que se abre cada
  pantalla (tutor, repaso, simulacro).
  - Se guarda en el servidor (campo en `User` o tabla de «vistos»; **migración**) para que no se
    repita en otro dispositivo.
  - Accesible: foco, Esc y texto para lectores de pantalla.
- **Sale cuando:** un test comprueba que el panel cambia según el objetivo, y un e2e que las pistas
  salen una vez y no vuelven.

### Oleada E: abrir el cobro (dueño + S1/S5)

Flags hoy, todos apagados [V]:
- `CERTIFICATION_PAYWALL` (`:285`);
- `CREATOR_PLAN_REQUIRED` (`:266`);
- `FREE_DAILY_QUOTA_ENABLED` (`:290`);
- `ANNUAL_PLAN_ENABLED` (`:348`);
- `PADDLE_ENVIRONMENT="sandbox"` (`:337`).

**Hay código de Stripe** (`/billing/checkout`, `/billing/webhook`) [P], **pero el cobro es Paddle**
(H.29). No se construye nada nuevo sobre Stripe.

Orden:
1. Staging (D2).
2. Precios y `pri_…` en Paddle sandbox, también los anuales de 40.9 (H.35, **(D)**).
3. Compra y reembolso de prueba en staging.
4. `PADDLE_ENVIRONMENT=production`.
5. Encender los flags de uno en uno, verificando cada uno.

**Sale cuando:** una compra real y un reembolso real pasan por los webhooks y quedan reflejados en
`User.subscription_*`.

### Oleada F: distribución (dueño + S6 + S1)

- **H.10:** beta de 30 personas.
- **Pitch (S6):** rehacerlo con las cifras de §0.3 y ADR-41/58/60.
- **Tiendas:**
  - Android tiene `@capacitor/android` y carpeta `frontend/android` [P];
  - **iOS no tiene ni `@capacitor/ios` ni carpeta** [V];
  - Sign in with Apple no existe [V] y es obligatorio si hay OAuth (ADR-13);
  - el webhook de RevenueCat existe sin el SDK del cliente [P];
  - bloqueado por H.2, H.3 y H.14.
- **Sale cuando:** D1/D7 están medidos con usuarios reales.

### Oleada G: creador

- A.3 cerrado.
- Payouts (H.25).
- Moderación de cursos.
- Instructores fundadores (H.40).
- **Sale cuando:** una venta real llega a payout.

### Oleada H: B2B

- Modelos y endpoints de organización, asiento y equipo, con su admin de empresa.
- Pilotos (H.39).
- Página `/empresas` (NECESITO de S6).
- **Sale cuando:** un piloto con equipo usa el panel.

### Contenido, en paralelo (COORD)

- Lo pendiente por track lo da `catalog_coverage.py`.
- Primero el AI-901 (track45), luego el resto de la cuña.
- Web3 y la reorganización de tracks: propuesta pendiente (§6).

---

## 5. Cola del dueño, ordenada por lo que desbloquea

| # | Qué | Desbloquea |
|---|---|---|
| 1 | Fusionar lo LISTO de uno en uno y probar a mano login → una respuesta → logout (CSRF #131) | Todo |
| 2 | D1 (vaciar `REDIS_URL`) y D4 (pre-deploy) | Límites coherentes; despliegues más cortos |
| 3 | D2 staging | Oleada E |
| 4 | Cobro con Paddle + precio anual (H.29, H.35) | Ingresos |
| 5 | Beta de 30 (H.10) | Toda métrica real |
| 6 | Cuentas de Apple y Google (H.2, H.3) | Tiendas, Sign in with Apple, IAP |
| 7 | Revisión legal (H.20) | Textos legales finales |
| 8 | Payouts (H.25) e instructores (H.40) | Oleada G |
| 9 | Pilotos B2B (H.39) y página `/empresas` | Oleada H |
| 10 | Facturación de GitHub Actions (H.13) | CI en la nube |
| — | Decisiones: B.4 y C.3 (S3), 41.10 CORS nativo | — |

**H.12 (clave de Groq), decisión del dueño del 2026-10-04: la clave se mantiene, sin rotar, con el riesgo aceptado.**
- Dónde está la clave: en el commit `ba37a0e` (`docs/STATUS.md`) [V].
- **Ese commit está en la historia de `master`**: `compare ba37a0e...master` da `behind_by = 0` [V].
  Borrar las ramas `railway/*` no la saca del repositorio: cualquiera con acceso al repo puede leerla.
- La única mitigación real es rotarla.

---

## 6. Después de este plan (orden del dueño): los 4 puntos nuevos

Cada uno se trae como propuesta detallada antes de tocar nada:

1. **Web3 y reorganización de los tracks «de la manera más lógica».** Una reorganización exige:
   - un mapa `id_viejo → id_nuevo` para tracks, módulos y skills;
   - una migración de datos que mueva `user_skill_states`, respuestas, lecciones vistas, certificados y
     compras;
   - `is_active=false` para lo retirado;
   - ningún ID reutilizado con otro significado;
   - ADR propio;
   - prueba con datos (`ci_local.sh`, «migración con datos») antes de fusionar.
2. **Lecciones corta/extensa:** es la oleada C.
3. **Login con Google y Apple,** en backend y frontend (ADR-13).
4. **UX del inicio de sesión** al estilo de las apps actuales: se investiga y se propone antes de
   construir.

## 7. Trampas comprobadas (para no repetirlas)

- `ci_local.sh` no corre `check_docs.py`: hay que pasarlo a mano antes del LISTO.
- El esquema de `tracks.json` es `name_es/name_en/order/color/icon`, nunca `title_*`: el cargador revienta.
- Una lección por skill y 150–300 palabras: los tests de contenido lo exigen.
- `selectedTrackId` no se persiste: por defecto vale `track01`.
- El examen de nivel acepta cualquier track, pero el onboarding siempre pide el `track01`.
- Los refresh opacos existen y no se usan; el refresh real es un JWT con `jvs`.
- El código de Stripe sigue en el repo, pero el cobro es Paddle (H.29).
- `REDIS_URL` vale por defecto `localhost`: en Railway no hay Redis.
- No hay `@capacitor/ios` ni carpeta `ios/`.
- GitHub Actions no tiene runner (H.13): su rojo con `runner_id: 0` no es del PR; se comenta una vez y no se relanza.
