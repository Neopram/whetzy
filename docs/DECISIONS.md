# Whetzy — Architecture Decision Log

## ADR-1 — Monolith, not microservices (2026-09-07)

**Decision:** FastAPI monolith with internal service boundaries (`content`, `engine`, `gamification`).

**Reason:** Single-person team, low traffic in early stage, microservices complexity not justified.

**Alternatives discarded:** Kubernetes + separate services (too much operational overhead).

---

## ADR-2 — Groq + qwen3.8-27b for AI tutor (2026-09-07)

**Decision:** Groq inference API with `qwen/qwen3.8-27b`.

**Reason:** Free tier, low latency (<500ms), no GPU cost. Quality sufficient for explanation use case.

**Alternatives discarded:** OpenAI (cost), llama-3.3-70b (not available on Groq free tier).

---

## ADR-3 — Alembic with auto-stamp in start.sh (2026-09-08)

> **Sustituida:** el arranque ya no hace `alembic stamp head`; solo `alembic upgrade head` (`backend/scripts/boot_tasks.sh`). Nota añadida el 2026-10-22 por ADR-69 #13 (H.58).

**Decision:** `start.sh` runs `alembic stamp head && alembic upgrade head` at startup.

**Reason:** Pre-existing production DB had no `alembic_version` row. Stamp avoids "target database is not up to date" on first deploy.

**Alternatives discarded:** Recreate DB from scratch (loses production users).

---

## ADR-4 — DKT with torch optional + EWA fallback (2026-09-08)

**Decision:** PyTorch LSTM for DKT only instantiated when `torch` is importable; falls back to exponential weighted average.

**Reason:** Railway free tier may OOM on PyTorch imports. EWA gives reasonable predictions without a model.

**Alternatives discarded:** Torch required (risky OOM in production).

---

## ADR-5 — Ledger-based orchestration (2026-09-08)

**Decision:** Autonomous sessions driven by `docs/AUTONOMOUS_STATE.md` ledger. Each session reads the ledger, picks the lowest-priority TODO without blocking deps, executes, marks DONE with evidence, commits, repeats. Sessions self-schedule via `mcp__scheduled-tasks__create_scheduled_task`.

**Reason:** A monolithic prompt degrades attention. State must live outside context. Each session makes its own scheduling decision, so the chain breaks cleanly when the backlog is exhausted.

**Alternatives discarded:** Cron without ledger check (burns budget), single giant prompt.

---

## ADR-6 — Parallel workers over shared files (2026-09-08)

**Decision:** Parallel worker agents operate on disjoint file sets (defined in G1–G7 groups in the ledger). No git worktrees needed.

**Reason:** Worktrees add merge cost. Disjoint file sets guarantee no conflicts.

**Alternatives discarded:** Always using worktrees (merge overhead per task).

---

## ADR-7 — Recurring cron task for session continuity (2026-09-08)

**Decision:** Autonomous loop runs as a cron task (originally `23 */6 * * *`; changed to `23 */4 * * *` by H.21 2026-09-18) instead of a one-shot. Pre-flight checks ledger; exits quickly if backlog is exhausted.

**Reason:** A one-shot chain dies permanently if a context-limit cut arrives before the next session is scheduled. Cron retries automatically.

**Alternatives discarded:** One-shot chain (fragile), no automation (requires manual session starts).

---

## ADR-8 — Raw token never stored; SHA-256 hash only (2026-09-08)

**Decision:** `PasswordResetToken` and `EmailVerificationToken` store only `sha256(raw_token)`. The raw token travels only in the email link.

**Reason:** If the token table is exfiltrated, tokens cannot be used without having received the email.

**Alternatives discarded:** Storing raw tokens (standard anti-pattern), bcrypt for tokens (overkill — token entropy already high, SHA-256 is sufficient for single-use secrets).

## ADR-9 — Executable practice is measured per track, and some tracks are exempt (2026-09-15)

**Context:** Red line 9 says a capability nobody has used is not an advantage,
and the competitive scorecard leans on the share of questions a learner actually
*runs* rather than picks an option for. That share is currently **6,6 %** across
the bank, and it fell from 15,57 % to 7,33 % between two sessions with nobody
deciding it should — it simply diluted as multiple-choice questions were added
to new tracks. Nothing measured it, so nothing noticed.

The obvious fix — "every track reaches 15 %" — is worse than the problem. You
cannot execute "should this be a microservice", a `docker build`, a CI pipeline
or an AWS console decision inside a Pyodide worker. Forcing the ratio there
produces fake exercises: a `fill_blank_exec` whose "execution" is a string
comparison. That inflates the very metric the scorecard reads, which is red
line 1 dressed up as progress.

**Decision:** `scripts/check_question_bank.py` reports the executable share
**per track**, against a 15 % target, with two carve-outs and a ratchet:

1. **Exempt tracks** (`EXEC_EXEMPT_TRACKS`): track05 (architecture), track08,
   track10 and track11 (AWS). Their format of practice is scenario + decision
   (`multiple_choice` with context). They are removed from the denominator
   rather than counted as failures.
2. **Exempt modules** (`EXEC_EXEMPT_MODULES`) inside tracks that do chase the
   bar: `mod0401` (Git), `mod0406` (Docker), `mod0407` (CI/CD). With these out,
   track04's honest number is **7,6 %** (21/276) rather than 5,1 % (24/474) —
   the exemption makes the figure *harder* to hit, not easier, because the
   denominator loses the modules that were never going to contribute.
3. **A ratchet** (`EXEC_FLOOR`), the same idiom as `MIN_LESSONS`: today's
   measured number per track, which may only ever rise. Falling below it is a
   hard failure; being below the 15 % target is a WARN, because closing it is
   authoring work and a tool that blocks on work-in-progress just teaches people
   to silence it.

