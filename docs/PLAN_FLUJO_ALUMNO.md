# Plan — Flujo del alumno listo para pruebas (anexo al plan ultracode, serie 43)

> **Normativo-vivo.** Anexo del dueño del 2026-10-17, sobre `master` `0de27ad`. Se copian sus §0-§3 y §5-§6 tal cual.
> El dueño marcó con [V] los hechos que reabrió en su sesión. La Oleada 0 repitió estos con el código de la rama:
> - `security.py:174-181` acepta `Authorization: Bearer` antes que la cookie;
> - `lesson_gate.py` cuenta como vista una lección con `attempts > 0`;
> - `CATALOGO_MAESTRO.md:60` da 0 proyectos.
>
> Decisiones: ADR-65. Filas: serie 43 del ledger.
>
> **Choque abierto (H.60):** D7 (práctica solo con la lección vista) más D4 (la prueba no marca lecciones vistas) anula
> el test-out por módulo de ADR-61 §9, que el código ofrece (`services/placement.py:343`, `can_skip`). Quien sale
> «avanzado» tendría que leer todas las lecciones antes de practicar. Lo decide el dueño antes de 43.5.

> **Nota de la Oleada 0 a D1 (comprobado en el código, 2026-10-17):** Safari también bloquea como de terceros la
> cookie de *refresh*. Con «el refresh sigue por cookie», la sesión en iPhone duraría 30 min
> (`ACCESS_TOKEN_EXPIRE_MINUTES`, `config.py:68`), no «lo que dura la pestaña». El backend ya acepta el refresh en
> el cuerpo de `POST /auth/refresh` (`auth.py:283`), y el login y el registro ya devuelven los dos tokens en JSON
> (`schemas/user.py:96-99`). Por eso 43.1 guarda en memoria los dos tokens y manda el refresh en el cuerpo, que
> es el efecto que D1 pide.

## 0. Respuesta corta: ¿es posible?

**Sí, casi todo, en la misma sesión que hace la Oleada 0. Hay dos excepciones que no dependen del código:**
1. **El arreglo definitivo de Safari/iPhone es infraestructura del dueño** (10 min):
   - registro DNS `api.whetzy.com` → Railway (dominio propio del servicio `api`);
   - variables `COOKIE_DOMAIN=.whetzy.com` y `VITE_API_URL`.

   El código deja todo listo y además trae un **puente** que funciona sin DNS (ver 43.1).
2. **Proyectos: 0 contenido** (`CATALOGO_MAESTRO.md:60` [V]), y ADR-62 pausa el contenido. Se arreglan el sitio, la
   persistencia y la validación; la entrada solo aparece en un track cuando tenga proyectos.

«100 % funcional para pruebas» se define abajo (§6) como una puerta medible, no como una promesa.

## 1. Cómo no rompe el plan anterior

- `docs/PLAN_ULTRACODE.md` y las series 41/42 **no se tocan**. Este plan es un anexo:
  `docs/PLAN_FLUJO_ALUMNO.md` (nuevo, normativo-vivo) más la **serie 43** del ledger.
- **Orden:**
  1. La sesión de la Oleada 0 **termina su PR de documentación** (41.x) sin interrupción.
  2. Después ejecuta la serie 43 (prioridad 0, lo que necesitan los probadores).
  3. Luego, lo que quede de la 42.
- **Solapes resueltos** (donde se solapan manda la 43; la Oleada 0 lo anota en la 42.x):
  - 42.1 estimador → hecho en #219 [V]; 43.3 lo reutiliza.
  - 42.2/42.3 E2E → #220 dejó 54/56; 43.8 cierra.
  - 42.6 readiness → se hace dentro de 43.4.
  - 42.8 prior/siembra → sustituida por 43.3 (siembra estratificada).
  - 42.10 historial → hecho en #218 [V].
  - El resto de la 42 (duelos, offline, blueprint, higiene) sigue igual, después.
- **Ledger.** Con 304 B de margen (61.136 de 61.440 B [V]), la serie 43 entra **después** de la 41.1, que libera
  ≥ 6 KB. Entra en filas cortas; el detalle vive en `PLAN_FLUJO_ALUMNO.md`.

## 2. Decisiones (tomadas por delegación expresa del dueño, 2026-10-17 → ADR-65)

