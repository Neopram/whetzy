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

**Decision:** Autonomous loop runs as a cron task (`23 */6 * * *`) instead of a one-shot. Pre-flight checks ledger; exits quickly if backlog is exhausted.

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