**track09 (PCEP) is deliberately not exempt** despite sitting at 0 %. It is a
*Python* certification, Python runs in the browser, and it is the wedge of lane 1
(decision #25). Its zero is a real gap, and exempting it would have hidden the
most commercially important hole in the bank behind a reasonable-looking rule.

**Reason:** A bar that every track is forced to clear stops measuring anything
the moment one track cannot honestly clear it. Naming the exemptions, with the
reason next to each, keeps the remaining number meaningful — and keeps the
scorecard from being quietly inflated by exercises that only pretend to run.

**Alternatives discarded:** One global ratio (hides which track is empty, and
was how the eight-point fall went unnoticed); a hard failure at 15 % (turns the
build red for authoring not yet done); exempting every non-Python track (would
have swallowed track09, the one that matters most commercially); counting
`code_output` as executable (the learner predicts output, they do not run it —
counting it would have reported ~22 % today by redefining the word).

---

## ADR-10 — JavaScript runtime via Blob-URL Web Worker, not eval or iframe (2026-09-18)

**Decision:** `useRuntime('js')` in `frontend/src/hooks/useRuntime.ts` uses a
Blob-URL Web Worker with `new Function('console', code)(fakeConsole)` inside the
worker. The worker is terminated after `timeoutMs` (default 5 000 ms).

**Reason:** Three constraints ruled out the alternatives in order:

1. `eval()` on the main thread: blocked by the app's `Content-Security-Policy`
   (`script-src 'self'`), and would block the UI while running.
2. `<iframe sandbox>`: would require a relaxed CSP (`sandbox allow-scripts`),
   adds a second document lifecycle, and DOM APIs would be reachable — the goal
   is a headless execution environment, not a browser.
3. An origin-isolated Worker loaded from a file (e.g. `/worker.js`): requires
   a separate build artifact, complicates the Vite setup, and is unnecessary
   when `URL.createObjectURL` with `{type: 'application/javascript'}` achieves
   the same isolation from a string literal in the component.

A Blob-URL Worker satisfies all three constraints: it runs off the main thread,
the Blob URL has no script-src CSP restriction in Chrome/Firefox/Safari, it
cannot access the DOM, and `worker.terminate()` provides hard timeout semantics
without a `try/catch` around `setTimeout` on the main thread.

**`new Function` instead of raw `eval`:** `new Function('console', code)(c)`
scopes `console` as a parameter, preventing the worker's native `console` from
printing to DevTools (where it would be invisible to the question runner) and
allowing the captured `logs` array to be `postMessage`-d back.

**Alternatives discarded:** `eval` on main thread (CSP + blocks UI); `<iframe
sandbox>` (CSP relaxation needed, DOM reachable); server-side execution (latency,
stateful server, no offline); Pyodide for JS (800 KB overhead for a language the
browser already runs natively).

---

## ADR-11 — Contenido solo desde fuentes gratuitas y legales (2026-09-18)

**Decisión:** ninguna pregunta, lección, término de glosario, bootcamp o proyecto se
escribe a partir de un libro de pago ni de un PDF obtenido fuera de su canal legal.
Las fuentes se clasifican en tres marcas, y solo la primera admite reutilizar texto:

1. **[reusar]** — MIT / Apache-2 / BSD / CC BY / CC0 / PSF / dominio público
   (NIST, RFC, docs de gobierno de EE. UU.). Puede entrar en la app con atribución.
2. **[H.LIC]** — CC BY-SA. Solo si el dueño acepta que lo derivado herede la licencia.
3. **(cita)** — gratis online pero CC BY-NC-* o propietario (AWS, Azure, GCP,
   CompTIA, ISC2, Cisco, MDN). Se lee, se aprende, se escribe original en ES y EN,
   se enlaza. Nunca se pega.

Inventario por área y track en `docs/CATALOGO_MAESTRO.md` §2.1.

**Razón:** decisión del dueño el 2026-09-18 tras el análisis de Educative y de la
lista de libros por track. Comprar un libro no da derecho a copiarlo, y «parafrasear»
texto protegido párrafo a párrafo es obra derivada. Con lo que ya es libre hay
material completo para los 27 tracks — incluidos libros enteros CC BY para los tres
tracks de 18.4 (Erickson, Peterson/Davie) — así que la restricción no encarece nada:
la autoría de Whetzy siempre fue original y citada (regla 5 del orquestador).

**Alternativas descartadas:** comprar manuales (coste, sin derecho de reutilización,
y el parafraseo sigue siendo derivado); PDFs pirateados (ilegal — no entran ni como
cita); depender de CC BY-SA sin decisión (hereda licencia sobre contenido propio).

---

## ADR-12 — Herramientas externas de autoría fuera de la app; `notebooklm-mcp` no se adopta (2026-09-18)

**Decisión:** las herramientas evaluadas el 2026-09-18 se usan, si se usan, como
utilidades de autoría en el PC del dueño y jamás entran en el bundle ni en el backend:

| Herramienta | Uso |
|---|---|
| `hainrixz/claude-webkit` (MIT) | referencia de skills de diseño/SEO para la landing (19.8); no se adopta Next.js ni Vercel |
| `AgriciDaniel/banana-claude` (MIT, Gemini de pago) | iconos y assets de tiendas (19.9); nunca diagramas técnicos |
| `Hainrixz/editor-pro-max` (MIT; Remotion gratis ≤ 3 personas) | post-producción del vídeo Manim (19.10) |
| Maia (Matillion) | no aplica: Whetzy no tiene pipelines de datos |
| `PleasePrompto/notebooklm-mcp` | **no se instala** |

**Razón:** línea roja 5 (sin terceros en prod) y mantenimiento. `notebooklm-mcp`
está **archivado desde septiembre de 2026**, no usa API (NotebookLM no tiene) sino
un Chrome con Patchright — evasión de detección de bots — que rasca la interfaz de
Google; es zona gris de sus términos, pone en riesgo la cuenta que se use, no crea
cuadernos ni sube PDFs por herramienta, y el siguiente cambio de interfaz lo rompe
para siempre. Lo único que aportaba —grounding con cita sobre un corpus cerrado— ya lo
da el BM25 propio de `services/ai/rag.py` apuntado a las fuentes libres (19.7).

**Alternativas descartadas:** depender del scraper archivado; usar la cuenta de Google
del dueño en un scraper; adoptar Next.js/Vercel por la landing (dos stacks para una
página).

---

## ADR-13 — Social login antes de tiendas; Sign in with Apple obligatorio en cuanto exista otro OAuth (2026-09-18)

**Decisión:** Whetzy deja de ser email-only. Orden de implantación: **19.1** GitHub +
Google en web por redirección OAuth 2.0 (sin SDK de terceros en el bundle) → **19.2**
Sign in with Apple (bloqueado por H.2: Services ID + clave `.p8`) → **19.3** Google
Sign-In nativo en Android + Google Play Billing vía RevenueCat. **Ninguna submission a
App Store sin 19.1 + 19.2 + 7.6.** Una cuenta existente con el mismo email verificado
se vincula, nunca se duplica; los tokens emitidos son los mismos que en `/auth/login`.

**Razón:** App Store Review Guideline 4.8 exige ofrecer Sign in with Apple si la app
ofrece cualquier otro login de terceros; el checklist de Apple decía «no aplica» solo
porque no había ninguno. Educative ofrece Google / GitHub / Apple / LinkedIn y en 2026
el registro por email es la fricción máxima; GitHub es lo que un desarrollador espera.

**Alternativas descartadas:** seguir email-only (conversión); OAuth de Google/GitHub
sin Apple (rechazo garantizado en revisión); SDK de proveedor en el bundle (línea
roja 5: redirección pura).

---

## ADR-14 — Modelos y tokens: sin Opus ni Fable en sesiones autónomas; Haiku por defecto (ACEPTADA 2026-09-18)

> **Enmendada por ADR-50 el 2026-09-26 y por ADR-52 el 2026-09-27:** en sesiones arrancadas por el dueño, hilo **Sonnet 5**, autoría masiva Haiku 4.5 y revisor Sonnet 5 (ADR-52); Fable y Opus 4.x prohibidos. Las sesiones programadas siguen con esta ADR (workers Haiku 4.5).

**Decisión:** El hilo principal autónomo corre en Sonnet 4.6 (`settings.json`, sin
cambios). Los workers son **Haiku 4.5 por defecto**; Sonnet solo cuando la tarea
**escribe** en la lista de ficheros de riesgo de `PROTOCOLO_VERIFICACION.md` §2.
**Opus y Fable quedan prohibidos** en sesiones programadas: si una tarea parece
necesitarlos, es `HUMAN-BLOCKED`. Dieta de contexto obligatoria: el ledger se lee por
secciones, `STATUS.md` y `archive/` no se leen, un worker recibe rutas y criterio.

**Razón:** El dueño tiene cupo semanal y presupuesto incierto más allá del
2026-10-06. Opus/Fable consumen 5-15× más cupo por token que Haiku; el ledger no
contiene ninguna tarea de arquitectura irreversible que los justifique; y una
sesión que lee 293 KB de ledger gasta más en leer que en trabajar.

**Alternativas descartadas:** Haiku también como orquestador (las decisiones de qué
commitear y qué cerrar necesitan juicio; el precedente de sesiones que cerraron
tareas sin evidencia es el argumento); mantener Opus ≤ 2/sesión (nadie lo ha
necesitado en 19 series).

## ADR-15 — Coste cero hasta 5.000 usuarios (ACEPTADA 2026-09-18)

**Decisión:** Ningún gasto nuevo —suscripción, add-on, cuenta de desarrollador,
servicio— sin pasar por `HUMAN-BLOCKED` con el coste en € y la evidencia de que no
existe alternativa gratuita. Lista blanca de servicios gratuitos: Railway (plan
actual), Cloudflare Pages/WAF/rate-rules (free), Groq (free tier), proveedor de email
en free tier, Sentry free, Dependabot, gitleaks, semgrep/bandit OSS, Instatus/Cloudflare
status free, UptimeRobot free. Todo lo «preparado para 1 M» se construye como
abstracción con backend gratuito hoy (memoria/DB) y backend de pago detrás de una
variable de entorno (Redis, réplicas, CDN de pago).

**Razón:** El dueño no tiene liquidez ahora; el valor acumulado es el trabajo. Un
producto que necesita 5.000 usuarios para pagarse no puede costar antes de tenerlos.

**Alternativas descartadas:** «Preparar para 1 M» comprando infraestructura ahora;
posponer toda la preparación (las abstracciones cuestan casi nada y evitan reescribir).

## ADR-16 — Rail de pagos y entidad: decidir con datos, no con prisa (ACEPTADA 2026-09-18)

> **Enmendada por ADR-47 el 2026-09-24:** la premisa griega queda suspendida; valor por defecto Merchant of Record + IAP tras `PaymentProvider`; entidad y jurisdicción sin decidir (H.29).

**Decisión:** Antes de activar cobros se ejecutan 21.1 (entidad/fiscalidad) y 21.2
(rail de pagos). Opciones sobre la mesa: (a) Stripe como particular en Grecia (H.4),
(b) *Merchant of Record* (Paddle / Lemon Squeezy: ellos liquidan IVA UE/OSS, sales tax
EE. UU. y facturan; pagan al particular), (c) solo IAP de tiendas (Apple/Google son
MoR, 15-30 %). **Revolut personal**: solo para recibir pagos de prueba; sus
condiciones prohíben uso comercial continuado, así que la investigación debe decir
cuándo y con qué coste se pasa a Revolut Business (plan €0) o a cuenta de empresa.
Entidad: se mantiene la decisión previa (autónomo griego → IKE a €2 K MRR) **hasta que
21.1 demuestre con fuentes oficiales fechadas** que otra vía (e-Residency, LLC) es
legal para un residente fiscal en Grecia y más barata en total.

**Razón:** Hoy no hay ingresos ni empresa; el error caro es cobrar sin IVA/OSS
correcto o usar una cuenta personal contra sus términos. Un MoR elimina casi todo
ese riesgo a cambio de ~5 % y no requiere sociedad.

**Alternativas descartadas:** Activar Stripe live sin investigación; constituir
sociedad ahora (coste fijo sin ingresos).

## ADR-17 — Español e inglés son dos segmentos, un producto (ACEPTADA 2026-09-18)

**Decisión:** Un usuario ve **un solo idioma** en toda su experiencia: UI, contenido,
tutor, emails, push, PDF, páginas legales, tienda y landing. Nunca hay fallback
silencioso al otro idioma: si una pieza no existe en el idioma del usuario, se oculta
y se registra como deuda, no se muestra en el otro. Landing/SEO/pricing/soporte se
diseñan por segmento (`/es`, `/en`, monedas y comunidades distintas). La paridad de
contenido sigue siendo obligatoria (línea roja 3); la **experiencia** no se mezcla.

**Razón:** Orden del dueño («sin combinar idiomas, son dos segmentos separados»). El
comprador hispanohablante y el anglófono llegan por canales, precios y competidores
distintos; una pantalla mezclada destruye la confianza en ambos.

**Alternativas descartadas:** Fallback al inglés cuando falte español (la deuda se
esconde); dos productos separados (duplica todo).

## ADR-18 — Despliegue autónomo: un solo push verificado por sesión (ACEPTADA 2026-09-18; resuelve H.16)

> **Sustituida por ADR-45 (2026-09-24)**: las sesiones no hacen push a `master`; trabajan en rama + PR y solo el dueño fusiona. Nota añadida el 2026-10-16 por ADR-61 §27.

**Decisión:** Las sesiones autónomas commitean en `master` **en local** y hacen
**un único `git push origin master` al final de la sesión**, solo con las cuatro
guardias en verde (`pytest tests/content`, `check_question_bank.py`, `check_docs.py`,
`npm run build`) y el verificador adversario aplicado a cada `DONE` de la sesión.
Migraciones: solo aditivas, con `downgrade` probado, y **nunca** en el mismo push que
un cambio de contenido. Si una guardia falla, no hay push; la sesión lo anota y el
siguiente disparo lo arregla primero. (Es la opción 1 de H.16 conservando la
autonomía: el «humano» que decide el merge es la puerta de verificación.)

**Razón:** `push` despliega (H.16) y provoca 60-90 s de 502; 28 pushes en un día
(sesión ar) son 28 cortes y 28 oportunidades de romper prod. Una rama separada
obligaría al dueño a hacer merges a mano, lo que contradice «control total mientras
duermo».

**Alternativas descartadas:** desconectar el auto-deploy (nadie despliega); rama +
merge humano (rompe la autonomía); seguir pusheando por tarea.

## ADR-19 — Preparado para un millón sin pagar por un millón (ACEPTADA 2026-09-18)

**Decisión:** Lo que se construye ahora para escala es **arquitectura, no
infraestructura**: rate limiting y caché tras una interfaz con implementación en
memoria (Redis detrás de `REDIS_URL` vacío), pool de conexiones parametrizado, paginación
en todo listado, trabajos asíncronos con cola en DB (email, DKT, exports), cabeceras de
caché en GET públicos, `capacity.md` con la tabla usuarios → réplicas → coste, k6 a
1.000 VUs contra local, simulacro de restore de backup. Nada de Kubernetes, multi-región
ni servicios gestionados hasta que el admin (22.1) muestre > 1.000 usuarios activos.

**Razón:** Orden del dueño: empezar al mínimo coste y dejar todo preparado para 1 M.
Las abstracciones cuestan horas; la infraestructura cuesta euros al mes.

**Alternativas descartadas:** Comprar Redis/réplicas ahora; ignorar la escala hasta que duela.

## ADR-20 — Verificación adversaria obligatoria para cada DONE (ACEPTADA 2026-09-18)

**Decisión:** Ninguna fila del ledger pasa a `DONE` sin el veredicto `CONFIRMADA` de
un verificador independiente (Haiku, prompt fijo de `PROTOCOLO_VERIFICACION.md` §7)
que reejecuta la evidencia e intenta refutarla. La evidencia que queda en la fila es
la del verificador. Mientras Actions esté bloqueado, «CI verde» está prohibido; se
escribe `CI-LOCAL` con la salida de `scripts/verify_ci_local.ps1` y el run id fallido.

**Razón:** Sesiones am, ao, ar y bf documentan `DONE` falsos o no reproducibles. El
dueño exige cero errores; el mecanismo más barato es que nadie se verifique a sí mismo.

**Alternativas descartadas:** Confiar en el resumen del worker; verificación solo en
el cierre (demasiado tarde: ya se construyó encima).

---
## ADR-21 — Precio Pro $14.99/mes (2026-09-18)

> **Enmendada por ADR-47 el 2026-09-24** (hipótesis Pro $9,99 / Plus $19,99, ninguno publicado) **y por ADR-41 el mismo día, más tarde** (decisión del dueño: Pro $14,99, Pro Max $19,99, Creador $99,99; publicados en la landing, cobro sin abrir). Manda ADR-41.

**Decisión:** Pro = $14.99/mes (no $9.99). Premium = $19.99 sin cambio.

**Razón:** El mercado aguanta $14.99 (Boot.dev cobra $49/mes, TryHackMe $10.50/mes annual, Codecademy $24.99/mes). A $9.99 el LTV anual es $120; a $14.99 es $180 — 50 % más sin perder conversión medible. El break-even baja de ~1,200 usuarios pagos a ~800.

**Evidencia de mercado:** Education app average subscription $8.13/mo o $56.09/year (Business of Apps 2026). Boot.dev $348/yr con 25K paying members = $10M ARR con 13 personas.

**Alternativas descartadas:** $9.99 (LTV insuficiente para sostenerse con pocos usuarios); $29.99 (frena conversión en LATAM con ingresos en moneda local depreciada).

**Errata 2026-09-24 (premisas, no decisión).** Re-descargadas las páginas de precios
(COMPETENCIA.md §A.1): Boot.dev cobra **$59/mes o $399/año**, no $49; Codecademy Plus
**$29.99 mensual / $14.99 al mes pagando el año**, no $24.99. «$348/yr», «25K paying
members» y «$10M ARR» no se han podido comprobar en fuente primaria y no deben
citarse. La conclusión aguanta mejor que antes: $14.99 mensual está por debajo de
todos los de catálogo verificados. Quedan abiertos el precio anual, la tarifa
regional y el corte gratis/Pro (H.35). ORCHESTRATOR.md decía $9.99; corregido el mismo día.

---

## ADR-22 — B2B antes que escalar B2C (2026-09-18)

> **Enmendada por ADR-47 el 2026-09-24:** B2B $99 por asiento y año, mínimo 10, como hipótesis interna sin publicar; 3 pilotos gratuitos (38.2, H.39).

**Decisión:** Prioridad de venta: contratos B2B piloto (upskilling Python/AI para empresas) antes de invertir en adquisición B2C masiva.

**Razón:** Un contrato B2B de 50 empleados a $500/persona/año = $25,000 — equivale a 1,667 suscriptores Pro. DataCamp hace 66% de revenue en B2B. El admin sub-app (Serie 22) ya incluye gestión de empresas. Costo de adquisición B2B: una conversación de LinkedIn. Costo de adquisición B2C masivo: campaña o tiempo de YouTube.

**Cómo ejecutar:** 3 contratos piloto gratuitos (a cambio de testimonios + datos de uso) a empresas LATAM/España con equipos de tecnología. Objetivo: antes del lanzamiento público.

**Alternativas descartadas:** B2C first (más lento, más costoso, retención Day-30 ~2%); esperar al lanzamiento completo (los contratos piloto dan datos reales del motor antes del lanzamiento).

---

## ADR-23 — YouTube como canal de distribución primario (2026-09-18)

**Decisión:** Canal de YouTube en español (Python para AI Engineering) como principal motor de adquisición orgánica. Costo: $0. Formato: 1 video/semana, CTA a Whetzy.

**Razón:** Boot.dev tiene canal con 100K+ suscriptores que genera usuarios constantemente. El contenido educativo en YouTube tiene SEO compuesto — un video de 2026 trae usuarios en 2028. TryHackMe creció vía contenido gratuito (77% del contenido es free). El gap en YouTube de Python/AI en español nativo es real — ningún canal combina motor adaptativo + comunidad + certificaciones.

**Alternativas descartadas:** Ads pagados (sin presupuesto, ADR-15); influencer marketing (sin presupuesto); ProductHunt solo (no alcanza comunidad hispanohablante).

---

## ADR-24 — Ventana de adquisición Coursera+Udemy (2026-09-18)

**Decisión:** Preparar campaña de migración para H2 2026 cuando cierre el merger Coursera-Udemy.

**Razón:** Coursera acordó adquirir Udemy (Dec 17, 2025, all-stock, ~$930M, esperado H2 2026). 197M usuarios registrados entre ambos van a sufrir: degradación de producto, confusión de marca, subidas de precio en integración. Los usuarios técnicos hispanohablantes son los más sub-servidos por ambas plataformas. Ventana de migración: 6-12 meses post-cierre.

**Acción concreta:** Landing page en ES y EN con comparativa Whetzy vs Coursera/Udemy en el nicho Python/AI. Activar cuando se confirme el cierre del deal.

---

## ADR-25 — Meta de contenido: 100 cursos × 27 tracks (2026-09-18)

> **Sustituida por ADR-53 el 2026-09-30:** la meta del catálogo ya no es un número de cursos
> sino suelo (50 skills · 800 preguntas por track) e ideal por temario, con tracks por demanda
> medida. Lo que sigue es histórico.
>
> **Enmendada por ADR-46 el 2026-09-24:** la meta es ≥ 50 cursos por track en todos los tracks de la industria (28 + 14 de `CATALOGO_MAESTRO.md` §2.0 y los que 37.1 confirme), sobre corpus abierto, con la guarda de diversidad 37.0 antes de cualquier pregunta nueva.

**Decisión:** La meta de contenido a largo plazo es 100 cursos por track × 27 tracks = 2,700 cursos adaptativos, con glosario máximo por área.

**Razón:** Con ese volumen Whetzy supera en cobertura a Platzi (1,900 cursos, no adaptativos), DataCamp (730 cursos en su nicho, sin español), y Codecademy (300 cursos). El motor BKT+FSRS+Elo+DKT con 2,700 nodos de conocimiento genera rutas de aprendizaje que ningún competidor puede replicar. El material fuente legal y gratuito existe (ver CATALOGO_MAESTRO.md §2.1 y §2.2 — libros completos CC BY 4.0 para cada área).

**Estructura por track:**
- Nivel 1 — Fundamentos (empleable como junior): sintaxis, estructuras básicas, Git, 2-3 proyectos
- Nivel 2 — Intermedio (mid-level): algoritmos, APIs, testing, proyectos con datos reales
- Nivel 3 — Avanzado (senior): system design, optimización, ML aplicado, open source
- Nivel 4 — Especialista: papers implementados, arquitecturas productivas, portfolio público

**Proyección competitiva al alcanzar ADR-25:**
- vs DataCamp: Whetzy gana en cobertura (27 dominios vs nicho data), gana en español, gana en motor adaptativo
- vs Platzi: Whetzy gana en motor (adaptativo vs video/cohort), comparable en volumen (2,700 vs 1,900), gana en certificaciones
- vs Boot.dev: Whetzy gana en scope (27 tracks vs 5), gana en español, gana en sofisticación del motor
- vs Codecademy: Whetzy gana en motor, gana en certificaciones, comparable en interactividad

**Cuándo se ejecuta:** Las Series 20-23 terminan la base técnica. La Serie 25 (nueva, ver ledger) ejecuta la expansión de contenido track por track usando el motor de generación Haiku + §7 quality gate del CATALOGO_MAESTRO.md.

**Alternativas descartadas:** Mantener 27 tracks con profundidad actual (suficiente para lanzar, insuficiente para competir en retención a largo plazo); expandir a más tracks antes de profundizar los existentes (dispersión, error de Platzi — muchos cursos sin completar).

---

## ADR-26 — Serie 24 scope completo: UI/UX + competencia + video (2026-09-18)

**Decisión:** Serie 24 = 15 tareas que cubren investigación competitiva en vivo (24.0), identidad visual (24.1), landing que vende (24.2), onboarding rediseñado (24.3), dashboard con motor visible (24.4), sesión adaptativa con BKT visual (24.5), gamificación original (24.6), panel de certificación (24.7), perfil público (24.8), panel B2B (24.9), panel de instructor (24.10), marketplace UI (24.11), mobile polish (24.12), producción de 3 videos demo (24.13), A/B test framework (24.14).

**Razón:** El motor técnico es extraordinario pero invisible. La Serie 24 lo hace visible y emocional. Requiere sesiones interactivas con el dueño — no puede ejecutarse en autónomo. El dueño aprueba cada pantalla antes de implementar.

**Alternativas descartadas:** Rediseño parcial (solo landing) — insuficiente para cambiar la percepción; delegar todo el diseño a Claude sin input del dueño — el dueño es la voz de la marca.

---

## ADR-27 — Distribución dual ES + EN con canales separados (2026-09-18)

**Decisión:** Dos canales YouTube (ES y EN), presencia separada en LinkedIn ES/EN, Reddit ES y EN simultáneamente. Todo el contenido es nativo — no se traduce de un idioma al otro (ADR-17). Ver `docs/DISTRIBUCION.md` para el plan completo.

**Razón:** El gap existe en ambos idiomas pero con competencias diferentes. ES: ningún competidor adaptativo. EN: competencia fuerte pero el motor sigue siendo superior. Empezar los dos en paralelo desde el día 1 porque construir audiencia en YouTube es exponencial y el tiempo perdido no se recupera.

**Herramientas:** 100% gratuitas — OBS, DaVinci Resolve free, Canva free, Buffer free tier. Sin publicidad pagada hasta ADR-15 se levante.

---

## ADR-28 — Segmentos de usuario: 5 personas con flujos diferenciados (2026-09-18)

**Decisión:** La app diferencia 5 segmentos desde el onboarding: Estudiante/Principiante, Career-switcher, Developer Senior, Profesor/Instructor, Empresa/B2B. Cada segmento tiene plan de precios diferente, CTA diferente y flujo diferente. Ver `docs/SEGMENTOS.md`.

**Razón:** "Sirvo a todos" = sirvo a nadie. Los benchmarks de conversión (2.6% freemium edtech) se mejoran cuando el producto habla directamente al dolor específico del usuario. Boot.dev tiene 1 segmento y convierte mejor que la media.

---

## ADR-29 — Marketplace de instructores: revenue share 70/30 (2026-09-18)

> **Enmendada por ADR-41 (2026-09-24)**: el reparto es 80/20 a favor del instructor (`CREATOR_REVENUE_SHARE = 0.80`, `backend/app/core/prices.py:19`). Nota añadida el 2026-10-16 por ADR-61 §27.

**Decisión:** Marketplace abierto a instructores externos con revenue share 70% instructor / 30% Whetzy. Todo contenido pasa el quality gate §7 antes de publicarse. Sin exclusividad requerida. Ver `docs/MARKETPLACE.md` para spec completo. Serie 28 implementa.

**Razón:** Multiplica la velocidad de generación de contenido sin multiplicar el costo. 20 instructores activos = 20x más contenido. 70% es más generoso que Udemy (25-37%) y Teachable (cobra plataforma). El motor adaptativo convierte el contenido del instructor en un producto mejor que el que ellos podrían ofrecer solos.

**Alternativas descartadas:** Solo contenido propio (cuello de botella de velocidad); revenue share 50/50 (poco atractivo para instructores de calidad).

---

## ADR-30 — Stack de producción de video 100% gratuito y legal (2026-09-18)

**Decisión:** Stack oficial para videos de marketing y tutoriales: OBS Studio (GPL-2) + DaVinci Resolve free + Canva free (thumbnails) + Audacity (GPL-3) + Inkscape (GPL-3) + CapCut free (móvil). Todos gratuitos, todos legales. Ver `docs/DISTRIBUCION.md` §2.3.

**Razón:** La producción de video es el canal de distribución con mayor ROI compuesto. Un video de 2026 trae usuarios en 2028. El stack gratuito es comparable en calidad al de pagado para el formato tutorial/demo.

---

## ADR-31 — Competencia indirecta: coexistir y posicionarse como "el siguiente paso" (2026-09-18)

**Decisión:** No competir contra freeCodeCamp, CS50, Khan Academy, YouTube ni GitHub repos — posicionarse como "el siguiente paso" después de ellos. Publicar en freeCodeCamp News, responder en Reddit con valor, aparecer en `awesome-python` y `free-programming-books`. Ver `docs/COMPETENCIA.md` §2.

**Razón:** Estos canales tienen audiencias de millones. Competir contra ellos por atención es imposible con presupuesto cero. Convertirlos en fuentes de tráfico es la estrategia correcta.

---

## ADR-32 — Métricas de producto: benchmarks del mercado como norte (2026-09-18)

> **Enmendada por ADR-53 el 2026-09-30:** las metas a 12 meses de abajo siguen como aspiración,
> pero los benchmarks sin verificar (2,6 % de conversión, «Platzi 70 %», «10-15 % industria»)
> se sustituyen por los comprobados de ADR-53 §8 (conversión freemium mediana 2,1 %; edX 3,13 %
> de todos y 46 % de quienes pagan; D30 de educación 2,7–3,2 %), que además fija el suelo mínimo.

**Decisión:** Las 10 métricas clave de producto (Day-1/7/30 retention, completion rate, freemium conversion, LTV, NPS, TTFQ, B2B NDRR, streak promedio) se miden desde el día 1 en el admin sub-app (Serie 22) y se comparan contra benchmarks del mercado del estudio 2025-2026. El objetivo es superar el benchmark en cada métrica dentro de 12 meses.

**Objetivos concretos:**
- Day-30 retention: > 10% (vs 2% industria)
- Completion rate: > 50% (vs 10-15% industria, Platzi 70%)
- Freemium→Pro conversion: > 4% (vs 2.6% benchmark)
- NPS: > 50 (vs Duolingo ~45, Boot.dev ~70)
- TTFQ: < 60s (ya medido en 11.6 ✅)

---

## ADR-33 — No hay token ni criptomoneda propia (RECHAZADO 2026-09-18)

**Propuesta del dueño:** integrar una cripto propia en Solana como recompensa por
aprender, como inversión (staking y otras modalidades) y como herramienta de
retención y de valoración.

**Decisión:** **No.** Whetzy no emite, custodia, cotiza ni reparte ningún token,
ni ahora ni cuando haya ingresos. La palabra «token» solo puede aparecer en los
documentos vivos para remitir a este ADR.

**Razón (en orden de gravedad):**

1. **Daño al único activo diferencial.** Si responder preguntas paga, aparecen bots y
   farmers que responden las 6.233 preguntas con scripts. Esos datos entran en
   BKT/FSRS/DKT y **envenenan el motor**. Ningún competidor sufriría este daño porque
   ninguno tiene motor.
2. **Regulación.** El dueño reside en Chipre (UE): MiCA está en vigor desde diciembre
   de 2024 y un token con «staking» e «inversión» no es un token de utilidad — es un
   instrumento financiero o exige licencia CASP. En EE. UU. es Howey de manual.
3. **Tiendas.** App Store Review 3.1.5 prohíbe ofrecer criptomoneda por completar
   tareas dentro de la app; Google Play va en la misma dirección. Contradice ADR-13.
4. **Coste cero (ADR-15).** Crear un SPL token cuesta céntimos; un token sin liquidez
   vale 0 $; la liquidez la pone el emisor con capital; a eso se suman opinión legal,
   auditoría de programas propios y KYC/AML si alguien convierte a fiat.
5. **Valoración.** Los adquirentes edtech (DataCamp, Coursera, Skillsoft, Pearson) no
   compran empresas con token vivo: es pasivo legal, no activo.
6. **Evidencia del mercado.** Learn-to-earn ya se probó y falló: Open Campus (EDU,
   2023), BitDegree (BDG, 2017); move/play-to-earn (STEPN, Axie) colapsaron por
   reflexividad. Coinbase y Binance *Learn & Earn* funcionan porque un exchange paga
   con dinero real como marketing. Ver `COMPETENCIA.md` §2.6.
7. **Motivación.** La recompensa extrínseca con precio de mercado desplaza la
   intrínseca. Duolingo y Boot.dev tienen gemas **sin valor externo a propósito**.

**Lo que sí se adopta de la idea:** ADR-34 (créditos cerrados), ADR-35 (referidos y
códigos), ADR-36 (USDC como rail), ADR-37 (credenciales verificables), ADR-38
(track32 Solana/Web3). Spec completo en `docs/ECONOMIA.md`.

**Condición para reabrir:** opinión legal MiCA fechada + plan de liquidez con capital
propio. Ambos son HUMAN-BLOCKED con € (ADR-15).

---

## ADR-34 — Créditos Whetzy: economía cerrada, sin valor externo (ACEPTADA 2026-09-18)

> **Enmendada por ADR-58 (2026-10-02)**: los créditos ya no compran simulacros ni cursos del marketplace; el acceso lo da el plan. Nota añadida el 2026-10-16 por ADR-61 §27.

**Decisión:** Whetzy tiene una moneda promocional cerrada («créditos») que se **gana
aprendiendo** y se **gasta en consumibles** dentro de la app (simulacros, congelar
racha, informes, bootcamps async, cursos del marketplace, seats extra para empresas).
Tres reglas inviolables, en código y en ToS: (1) sin valor monetario ni canje por
dinero; (2) no transferibles entre usuarios; (3) no se compran con dinero. Caducan a
los 90 días (FIFO). Tope de ganancia por aprendizaje 1.500/mes. Nunca compran meses de
suscripción por goteo. Saldo = suma de un **ledger append-only con idempotencia**;
no existe columna `users.credits`. Canje de códigos y consulta de saldo **solo en web**
(Apple 3.1.1); las apps nativas reflejan el estado. Spec: `ECONOMIA.md` §1–§2, §5.

**Razón:** El instinto del dueño («una recompensa que retenga») es correcto; lo que
lo vuelve tóxico es el valor externo. Sin él, es la misma figura que Duolingo, Boot.dev
y DataCamp usan con éxito, no requiere licencia ni abogado previo, y cuesta 0 $.

**Alternativas descartadas:** token (ADR-33); créditos comprables (obliga a IAP en iOS
y a régimen de prepago en la UE); créditos que compran Pro (canibaliza la suscripción);
saldo sin caducidad (pasivo contable, sin urgencia).

---

## ADR-35 — Referidos por activación y códigos autogenerados de cinco tipos (ACEPTADA 2026-09-18)

> **Enmendada por ADR-57 y ADR-41**: ver esas ADR para los premios y los precios vigentes. Nota añadida el 2026-10-16 por ADR-61 §27.

**Decisión:** Programa de referidos de doble cara que **paga por activación, nunca
por registro** (activación = email verificado + diagnóstico + primer módulo + racha
de 3 días; abono 7 días después). Escalera acumulativa: 1 → 300 créditos; 3 → 1 mes
Pro (entitlement en servidor); 10 → certificación oficial (HUMAN-BLOCKED por importe
hasta que haya ingresos; mientras, 6 meses Premium); 25 → badge Embajador. Tope 10
activaciones/mes. **Antifraude obligatorio antes de abrir:** email verificado, hash
propio de dispositivo/IP sin terceros, 1 activación por dispositivo/IP cada 30 días,
auto-referido bloqueado, cola de revisión, clawback, pausa automática si fraude > 5 %.

Códigos autogenerados de **cinco tipos**: referido (1 por usuario), campaña (uno por
pieza publicada = **atribución de canal a coste cero**), lote de un solo uso
(universidades, pilotos B2B), instructor (descuento + atribución de ventas) y
reactivación (72 h, a 14 días de inactividad). Alfabeto sin `0 O 1 I L`, canje
idempotente `(code_id, user_id)`, un código lleva idioma (ADR-17). Spec: `ECONOMIA.md` §3–§4.

**Razón:** Los referidos traen el 10–30 % de los registros en programas bien hechos y
los usuarios referidos retienen mejor; pagar por registro los convierte en granja de
bots en una semana. Los códigos de campaña son **la única analítica de atribución que
Whetzy puede tener sin terceros en prod ni presupuesto**: cada vídeo, artículo y
comunidad de las Series 26-27 lleva el suyo.

**Cuándo:** Serie 29, **después** de la 24 y con retención base medida (ADR-32) — un
programa de referidos amplifica lo que hay; con Day-30 al 2 % no hay nada que referir.

**Alternativas descartadas:** recompensa por registro (fraude); referidos en dinero
(regulación, Apple 3.1.5); analítica de terceros para atribución (línea roja 5, coste).

---

## ADR-36 — Stablecoin como rail de pago, nunca como activo (ACEPTADA 2026-09-18; subordinada a H.19)

**Decisión:** Si H.19 (ADR-16) elige Stripe, se activa **Stripe *Pay with Crypto***:
el cliente paga en USDC (Solana, Ethereum, Polygon, Base) y Stripe **liquida en fiat**
a Whetzy (~1,5 %), sin integración adicional sobre 7.2. Para **payouts a instructores**
en países sin Stripe Connect (la mitad de LATAM), el instructor puede elegir USDC en
Solana (fee ≈ 0,001 $) o Wise; su fiscalidad es suya (21.1). **Whetzy nunca custodia
cripto, nunca tiene wallet con saldo operativo, nunca cotiza en cripto** y no acepta
nada que no sea USDC liquidado en fiat. Si H.19 elige un MoR, se documenta la
alternativa del MoR o se descarta sin sustituto.

**Razón:** Resuelve un dolor real y medible del segmento LATAM (tarjetas que no pasan
en Argentina/Venezuela; instructores en Colombia que no pueden cobrar) a coste cero y
sin tocar ADR-33. Es «Solana para pagos» — el instinto correcto del dueño.

**Alternativas descartadas:** aceptar cripto directamente en wallet propia (custodia,
KYC, contabilidad); aceptar cualquier token (volatilidad); cobrar en cripto sin fiat
(exposición de balance).

---

## ADR-37 — Credenciales verificables: Open Badges 3.0 obligatorio, cNFT opcional (ACEPTADA 2026-09-18)

**Decisión:** Todo certificado de track y de simulacro se emite como **Open Badges 3.0**
(1EdTech; formato W3C Verifiable Credentials): JSON-LD firmado por Whetzy, endpoint
público de verificación y revocación (`whetzy.com/verify/<código>`, extendiendo
`GET /api/v1/exams/certificates/{code}`), QR en el PDF, compatible con LinkedIn y
Credly. **Opcional y tras H.27:** copia pública como cNFT **no transferible** en Solana
(~0,0001 $ por emisión; requiere wallet emisora con céntimos de SOL). Nunca token
fungible, nunca NFT vendible.

**Razón:** «Que exista on-chain» buscaba prueba pública verificable por empleadores.
Eso lo dan las Verifiable Credentials, que es lo que los empleadores y LinkedIn ya
reconocen; el cNFT añade visibilidad en el ecosistema Solana a coste casi nulo, pero
por ADR-15 cualquier gasto con alternativa gratuita pasa por HUMAN-BLOCKED.

**Alternativas descartadas:** solo PDF (no verificable); NFT transferible (mercado
secundario de certificados); blockchain como única prueba (los empleadores no la leen).

---

## ADR-38 — track32 Solana/Web3 developer en español; segmento 6; Superteam como canal (ACEPTADA 2026-09-18)

**Decisión:** El catálogo pasa de 27 a **28 tracks de aprendizaje** con **track32 —
Solana / Web3 developer** (JS con `@solana/web3.js` en el Worker; Python stdlib para
hashes, base58 y serialización; Rust/Anchor como escenario + decisión, exento ADR-9).
Fuentes: `solana-labs/solana` y `solana-program-library` (Apache-2), docs y cookbook
de `solana-developers`/`solana-foundation` (MIT/Apache-2), `@solana/web3.js` (MIT),
Anchor (Apache-2) — licencias a confirmar en 25.14 antes de reutilizar texto. Sin
certificación oficial: la evidencia de empleabilidad son **bounties de Superteam
Earn** resueltos por alumnos. Nace el **segmento 6 — Developer Web3/Solana hispano**
(`SEGMENTOS.md`). Superteam (capítulos México, Argentina, Brasil) y los programas de
grants de la Solana Foundation entran en `DISTRIBUCION.md` como canal P2 (26.8, 27.9)
y como **financiación no dilutiva** (H.28; montos vigentes a verificar por el dueño).
La meta de ADR-25 pasa a **100 × 28 = 2.800 cursos y ≥ 2.800 términos**. *(Histórico: esa
meta la sustituyó ADR-46 y a esta ADR-53; track32 sigue en el plan como nivel C de demanda.)*

**Razón:** «Solana está despertando» es cierto como **mercado de contenido**, no como
token. No existe un track Solana de calidad en español; el ecosistema tiene una
comunidad organizada que busca exactamente eso y paga por contenido educativo. Aquí
Solana paga a Whetzy, no al revés. Es el único segmento nuevo con canal propio ya
existente.

**Alternativas descartadas:** token (ADR-33); track genérico «blockchain» (sin
comunidad ni bounties); esperar a que Platzi lo haga.

---

## ADR-39 — El panel `/admin` se autentica solo con JWT `role=owner`; `X-Admin-Key` no se extiende a él (ACEPTADA 2026-09-19)

**Contexto:** el criterio de 22.1 pedía que el panel de administración «reutilice
`X-Admin-Key` para scripts y añada el claim JWT `role=owner`». Se implementó solo la
segunda mitad, y el verificador adversario refutó 22.8 en parte por eso. Había que
decidir: añadir la clave estática o recortar el criterio por escrito.

**Decisión:** el panel `/admin` se autentica **únicamente** con el JWT y el rol
(`require_admin` / `require_owner` en `backend/app/api/v1/endpoints/admin.py`).
`X-Admin-Key` (`CONTENT_ADMIN_KEY`) **se queda donde ya está y no se extiende**: las
rutas de ingesta que sí las usa un script sin sesión — `content.py`, `push.py`,
`analytics.py`. El criterio de 22.1 queda recortado en ese punto.

**Razón:** `X-Admin-Key` es un secreto compartido de vida larga. En el panel no tiene
ningún llamante: las métricas las mira una persona con sesión iniciada, no un cron. Un
secreto sin llamante es superficie de ataque sin contrapartida, y este repo ya tiene el
precedente de H.12 (la `GROQ_API_KEY` commiteada en claro en `docs/STATUS.md`). Añadir
un segundo camino de autenticación a los datos más sensibles del producto —ingresos,
eventos de auth, cola GDPR— para una comodidad que nadie ha pedido va en contra de la
regla de dueño «lo simple que funciona hoy».

**Consecuencia:** si algún día un script necesita leer métricas sin navegador, se le
emite un JWT de servicio con `role=owner` y caducidad corta, no una clave estática.
Ningún endpoint de `/admin/**` debe aceptar `X-Admin-Key`; si aparece uno, es un bug.

**Alternativas descartadas:** añadir `X-Admin-Key` al panel (un secreto más, sin
llamante); dejar el criterio sin cumplir y sin explicación (fue justo lo que provocó la
refutación de 22.8).

---

## ADR-40 — La memoria del proyecto es el repositorio, no un servicio externo (ACEPTADA 2026-09-19)


**Aceptada por el dueño** el 2026-09-19, en la sesión interactiva, tras leer la
propuesta y el informe que la sostiene. La propuso un agente; la decisión es suya.

**Contexto:** el dueño preguntó si montar `notebooklm-mcp` en Docker Desktop, alimentado
con toda la documentación, reduciría el gasto de tokens y acercaría el proyecto a la
perfección; y si no, si hacía falta Obsidian. La pregunta es legítima: `docs/**/*.md`
pesa ~1,2 MB (~305.000 tokens) y `AUTONOMOUS_STATE.md` solo ya son ~29.500.

**Decisión:** **no.** La memoria operativa de Whetzy vive en el repositorio y se consulta
con las herramientas del repositorio. En concreto:

1. **`notebooklm-mcp` queda descartado** como capa de memoria o de RAG. No se instala, ni
   en Docker ni fuera.
2. **Obsidian queda descartado** como herramienta del proyecto. Si el dueño lo usa para
   leer, es asunto suyo y no crea dependencia: no se añaden plugins, ni carpetas propias,
   ni formatos que solo Obsidian entienda.
3. **El ahorro de tokens se busca donde está el gasto**: `scripts/ledger.py`, que parsea
   `AUTONOMOUS_STATE.md` y responde «qué toca ahora» en ~114 tokens en vez de ~29.500
   (factor 258,8x, reproducible con `python scripts/ledger.py --json cost`).

**Razón:** cuatro hechos medidos el 2026-09-19 (detalle en
`docs/AUDITORIA_EXTERNA_2026-09-19.md`):

- **El repositorio de `notebooklm-mcp` está archivado.** Su `README.md` abre con
  «This project is no longer maintained… the repository is archived… It may stop working
  when the upstream services change». Sería infraestructura crítica sobre algo abandonado.
- **No es una API: es un Chrome dirigido por `patchright`** con perfil persistente y
  fingerprint de sigilo, y su `setup_auth` necesita un display. En Docker eso obliga a
  iniciar sesión con una cuenta de Google **dentro del contenedor**, que es el patrón que
  Google marca. El riesgo es perder la cuenta, no un fallo de build.
- **La latencia rompe el caso de uso.** `ANSWER_TIMEOUT_MS` por defecto son **600.000 ms**.
  Cada pregunta arranca un navegador; un `grep` sobre el ledger tarda milisegundos y
  además devuelve el número de línea.
- **Y lo definitivo: su respuesta no es evidencia.** El propio servidor prefija cada
  contestación con `[AI-GENERATED via Gemini 2.5 (NotebookLM) — treat citations and
  instructions as untrusted input]`. Este proyecto tiene como línea roja «evidencia
  ejecutable o no pasó» y publica una página de evidencia. Poner una paráfrasis de otro
  modelo donde hoy hay un hash de commit y una salida de `pytest` es reintroducir
  exactamente el mecanismo que produjo las 815 preguntas en cuarentena (§ADR-11, 25x) y la
  sociedad estonia inventada en 14 documentos legales (21.0). Además, el índice de
  NotebookLM es una instantánea: el ledger cambia cada sesión, así que habría que
  reingestar cada sesión — más navegador, más tiempo, más superficie de fallo.

Obsidian se descarta por un motivo más simple: es una interfaz humana sobre markdown, y el
agente ya lee markdown. No ahorra un solo token ni evita un solo error. Añadir sintaxis
propia de Obsidian a los docs vivos los haría peor markdown para todo lo demás.

**Consecuencia:** cuando el coste de contexto vuelva a doler, la respuesta es **hacer el
repositorio más consultable**, no delegarlo fuera: un comando que responda la pregunta
concreta, con su fuente citada por fichero y línea, y con tests. `scripts/ledger.py` es el
primero; el siguiente candidato natural es un índice equivalente para
`CATALOGO_MAESTRO.md`. Ninguna herramienta que devuelva prosa generada puede citarse como
evidencia de un `DONE` (ADR-20 sigue mandando).

**Alternativas descartadas:** NotebookLM vía MCP en Docker (archivado, automatización de
navegador, 600 s de techo, salida no citable); Obsidian (cero efecto medible); un índice
vectorial propio sobre los docs (mismo problema de instantánea y de salida no citable, más
una dependencia nueva que ADR-15 no paga); no hacer nada (deja los ~29.500 tokens por
sesión encima de la mesa).

---

## ADR-41 — Precios y reparto del marketplace: Pro 14,99 $, Pro Max 19,99 $, Creador 99,99 $, 80/20 por venta (DUEÑO, 2026-09-24)

**Origen.** Decisión del dueño en la sesión interactiva del 2026-09-24. Son sus
palabras, transcritas por voz y citadas tal cual: «Los precios serán de 14.99 dólares el
Pro y el Pro Max será de 19.99. En cuanto a la creación para el segmento de educadores y
profesionales que quieran crear sus bootcamps será 99.99 mensual.» Y del reparto: «de la
cantidad de dinero por el que venda el bootcamp el creador le quedará el 20% a la tienda
Wetsy». Se lee como: **el creador se queda el 80 % y Whetzy el 20 %** de cada venta.

**Decisión.**

| Plan (nombre de cara al usuario) | Tier en código | Precio | Qué da hoy, en código |
|---|---|---|---|
| Gratis | `free` / `NULL` | 0 $ | Todo el contenido, el motor adaptativo **y el repaso espaciado** |
| **Pro** | `plus` | **14,99 $/mes** | Tutor con IA (`require_tier("plus")`) y el modo examen del quiz |
| **Pro Max** | `pro` | **19,99 $/mes** | Todo Pro. ~~Lo que añade sobre Pro no está definido~~ → **tutor IA ilimitado (ADR-49, 2026-09-25)**; en código, todavía nada (38.6) |
| **Creador** | `creator` | **99,99 $/mes** | Todo Pro Max + publicar bootcamps en el marketplace |

- **Reparto del marketplace: 80 % creador / 20 % Whetzy** (antes 70/30).
  - Se aplica, como el 70/30 anterior, **sobre lo que queda tras la comisión de Paddle
    (7,5 %)**.
  - Después, `PaymentService` retiene un 22 % al creador (supuesto de H.29).
  - Resultado para una venta de 100 $: el creador recibe **57,72 $ netos** y Whetzy retiene
    34,78 $. Esa cifra incluye la retención, que no es ingreso de Whetzy.
  - Si la intención es «80 % del precio de venta», hay que cambiar el orden del cálculo;
    lo decide el dueño (H.35).
- **Los ids de tier no cambian** (`plus`, `pro`): están en la base de datos y en Stripe.
  Solo cambian los nombres que ve el usuario.
- **Publicar exige el plan Creador**, detrás de `CREATOR_PLAN_REQUIRED`.
  - Está **apagado** hasta que abra el cobro (H.19/H.29). Exigir un plan que nadie puede
    comprar cerraría el marketplace.
  - El dueño y los admins quedan fuera de la regla.
- **El repaso sale del muro de pago.** `POST /quiz/start` con `mode=review` devolvía 403 a
  todo usuario sin plan, es decir, a todos. Sin embargo, la landing prometía «repasos
  programados» gratis y Home ofrece «Repasar». Es el motor (FSRS), no un extra.

**Pendiente del dueño (H.35):**
- precio anual;
- tarifa regional;
- qué añade Pro Max sobre Pro;
- si el 80 % es sobre el precio de venta o tras la comisión.

**Supera a ADR-21** en los nombres (Pro/Premium → Pro/Pro Max). Los importes mensuales son
los mismos.

---

## ADR-45 — Control total de la sesión: rama + PR; `master` lo fusiona el dueño a mano (ACEPTADA 2026-09-24; era «ADR-41» en el PR #7 hasta que `master` ocupó ese número con los precios del dueño)

**Aceptada por el dueño** el 2026-09-24 («lo hago manualmente»), en la sesión interactiva
que preparó el prompt de control total (`docs/PROMPT_CONTROL_TOTAL.md`).

**Contexto:** `git push origin master` despliega backend, migraciones y `content_loader`
(H.16) y, desde el 2026-09-24, también el frontend (Cloudflare Pages conectado a Git).
No hay nada en medio: el CI de GitHub no corre (H.13/H.17) y el login de producción se
rompió así (serie 30). El contrato de autonomía de `ORCHESTRATOR.md` todavía decía
«`git push` a `master` sin preguntar».

**Decisión:**
1. Una sesión autónoma tiene **control total dentro de su rama**: escribe código,
   contenido, docs, migraciones aditivas, tests, scripts; corre lo que haga falta;
   reorganiza; abre y actualiza **un PR por oleada** con capturas y evidencia.
2. **Ninguna sesión hace `push` a `master` ni fusiona un PR.** `master` recibe solo lo
   que el dueño fusiona a mano tras ver el preview de Cloudflare Pages
   (`<rama>.whetzy.pages.dev`) y el veredicto de las guardas locales
   (`.githooks/pre-push`, `scripts/ci_local.sh`). Tras cada fusión: `node
   scripts/check-deployed.mjs` en PASS o no está hecho.
3. Lo que sigue **fuera** de la autonomía (se prepara, se documenta en `HUMAN-BLOCKED`,
   se sigue con otra cosa): gasto de dinero, claves live, DNS, datos de usuarios reales,
   operaciones destructivas sobre la DB de producción, submisión a tiendas, rotar
   secretos, crear cuentas en servicios (aunque sean gratis), reabrir una decisión
   cerrada.
4. Presupuesto: la sesión trabaja **hasta que el límite la detenga**. No raciona ni
   se cierra sola mientras quede una fila ejecutable (`python scripts/ledger.py next`).

**Consecuencias:** H.16 pasa a tener respuesta (opción 2: `master` solo por PR); solo
queda que el dueño active la protección de rama en GitHub. `ORCHESTRATOR.md`
(contrato) y `CLAUDE.md` (invariantes) se actualizan en esta misma sesión.

---

## ADR-46 — Catálogo total: todos los tracks de la industria, ≥ 50 cursos por track, sobre un corpus abierto descargado y verificado (ACEPTADA 2026-09-24)

> **Sustituida en su meta por ADR-53 el 2026-09-30:** los puntos 1 (alcance) y 3 (meta de
> volumen) ya no rigen: manda el suelo de 50 skills · 800 preguntas por track, el ideal por
> temario y los tracks por demanda medida. Siguen vigentes el corpus abierto fuera del repo
> (puntos 4–5) y la guarda de diversidad 37.0 (punto 6). El punto 2 («curso = módulo») queda
> solo como unidad de presentación en la web.

**Aceptada por el dueño** el 2026-09-24. Sustituye la meta de ADR-25 (100 cursos × 27/28
tracks), que nunca definió qué era un «curso» y cuyo primer intento (serie 25, 2026-09-19)
no pasó la puerta de calidad: 800 preguntas con 14 enunciados distintos por track.

**Decisión:**
1. **Alcance:** cubrir **todos los tracks que existen en la industria** del software y la
   informática, no solo los 28 del mapa de 2026-09-16. La lista vive en
   `CATALOGO_MAESTRO.md` §2 (28 actuales) y **§2.0** (ampliación, 14 tracks más; se amplía
   cuando el inventario 37.1 encuentre un área sin track).
2. **Curso = módulo del molde** (catálogo §2): **4 skills · 60 preguntas · 4 lecciones ·
   ≥ 8 términos · ≥ 15 % ejecutable donde el navegador ejecute** (Python, SQL, JS) o
   exento con razón (ADR-9). Es la unidad que ya existe en `tracks.json`; no se inventa
   otra. `check_docs.py` sigue contando «cursos = track × nivel» hasta que 37.2 cambie el
   recuento a módulos en el mismo commit que la web.
3. **Meta:** **≥ 50 cursos por track** = 200 skills · 3.000 Q · 200 lecciones · ≥ 400
   términos por track. Con 42 tracks: ≈ 126.000 preguntas. Hoy: 6.305. A la velocidad
   medida de la sesión 18.4 (`bec734c`: 518 Q verificadas en tres tracks en una sesión),
   son ≈ 240 sesiones de contenido. Es una meta de años; se persigue sin fecha y sin
   racionar, un bloque = un PR verde.
4. **Corpus abierto, descargado y verificado (petición del dueño):** la sesión descarga
   **toda la fuente legal y abierta** que sirva a un track —repositorios (`git clone`),
   dumps y volcados masivos (Wikipedia, Gutenberg, arXiv bulk, docs oficiales con
   licencia libre), **torrents solo cuando sean el canal de distribución oficial de un
   corpus legal** (Gutenberg, Wikimedia, Internet Archive con licencia declarada)—, la
   **verifica** (fichero `LICENSE` leído; entrada en `content/sources/index.json` con
   URL, fecha, licencia y hash) y la **limpia** (deduplicación, extracción de texto,
   separación por track y skill). Nada pirata, nada CC BY-NC, nada propietario entra al
   corpus como material reutilizable (ADR-11); lo propietario se cita.
5. **El corpus vive fuera del repo**: `corpus/` (gitignored) o un volumen local; el repo
   solo recibe `content/sources/index.json` y el contenido **original** derivado, ES y EN
   nativos, con la fuente citada por pregunta y lección.
6. **Puerta de calidad antes que volumen:** nada de la serie 37 escribe preguntas hasta
   que exista la **guarda de diversidad semántica** (37.0): enunciados distintos ≥ 90 %
   por track, opciones de una palabra ≤ 40 %, cero ejecutables sin código, distractores
   defendibles. Se muta a propósito y se ve en rojo antes de fiarse (CLAUDE.md, estilo).

**Consecuencias:** serie 25 se subordina a 37.0 y se reabre; nace la serie 37 (catálogo
total + corpus) con su propio orden; `CATALOGO_MAESTRO.md` cambia de objetivo y corrige la
proyección competitiva de §12 (su tabla sumaba 49 donde decía 44).

---

## ADR-47 — Valores por defecto de la cola humana, para que la sesión no se detenga (ACEPTADA 2026-09-24; numerada 47 el 2026-09-25 porque `master` ya tenía ADR-41…44 ocupadas por decisiones paralelas del dueño)

> **Enmendada**: modelos por ADR-52; entidad y jurisdicción por ADR-61 §22 (Chipre como destino, sin entidad constituida; H.54); marca por la aprobación del dueño del 2026-10-13 (colores del logo, #197). Nota añadida el 2026-10-16 por ADR-61 §27.

**Aceptada por el dueño** el 2026-09-24 («eso lo dejo para el final»): las decisiones que
solo él puede tomar quedan en `HUMAN-BLOCKED`, pero cada una lleva un **valor por
defecto** que la sesión asume mientras él no lo vete. Nada de esto gasta dinero ni
publica nada.

| Bloqueo | Valor por defecto | Por qué |
|---|---|---|
| H.LIC / H.22 (CC BY-SA) | **No.** Se cita y enlaza, no se reutiliza. | El banco de preguntas es el activo; heredar copyleft lo regala. NIST, MITRE, RFC y docs Apache/MIT bastan. |
| H.19 / H.29 (rail y entidad) | **Merchant of Record** (Paddle o Lemon Squeezy) en web + IAP (RevenueCat) en tiendas, tras una abstracción `PaymentProvider`; **entidad y jurisdicción sin decidir**: la premisa griega de ADR-16 queda **suspendida**, no se escribe «autónomo griego» en ningún doc vivo. | MoR cobra IVA por nosotros y no exige sociedad; el dueño elige después sin rehacer código. |
| Precios | **Los fijó el dueño en ADR-41 (2026-09-24): Pro 14,99 $ · Pro Max 19,99 $ · Creador 99,99 $, reparto 80/20; se publican (35.7).** Esta ADR no añade hipótesis propia. Quedan en H.35: anual, tarifa regional, qué añade Pro Max y si el 80 % es sobre venta o tras comisión. **B2B: $99 por asiento y año, mínimo 10** (hipótesis; ADR-22 decía $500/persona). | Tres documentos daban cuatro precios; la decisión del dueño los sustituye a todos. |
| H.23 (abrir distribución) | **Sí.** Se redacta todo (artículos, guiones, landings, PRs a listas). Solo **publicar bajo una cuenta nueva** sigue siendo del dueño. | Lo redactado no caduca; crear cuentas sí es acto del dueño (ADR-45 §3). |
| H.24 / marketplace | **Se construye entero (serie 28); no se abre al público antes de ≥ 100 usuarios activos** (catálogo §9). | Sala vacía. |
| H.26 (economía) | **Se acepta la tabla de `ECONOMIA.md` §2.2–§2.3 como hipótesis**; la serie 29 sigue en código; ninguna recompensa con importe hasta que haya ingresos. | Igual que los precios. |
| H.27 (cNFT) | **No.** Solo Open Badges 3.0. | €0 y sin wallet. |
| Marca | **Paleta Obsidian de la serie 34**: oscuro por defecto, cian `#06B6D4`, verde solo para éxito; claro solo en `[data-theme="light"]`. | El «azul cielo, modo claro por defecto» de `ORCHESTRATOR.md` ya no describe la app. |
| Modelo de sesión | ADR-14 sigue para las sesiones programadas. **Una sesión interactiva usa el modelo que el dueño fije al arrancarla.** | El dueño eligió Fable 5.1 el 2026-09-24. |

**Planes de la documentación que se adoptan** (con fila en el ledger desde hoy): cuota
de tokens por usuario en `/tutor`, arranque en frío de Railway, fase 3 del modelo de
amenazas (HMAC, RS256, cookies HttpOnly), confirmación de edad mínima en el registro,
proceso DMCA y DPIA, monitoreo trimestral de competencia, KPIs de `DISTRIBUCION.md` §10
en el admin, oferta de 3 pilotos B2B gratuitos, kit de reclutamiento de instructores,
dossier de afiliación (Python Institute, CompTIA), blog `/blog` y newsletter,
comparativa honesta frente a Coursera/Udemy, IAP (la vieja 7.6, sin fila desde hace
meses).

**Planes que se descartan por escrito:** clases en vivo (LiveKit/Daily), boss battles y
clanes, mock interviews con IA, mentoring, patrocinadores de tracks, TikTok/Reels y
Telegram, white-label/LMS-SCORM para universidades (hasta que un piloto B2B lo pida),
DPO (no exigible a este tamaño), Creator Pro como plan aparte (se funde en la 28).
Cualquier «Fase 1/3/5/6 del plan del 2026-09-24» no existe en el repo: **las series 30-35
son la única fuente**.

---

## ADR-48 — Documentos de planificación paralelos se archivan; el ledger es el único plan (ACEPTADA 2026-09-24)

**Decisión:** `EXECUTION_PLAN_25-29.md`, `ROADMAP_25-29.md`, `26/28/29-PLANNING.md`,
`28-INTEGRATION.md`, `SERIE29_STATUS.md`, `SERIES_22_4_7_SUMMARY.md`,
`SERIE_24_SUMMARY.txt` y `VERIFICATION_CHECKLIST_FINAL.md` pasan a `docs/archive/`.
Reutilizaban IDs del ledger para tareas distintas (25.1, 25.14, 28.4, 29.2, 29.6),
declaraban «ALL GATES OPEN» con H.29 abierta y daban tres mínimos de payout distintos
($10, $50, €50). `25.0-planning.md` se queda porque un test lo exige
(`tests/integration/test_security_tracks.py:82`), con cabecera de superado.
**Regla:** un plan que no sea una fila del ledger no es un plan; si merece existir, se
convierte en fila. Los cuatro HTML duplicados de `analisis-estrategico/` con un carácter
invisible (U+F00D) en el nombre se borran: eran copias anteriores de los mismos ficheros.

---

## ADR-49 — Pro Max = tutor IA ilimitado; certificación a 39,99 $ de pago único (DUEÑO, 2026-09-25)

**Origen.** Respuesta del dueño a H.35 (3) y a la pregunta sobre certificaciones, en la
sesión interactiva del 2026-09-25, citada tal cual: «Pro Max añade tutor IA ilimitado;
39,99 pago único por certificación».

**Decisión 1 — Pro Max.** Lo que Pro Max (`pro`) añade sobre Pro (`plus`) es el **tutor IA
ilimitado**. Consecuencia necesaria: **Pro pasa a tener un cupo** de tutor. Hoy el cupo no
existe: `POST /tutor/explain` solo exige `require_tier("plus")` y el único freno es el
límite por minuto e IP del middleware.
- **Cupo diario de Pro: sin fijar por el dueño (H.35-5).** Valor por defecto (ADR-47) para
  poder construir: `TUTOR_DAILY_LIMIT_PLUS = 20` explicaciones al día. No se publica
  hasta que el dueño lo confirme.
- «Ilimitado» no quita el freno por minuto contra abuso: es un límite técnico, no de plan.
- El coste del LLM (Groq) crece con el uso ilimitado y **no está medido**. 38.6 lo registra
  por usuario para que el dueño vea el coste real de Pro Max.

**Decisión 2 — Certificación.** Cada certificación se desbloquea con un **pago único de
39,99 $**, aparte de la suscripción.

**Hallazgo que condiciona la decisión 2.** Hoy un track de certificación no emite
certificado:
- `start_track_final` rechaza los tracks con `is_certification`
  (`backend/app/services/track_exam.py:214`).
- Esos tracks solo tienen simulacro (`/exams/mock/start`) y readiness.
- Los certificados que existen son los del examen final de los tracks de aprendizaje, y
  son gratis para cualquier usuario con sesión (`exams.py:271`, sin comprobación de plan).

**Valores por defecto (ADR-47; el dueño los revoca con una línea):**

| Punto | Por defecto |
|---|---|
| Qué se compra | Por cada track de certificación (`is_certification`: hoy track08, 09, 10, 11 y 40): un **examen certificador** en el formato del blueprint oficial. Si se aprueba, se emite un certificado Whetzy verificable por URL. |
| Reintentos | Incluidos: pago único significa que no se vuelve a pagar por suspender. |
| Quién puede comprar | Cualquier plan, gratis incluido. Ninguna suscripción lo incluye. |
| Qué sigue sin pagar aparte | La preparación: lecciones, quiz, simulacros y readiness, según el plan de cada uno. |
| Certificados de tracks de aprendizaje | Siguen gratis. |
| Nombre | «Certificado Whetzy de preparación para <certificación>». **Nunca** «certificación oficial»: AWS, ISC2 y Python Institute emiten las suyas. |
| Cobro | Detrás de `CERTIFICATION_PAYWALL`, **apagado** hasta que abra el cobro (H.19/H.29). Es el mismo motivo que `CREATOR_PLAN_REQUIRED` en ADR-41: exigir un pago que nadie puede hacer cerraría el producto. |

**Supera a** ADR-41 en la fila «Pro Max: lo que añade sobre Pro no está definido».
**Choca con** la ficha de App Store (`docs/store/ios/listing.md:152`,
`app.whetzy.plus.yearly $39.99/año`): ese importe anual no sale de ninguna decisión del
dueño y ahora, además, coincide con el precio de la certificación. Se limpia en 38.1.

---

## ADR-50 — Aprobación en bloque del dueño y decisiones de la noche del 2026-09-26 (DUEÑO en bloque; valores elegidos por la sesión)

> **Enmendada por ADR-52 (2026-09-27)** en las decisiones de modelos. Nota añadida el 2026-10-16 por ADR-61 §27.

**Origen.** Mensajes del dueño en la sesión interactiva del 2026-09-26, citados tal cual:
«DESBLOQUEA TODO, MI DESICIONES SON A TODO APROBADO!», «HAZLO TODO SI ESTA EN TUS MANOS»,
«PROCEDE Y ADEMAS DECIDE POR MI TODO ESTO» (sobre H.31, H.30, H.13/H.17, H.15, H.41 y H.16).
El dueño aprobó **en bloque**; **los valores concretos los eligió la sesión** y aquí se
dice cuál es cuál. Cualquiera se revierte con una línea del dueño.

**Límites que la aprobación no levanta** (prompt de control total v5, §2): no fusionar
`master` (ADR-45), no gastar dinero, no abrir cuentas, no publicar, no escribir datos de
personas reales. La única escritura en producción de la noche fue la de H.41, pedida por el
dueño por su nombre.

| # | Punto | Decisión y estado |
|---|---|---|
| a | Plan Free | 5 lecciones y 30 preguntas **nuevas** al día, reinicio a medianoche UTC; exentos los repasos FSRS, el placement y los exámenes. Detrás de `FREE_DAILY_QUOTA_ENABLED=false` hasta que abra el cobro (H.19/H.29): limitar para empujar a un plan que nadie puede comprar cierra el producto. El tutor sigue sin acceso en Free (`tutor.py`, `require_tier("plus")`). |
| b | Anuncios | No en la v1 (ATT de Apple, consentimiento, COPPA). Se revisa con ≥ 20K usuarios activos al mes. |
| c | Precio por plataforma | El mismo en web, iOS y Android. |
| d | Formato de lección (§25 de la evaluación) | En la **plantilla** de `LessonScreen` (secciones con icono accesible, `aria-hidden` en lo decorativo); no se reescribe el texto de las lecciones. |
| e | LICENSE | Código propietario («All rights reserved»); contenido educativo original **CC BY-NC-ND 4.0**, porque es lo que ya publican los Términos (§3.1) y un LICENSE no puede contradecirlos; el material de terceros conserva su licencia según `content/sources/index.json`. Hecho: `LICENSE` en la raíz. |
| f | LLM de respaldo | Proveedor compatible con OpenAI configurable por entorno; vacío = sin respaldo. |
| g | Emails de re-enganche | 3, 7 y 30 días de inactividad, baja en un clic (CAN-SPAM), flag apagado. |
| h | Certificaciones siguientes | Las 11 actuales ya incluyen Security+ (track42) y AZ-900/AI-900/DP-900 (track44–46). Siguientes, dentro de 37.10: **CCNA → LPIC-1 → CKA → GCP Associate Cloud Engineer**. *Reordenado por ADR-53 (2026-09-30): primero las que se examinan en español —GCP ACE, LPIC-1, AZ-104—; después CKA (sin español) y CCNA (idioma sin comprobar).* |
| i | Idiomas | ES y EN. El siguiente, pt-BR, solo con revisión nativa. |
| j | Analítica de producto (H.42) | **Revisada la misma noche:** la analítica ya es **propia** (`services/analytics.py` → tabla `analytics_events`, embudo registro→primer quiz→D1→D7 en el admin) y la landing promete «sin analítica de terceros» y no hay banner de consentimiento. Por eso **no se instala PostHog ni Mixpanel en el navegador**. Si hace falta un panel externo, PostHog entra solo como destino **desde el backend**, con la política de privacidad actualizada antes (fila H). |
| k | Errores (H.41) | **Sentry, ejecutado, solo en el backend** (en el navegador sería un origen de terceros con la CSP y la promesa de la landing en contra). Privacidad y DPA actualizados el mismo día. Proyecto `whetzy-backend` (org `whetzy`, región `de.sentry.io`) creado con el conector y `SENTRY_DSN` puesto en Railway. Deploy `f097361c` en `SUCCESS` con el log `Sentry initialised (env=production, traces_sample_rate=0.1)` (11:34 UTC). `send_default_pii=False`. El cambio de variable produjo ~20 s de 502 (11:34:31–11:34:41 UTC). El monitor de uptime de Sentry **no** se creó: puede consumir cuota de pago. |
| l | H.30 correo | Proveedor por defecto: **Resend** (el código ya lo soporta con solo `RESEND_API_KEY`). Crear la cuenta y la clave es del dueño. Mientras tanto, `bb59562`: en producción sin proveedor, `forgot-password` y `resend-verification` responden 503 `email_not_configured` y la pantalla lo dice, en vez de afirmar que el enlace se envió. |
| m | H.31 landing | **Ya resuelta**: la landing servida el 2026-09-26 no contiene testimonios ni «1.2M»; las tarjetas muestran afirmaciones comprobables («Cada pregunta cita su fuente»). |
| n | H.15 proxy de vite | **Ya resuelta**: el proxy apunta a `127.0.0.1:8000` y `pretest:e2e` (`scripts/check-e2e-target.mjs`) impide correr e2e contra producción. |
| o | H.13/H.17 GitHub Actions | GitHub → Settings → Billing: poner el **spending limit de Actions a $0** y corregir el método de pago si hay factura fallida. Solo el dueño puede. Mientras tanto, la puerta es local (`.githooks/pre-push` + `ci_local.sh`). |
| p | H.16 / 30.2 / 31.1 despliegue y staging | Se mantiene el despliegue automático desde `master` (ADR-45). Se aprueba **proteger `master`** (PR obligatorio, sin push directo; las fusiones del dueño y de Dependabot pasan por PR) — lo configura el dueño en GitHub → Settings → Branches. Se aprueba el **staging** de 31.1 (entorno Railway `staging` + preview de Pages); su alta cuesta dinero y la hace el dueño. Hasta entonces, la prueba de arranque local (Postgres 16, `start.sh` paso a paso) es la puerta obligatoria para `content/` y `backend/`. |

> **Enmienda a ADR-14 (2026-09-26).** Frase del dueño: «ACTUALIZALO PARA QUE USE LAS LLM QUE ME
> RECOMIENDAS TANTO EL MODELO PRINCIPAL COMO LOS SUBAGENTES». En las sesiones **arrancadas por el
> dueño**: hilo principal Opus 5.5 (effort high), subagentes Haiku 4.5 y Sonnet 5 solo para
> escribir en la lista de riesgo. ADR-14 sigue igual para las sesiones programadas.

> **Enmienda a ADR-50 y a CLAUDE.md §Modelos (2026-09-26, tarde; decisión de la sesión con la
> delegación del dueño).** **Autoría y revisión de contenido: Sonnet, no Haiku.** Haiku queda
> para lecturas, inventarios y diffs de solo lectura. Evidencia: en el piloto de lecciones de
> track28 (2026-09-26), 7 de 10 lecciones escritas por Haiku traían frases de relleno sin
> sentido, errores técnicos (un 302 presentado como redirección permanente) o fuentes que no
> respaldaban el texto, y un segundo lote no devolvió nada; en la sesión anterior, las tres
> reescrituras de distractores de track11 hechas por Haiku se rechazaron (relleno, opciones
> duplicadas, la correcta copiada en otra ranura en 51 preguntas). Sonnet tampoco es fiable
> solo: el reescritor Sonnet movió claves de ranura en track28 (4), track29 (6) y `mod3002`
> (52), por eso cada lote pasa por `check_key_drift.py`. Con Sonnet como autor, revisor y corrector,
> más la verificación propia con `scripts/content_qa/`, las lecciones de 18-20 y 26-30 y las
> 1.404 explicaciones de 39.29 entraron sin fallos de guarda. Coste mayor por fichero y
> aceptado: un banco con claves malas es peor que uno más corto.

## ADR-51 — Decisiones de la sesión del 2026-09-26 por la noche (delegación total del dueño; valores elegidos por la sesión)

**Contexto.** El dueño arrancó la sesión con el prompt de control total v6.1 («DESBLOQUEA TODO,
MI DESICIONES SON A TODO APROBADO!», «HAZLO TODO SI ESTA EN TUS MANOS») y se fue a dormir. Lo que
aprobó en bloque es ADR-50; lo que sigue son valores que eligió la sesión, cada uno con su motivo.

| # | Tema | Decisión de la sesión | Motivo |
|---|---|---|---|
| a | Rama | Se trabaja en `claude/gallant-tesla-fnzy1g` (la asignada a la sesión) con un *merge* de `claude/trusting-franklin-2wwmmr`; el PR nuevo (#34) contiene #33 | La sesión no puede empujar a otra rama sin permiso; un merge no reescribe historia (ADR-45) |
| b | 39.4 «pregunta nueva» | La primera respuesta del usuario a esa pregunta, hoy (UTC), en una sesión `study`. Repaso, placement y examen no gastan ni se bloquean | ADR-50a exime repasos FSRS, placement y exámenes; contar por respuesta (no por pregunta servida) evita gastar cupo con preguntas que el alumno no llegó a ver |
| c | 39.4 al agotarse | `POST /quiz/start` → 429 `{code: free_daily_quota, kind, limit, resets_at}`; `POST /quiz/answer` → `next_question: null` + `quota_reached: true` | El cliente ya trata `next_question: null` como fin de sesión («Ver resultados»); el 429 lleva cuándo se reinicia |
| d | 39.4 lecciones | Se cuentan solo con sesión iniciada (`get_optional_user`; un token malo = anónimo). Sin sesión la lección sigue pública | Cerrar las lecciones públicas rompería la landing y el SEO, y ADR-50a no lo pide. Limitación conocida: quien cierre sesión lee sin cupo. Antes de encender el flag falta el texto de la UI (ES/EN) |
| e | 39.28 alcance | La fila nombraba dos familias de coletillas; se amplía a la tercera (minada del banco: colas de 2-6 palabras en cientos de incorrectas y 0-2 correctas) y a «as the primary concept» (673 opciones EN que la guarda no veía) | Es el mismo defecto de generador; dejarlo fuera habría dado el track por limpio con la mitad de la coletilla dentro. La línea base se re-midió al alza porque la guarda ve más, no porque el banco empeorase |
| f | 39.28 método | Parches por pregunta (solo `options_es`/`options_en`), aplicados por script; nunca el fichero entero reescrito por un agente | Por construcción no cambian ids, claves, enunciados ni explicaciones; `check_only_fields` y `check_key_drift` lo confirman |
| g | Claves falsas encontradas | Se corrigen en su sitio con la doc oficial abierta (p. ej. `q220103001`: la duración **máxima** en el plan de consumo de Azure Functions es 10 min, no 5) | `content_loader` nunca borra preguntas: se arreglan sin renombrar ids |
| h | Tests que ya fallaban en `master` | OAuth (esperaban el token en la URL, el código usa cookies HttpOnly) y `ledger.py check` (55 problemas): se arreglan en este PR | «Correr la suite entera» no sirve de puerta si ya está roja |
| i | Capturas de 39.5 | Van a `frontend/test-results/` (ignorado) y al informe, no al repo | Límite duro: sin binarios en el repo |

## ADR-52 — Política de modelos del dueño (DUEÑO, 2026-09-27; sustituye la línea de modelos de ADR-50 y su enmienda del 2026-09-26)

> **Enmendada por ADR-59 el 2026-10-03:** la autoría de contenido para el alumno la escribe
> **Sonnet 5**, no Haiku 4.5. Se mantienen el piloto de 10 ítems con su umbral de 3/10 y el
> resto de la tabla. La fila «Autoría masiva… Haiku 4.5» de abajo es histórica.

**Decisión del dueño (literal, 2026-09-27):**

```
Hilo principal interactivo (tú aquí):  Sonnet 5   → −33% vs ahora, mejor cutoff
Subagentes de autoría masiva:          Haiku 4.5  → sin cambio (ya es el más barato)
  + Batch API para fillers:            Haiku 4.5  → −50% adicional por lote
Revisor de calidad en Workflow:        Sonnet 5   → −33% vs Sonnet 4.6
Sesiones autónomas programadas:        Haiku 4.5  → ADR-14 ya lo manda

Fable 5.1 y Opus 4.x: no usar para Whetzy.
  Fable = razonamiento largo; no es el cuello de botella aquí.
  Opus 4.x = legacy más caro que Sonnet 5 con peor conocimiento.
```

**Cómo lo aplica el repo:**

| Papel | Modelo | Notas |
|---|---|---|
| Hilo principal de una sesión interactiva | **Sonnet 5** | Lo fija el dueño al arrancar la sesión; una sesión no puede cambiar su propio modelo. Sustituye «hilo Opus 5.5 effort high» de ADR-50 |
| Autoría masiva de contenido (lecciones, preguntas, distractores, explicaciones) | **Haiku 4.5** | `Workflow` con `model: "haiku"` para el escritor |
| Revisor de calidad y corrector en `Workflow` | **Sonnet 5** | Revisión adversaria **completa** (no por muestreo) de todo lo que escribe Haiku, más `scripts/content_qa/` y la puerta de `CATALOGO_MAESTRO.md` §7 |
| Worker que escribe en la lista de riesgo (`PROTOCOLO_VERIFICACION.md` §2) | **Sonnet 5** | La tabla del dueño no lo nombra; la sesión lo asimila al papel de «revisor de calidad» (es código de riesgo, no autoría masiva) |
| Lecturas, inventarios, diffs, verificador §7 de tareas que no son contenido | **Haiku 4.5** | Sin cambio |
| Sesiones autónomas programadas | **Haiku 4.5** en los workers | ADR-14 tal cual: workers Haiku; el hilo, el que fije `settings.json` hasta que el dueño lo cambie |
| Fable (cualquier versión) y Opus 4.x | **Prohibidos** en cualquier papel | Opus 5.5 tampoco tiene papel: el hilo interactivo pasa a Sonnet 5 |

**Riesgo que la sesión deja escrito (no cambia la decisión):** la enmienda a ADR-50 del
2026-09-26 pasó la autoría a Sonnet por evidencia medida, no por preferencia: en el piloto de
track28, 7 de 10 lecciones escritas por Haiku traían relleno, errores técnicos o fuentes que no
casaban, y un lote volvió vacío (RUNBOOK, «Contenido reescrito por agentes»). Con Haiku de
escritor, el revisor Sonnet 5 debe esperar más rechazos por lote. Mitigación que aplica la
sesión: el primer bloque de Haiku va como piloto de 10 ítems con revisión completa; si más de 3
de 10 salen con problema `blocker` o `major`, se para y se anota en el ledger para que el dueño
decida, sin volver a Sonnet por cuenta propia.

**Batch API:** ningún código del repo llama a la API de Anthropic (búsqueda del 2026-09-27 de
`anthropic` y `claude-` en `*.py`, `*.ts`, `*.toml`, `*.txt` y `*.json` fuera de `content/`
y `node_modules`: 0 resultados). Un lote por Batch API necesita un script nuevo y una clave de
API con gasto, es decir, una cuenta y un secreto: queda en la cola humana (H.48) hasta que el
dueño ponga la clave. Hasta entonces los rellenos van por `Workflow` sin descuento de lote.

**Cifras:** los porcentajes de ahorro son del dueño; la sesión no los ha comprobado.

---

## ADR-53 — Plan del catálogo por cobertura: suelo competitivo, ideal por temario, simulacros reservados y prioridad por demanda (DUEÑO, 2026-09-30; cifras elegidas por la sesión con fuentes; sustituye la meta de volumen de ADR-46)

> **Sustituida en su suelo e ideal por ADR-54 (2026-10-01).** `scripts/metas_adr53.json` se llama
> desde entonces `scripts/metas_catalogo.json`. Lo que sigue es histórico.

**Origen.** El 2026-09-29 el dueño preguntó si la meta de ADR-46 (≥ 50 cursos × 42 tracks
= 8.400 skills · 126.000 preguntas) estaba sobredimensionada frente a la competencia directa, y
el 2026-09-30 pidió investigar en internet las métricas ideales «sin dejar nada por fuera» y
rehacer el plan y **todos** los documentos sobre ellas. La sesión investigó con 4 agentes
(≈ 150 fuentes) y **descargó y leyó ella misma** cada cifra en la que se apoya esta decisión
(tabla de evidencia abajo; lo que solo leyó un agente se marca). Los números de las metas son
elección de la sesión sobre esa evidencia; el dueño manda cambiarlos.

**Qué falla en ADR-46.** No el número de preguntas por skill (15, ya cumplido) sino **200
skills por track**, el doble de cualquier temario de referencia (mediana de 56 roadmaps de
roadmap.sh ≈ 113 nodos; Python 87), la unidad «curso» (en Whetzy es un módulo de 4 skills; en
Platzi o Boot.dev es un curso de horas) y una lista fija de 42 tracks sin medida de demanda.

**Decisión:**

1. **Unidad de medida: la skill** (componente de conocimiento). «Curso = módulo» sigue solo
   como unidad de presentación en la web (`frontend/src/lib/catalog.ts`); no es meta.
2. **Suelo por track de aprendizaje** (lo que ya compite): **50 skills · 800 preguntas
   (≥ 16 por skill) · 1 lección por skill · 1 término de glosario por skill · ≥ 15 %
   ejecutable donde el navegador ejecute** (regla de ADR-9 sin cambios) · guarda 37.0 en verde.
   Equivale a unas 15–20 h de estudio, la mediana de un curso de Boot.dev (20 h).
3. **Ideal por track (cobertura):** tantas skills como **nodos del temario de referencia
   asignados al track** (roadmap.sh, nodos `topic` + `subtopic` del JSON público), nunca menos
   que el suelo; **20 preguntas por skill** (15 si es de recordar un dato, 25 si es de
   procedimiento o ejecutable; un generador parametrizado cuenta por sus variantes); 1 lección
   de 6–10 min por skill. Los denominadores viven en `scripts/metas_adr53.json` (URL y fecha
   por cifra). Un track sin temario de referencia tiene el suelo como ideal hasta que 37.1 lo
   fije. Un roadmap compartido se reparte entre tracks sin contarse dos veces.
4. **Certificaciones:**
   - *Suelo:* 100 % de los objetivos oficiales con ≥ 1 skill cada uno · ≥ 15 preguntas de
     práctica por skill · **banco de simulacro reservado de 6 × la longitud del examen**,
     marcado `"pool": "simulacro"`, que **no** sale en práctica ni repaso · formato del
     simulacro = el que publica el proveedor (URL y fecha).
   - *Ideal:* 2 skills por objetivo · 20 preguntas por skill · el mismo banco reservado.
   - Hoy el simulacro saca sus preguntas del mismo banco que la práctica
     (`backend/app/services/mock_exam.py:110-136`): la nota mide en parte memoria. Es la
     primera obra de esta ADR.
5. **Qué tracks existen: los que tengan demanda medida**, no una lista fija. Nivel por uso
   en Stack Overflow Developer Survey 2025 (All Respondents): **A ≥ 25 %**, **B 10–25 %**,
   **C < 10 % o sin medida**. Los tracks ya construidos se quedan. Los nuevos llegan al suelo
   en orden A → B; los C solo cuando todos los A y B estén en el suelo. Tabla por track en
   `scripts/metas_adr53.json` (45 filas: los 42 del mapa anterior + PHP, Ruby y R).
6. **Orden de ejecución** (serie 37 del ledger):
   - **Fase 0:** banco de simulacro reservado (4), formatos de examen corregidos (AIF-C01,
     MLA-C01 y los tres de Microsoft) y métricas de producto instrumentadas (8).
   - **Fase 1:** las 11 certificaciones al suelo.
   - **Fase 2:** los 24 tracks construidos al suelo (A primero), y track24/25 reconstruidos.
   - **Fase 3:** tracks nuevos A (Java, C#, TypeScript) y B (móvil, Go, Rust, C/C++, SRE,
     PowerShell, PHP) al suelo.
   - **Fase 4:** el ideal, por nivel de demanda; después, los tracks C.
   - **Certificaciones nuevas:** primero las que se examinan en español (GCP Associate Cloud
     Engineer, LPIC-1, AZ-104; comprobado el 2026-09-30), después CKA/CKAD (solo inglés, chino
     y japonés) y CCNA (idioma sin comprobar).
7. **Se mantiene de ADR-46:** el corpus abierto fuera del repo (§4–5), la guarda de diversidad
   37.0 antes de cualquier pregunta nueva (§6) y las fuentes de ADR-11. **Se va:** «todos los
   tracks de la industria», «≥ 50 cursos por track», 200 skills · 3.000 preguntas · 200
   lecciones · ≥ 400 términos por track, y las ≈ 240 sesiones.
8. **Métricas de producto con suelo** (el contenido no es el cuello de botella: un catálogo
   perfecto con la retención media de educación fracasa). Es el **mínimo**, no la aspiración:
   las metas a 12 meses de ADR-32 (D30 > 10 %, conversión > 4 %, completion > 50 %) siguen
   por encima; la cohorte beta de H.10 tiene las suyas (D1 ≥ 40 %, D7 ≥ 20 %).

   | Métrica | Suelo | Referencia comprobada |
   |---|---|---|
   | D1 | ≥ 15 % | Education D1 13,93 % Android / 14,59 % iOS (AppsFlyer) |
   | D7 | ≥ 7 % | umbral de cuartil superior de Amplitude (lectura de agente, sin reproducir) |
   | D30 | ≥ 4 % | Education D30 2,69 % / 3,23 % (AppsFlyer); 2 % (Business of Apps) |
   | Conversión a pago a D35 | ≥ 2,1 %, meta 3 % | freemium, mediana 2,1 %; Education iOS 3,1 % (RevenueCat 2026) |
   | Terminan el track entre quienes pagan | 40–55 % | edX: 46 % de los verificados, 3,13 % de todos (2017-18) |
   | Alumnos de pago con ≥ 30 min/semana | ≥ 25 % (hipótesis) | Khan Academy: 30+ min/semana ↔ ~20 % más ganancia (correlación) |
   | CURR (vuelven mañana los activos de la semana) | medirla desde el día 1 | Duolingo: 84 % (Q2 2026) |
   | Calibración del simulacro frente al examen real | publicarla siempre con n | nadie en el mercado publica una auditada |

**Evidencia** (descargada y leída por la sesión el 2026-09-30 salvo donde se indica):

| Qué | Cifra | Fuente |
|---|---|---|
| Práctica para dominar una skill | «about seven opportunities per component of knowledge»; mediana 7,24, media 12,27 | Koedinger et al. 2023, PNAS (texto completo en Europe PMC, PMC10068755) |
| Ítems por skill en un sistema real | «three in a row» para dominar, máximo 10 por sesión, «between 20-100 practice problems» por skill | assistments.org, Skill Builders |
| Banco para simulacros | «six to eight linear tests»; «about 12 times the length» del examen | Stocking 1994 (ETS RR-94-05); Way 2006 (Pearson) |
| Retención objetivo del repaso | «The default is 90%» | docs.ankiweb.net (FSRS) |
| Repasos por ítem al año | ≈ 9–10 a retención 0,90 | simulación de un agente con py-fsrs 6.3.2; **sin reproducir** |
| Tamaño de un temario | python 87 · sql 113 · backend 155 · cyber-security 301 · docker 57 (56 roadmaps contados) | `https://roadmap.sh/<slug>.json` |
| Objetivos por examen | CLF-C02 19 · SAA-C03 14 · AIF-C01 14 · MLA-C01 12 · PCEP 13 · PCAP 21 · ISC2 CC 19 · AZ-900 11 · AI-900 11 · AI-901 7 · DP-900 11 | guías oficiales de AWS, Python Institute, ISC2 y Microsoft Learn |
| Formato AIF-C01 | «65 questions», 90 min, 15 sin puntuar | aws.amazon.com y guía oficial (el repo dice 85 y 120: fila 37.19) |
| Competencia | Boot.dev 51 cursos · 2.823 lecciones · 1.053 h, mediana 20 h por curso; Pocket Prep ISC2 CC 800 preguntas; Kodree 42 tarjetas de curso, 687 lecciones, 2.559 tareas; Exercism 83 lenguajes, Python 146 ejercicios | boot.dev/courses, pocketprep.com, kodree.com, exercism.org |
| Demanda | JavaScript 66 % · SQL 58,6 % · Python 57,9 % · Bash 48,7 % · TypeScript 43,6 % · Java 29,4 % · C# 27,8 % · C++ 23,5 % · PowerShell 23,2 % · PHP 18,9 % · Go 16,4 % · Rust 14,8 % · Kotlin 10,8 % · Ruby 6,4 % · R 4,9 %; Docker 71,1 % · AWS 43,3 % · Kubernetes 28,5 % · Azure 26,3 % · GCP 24,6 % · Terraform 17,8 % · Prometheus 11,8 % | survey.stackoverflow.co/2025/technology |
| Examen en español | GCP ACE, LPIC-1, AZ-104, AIF-C01 sí; CKA/CKAD/CKS no | páginas de Google Cloud, LPI, Microsoft Learn, Linux Foundation, AWS |

**Cifras a fecha** (`python scripts/catalog_coverage.py`, 2026-09-30):

- Tracks del plan 45 · construidos 24 · en el suelo 1 (track01).
- Suelo: skills 525/2.250 (23,3 %) · preguntas 8.313/36.000 (23,1 %).
- Ideal: skills 525/4.819 (10,9 %) · preguntas 8.380/96.380 (8,7 %).
- Certificaciones: práctica al suelo 1.926/2.175 (88,6 %), al ideal 2.309/5.800 (39,8 %);
  banco reservado 0/3.120 (0 %); Security+ sin objetivos contados y los tres de Microsoft
  sin longitud de examen publicada.
- Ritmo: a 518 preguntas verificadas por sesión (único dato medido, sesión 18.4), el suelo
  pide ≈ 60 sesiones (27.687 preguntas de tracks + 249 de práctica de certificación + 3.120
  reservadas = 31.056) y el ideal ≈ 183 (88.000 + 3.491 + 3.120 = 94.611). Es un orden de
  magnitud, no un plan de fechas.

**Límites que la sesión deja escritos:**
- Koedinger mide matemáticas, ciencias e idiomas, no programación: aplicarlo aquí es una
  extrapolación.
- «1 nodo de roadmap ≈ 1 skill» se calibra con un solo dato (Python: 87 nodos, 100 skills en
  track01–03). 37.1 lo sustituye por el mapa skill → nodo.
- Ningún estudio fija un «número ideal de tracks»; por eso manda la demanda medida.
- Glosario de 1 término por skill y lección de 6–10 min son elección de la sesión con
  evidencia débil (Guo 2014 mide enganche en vídeo, no aprendizaje).
- La conversión Education y los datos de retención son medianas de terceros, no de Whetzy:
  se recalibran con la primera cohorte (H.10).

**Consecuencias:** la serie 37 del ledger se reescribe sobre esta ADR y absorbe la serie 25;
`CATALOGO_MAESTRO.md` cambia de meta y de tabla de competencia; el teardown suma §14; ADR-25 y
ADR-46 llevan la línea «Sustituida»; la fila h de ADR-50 cambia de orden de certificaciones;
`scripts/catalog_coverage.py` + `backend/tests/test_cobertura_plan.py` mantienen el plan y el
catálogo en el mismo mundo; `check_docs.py` impide que un documento vivo vuelva a dar la meta
de ADR-46 como vigente.

## ADR-54 — Catálogo uniforme 32 × 10 (2026-10-01, decisión del dueño). Sustituye el suelo y el ideal de ADR-53.

> **Punto 7 (orden) enmendado por ADR-59 el 2026-10-03:** el contenido nuevo ya no espera al
> piloto (31.8) y se produce en paralelo, en el orden de `docs/PLAN_CONTENIDO.md`. Las metas
> no cambian.

**Origen.** Prompt del dueño del 2026-10-01 («lanzamiento piloto + ADR-54»), que aprueba esta
decisión tal como se escribe aquí. ADR-53 pedía ≈ 31.056 preguntas solo para su suelo
(≈ 60 sesiones) y un «ideal por temario» de ≈ 94.611, antes de tener un solo usuario real.

**Decisión:**

1. **Track de aprendizaje, forma única:** 32 skills (8 módulos × 4) · 10 preguntas por skill
   (= 320 por track), ≥ 3 de ellas ejecutables o interactivas donde el navegador ejecute
   (Python, SQL, JS; exento con razón escrita en otro caso) · 1 lección por skill · 1 término
   por skill.
2. **roadmap.sh deja de fijar cantidades:** solo sirve para elegir QUÉ 32 skills entran. Se
   elimina el «ideal por temario».
3. **Nada se borra:** un track por encima de 32 skills o de 10 preguntas por skill conserva
   lo que tiene.
4. **Certificación, regla única:** 100 % de objetivos oficiales cubiertos · práctica
   ≥ máx(300, 3 × preguntas del examen) · banco reservado de simulacro = 2 × preguntas del
   examen (`pool: "simulacro"`), en vez de 6 ×. Examen sin número de preguntas publicado:
   reservadas «pendiente», con la nota de por qué; nunca un número inventado.
5. **Tracks nuevos:** solo por la demanda medida de ADR-53 (niveles A/B/C), con la misma forma.
6. **Se mantiene de ADR-53:** niveles de demanda, mecanismo del banco reservado (37.18) y
   suelos de métricas de producto (vetados hasta ≥ 100 registrados reales, 31.5).
7. **Orden:** ningún contenido antes del piloto (`LANZAMIENTO_PILOTO.md`); después, primero
   los tracks que usen los pilotos.

**Qué cuenta como ejecutable** (elección de la sesión, escrita en `scripts/metas_catalogo.json`):
`fill_blank_exec`, `fix_bug`, `sql_exec`, `js_exec` y `code_output` (la UI ofrece «▶ Ejecutar
para verificar»). `fill_blank` no: se corrige comparando texto. Un track sin preguntas
ejecutables ni exención escrita sale «sin medir»; hoy son 11 (track18-23 y 26-30).

**Evidencia** (leída por la sesión del 2026-09-30, no releída hoy: **[Likely]**):
`CATALOGO_MAESTRO.md` §8 — Kodree 687 lecciones / 2.559 tareas; Boot.dev mediana de 51
lecciones y 20 h por curso; Exercism Python 146 ejercicios; Pocket Prep ISC2 CC 800
preguntas; Tutorials Dojo / Udemy 390 preguntas por examen AWS (lectura de agente, Udemy
devolvió 403). Mediana de ≈ 7 oportunidades de práctica por componente de conocimiento
(Koedinger et al. 2023, PNAS), citada en ADR-53: 10 preguntas por skill la cubren con margen.

**Cifras** (`python scripts/catalog_coverage.py` sobre `master` `80cd3ad`, 2026-10-01; 24
tracks construidos, 11 certificaciones):

| Qué falta | ADR-54 |
|---|---|
| Skills en tracks construidos | +261 |
| Lecciones | +261 |
| Términos de glosario | +266 |
| Preguntas en tracks | +2.610 |
| Práctica de certificación | +907 |
| Reservadas de simulacro (sin AZ-900, AI-900 y DP-900: sin longitud publicada) | +1.040 |
| **Total de preguntas** | **4.557 ≈ 9 sesiones** a 518/sesión (estimación) |

Frente a 31.056 preguntas (≈ 60 sesiones) del suelo de ADR-53. La cifra de referencia del
prompt (+867 de práctica de certificación, ≈ 4.500 en total) se calculó sobre `e83bf63`,
antes de fusionar el PR #34: con el mismo script sobre ese commit sale 867 exacto. El #34
retiró 45 preguntas de relleno de track43 y sumó 5 a AZ-900; neto, +40.

**Límites que se dejan escritos:**
- No supera a Boot.dev en horas de lección ni a Pocket Prep en volumen de ISC2 CC. Si CC pasa
  a prioridad, ≈ +250 solo ahí (800 − 353 de práctica − 200 reservadas = 247).
- Compite en práctica adaptativa, ES/EN nativo y ejecución en el navegador.
- La cobertura de objetivos de certificación se mide con un proxy (una skill por objetivo):
  no hay mapa objetivo → skill. Security+ (SY0-701) sigue sin objetivos contados.
- El ritmo de 518 preguntas por sesión es el único dato medido (sesión 18.4); la estimación
  de sesiones es un orden de magnitud.

**Consecuencias:** `scripts/metas_adr53.json` → `scripts/metas_catalogo.json`;
`scripts/catalog_coverage.py` mide la forma 32 × 10 y la regla de certificación;
`backend/tests/test_cobertura_plan.py` tiene un test por regla, cada uno mutado a rojo. La
propagación a los documentos vivos y la guarda de `check_docs.py` van en el PR siguiente.

## ADR-55 — Fuente legal canónica: lo publicado (2026-10-01; el dueño lo delegó en la sesión: «investiga, asume los roles que debas»)

**Origen.** Había cuatro sitios con textos legales y la web solo usaba uno: las claves i18n
`legal.*` que pinta `LegalScreen.tsx` (whetzy.com/privacy, /terms, /refund); `docs/legal/`
(borradores largos ES/EN, «NO debe utilizarse en producción»); `legal/` en la raíz (otra
versión, bilingüe en un fichero); y `content/legal/` (textos comerciales que ningún código
carga). Las copias ya divergían: los borradores daban Stripe como procesador cuando el dueño
lo descartó (H.29), el de reembolsos prometía «14 días de prueba gratis» que no existen y
todos dejaban `[ENTIDAD LEGAL PENDIENTE]`.

**Decisión.**

1. **Manda lo publicado.** Privacidad, términos y reembolsos son las claves i18n `legal.*`
   en ES y EN. Es lo que el usuario ve y acepta, y lo que ya vigilaban las guardas
   (`check_legal_facts.py`, paridad i18n). Cambiar una política es cambiar esas claves.
2. **Una sola carpeta para lo demás: `docs/legal/`.** Allí quedan los borradores que la app
   aún no publica (aviso de IA, DPA, marcas), los textos comerciales que venían de
   `content/legal/` y los instrumentos internos que venían de `legal/`.
3. **Los borradores largos se archivan** en `docs/archive/legal-borradores/`, como material
   para la revisión profesional (H.20). No mandan.
4. **Guardas.** `check_legal_facts.py` [5b] falla si vuelve una copia de privacidad, términos,
   reembolsos o cookies a `docs/legal/`. [1] aplica las afirmaciones prohibidas también al
   texto publicado. [1b] exige que la política publicada nombre a cada procesador que el código
   usa (Paddle, Groq, Resend, Sentry), comprobado por contenido del fichero y no solo por su
   existencia.
5. **Lo publicado se completa con lo que exige el art. 13 RGPD y faltaba en pantalla:**
   - quién trata los datos (Railway, Cloudflare, Groq, Resend, Sentry, Paddle, verificados en
     el código y en el log de producción del 2026-10-01);
   - que algunos tratan datos fuera del EEE, y cómo pedir sus garantías;
   - el derecho a reclamar ante la autoridad de control, cookies y menores. Estas tres claves
     existían en i18n pero ningún componente las pintaba.

**Pendiente del dueño** (no lo resuelve una sesión):
- el nombre legal del titular, para identificar al responsable del tratamiento y a la parte
  de los Términos;
- confirmar con cada proveedor fuera del EEE la garantía de la transferencia, por ejemplo con
  cláusulas contractuales tipo;
- la revisión profesional (H.20).

## ADR-56 — Fin de la pausa de sesiones (DUEÑO, 2026-10-01)

**Origen.** El dueño, preguntado en sesión «¿Se acabó la pausa?», respondió «YES». La pausa
(31.7, `CIERRE_2026-09-30.md`) mandaba a toda sesión sin instrucciones explícitas parar y no
ejecutar `ORCHESTRATOR.md`.

**Decisión.** La pausa queda levantada. Se mantienen:
- rama + PR por oleada, y `master` solo lo fusiona el dueño (ADR-45);
- la política de modelos (ADR-52);
- la dieta de contexto de `CLAUDE.md`.

`CIERRE_2026-09-30.md` sigue vivo como registro y por sus §2 (scorecard) y §7 (trampas del
entorno). `check_docs.py` [11] invierte su regla: con la pausa levantada falla si `CLAUDE.md`,
`ORCHESTRATOR.md` o `docs/README.md` siguen mandando parar.

## ADR-57 — Referidos abiertos ya, sin esperar al «cuándo» de ADR-35 (DUEÑO, 2026-10-01)

**Origen.** ADR-35 abre el programa «después de la Serie 24 y con retención base medida».
Ninguna de las dos cosas está hecha: la Serie 24 va 1/9 y la retención la mide la cohorte de
H.10, que está HUMAN-BLOCKED. Mientras tanto, nada activaba ni abonaba un referido:
`activate_referral` y `credit_matured_referrals` solo los llamaban los tests. Preguntado con
las cuatro opciones (apagado, completo, solo créditos, eliminar), el dueño eligió **cablearlo
completo ya**.

**Decisión.** Se cablea el programa de ECONOMIA.md §3 tal cual, salvo el «cuándo»:
- Activación con las cuatro condiciones del §3.1. El job `referral_program_loop` corre cada 6 h
  y un solo worker a la vez (advisory lock).
- Abono 7 días después: 300 créditos por activación, con tope de 10 al mes.
- Escalera acumulativa: al 3.º, 1 mes de Pro; al 10.º, 6 meses de Pro Max (la certificación
  sigue HUMAN-BLOCKED, ADR-15); al 25.º, la insignia «Embajador».
- 200 créditos de bienvenida al referido.
- Pausa manual (`REFERRALS_PAUSED`) y automática si el fraude supera el 5 % dos semanas
  seguidas.

**Lecturas de la sesión** (ninguna está en ADR-35 y todas se revierten sin migración):
1. **«Completar el diagnóstico».** El onboarding solo manda a la prueba de nivel a quien ya
   programa (`onboarding_experience` ≥ 1). Para esos cuenta la prueba terminada; para quien
   empieza de cero, el propio onboarding. Exigir la prueba a todos dejaría fuera a cada
   principiante.
2. **«Terminar el primer módulo»** usa la regla con la que la app pinta un módulo
   «completado»: la media de dominio de sus skills alcanza `min_mastery_to_unlock`. No es el
   «BKT ≥ 0,8 en todas» de ECONOMIA §2.2, que ninguna pantalla usa.
3. **«Mantiene una racha de 3 días»** se lee como `max_streak` ≥ 3, es decir, la ha
   alcanzado. El job corre cada 6 h y una racha que se rompe entre dos vueltas no debe borrar
   el mérito.
4. **El tiempo de plan ganado va en columnas propias** (`users.granted_tier`,
   `granted_tier_expires_at`), no en las de suscripción, que reescriben los webhooks de
   Paddle, Stripe y RevenueCat. `user_meets_tier` toma el mayor de los dos mientras estén en
   fecha. En `/auth/me`, `is_premium` sigue siendo solo el plan de pago: el checkout lo usa
   para decir «ya tienes suscripción» y para dar por llegado un pago. El plan ganado sale
   aparte (`granted_tier`, `granted_tier_expires_at`); el frontend junta los dos para
   desbloquear, y Yo dice cuál es y hasta cuándo.
5. **El email verificado se exige al activar, no al registrar el código** (§3.5 ya lo decía
   así). Exigirlo al registrar perdía el referido de todo el que no entraba con OAuth: el
   onboarding llama antes de que nadie abra el correo.

**Sin cablear, y por qué:**
- **Dispositivo/IP (1 activación cada 30 días).** El código existe, pero el frontend no manda
  `X-Device-Fingerprint` y la política de privacidad publicada (ADR-55) no declara ese
  tratamiento. Encenderlo exige primero declararlo en `legal.privacy*` ES/EN.
- **Clawback.** No hay flujo de baneo ni de «fraude confirmado» que lo dispare. Un referido
  cuya cuenta se borra antes del abono queda `rejected` y no se paga.
- **El acceso anticipado del hito 25** no existe como programa.

## ADR-58 — Los créditos no compran simulacros ni cursos: el acceso lo da el plan; política de privacidad con IP y navegador (DUEÑO, 2026-10-02)

**Decisión del dueño (2026-10-02):** «el simulacro y los cursos no se pagan con créditos, solo
dependen del tipo de suscripción».

- **Créditos.** Quedan fuera de los sumideros de ECONOMIA §2.3 el simulacro (500) y el curso del
  marketplace (≥ 1.000). Los créditos siguen comprando el comodín de racha y el informe de dominio.
  Hoy el simulacro va en todos los planes publicados, Free incluido (`landing.planFree.perks[4]`).
- **Cursos del marketplace.** Siguen con precio propio (`price_cents`) y reparto 80/20 por venta
  (ADR-41): el dueño aclaró el mismo día que la decisión es solo «no con créditos», no que los
  cursos vayan incluidos en un plan. ADR-41 no cambia.
- **Privacidad.** El texto de IP y navegador de los inicios de sesión se publica como final
  (`legal.privacyL13`, `privacyL14`, `privacyRetentionSecurity`, `privacyUpdated`), sujeto a la
  revisión legal (H.20). Para que sea verdad, `periodic_jobs_loop` borra a los 90 días
  `login_attempts`, `audit_log` y las sesiones sin actividad, y a los 30 las huellas del antifraude.
  **El antifraude por huella de dispositivo sigue apagado:** la huella (pantalla, zona horaria,
  idioma) puede caer en el art. 5(3) de ePrivacy y exigir consentimiento; lo decide la revisión
  legal antes de encenderlo (`docs/legal/antifraud-legal-basis.md`).

## ADR-59 — Autoría de contenido: Sonnet 5 escribe desde la fuente, por `Workflow`, en paralelo al piloto (DUEÑO, 2026-10-03; enmienda la fila de autoría de ADR-52 y el punto 7 de ADR-54)

**Origen.** El 2026-10-03 la sesión 2 paró la serie 37 porque el volumen pendiente (≈ 4.557
preguntas, ADR-54) no se escribe a mano. El dueño respondió en la sesión de coordinación a tres
preguntas cerradas: «¿Workflow para la autoría masiva?» → **Sí, autorizado**; «¿qué modelo
escribe?» → **Solo Sonnet**; «¿el contenido puede ir antes de cerrar el piloto con alumnos
(31.8)?» → **Sí, adelantarlo**.

**Decisión.**
1. **La autoría masiva de contenido va por `Workflow`**, con el método de
   `docs/PLAN_CONTENIDO.md`. Ninguna pregunta se escribe de memoria: cada una sale de un
   fragmento de una fuente marcada `reusar` en `content/sources/index.json` y cita esa URL en
   `source`.
2. **Escribe Sonnet 5.** El escritor, el revisor (revisión adversaria completa contra el
   fragmento) y el corrector son Sonnet 5. Haiku 4.5 sigue solo para lecturas, inventarios y
   diffs (ADR-52).
3. **Piloto antes de escalar.** El primer bloque son 10 ítems con revisión completa. Si más de
   3 de 10 salen con problema `blocker` o `major`, se para y decide el dueño (umbral de ADR-52).
4. **Orden.** El contenido corre en paralelo al piloto con alumnos (31.8). El orden es 37.10
   (MLA-C01 y las tres de Microsoft), luego 37.6 (lista A), luego 39.8.
5. **Un solo motor.** La producción nueva la lleva la sesión coordinadora. La sesión de
   contenido (S2) cierra sus PRs en curso y no empieza autoría nueva. Un track por rama y por PR,
   y se fusionan de uno en uno.

**Evidencia.**
- Piloto Haiku de track28 (2026-09-26): 7 de 10 lecciones con relleno, errores técnicos o
  fuentes que no casaban (ADR-52, «Riesgo»).
- Piloto Haiku de 39.37 (track20, `STATUS.md`): en la ronda 1, `correct_index` era siempre 0;
  en la ronda 2, 6 de 10 eran redundantes. Las dos superan el umbral. Con Sonnet como autor,
  autorizado por el dueño, 39.37 quedó DONE.

**Consecuencias:**
- `CLAUDE.md` («Modelos»), `CATALOGO_MAESTRO.md` §6, §7 y §10, `PROTOCOLO_VERIFICACION.md` §2,
  `ORCHESTRATOR.md`, `RUNBOOK.md` y el ledger (cabecera de la serie 37, fila 37.25) cambian
  «escritor Haiku» por «escritor Sonnet» y quitan «nada antes del piloto».
- La enmienda de ADR-52 que `RUNBOOK.md` §D dejaba pendiente de firma queda firmada aquí.
- Sonnet 5 cuesta más por token que Haiku 4.5. El coste por pregunta aceptada no se conoce: lo
  mide el piloto antes de escalar, y la cifra se anota en `PLAN_CONTENIDO.md`.

**Fuentes `cita` (dueño, 2026-10-03, misma sesión).** Para las certificaciones de AWS (track43
MLA-C01 y track11 AIF-C01), cuya documentación no es reutilizable (`CATALOGO_MAESTRO.md` §2.1:
«docs propietarias … se citan, nunca se copian»), el dueño eligió **redactar original con cita**:
el escritor recibe el fragmento de la doc oficial como base de hechos, escribe con sus palabras
sin copiar frases, y `source` enlaza la URL de `docs.aws.amazon.com`. El revisor añade un
criterio: copiar más de 8 palabras seguidas del fragmento es `major`. El fragmento se guarda solo
como evidencia de la revisión y nunca entra en el banco. Es el camino que §2.1 ya fija para
cualquier fuente («Los hechos son libres; la redacción no»); esta línea lo vuelve explícito para
la producción por `Workflow`.

## ADR-60 — Decisiones de producto del 2026-10-10: Knowledge/Retention/Readiness, principio rector y Career Path (DUEÑO)

**Origen.** Cuatro documentos de visión de producto revisados en la sesión del 2026-10-10.
El dueño confirmó que los hallazgos técnicos de la auditoría (Olas 0–3) ya están suficientemente
cubiertos y que no hacen falta más auditorías; lo que falta son tres decisiones de producto que
impidan desviaciones en las olas en curso.

---

### UX-DEC-01 — Knowledge, Retention y Readiness son conceptos distintos; ninguno es un porcentaje hasta que el modelo esté calibrado

**Definiciones canónicas:**
- **Knowledge** — evidencia de que el usuario puede responder correctamente un conocimiento o
  habilidad (fuente: BKT `p_known`, Elo, respuestas correctas recientes).
- **Retention** — evidencia de que puede recuperarlo después de un intervalo de tiempo (fuente:
  FSRS `stability`, tasa de acierto en repaso diferido).
- **Readiness** — evidencia disponible respecto a un objetivo concreto, por ejemplo una
  certificación (fuente: cobertura de skills + `p_known` promedio ponderado por peso del examen).

**Regla de presentación:** mientras los modelos no estén calibrados, la interfaz presenta estados
cualitativos con su evidencia:
- *Fuerte* (evidencia sólida y reciente)
- *En desarrollo* (evidencia parcial o antigua)
- *Evidencia insuficiente* (< 7 respuestas en el módulo o sin repaso diferido)

No se muestran porcentajes hasta que un estudio de calibración externo valide que los números del
modelo corresponden a rendimiento real (Ola 5, serie D7).

**Qué prohíbe:** mostrar `Knowledge: 84 %` o `Readiness: 72 %` antes de esa calibración.

**Enmienda del dueño (2026-10-18).** *Fuerte* por skill exige ≥ 7 respuestas, `p_known` ≥ 0,95
**y** aciertos/respuestas ≥ 0,7 (`frontend/src/lib/evidenceBand.ts`). BKT pesa lo último: con los
parámetros por defecto, tres aciertos seguidos tras fallos llevan `p_known` de ~0,23 a ~0,97, y en
local se vio «Fuerte — 10 respuestas · 4 aciertos». Los parámetros del motor no se tocan sin datos
de calibración (`backend/tests/unit/test_engine_bkt.py::TestRecencyOverAccuracy`).

---

### PRODUCT-PRINCIPLE-01 — El algoritmo navega al usuario hacia su siguiente acción relevante

Whetzy es un sistema adaptativo, no un dashboard. La pregunta principal de la interfaz es
**«¿Qué deberías hacer ahora?»**, no **«¿Cuánto llevas?»**.

**Principio:**
> Whetzy prioriza la siguiente acción relevante sobre la exposición de métricas. Toda
> recomendación importante debe poder explicar brevemente por qué aparece. La fuerza de la
> recomendación debe ser proporcional a la evidencia disponible.

**Criterio de aceptación transversal:** cualquier pantalla o componente que muestre progreso o
sugiera una acción debe poder responder «¿por qué me recomendas esto?» con una frase basada en
evidencia observable (número de respuestas, aciertos, intervalo transcurrido). Una pantalla que
solo muestre un porcentaje sin esa explicación no cumple el principio.

**Qué no prohíbe:** mostrar métricas como información secundaria o confirmatoria, siempre que no
sean el elemento principal de navegación.

---

### ROADMAP-01 — Career Path queda fuera del alcance de las olas actuales

**Definición del concepto futuro:**
Career Path es una capa de navegación profesional: rol de destino → conjunto de competencias →
certificaciones → tecnologías → proyectos → evidencia acumulada. Es sustancialmente más complejo
que un filtro del catálogo.

**Decisión:** Career Path no forma parte de las Olas 0–4. No debe introducir dependencias en C1,
C2 ni en ninguna tarea en curso. El catálogo de certificaciones (ADR-54) y el trabajo de
onboarding (C1) no deben diseñarse como si Career Path fuera a encajar directamente: cuando llegue,
será un producto propio que puede reutilizar las piezas, no una extensión del flujo actual.

**Criterio de entrada al roadmap:** al menos dos certificaciones con banco completo y pool de
simulacro activo, y un mínimo de 100 alumnos con datos reales de uso (condición de Ola 5).

---

## ADR-61 — Decisiones del dueño tras la auditoría de integración y de docs (DUEÑO, 2026-10-09; transcrito el 2026-10-16 por la Oleada 0; **confirmado fiel por el dueño el 2026-10-22, salvo la edad mínima: 16 años**, ADR-70)

**Origen.** Texto propuesto «para S5 como ADR-61» en el issue #89
(<https://github.com/Neopram/whetzy/issues/89#issuecomment-6075139738>, 2026-10-09 05:48 UTC,
`[COORD] DECISIONES DEL DUEÑO`), con la precisión a §22 del comentario siguiente
(<https://github.com/Neopram/whetzy/issues/89#issuecomment-6075158638>). Ninguna sesión lo llegó a
escribir aquí, aunque `CATALOGO_MAESTRO.md` cita sus puntos §22, §23 y §25 como «ADR-61 … prop.».
Se transcribe sin cambios. El número 60 lo ocupó después ADR-60 (2026-10-10), no las decisiones
del 2026-10-04/05 que el texto original le atribuía.

> **Precisión del dueño a §22 (2026-10-09):** todavía no existe ninguna entidad. Chipre es el
> destino, pero no está constituida. Hoy no hay sociedad, así que no hay régimen fiscal propio ni
> payouts posibles, y `GRECIA_TAX_RATE` no corresponde a ninguna entidad real. Paddle sigue en
> producción como está (§3).
>
> **Choque abierto (H.54):** §22 sustituye a «Grecia» en H.29, pero el código sigue en Grecia
> (`backend/app/services/payment_service.py:22`) y la Oleada 0 no lo toca. Lo decide el dueño.

**Seguridad, dinero y cumplimiento**
1. Edad mínima en el alta por OAuth: pantalla de confirmación en el primer inicio con Google o GitHub. Edad mínima: 13 años, sujeta a la revisión de S4 y del abogado (H.20). **Corrección del dueño del 2026-10-22: 16 años (ADR-70).**
2. Analítica: los eventos individuales se borran a los 30 días y se conservan solo agregados. Así se cumple lo publicado en el DPA.
3. Paddle sigue en producción a propósito. La certificación no se cobra hasta cumplir el punto 4 y 37.24. Los flags `CERTIFICATION_PAYWALL`, `CREATOR_PLAN_REQUIRED`, `FREE_DAILY_QUOTA_ENABLED` y `ANNUAL_PLAN_ENABLED` siguen **apagados** durante el piloto.
4. AZ-900, AI-901 y DP-900: simulacro gratuito con «formato Whetzy» declarado y la duración oficial. Su examen certificador **no se vende** hasta tener la cifra oficial de preguntas.
5. Marketplace de pago: `enroll` bloqueado ya (41.6) y se envían a Paddle las 13 preguntas de 44.18 antes de diseñar los payouts.
6. Perfil público (opt-in, decisión del 2026-10-04): muestra solo nombre visible, avatar y certificados verificables. No muestra dominio medio, racha ni proyectos.
7. El antifraude por huella sigue apagado. `ANTIFRAUD_SALT` pasa a ser obligatoria y desaparece el valor por defecto del código.
8. Lo que ve gente de fuera se retira o se corrige antes de publicar o enviar nada: guiones de vídeo, fichas de tienda, `Whetzy.pdf` (fuera del repo) y las marcas ✅ de `COMPETENCIA.md`. `docs/analisis-estrategico/` pasa a `docs/archive/` con aviso de fecha.

**Producto y motor**
9. Prueba de nivel: fija un punto de partida por módulo, siempre por debajo de 0,95 (`MASTERY_THRESHOLD`), **y además** ofrece el test-out de cada módulo marcado `can_skip`. Resuelve B.4.
10. El simulacro no actualiza BKT. Su resultado se muestra en la pantalla de preparación.
11. Contenido escrito por IA (ADR-59): aviso visible en la app y campo de procedencia en cada pregunta.
12. Posicionamiento confirmado (la cuña del 2026-10-04): certificaciones técnicas para particulares.
13. Onboarding más fino (5 niveles, tecnologías conocidas): después del piloto.
14. Modo Enfoque/Competitivo/Social: no por ahora. Basta con `leagues_opt_out`.
15. XP separado y `Module.level` renombrado, como recomienda S3 (C.3 del plan de UI/UX).
16. CORS para la app nativa (41.10): cuando exista el proyecto iOS o Android.

**Infraestructura (D1–D4 de S5)**
17. D1: se vacía `REDIS_URL`. 18. D2: staging se da de alta antes de abrir a usuarios de pago. 19. D3: el worker sigue igual. 20. D4: el contenido se carga en el pre-deploy de Railway.
21. El detector de duplicados se corre fuera de producción como script con `sentence-transformers`. En Railway se retira el camino de vectores aleatorios.

**Documentación y gobierno**
22. **Entidad y jurisdicción: Chipre, a la que se llegará más adelante.** Sustituye a «Grecia» en H.29 y a «sin decidir» en ADR-47. Concuerda con ADR-33. Queda por definir el régimen hasta que se constituya la entidad; mientras tanto no se pagan payouts (punto 5). La retención griega del código (`payment_service.py:26`, `GRECIA_TAX_RATE = 0.22`) deja de ser válida y se revisa antes del primer payout.
23. «Ejecutable» se reserva para las preguntas que se ejecutan de verdad (`fill_blank_exec`, `fix_bug`, `sql_exec`, `js_exec`; 612). «Con código» abarca además `code_output` (1.377).
24. CC BY-SA no se reutiliza (ADR-47).
25. En licencias manda `content/sources/index.json`. Se corrige `CATALOGO_MAESTRO.md` y se comprueba que ninguna pregunta copia texto de OWASP Top 10 ni de los RFC (los dos son «cita»).
26. Clasificación por edad en tiendas: 12+ (iOS) y Teen (Android), a confirmar con el cuestionario de cada tienda.
27. S5 escribe ADR-60 y este ADR-61, y añade notas «sustituida/enmendada por» a ADR-18, 29, 34, 35, 47 (marca), 50 y 14.
28. Sobre quién escribe qué fichero manda `docs/SESIONES.md`; se corrigen sus líneas 36-38.

---

## ADR-62 — Contenido nuevo en espera por consumo de tokens; el contenido de estudio queda como deuda registrada (PROPUESTA de la sesión, 2026-10-16; **firmada por el dueño el 2026-10-22: se mantiene la pausa**, ADR-70)

**Origen.** Petición del dueño del 2026-10-16 (plan ultracode, `PLAN_ULTRACODE.md` §7). Enmienda
ADR-59 y el punto «el contenido corre en paralelo» de ADR-54.

**Decisión propuesta.**
1. Hasta nueva orden no se escriben preguntas, lecciones ni términos ni se amplían tracks;
   `PLAN_CONTENIDO.md` y la FASE 2 punto 3 de `PROMPT_CONTROL_TOTAL.md` quedan en espera.
   Excepción: retirar (no reescribir) un ítem con error de hecho.
2. La forma del catálogo (ADR-54) sigue siendo la meta.
3. Deuda registrada: H.55 (contenido de estudio frente a banco de preguntas).

---

## ADR-63 — Política de evidencia por fuente y prior del onboarding (PROPUESTA de la sesión, 2026-10-16; **firmada por delegación el 2026-10-22**, ADR-69 #5)

**Firmada por delegación el 2026-10-22 (ADR-69 #5)** con los valores recomendados: prior 0,10/0,20/0,30, k = 4 y tope 0,94, puerta solo con práctica.

**Origen.** Plan ultracode del dueño (`PLAN_ULTRACODE.md` §7). Subordinada a ADR-60 UX-DEC-01.

**Contexto.** Hay una fila `UserSkillState` por (usuario, skill), y la escriben con reglas
distintas la práctica, el duelo, el test-out y la prueba de nivel. El onboarding se guarda
(`auth.py`), pero el punto de partida es fijo: `p_l0 = 0,1` (`backend/app/services/engine/bkt.py:22`).
ADR-60 define «evidencia insuficiente» como «< 7 respuestas en el módulo o sin repaso diferido».

**Propuesta.**
1. Prior por experiencia: 0/1/2 → 0,10/0,20/0,30 (a calibrar). No suma intentos.
2. Siembra de la prueba con encogimiento, k = 4 y tope 0,94; D-18 se mantiene. Con eso, 1/1 pasa
   de 0,94 a 0,28 y 8/8 da 0,70.
3. «Dominada» = `p_known` ≥ 0,95 y ≥ 7 respuestas de práctica. El duelo, la prueba y el test-out
   mueven `p_known`, pero no cuentan para la puerta y no pasan de 0,94 por sí solos.
4. Tabla por fuente:
   - práctica: BKT sin tope, cuenta para la puerta, FSRS;
   - duelo: BKT con tope 0,94, no cuenta, FSRS como hoy;
   - prueba de nivel: siembra una vez;
   - test-out: por documentar leyendo `exams.py:395`;
   - onboarding: solo prior.

---

## ADR-65 — Flujo del alumno listo para pruebas (DECIDIDO por delegación expresa del dueño, 2026-10-17)

**Origen.** Anexo del dueño al plan ultracode (`docs/PLAN_FLUJO_ALUMNO.md`), pegado en la sesión de la Oleada 0 el
2026-10-17. Sus §5.3 dicen «redacta ADR-65 … como DECIDIDO por delegación expresa del dueño». Las decisiones se
transcriben sin cambios. Las filas son la serie 43. El número 64 queda libre: la Oleada 0 no encontró en
`LEDGER_HISTORY` §J las D-xx que el prompt pedía transcribir en ADR-64.

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

> **Nota de la Oleada 0 a D1 (comprobado en el código, 2026-10-17):** Safari también bloquea como de terceros la
> cookie de *refresh*. Con «el refresh sigue por cookie», la sesión en iPhone duraría 30 min
> (`ACCESS_TOKEN_EXPIRE_MINUTES`, `config.py:68`), no «lo que dura la pestaña». El backend ya acepta el refresh en
> el cuerpo de `POST /auth/refresh` (`auth.py:283`), y el login y el registro ya devuelven los dos tokens en JSON
> (`schemas/user.py:96-99`). Por eso 43.1 manda el refresh en el cuerpo.
>
> **Decisión del dueño (2026-10-17, en la sesión).** «Solo en memoria» tampoco basta: tras el login, la app recarga
> la página entera (`App.tsx:222`, `window.location.replace(next)`), y la memoria se pierde ahí y en cada
> recarga. El dueño eligió esto: tras el login se prueba `/auth/me` solo con la cookie, y si da 401 los dos tokens
> van a `sessionStorage` (dura la pestaña) como `Authorization: Bearer`. Nunca en `localStorage`. Coste aceptado:
> en Safari, un XSS podría leerlos mientras la pestaña esté abierta. PR #226.

> **Choque abierto (H.60), anotado por la Oleada 0:** D7 (la práctica exige la lección vista; se quita
> `attempts > 0` de `lesson_gate.py`) junto con D4 (la prueba no marca lecciones vistas) deja sin efecto el test-out
> por módulo de ADR-61 §9, que el código ofrece (`backend/app/services/placement.py:343`, `can_skip`). Recomendado: un
> módulo con test-out aprobado, o con ≥ 70 % en la prueba, cuenta como «lección vista». Hay que decidirlo antes de
> 43.5.
>
> **Decidido por el dueño el 2026-10-17 (H.60):** la opción recomendada. Un módulo con test-out aprobado, o con
> ≥ 70 % en la prueba de nivel (los que en 43.3 «empiezan con ventaja»: ≥ 70 % de ≥ 2 preguntas), desbloquea la
> práctica de sus skills sin abrir las lecciones. Las lecciones no se marcan como vistas: siguen disponibles.
>
> **Decidido por el dueño el 2026-10-17 (D8, 43.6):** los pasos SQL de un proyecto se ejecutan en el servidor
> (SQLite en memoria, sin red ni ficheros y con límite de tiempo) y el `passed` del cliente se ignora. Python y JS
> siguen en el navegador: el servidor impone el orden de los pasos y guarda el código, pero esas finalizaciones
> no cuentan como verificadas (no salen en el perfil público) hasta que haya un sandbox para ellos.

## ADR-66 — Alta con correo (DECIDIDO por el dueño, 2026-10-17, al fusionar #240)

**Origen.** Prueba del dueño en iPhone el 2026-10-17: el registro mandó dos correos (bienvenida y verificación), los dos
en inglés, y la app nunca dijo «verifica tu correo». Plan en `docs/PLAN_CORREO_ALTA.md`; las filas son la serie 45, que
va con la 43 en `master` y antes de la 44.

| # | Decisión |
|---|---|
| E1 | El idioma de la cuenta es el que ve el alumno al registrarse: `?lang=`, luego `whetzy_lang`, luego el navegador. Vale para el formulario, la portada y OAuth. Después solo lo cambia el alumno en Yo. |
| E2 | Al registrarse sale un solo correo, el de verificación. La bienvenida sale al verificar, una vez. Con OAuth (cuenta ya verificada) sale al crearla. |
| E3 | La app no se bloquea por no verificar: tras registrarse se entra al onboarding. |
| E4 | Mientras no esté verificado, una franja en el armazón de la app: «Te enviamos un enlace a fe***@… · Reenviar · ×». Reenviar usa el endpoint público con 60 s entre reenvíos en el cliente; la × la oculta en esa sesión del navegador. |
| E5 | El enlace del correo lleva el idioma (`/verify-email?token=…&lang=`). Con sesión, «Continuar» lleva a `/` y refresca `/auth/me`; sin sesión, «Iniciar sesión» lleva a `/login?lang=`. |
| E6 | Los errores de OAuth del formulario pasan a i18n ES/EN. |

**Lo que no cambia.** Estar verificado sigue afectando solo a las recompensas por invitar y a algunos correos
periódicos. Sin migraciones y sin `content/**`.

## ADR-67 — Decisiones D1–D4 de la serie 46 (DECIDIDO por el dueño, 2026-10-19)

**Origen.** `docs/PLAN_UI_AVANZADA.md` §4: cuatro decisiones que solo toma el dueño, preguntadas en un solo mensaje
al cerrar la ola 1 (46.0–46.7), antes de la ola 2. Respondidas en la sesión del 2026-10-19.

| # | Decisión |
|---|---|
| D1 | **Sin excepción a ADR-62.** El piloto 40.2 sale con los 3 widgets (búsqueda binaria, CIDR, JOIN) y un ítem de demostración cada uno, no persistido en `content/`. Los 30 ítems `interactive` esperan a que ADR-62 permita contenido nuevo. |
| D2 | **Mascota, sí.** SVG + Lottie (ya en el bundle); **no Rive**. Sustituye la línea «sin mascota» de `design/v2/GUIA.md` y la de `docs/design/decisiones-24.0.md` §4, enmendadas con esta fecha. Tiene que casar con la personalidad de la guía (precisa, tranquila, técnica): nada de caricatura ruidosa. **La dibuja una persona** (segunda respuesta del dueño, mismo día): lo que hace una IA no es exclusivo ni registrable como marca (`design/iconos/PROCEDENCIA.md`). La sesión entrega un brief con tres direcciones bocetadas con IA (`design/mascota/`, fila 46.8); la mascota entra en la app cuando el dueño tenga el diseño final del ilustrador, con capturas aprobadas en su PR. |
| D3 | **Sonido encendido por defecto.** Para quien no tiene preferencia guardada; quien ya la tiene la conserva. Sigue sin sonar antes del primer gesto (política de autoplay) y se apaga en Perfil (fila 46.9). |
| D4 | **`@capacitor/haptics`, sí**, en su propio PR (46.2b) con `package.json` y lockfile, y la licencia comprobada antes. En web sigue `navigator.vibrate`. |

**Lo que no cambia.** Ninguna ceremonia celebra un ascenso de liga mientras el servidor no lo aplique (§6.2). Sin
migraciones y sin `content/**`.

## ADR-68 — Fin del veto a la analítica y pase de movimiento por toda la app (DECIDIDO por el dueño, 2026-10-20)

**Origen.** Sesión del 2026-10-20. El dueño pidió instrumentar `fx_emitted` (plan §6.0 punto 5) y completar el
movimiento de la app «sin dejar nada detrás», empezando por la analítica. La regla del 2026-09-30 (ledger 31.5,
`ORCHESTRATOR.md`) vetaba la analítica hasta tener ≥ 100 registrados reales; preguntado expresamente con tres
opciones, el dueño eligió **levantar el veto entero**.

| # | Decisión |
|---|---|
| 1 | **El veto de 31.5 a la analítica y las métricas deja de aplicar**, sin condición de registrados. La otra mitad de 31.5 (PRs pequeños: una fila u oleada ≤ 500 líneas netas) **sigue en vigor**. |
| 2 | La analítica sigue siendo **propia** (`analytics_events`, ADR-50j revisada): ni SDK de terceros en el navegador ni PostHog/Mixpanel en el cliente. |
| 3 | Los eventos de efectos (`fx_emitted`, `fx_skipped`, `sound_toggled`, `haptic_toggled`) se guardan **sin `user_id` ni IP**: la tasa de salto por nivel es un recuento agregado y no necesita saber quién. Así no amplían lo que la política de privacidad publicada dice que se trata (ADR-55). |
| 4 | El pase de movimiento cubre las 33 pantallas (`PLAN_UI_AVANZADA.md` §7) con las líneas rojas de §6.0 intactas: presupuesto por nivel, `prefers-reduced-motion`, nada antes del primer gesto, sin azar ni recompensas que el servidor no haya dado, sin porcentajes del modelo. |

**Lo que no cambia.** `legal.*` lo fija el dueño (ADR-55); la mascota espera al ilustrador (ADR-67 D2); ninguna
ceremonia celebra un ascenso de liga que el servidor no aplique.

## ADR-69 — Decisiones delegadas del 2026-10-22: cola humana con su valor recomendado (DECIDIDO por delegación expresa del dueño)

**Origen.** Sesión del 2026-10-22. El dueño: «toma todas las decisiones excepto: rotar la clave de Groq (H.12);
Paddle T1, anual y tarifa regional (H.35); tiendas; cohorte beta (H.10); contenido. Concluye todo lo demás en un
PR unificado». La sesión toma, en cada fila, el valor recomendado que ya estaba escrito en el ledger. Ninguna
decisión de esta tabla reabre una ADR del dueño.

| # | Fila | Decisión |
|---|---|---|
| 1 | PYSEC-2026-4298 | Se cambia python-jose por **PyJWT** (sin ignorar el aviso en el CI). La guarda de confusión de algoritmo se queda. |
| 2 | #318 | Los enlaces legales de `/auth` siguen **en línea dentro de la frase** (excepción de WCAG 2.5.8); `touchTargets` la reconoce. |
| 3 | #315 | Se cierra: su único commit va en #321. |
| 4 | PR unificado | Los PR #309–#314 y #316–#321 se integran en un solo PR; los individuales se cierran como sustituidos cuando el unificado esté en verde. |
| 5 | H.51 | **Se firma ADR-63** con los valores recomendados: prior 0,10/0,20/0,30 por experiencia, encogimiento k = 4 con tope 0,94, y la puerta de «dominada» (≥ 0,95 y ≥ 7 respuestas) solo con práctica. |
| 6 | H.52 | Duelos: con el opt-out de ligas no se reta ni se es retado; un reto caduca a los 7 días; los duelos no dan XP; el desempate es por tiempo de servidor. |
| 7 | H.53 | `exam_pass_predictor` sale de `backend/app/services/` a `backend/app/ml/` (ningún código de la app lo importa; solo su test y un script de calibración). |
| 8 | H.56 | Se retira de `docs/legal/b2b_pilot_offer_*.md` la promesa de un «panel de equipo» que no existe. |
| 9 | H.57 | La tabla de modelos de `CLAUDE.md` no cambia. |
| 10 | H.44 | Firecrawl, Amplitude, Mailchimp y Lusha se quitan. Desconectarlos es un paso del dueño en los ajustes de conectores de claude.ai; ningún código los usa. |
| 11 | H.46 | No se activa el monitor de uptime de Sentry: puede gastar cuota de pago. |
| 12 | H.47 | El correo de contacto de `/evidence` se queda hasta que exista un alias (`support@`), que depende de Cloudflare Email Routing (cuenta del dueño). |
| 13 | H.58 | Las preguntas escaladas por el barrido de la Oleada 0 se resuelven con su opción recomendada, que es la primera de cada una. |

**Lo que sigue en manos del dueño.**
- Lo que él mismo excluyó: H.12, H.35, tiendas (H.2, H.3, H.5, H.14), H.10 y el contenido.
- H.54 (jurisdicción): depende de la entidad legal, la misma cuestión que Paddle T1.
- H.16 (proteger `master` en GitHub): la integración de esta sesión no tiene permiso sobre la protección de ramas (`GET …/branches/master/protection` → 403); se hace en Settings → Branches.
- Lo que exige cuentas o personas: publicar en redes (H.23), la revisión legal profesional (H.20), los pagos a instructores (H.25), el staging con coste (31.1) y reconectar GitHub en Railway tras su incidente del 2026-10-21.

## ADR-70 — Decisiones del dueño del 2026-10-22: precios que faltaban, titular, edad mínima y contenido (DUEÑO; y por delegación lo marcado)

**Origen.** Sesión del 2026-10-22. El dueño contestó a las preguntas que ADR-69 dejó en sus manos. Lo marcado «por delegación» lo decide la sesión con el valor que ya estaba escrito en el ledger, como en ADR-69.

| # | Fila | Decisión | Quién |
|---|---|---|---|
| 1 | H.35 (1) | **Plan anual = «2 meses gratis»:** Pro 149,99 $/año y Pro Max 199,99 $/año (`app/core/prices.py`). La bandera `ANNUAL_PLAN_ENABLED` sigue apagada en el piloto (ADR-61 §3). | Dueño |
| 2 | H.35 (2) | **Tarifa regional:** LatAm −40 % (Pro ≈ 8,99 $, Pro Max ≈ 11,99 $), con precios por país en Paddle. España y el resto de la UE, precio pleno. | Dueño |
| 3 | Paddle T1 / H.54 | **Titular: persona física** hasta constituir la empresa (destino: Chipre, ADR-61 §22). Entonces cambian titular y código (`payment_service.py`). Falta que el dueño dé su nombre legal para los Términos. | Dueño |
| 4 | ADR-61 | **Fiel**, con una corrección: **edad mínima 16 años**, no 13. Cambia la casilla del alta, su error, los Términos (`termsP2`), la Privacidad (`privacyCoppaDesc`), el mensaje del backend y los e2e. Lo vigila `tests/unit/test_edad_minima.py`. | Dueño |
| 5 | ADR-62 / H.55 | **Se mantiene la pausa de contenido.** Nada nuevo, tampoco correcciones de los defectos del piloto de auditoría, hasta después del piloto con usuarios. | Dueño |
| 6 | H.35 (4) | El 80 % del creador se sigue calculando como hoy: tras la comisión de la pasarela y la retención de H.29. | Delegación |
| 7 | H.35 (5) | Cupo del tutor en Pro: 20 al día (valor de ADR-47). | Delegación |
| 8 | H.35 (6) | Certificación a 39,99 $ con los valores de ADR-49. | Delegación |
| 9 | H.13 | **Cerrada:** Actions vuelve a tener runner desde el 2026-10-21. El CI del PR unificado salió verde (run 39763272777). | Delegación |
| 10 | H.20 | La revisión legal profesional se aplaza hasta tener ingresos; los textos siguen marcados como borrador. | Delegación |
| 11 | H.25 | Los pagos a instructores se aplazan hasta su primera venta; la venta del marketplace sigue cerrada. | Delegación |
| 12 | H.27 | Certificados solo como Open Badges, sin cNFT. | Delegación |
| 13 | H.48 | No hace falta clave de API de Anthropic: ningún código la usa. | Delegación |

**Sigue en manos del dueño.** Su nombre legal (T1); dar de alta los precios anual y regional en Paddle; rotar la clave de Groq (H.12); las tiendas (H.2, H.3, H.5, H.14); la cohorte beta (H.10); y las acciones con cuentas personales (H.23, 26.7, 27.5, 27.6, H.38–H.40, H.28).


## ADR-71 — Decisiones de UI del 2026-10-23, tomadas por delegación del dueño (DELEGACIÓN)

**Origen.** Revisión completa de la app y de los documentos del 2026-10-23. El dueño pidió el PR de fallos y el de documentación, y delegó todas las decisiones en la sesión («toma todas las decisiones tú como dueño»). Cada una lleva su guarda.

| # | Asunto | Decisión | Guarda |
|---|---|---|---|
| 1 | ADR-60, landing | **El «75 %» de «acierto objetivo por pregunta» se queda.** No es una estimación del alumno: es el objetivo fijo del selector (`TARGET_SUCCESS_PROBABILITY = 0.75`, `backend/app/services/quiz.py`). Si el parámetro cambia, la cifra cambia con él. | `adr60.sinPorcentajeDelModelo.test.ts` ata la cifra a la constante |
| 2 | ADR-60, Rutas | **La nota del umbral no dice «95 % de probabilidad de conocimiento (BKT)».** Dice en palabras que una habilidad cuenta como dominada cuando el motor tiene evidencia fuerte. | `tracks.thresholdNote` entra en la lista de claves sin `%` |
| 3 | ADR-60, prueba de nivel | **Se quita la barra «Nivel estimado»** que se llenaba con theta durante la prueba: era un % del modelo dibujado. El resultado ya se dice en palabras (`placement.abilityResult`). | La misma guarda: `PlacementScreen.tsx` sin `thetaAPorcentaje` |
| 4 | D-28 (34.8) | **Las capturas aprobadas viven en el repo:** las 64 PNG de `frontend/e2e/__screenshots__/linux/` que usa `playwright.visual.config.ts`. Solo se regeneran en un PR que lo diga, con el antes y el después. | 34.8 pasa a esperar solo axe por ruta |
| 5 | Documentos de diseño | Donde un documento de `docs/design/`, `SEGMENTOS.md` o un plan choca con un ADR posterior o con el código verificado, **manda el ADR más reciente**; el documento se corrige con una nota de fecha, sin reescribir su historia. | `check_docs.py` |