| # | Decisión |
|---|---|
| D1 | Sesión en iPhone. Definitivo: API en `api.whetzy.com` + `COOKIE_DOMAIN` (dueño). Puente inmediato: el frontend guarda el **access token en memoria** y lo manda como `Authorization: Bearer` (el backend ya lo acepta: `security.py:174-181` [V]); el refresh sigue por cookie. En Safari sin DNS, la sesión dura lo que la pestaña. |
| D2 | Onboarding: registro → objetivo (aprender / certificarme / ambos) → **elegir track de aprendizaje** (rejilla de los 24 tracks agrupados) → certificación opcional relacionada → experiencia → **prueba de nivel del track** (o «empiezo de cero») → resultado → **Hoy**. Se quita la pregunta de idioma (ya está en el registro) y la de horas pasa al perfil. |
| D3 | Prueba de nivel de **20 preguntas**: 15 estratificadas (5 básicas, 5 intermedias y 5 avanzadas, repartidas por módulos) + 5 adaptativas en la banda frontera. Banda de una pregunta: su `difficulty_tier` si lo tiene; si no, el tercio del módulo dentro del track (16 tracks no tienen tier [V]). θ con la EAP de #219. |
| D4 | Siembra tras la prueba, por módulo y no por pregunta suelta. Un módulo con ≥ 70 % deja sus skills en 0,6 (practicables, no «dominadas»); el resto, con encogimiento hacia 0,1. Nunca baja una skill con historial (D-18). La prueba **no** marca lecciones como vistas. |
| D5 | **Ruta activa** = `target_track_id` en servidor. Se cambia desde Rutas/catálogo («Hacer esta mi ruta») y desde Yo. Al cambiar a un track sin progreso, se ofrece su prueba de nivel. Nunca se borra progreso: todo vive por skill y por track [V `models/user.py:168`]. |
| D6 | **Hoy filtrado por la ruta activa**: cabecera «Tu ruta: <nombre>» con «Cambiar». La banda de preparación, el siguiente paso, los repasos y el territorio salen solo de ese track. «Otras rutas en curso» va abajo. |
| D7 | **Lección primero**, siempre, fuera de exámenes y quizzes de evaluación. «Estudiar» abre la siguiente lección no vista del track; si están todas vistas, practica. Desbloquear la práctica exige la lección vista (se quita `attempts > 0` de `lesson_gate.py:54` [V]). Los duelos, solo sobre skills con la lección vista por los dos. |
| D8 | **Proyectos** dentro de cada track, como cierre de módulo (tras sus lecciones), visibles solo si el track tiene proyectos. El progreso se guarda en servidor, y los pasos con tests deterministas se validan en servidor. |
| D9 | **Playground** contextual: «Probar este código» en cada lección (las 730 tienen `example_code`), fragmentos guardados por skill y acceso secundario desde Rutas. Sale de Hoy. |
| D10 | Registro sin fricción: errores 409/422 traducidos y por campo; email normalizado a minúsculas (antes, comprobar colisiones en la base); filtro de palabras por palabra completa para los términos cortos; «onboarding hecho» en servidor. |

## 3. Serie 43 — oleadas (cada una: rama + PR, test rojo → verde, suite entera, verificador §7)

