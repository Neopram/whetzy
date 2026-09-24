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

---
## ADR-21 — Precio Pro $14.99/mes (2026-09-18)

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
La meta de ADR-25 pasa a **100 × 28 = 2.800 cursos y ≥ 2.800 términos**.

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
| **Pro Max** | `pro` | **19,99 $/mes** | Todo Pro. **Lo que añade sobre Pro no está definido**: queda para H.35 |
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