| Fila | Qué | Ficheros clave | Tests (rojos hoy) |
|---|---|---|---|
| 43.1 (S) | Sesión iPhone: token en memoria y `Authorization`; los pasos DNS/Railway del dueño en `RUNBOOK`; fila H para el DNS | `frontend/src/services/api.ts` (`getHeaders` :113), `AuthScreen.tsx`, `useAppStore.ts`, `backend/app/core/cookies.py` | Playwright con cookies de terceros bloqueadas: registro → Hoy sin volver a la portada |
| 43.2 (S) | Registro: mensajes ES/EN por campo (409, 422), email en minúsculas en registro y login, filtro por palabra completa, recorte del usuario antes de validar | `auth.py:94-150,222`, `schemas/user.py`, `username_filter.py:65`, `AuthScreen.tsx:117-151`, i18n | backend: `Maria@Gmail.COM` se registra y entra en minúsculas; «computo» pasa. Frontend: el 409 muestra texto traducido |
| 43.3 (L) | Onboarding D2 + prueba D3 + siembra D4 + `onboarding_completed_at` (migración) + resultado → Hoy | `OnboardingScreen.tsx`, `PlacementScreen.tsx:224`, `services/placement.py`, `engine/placement.py`, `models/user.py`, `App.tsx:189-192`, `auth.py:424-431` | 20 preguntas exactas, 5/5/5 + 5; banda por tercio de módulo en un track sin tier; siembra por módulo; otro navegador no repite el onboarding |
| 43.4 (M) | Ruta activa D5 + Hoy D6 (+ readiness sobre todas las skills del dominio, de la 42.6) | `HomeScreen.tsx:35-38,98`, `TracksScreen.tsx`, `ProfileScreen.tsx`, `useAppStore.ts:228-233`, `progress.py`, `domain_mastery.py:66` | cambiar de ruta persiste tras recargar; Hoy no muestra skills de otro track; el progreso del track anterior queda intacto |
| 43.5 (M) | Lección primero D7 | `HomeScreen.tsx:98`, `quiz.py:252,344`, `lesson_gate.py:54`, `QuizScreen.tsx:399-433`, `duels.py:66`, `MarketplaceScreen.tsx:153` | con una cuenta nueva, «Estudiar» abre la lección; tras la prueba, no se puede practicar sin la lección vista |
| 43.6 (M) | Proyectos D8: entrada en el detalle del track/módulo, `start`/`submit-step` desde la UI, validación en servidor | `ProjectScreen.tsx:37,88,95`, `endpoints/project.py:120-143`, `TracksScreen.tsx`, `HomeScreen.tsx:300` | el progreso sobrevive a salir; `passed=true` sin tests no completa |
| 43.7 (S-M) | Playground D9 | `LessonScreen.tsx`, `PlaygroundScreen.tsx:50`, `playgroundDb.ts`, `HomeScreen.tsx:295` | «Probar este código» abre el ejemplo de la lección; el fragmento guardado reaparece |
| 43.8 (M) | Puerta «lista para pruebas»: E2E del recorrido completo (registro → onboarding Ciberseguridad → prueba de 20 → Hoy de Ciberseguridad → lección → práctica → cambiar a Python → volver sin perder progreso), en Chromium y, si existe, en WebKit; specs desfasados en verde | `frontend/e2e/alumno.spec.ts` (nuevo), `playwright.config.ts`, `scripts/ci_local.sh` | el propio spec |

**Forma por oleada (Workflow):**
1. Autor de tests (Sonnet, solo especificación).
2. Implementador backend e implementador frontend, en worktrees separados.
3. Migración (agente propio, `downgrade` probado, HEAD triple).
4. Verificador §7 (Haiku).

El E2E va serializado desde el hilo principal (puertos fijos). Sin `content/**`.

## 5. Prompt para la sesión de la Oleada 0 (literal)

```
Anexo del dueño (2026-10-17): docs/PLAN_FLUJO_ALUMNO.md (PR del anexo; si no está en master, léelo de la rama claude/gracious-hopper-49un93).
1. No interrumpas la Oleada 0: termina y entrega su PR (41.x) como estaba previsto.
2. En F1, tras 41.1, inserta también la serie 43 (filas cortas de PLAN_FLUJO_ALUMNO.md §3) entre la 42 y «## 3.», y añade a §3 la fila H «DNS api.whetzy.com + COOKIE_DOMAIN (dueño)». En 42.1, 42.6, 42.8 y 42.10 anota «ver 43.x / hecho en #219, #218» como dice §1 del anexo.
3. En F4, redacta ADR-65 «Flujo del alumno» con las decisiones D1-D10 de §2, como DECIDIDO por delegación expresa del dueño del 2026-10-17.
4. Después de la Oleada 0, ejecuta la serie 43 en orden 43.1 → 43.8, una rama y un PR por fila, con Workflow, y solo entonces lo pendiente de la 42. Sin contenido nuevo (ADR-62).
5. Termina cuando la puerta de §6 del anexo esté en verde y entrega al dueño la lista de lo que necesita hacer él (DNS).
```

## 6. Puerta «lista para pruebas» (verificación de extremo a extremo)

- `bash scripts/ci_local.sh` entero y `npx playwright test` sin rojos (saltos con causa escrita).
- `e2e/alumno.spec.ts` verde en Chromium, y también con cookies de terceros bloqueadas (simula el iPhone).
- Tras la fusión del dueño:
  - `node scripts/check-deployed.mjs` PASS y `/health` 200;
  - el mismo recorrido a mano en whetzy.com desde un iPhone: registro → Hoy sin volver a la portada.
- Logs de Railway: `POST /auth/register` 201 seguido de `GET /auth/me` 200 (hoy 401 [V]).
- `catalog_coverage.py` con las mismas cifras de partida, como prueba de que no se tocó contenido.
- Pendiente fuera del código, nombrado en el PR final: DNS `api.whetzy.com` (dueño) y contenido de proyectos (ADR-62).
