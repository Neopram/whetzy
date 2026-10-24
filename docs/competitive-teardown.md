# Whetzy — Competitive Teardown
*Prepared 2026-09-08 · Autonomous session ah*

> **§1–§5 son una foto del 2026-09-08 y no se reescriben** (las secciones con fecha que
> siguen son el registro; la última puntuación es §14). Contrastado con el código el
> 2026-10-09 (44.60, sobre `8f54083`), ya no vale de §1–§5:
> - **Pago web:** no es Stripe. H.29 (2026-10-01) eligió Paddle en web y RevenueCat en
>   tiendas, sin Stripe; `/checkout` existe y falta el alta de Paddle.
> - **Planes:** Free, Pro, Pro Max y Creador (ADR-41, ADR-49), no «Free + Plus/Pro».
> - **GAP-2, landing:** existe en `/landing` (`frontend/src/App.tsx`).
> - **GAP-5, tutor:** el botón «¿Por qué?» está en línea en `QuizScreen`
>   (`components/quiz/WhyButton.tsx`), visible por defecto y con interruptor en el perfil.
> - **GAP-4, certificaciones:** 11 tracks con certificación en
>   `content/curriculum/tracks.json` (CLF-C02, PCEP-30-02, SAA-C03, AIF-C01, CC,
>   PCAP-31-03, SY0-701, MLA-C01, AZ-900, AI-901, DP-900); la serie 10 que cita §3 no
>   tiene filas en el backlog del ledger (`python scripts/ledger.py series 10`).

## Scope

Head-to-head analysis of Whetzy against the three platforms most likely to appear in a user's mental shortlist: **Duolingo**, **Brilliant**, and **DataCamp**.  
Ratings: ✅ Strong · ⚠️ Gap · ❌ Missing

---

## 1. Feature Matrix

| Dimension | Whetzy | Duolingo | Brilliant | DataCamp |
|---|---|---|---|---|
| **Adaptive learning (BKT/DKT)** | ✅ BKT + DKT A/B | ⚠️ Rule-based streak | ⚠️ Light mastery gates | ⚠️ Skill tree |
| **Spaced repetition (FSRS)** | ✅ Full FSRS | ✅ Hearts/Super Duolingo | ❌ | ❌ |
| **Bilingual content** | ✅ ES/EN full | ✅ 40+ langs | ❌ EN only | ❌ EN only |
| **PWA / offline** | ✅ IDB queue | ✅ (limited) | ❌ | ❌ |
| **Native iOS/Android** | ⚠️ Capacitor shell ready | ✅ Native | ✅ Native | ✅ Native |
| **IAP / subscription** | ⚠️ Stripe web (blocked on iOS) | ✅ Premium | ✅ | ✅ |
| **AI tutor / explain** | ✅ Groq Qwen | ❌ | ⚠️ AI hints | ⚠️ AI assistant |
| **Gamification (leagues, duels)** | ✅ | ✅ Heavy | ❌ | ❌ |
| **Content quality pipeline** | ✅ QA agent + dupe detection | ❌ crowd | ❌ editorial | ✅ expert |
| **Progress analytics (admin)** | ✅ full dashboard | ❌ | ❌ | ✅ learner-level |
| **GDPR / data export** | ✅ | ✅ | ⚠️ | ⚠️ |
| **WCAG 2.2 AA** | ✅ (tested axe) | ⚠️ partial | ⚠️ | ⚠️ |
| **Exec / code sandbox** | ✅ Pyodide WASM | ❌ | ✅ (Brilliant cells) | ✅ (DataCamp IDE) |
| **Certification tracks** | ⚠️ Phase 10 roadmap | ❌ | ❌ | ✅ (career tracks) |
| **Marketing site** | ❌ (9.8 TODO) | ✅ | ✅ | ✅ |
| **Pricing / freemium wall** | ⚠️ Free + Plus/Pro Stripe | ✅ Hearts model | ✅ Free/Premium | ✅ Free/Teams |

---

## 2. Where Whetzy Leads

### 2.1 Adaptive Engine Depth
Whetzy is the only platform in this set that runs a **full three-model stack** (BKT mastery + FSRS scheduling + Elo item difficulty) with a live A/B experiment comparing BKT to a DKT LSTM. Duolingo's hearts/streak system is motivational, not diagnostic; Brilliant's mastery gates are binary; DataCamp uses a static skill tree. Whetzy's approach is closer to what research (Piech 2015, Settles & Meeder 2016) shows maximises long-term retention.

### 2.2 Bilingual-First Architecture
Full ES/EN content with i18n-capable React frontend. None of the competitors serve Spanish as a *source* language for technical content — they are EN-first with EN-only explanations. This is a defensible wedge for the Spanish-speaking professional market (LATAM + Spain ≈ 500 M people).

### 2.3 Content Pipeline Automation
The author agent + QA agent + duplicate detector pipeline can generate and validate questions at 10–100× human speed with traceable citations. Competitors rely on editorial teams (DataCamp) or crowdsourcing (Duolingo). This is a structural moat if the pipeline output quality stays high.

### 2.4 Pyodide Code Execution
In-browser sandboxed Python execution (Pyodide + SharedArrayBuffer + import-block) without a remote eval server. Brilliant has a similar feature but requires account sign-in and a subscription. Whetzy's sandbox is COOP/COEP hardened and has a 5-second interrupt — meeting ASVS L2.

---

## 3. Concrete Gaps and Actions

### GAP-1: No native IAP → iOS App Store blocker (HIGH)
**Duolingo / DataCamp / Brilliant**: All have native IAP on iOS.  
**Whetzy**: Stripe web checkout violates 3.1.1. App Store rejection is certain.  
**Action**: 17.14 RevenueCat IAP — required before any iOS submission. No workaround.  
**Owner**: Human (Apple Dev account + device).

### GAP-2: No marketing site → zero organic acquisition (HIGH)
**All competitors**: Full-featured landing page, pricing comparison, testimonials, blog.  
**Whetzy**: No landing page; `whetzy.com` serves the SPA directly to un-authenticated users.  
**Action**: 9.8 — one-page landing with value props, pricing table, CTA to signup. Can be a separate static route (`/landing`) or a full Cloudflare Pages site.  
**Effort**: 1–2 days frontend, 0 backend. Unblocked.

### GAP-3: Native shell unfinished → no App Store / Play Store presence (HIGH)
**Competitors**: Native experiences with platform-native gestures, deep link handling.  
**Whetzy**: Capacitor shell generated, Android icons patched, but no submission yet.  
**Action**: H.4 (Google Play internal test), H.5 (Apple TestFlight) — human-blocked on accounts.

### GAP-4: No certification tracks → DataCamp's biggest differentiator (MEDIUM)
**DataCamp**: Career tracks and certificates. Highly employability-focused.  
**Whetzy**: Phase 10 roadmap exists but not started.  
**Action**: 10.1–10.3. Starts after Phase 9 closes.

### GAP-5: AI tutor visibility low → Brilliant's explainer advantage (MEDIUM)
**Brilliant**: "Explain why" button is prominent on every question.  
**Whetzy**: `/tutor/explain` exists (Plus tier) but the quiz UX buries it.  
**Action**: Surface the "¿Por qué?" / "Why?" button inline in QuizScreen (no backend change needed). Low effort, high perceived value.

### GAP-6: No social proof or testimonials on landing (MEDIUM — follows GAP-2)
**Duolingo / DataCamp**: DAU metrics, celebrity endorsements, case studies.  
**Whetzy**: Zero. At launch, replace with quantified product claims: "X questions answered", "Y% average accuracy gain over 7 days", generated from the analytics dashboard.

### GAP-7: k6 load test not run against Railway prod (LOW)
Local 4-worker uvicorn ≠ Railway free tier (single dyno, cold-start ~3s).  
**Action**: Run `k6 run` against `https://api.whetzy.com` once prod is warm. Adjust `P95_BUDGET_MS` threshold to 3000 for prod baseline.

---

## 4. Priority Matrix

| Gap | Impact | Effort | When |
|---|---|---|---|
| GAP-2: Marketing site | HIGH | LOW | Now (9.8) |
| GAP-5: AI tutor button | HIGH | LOW | Now (QuizScreen tweak) |
| GAP-1: IAP RevenueCat | CRITICAL | HIGH | After human unblocks Apple Dev |
| GAP-3: Store submission | CRITICAL | MEDIUM | After GAP-1 |
| GAP-4: Certs | MEDIUM | VERY HIGH | Phase 10 |
| GAP-6: Social proof | MEDIUM | LOW | After GAP-2 |
| GAP-7: Prod load test | LOW | LOW | Any time |

---

## 5. Strategic Summary

Whetzy's defensible position is **adaptive depth + bilingual content + automated pipeline** — none of the three competitors have all three simultaneously. The critical path to the market is:
1. **Close IAP blocker** (17.14) → enables iOS → enables App Store review.
2. **Marketing site** (9.8) → enables user acquisition before stores.
3. **Surface AI tutor inline** → differentiates on first-use experience.

DataCamp is the closest competitor on content quality but has no adaptive engine. Duolingo is the closest on gamification but has no professional/technical track. Brilliant has the code execution and interactive explanation but is EN-only and has no spaced repetition. Whetzy's gap is distribution (no app store presence, no marketing site) not product — close those two and the wedge is real.

---

## 6. Re-evaluación honesta — 2026-09-12

The 8 September teardown and the 11 September Launch Console (77/100) scored **code inventory against products in market**. The owner asked whether that was brutally realistic. It was not. This section replaces the earlier scoring; §1–§5 stay as the feature inventory they are.

### 6.1 What was inflated, and why

| Claim | What §1 said | What is true today | Honest score |
|---|---|---|---|
| Adaptive engine | Whetzy 95, Duolingo 40 | Duolingo *invented* half-life regression (Settles & Meeder 2016 — the paper cited in §2.1 in Whetzy's favour) and trains it on billions of responses. Whetzy's own eval (4.2): DKT AUC 0.24, BKT 0.33 on 3 validation sequences — **both below chance**. The stack exists; its efficacy has zero evidence | **35** (Duolingo 85) |
| Content quality | 80 vs DataCamp 90 | 1,253 MCQ / fill-blank items vs thousands of hours of video, notebooks and projects (DataCamp) or interactive visualisations per lesson (Brilliant). 100 % sourced is real and rare — but it is thin | **35** |
| AI tutor | 85, "grounded RAG" | ChromaDB + sentence-transformers were **removed from prod** (OOM on Railway free tier, session o). The prod tutor is Qwen-27B with the canonical explanation pasted in — no retrieval. `grounded=True` is not backed by a retrieved source. Khanmigo / DataCamp AI are years ahead | **45** |
| Code execution | 80 vs DataCamp 90 | 7 exec questions out of 1,253 (0.6 %). DataCamp *is* an IDE | **30** |
| Gamification | 75 | 5 leagues, 4 missions, 8 badges, duels — touched by **zero users**. No D1/D7 measured | **40** |
| Bilingual | 90 | Genuinely native ES+EN with sources. Real niche. Still 1,253 items | **80** |
| PWA / offline | 85 | Implemented and E2E-tested in Chromium; never verified on a real mid-range Android over 4G | **70** |
| WCAG | 90 | axe-core clean; no screen-reader pass (9.7 blocked) | **75** |
| Distribution | 25 | Zero users, zero store presence, backend **down** since ≤ 2026-09-11 | **0** |
| Pricing | "competitive" | $9.99 / $19.99 for an unknown MCQ app vs Duolingo Super at $6.99. Aspirational, not tested | — |

**Weighted honest score: Whetzy ≈ 30 / 100.** Duolingo ≈ 72, DataCamp ≈ 68, Brilliant ≈ 66, Codecademy ≈ 58 (their scores in the earlier table were also depressed to flatter the comparison).

### 6.2 What is genuinely true and defensible

- **Spanish-native technical content with canonical citations.** Nobody in the set does this. It is a real thesis for a ~500 M-speaker market — but it is a thesis, not a validated advantage, until users retain on it.
- **Engineering hygiene far above an indie baseline**: 451 tests, mypy/tsc strict, ASVS L2 audit, real GDPR export/delete, WCAG AA (axe), CI green, Alembic discipline, k6 load test. This is a **foundation**, not a moat — users do not see it.
- **Content pipeline (5.1–5.3) exists.** It is a capability; the bank is still 1,253.
- **Team of one + AI** against companies with hundreds of engineers and a decade of learner data. That asymmetry does not go away by writing it down.

### 6.3 What would make "Whetzy leads" a true sentence

Each row maps a gap to the ledger task whose acceptance criterion is the *evidence* that would move the score. None of these is DONE by existing; each is DONE by measuring.

| Gap | Evidence that closes it | Ledger | Score moves |
|---|---|---|---|
| Tutor not grounded in prod | BM25 retrieval in prod, self-retrieval ≥ 95 % top-3, `grounded` reflects a real hit | 11.1 | AI tutor 45 → 70 |
| Tutor invisible | Inline "¿Por qué?" on every feedback, Playwright-tested, ES/EN | 11.2 | AI tutor +10 |
| Engine has no evidence | DKT AUC ≥ 0.70 and > BKT on the public `synthetic-5` benchmark (Piech 2015) | 11.3 | Adaptive 35 → 60 |
| Exec questions 0.6 % | ≥ 15 % exec in tracks 01–03, every expected output verified by actually running CPython in CI | 11.4 | Code exec 30 → 60 |
| Bank at 1,253 | ≥ 1,500 sourced items, structural QA green | P.8 | Content 35 → 45 |
| Coverage is a guess | Measured ≥ 80 % with `--cov-fail-under` | 11.5 | (foundation) |
| No users | 30-person beta: D1 ≥ 40 %, D7 ≥ 20 %, mean `p_known` gain ≥ +0.20 per practised skill | 11.8 (H.10) | Adaptive +15, Gamification 40 → 60 |
| Backend down / unmeasured in prod | TTFQ < 60 s and p95 < 500 ms against `whetzy.com` | 11.6, 11.9 (H.1) | Distribution 0 → 15 |
| No organic acquisition | Lighthouse SEO ≥ 95, sitemap, hreflang | 11.7 | Distribution +10 |
| Not in stores | IAP + submission | 17.14, H.2–H.5 | Distribution +30 |

Realistic ceiling with all of the above done and measured: **≈ 60–65 / 100** — parity on a narrower, better-served niche, not dominance. "Superar con creces a toda la competencia" is not a claim this document can make; it is a target the ledger can earn.

---

## 7. Recálculo — 2026-09-13 (sesión al)

Cinco tareas de §6.3 cerraron **con evidencia ejecutable pegada en el ledger**. Esta sección aplica sus movimientos y sólo los suyos. Regla de la decisión #9: una capacidad sin evidencia de resultado no puntúa, y una tarea sólo mueve el marcador por lo que midió, no por lo que prometía.

### 7.1 Pesos, explícitos por primera vez

El ≈30 de §6 salió de una ponderación que nunca se escribió, así que nadie podía auditarla. Se hace explícita aquí. Estos pesos reproducen el ≈30 anterior (30,4), por lo que el antes y el después son comparables:

| Dimensión | Peso |
|---|---|
| Distribución (usuarios, stores, prod viva) | 0,34 |
| Motor adaptativo | 0,14 |
| Contenido | 0,14 |
| Tutor AI | 0,09 |
| Ejecución de código | 0,07 |
| Gamificación | 0,06 |
| Bilingüe | 0,06 |
| PWA / offline | 0,05 |
| Accesibilidad | 0,05 |

Distribución pesa un tercio a propósito: es la única dimensión que mide si alguien **usa** el producto. Mientras valga 0, ninguna mejora técnica puede levantar el total por encima de ~66.

### 7.2 Qué se movió, y exactamente por qué

| Dimensión | Antes | Ahora | Evidencia que lo justifica — y qué la limita |
|---|---|---|---|
| **Tutor AI** | 45 | **80** | 11.1 + 11.2 DONE. El RAG dejó de ser decorativo: BM25 puro Python que sí cabe en el free tier, self-retrieval top-3 **99,60 % ES / 99,68 % EN** sobre las 1.253 preguntas reales, índice en 0,569 s, +6,9–15,7 MB de RSS. `grounded` pasa de literal `True` a `any(chunk.source for chunk in rag_chunks)`. Y ahora **se ve**: botón «¿Por qué? / Why?» bajo cada feedback, axe 0 violaciones, ES/EN. Sigue por debajo de Khanmigo (85+): un LLM de 27B con BM25 no es GPT-4 con retrieval entrenado, y nadie lo ha usado todavía |
| **Motor adaptativo** | 35 | **55** | 11.3 DONE. Por primera vez hay un número contra un dataset público en vez de 3 secuencias inventadas: DKT **0,8294** vs BKT **0,7983** en synthetic-5, reproducido 3 veces. **No subo a los 60 que §6.3 preveía**, por dos razones que están en el JSON: el benchmark indexa por *concept id*, no por *question id* como el paper — tarea más fácil, AUC no comparable con el 0,75/0,62 publicado — y el margen DKT−BKT es **+0,031** frente al +0,13 del paper. Que tu red gane a tu propio BKT por tres centésimas en la variante fácil es evidencia de que el motor funciona, no de que sea superior a nadie. Duolingo sigue en 85 y con miles de millones de respuestas |
| **Bilingüe** | 80 | **80** | Sin cambio de número, pero el 80 anterior era generoso: 11.10 encontró que la pantalla de liga entera renderizaba `League.name`, que el seeder escribe **sólo en español**, así que un usuario en inglés leía "League Platino". Arreglado por i18n con dos tests que impiden la regresión. El 80 pasa de afirmado a ganado |
| **Distribución** | 0 | **0** | 11.7 DONE con Lighthouse **SEO 100 / Performance 99** (desktop) y 11.11 bajó la carga inicial del landing de 202 kB gzip a ~96. Pero §6.3 preveía "+10" y **no lo aplico**: el backend lleva caído desde ≤ 2026-09-11 (H.1). SEO perfecto hacia un producto cuya API devuelve 404 no adquiere a nadie. Es exactamente el caso que la decisión #9 describe — una capacidad construida que nadie ha usado. Queda **en depósito**: el día que H.1 se resuelva, estos +10 se cobran sin trabajo adicional |
| Contenido | 35 | 35 | 11.4 y P.8 siguen abiertas. 1.253 preguntas |
| Ejecución de código | 30 | 30 | 11.4 en curso. Sigue en 7 de 1.253 (0,56 %), medido hoy |
| Gamificación | 40 | 40 | Cero usuarios. No se mueve hasta 11.8 (H.10) |
| PWA / offline | 70 | 70 | Sin medición nueva en un Android real |
| Accesibilidad | 75 | 75 | 9.7 sigue bloqueada por dispositivo físico (H.9) |

### 7.3 El número

```
0,34×0  + 0,14×55 + 0,14×35 + 0,09×80 + 0,07×30
        + 0,06×40 + 0,06×80 + 0,05×70 + 0,05×75   =  36,35
```

**Whetzy ≈ 36 / 100** (antes ≈ 30). Duolingo ≈ 72, DataCamp ≈ 68, Brilliant ≈ 66, Codecademy ≈ 58 — sin cambios; nada de lo hecho esta sesión les afecta.

Seis puntos en una sesión, todos comprados con evidencia ejecutable. Y sigue siendo **la mitad que Duolingo**, porque el tercio del marcador que mide si alguien usa el producto vale cero mientras el backend esté caído.

### 7.4 Lo que esto no significa

- No significa que el motor sea mejor que el de nadie. Significa que ya **se puede medir**, que es el requisito previo.
- No significa que el tutor compita con Khanmigo. Significa que dejó de mentir sobre sus citas.
- No significa que haya adquisición. Significa que la infraestructura para tenerla existe y está medida, esperando a que haya un producto vivo al que mandar tráfico.

El techo de §6.3 no se mueve: **≈ 60–65** con todo hecho y medido, y sólo llegando a paridad en un nicho más estrecho y mejor servido. La ruta más corta a subir sigue siendo la misma y no es técnica: **levantar el backend (H.1)** y **poner 30 personas reales a usarlo (H.8/H.10)**. Entre las dos valen más puntos que todo el trabajo de ingeniería pendiente junto.

### 7.5 Segunda tanda de la misma sesión — contenido

Dos filas más de §6.3 cerraron con evidencia después del recálculo de §7.3.

| Dimensión | Antes | Ahora | Evidencia — y qué la limita |
|---|---|---|---|
| **Contenido** | 35 | **45** | P.8 DONE: el banco pasa de 1.253 a **1.507 preguntas**, las 207 skills con ≥ 6 Q, 100 % con `source` no vacío, 0 huérfanas al cargar, 1.507 ids únicos. Es exactamente el movimiento que §6.3 predijo para esta tarea, ni un punto más: **sigue siendo texto** frente a las horas de vídeo, notebooks y proyectos de DataCamp o las visualizaciones interactivas de Brilliant. 1.507 preguntas bien citadas es un banco decente, no una biblioteca |
| **Ejecución de código** | 30 | **60** | 11.4 DONE: de 7 preguntas ejecutables a **111**, y el ratio en tracks 01-03 sube de 1,15 % a **15,57 %**. Lo que hace que esto puntúe no es el número sino la verificación: un test de CI ejecuta los 111 programas de referencia en CPython real y compara su stdout con la respuesta que la pregunta anuncia — 100 % coinciden. Una pregunta "ejecuta este código" cuya respuesta publicada estuviera mal es peor que no tenerla. Aun así 60 y no más: DataCamp **es** un IDE con dataset, sesión persistente y proyectos; esto son ejercicios de una celda dentro de Pyodide |

```
0,34×0  + 0,14×55 + 0,14×45 + 0,09×80 + 0,07×60
        + 0,06×40 + 0,06×80 + 0,05×70 + 0,05×75   =  39,85
```

**Whetzy ≈ 40 / 100** (≈ 30 al empezar la sesión, ≈ 36 tras §7.3). Duolingo ≈ 72, DataCamp ≈ 68, Brilliant ≈ 66, Codecademy ≈ 58 — sin cambios.

Diez puntos en una sesión, todos con salida ejecutable pegada en el ledger. Y el techo sigue donde estaba: con **todo** el trabajo técnico restante hecho y medido, ≈ 60-65. La distancia que queda hasta Duolingo no se cierra escribiendo más código.

**Lo que de verdad falta, en orden de puntos:**

1. **Levantar el backend (H.1).** Distribución vale 0 y pesa 0,34 — un tercio del marcador. Mientras la API devuelva 404, el SEO de 11.7, el tutor de 11.1/11.2 y las 1.507 preguntas son inventario. El arranque ya está verificado con el código de hoy (ver H.1): es entrar a Railway y desplegar.
2. **30 usuarios reales (H.8/H.10).** Sin retención medida, "motor adaptativo" y "gamificación" siguen siendo capacidades. El benchmark de 11.3 prueba que el motor *funciona*; sólo una cohorte prueba que *sirve*.

Las dos juntas valen más que todo el backlog de ingeniería pendiente. Ninguna de las dos la puede hacer un agente.

---

## 8. Recálculo — 2026-09-14 (sesión an/ao)

Mismos pesos de §7.1. Se aplican sólo los movimientos con evidencia pegada en el ledger desde §7.

### 8.1 Qué se movió

| Dimensión | §7 | Ahora | Evidencia — y qué la limita |
|---|---|---|---|
| **Distribución** | 0 | **5** | H.1 resuelto: el backend está vivo (`/health` 200, 61 rutas, `/tutor/explain` y `/exam` presentes, verificado por HTTP hoy). Pero los "+10 en depósito" de §7.2 **se cobran sólo a medias**, y por una razón comprobada, no estimada: el frontend desplegado es un build anterior a 9.8/11.2/11.7/11.11 (H.11). Medido hoy contra `whetzy.com`: `/sitemap.xml` devuelve `text/html` en vez de `text/xml`, y el HTML servido tiene **0** etiquetas `hreflang`. El SEO de 11.7 existe en el repo y **no llega a nadie**. La API viva vale 5; los otros 5 siguen en depósito hasta que Pages sirva el build nuevo |
| **Contenido** | 35 | **50** | P.8 cerrada: **1.507 preguntas** (meta 1.500), 207/207 skills con ≥6, 100 % con `source`, 0 skipped. Más 10.2 completa — **300 preguntas de AWS Cloud Practitioner** cubriendo los 4 dominios según pesos oficiales, con 18 fuentes verificadas — y 10.3, simulacro cronometrado con informe por dominio. Eso es el diferenciador de DataCamp, en su primera versión. No sube más porque DataCamp sigue teniendo miles de horas de vídeo, notebooks y proyectos: 90 es suyo con razón |
| **Ejecución de código** | 30 | **55** | 11.4 DONE: de 7 preguntas ejecutables (0,56 %) a **15,57 %** en los tracks 01–03, con cada salida esperada verificada ejecutando CPython en CI. No llega a 60 porque los tracks 04–07 siguen sin exec y DataCamp *es* un IDE |
| Motor adaptativo | 55 | 55 | Sin evidencia nueva desde 11.3. La salvedad del *concept id* sigue en pie |
| Tutor AI | 80 | 80 | Sin cambio. 11.2 ya estaba contado en §7 — y sigue sin llegar a producción por H.11 |
| Gamificación | 40 | 40 | Cero usuarios. No se mueve hasta 11.8 (H.10) |
| Bilingüe | 80 | 80 | 11.12 (exec bilingüe) refuerza el 80; no lo sube |
| PWA / offline | 70 | 70 | Sin medición en Android real |
| Accesibilidad | 75 | 75 | 9.7 sigue bloqueada por dispositivo (H.9) |

### 8.2 El número

```
0,34×5  + 0,14×55 + 0,14×50 + 0,09×80 + 0,07×55
        + 0,06×40 + 0,06×80 + 0,05×70 + 0,05×75   =  41,90
```

**Whetzy ≈ 42 / 100** (≈36 en §7, ≈30 en §6). Duolingo ≈ 72, DataCamp ≈ 68, Brilliant ≈ 66, Codecademy ≈ 58 — sin cambios.

### 8.3 El techo, calculado con los mismos pesos

Con **todo** el backlog cerrado — frontend desplegado, cohorte beta midiendo retención, IAP, stores, VoiceOver:

```
0,34×45 + 0,14×65 + 0,14×55 + 0,09×85 + 0,07×60
        + 0,06×60 + 0,06×85 + 0,05×80 + 0,05×90   =  61,15
```

**Techo ≈ 61.** Conviene decir en voz alta lo que eso significa: con absolutamente todo hecho, Whetzy superaría a **Codecademy (58)** y seguiría por debajo de **Brilliant (66), DataCamp (68) y Duolingo (72)**.

Distribución a 45 ya es optimista — supone stores, tráfico orgánico funcionando y una base de usuarios establecida, que es trabajo de meses y de mercado, no de backlog. Ésa es la aritmética honesta: **el marcador global no se gana construyendo**. Se gana teniendo usuarios, y ese tercio del marcador no lo mueve ningún agente.

### 8.4 Entonces, ¿se supera a la competencia?

En el marcador global, no — ni con el backlog entero cerrado. La pregunta útil es otra, y ahí la respuesta cambia:

**Para un autodidacta hispanohablante que quiere aprender Python en serio**, Whetzy ya gana hoy en las dimensiones que le importan a esa persona: contenido técnico nativo en su idioma con fuente canónica citada (Duolingo no tiene tracks técnicos; DataCamp, Brilliant y Codecademy son EN-only), motor que no infla el progreso, tutor que dice cuándo no sabe, offline real y accesibilidad AA. Ese segmento no lo atiende bien nadie del set, y no es pequeño.

La estrategia defendible no es «superar a toda la competencia». Es **ser incuestionablemente el mejor en un nicho que los cuatro ignoran**, y dejar que el marcador global suba solo cuando ese nicho traiga usuarios. Lo primero que hace falta para empezar a comprobarlo es que alguien pueda *ver* el producto: H.11.

---

## 10. Recálculo — 2026-09-18 (sesiones ay–bb)

Mismos pesos de §7.1. Se aplican sólo los movimientos con evidencia.

### 10.1 Qué se movió

| Dimensión | §8 | Ahora | Evidencia — y qué la limita |
|---|---|---|---|
| **Ejecución de código** | 55 | **57** | 18.3 DONE: runtime JS real — Blob URL Web Worker, sin eval en hilo principal, console capturado, timeout via `terminate()`. Tercer entorno de ejecución en el navegador (Python + SQL ya contados). 2 preguntas `js_exec` en track14; EXEC_FLOOR ratchet activo. No sube más porque DataCamp *es* un IDE con datasets reales y el banco de js_exec son 2 preguntas en un stub de 12 |
| **Contenido** | 50 | **52** | Track13 ciberseguridad: 326 Q reales, 15 % exec (hashlib/hmac/secrets/html/re/ipaddress stdlib). Track14 Frontend JS: 12 Q stub. Banco total: **5.715 Q** / 15 tracks / 342 skills. Sigue siendo texto frente a horas de vídeo de DataCamp; el 52 se compra con 691 preguntas nuevas bien citadas, no con video ni proyectos |
| **Distribución** | 5 | **5** | H.11 sigue sin resolver. API prod `healthy` (verificado). Frontend en whetzy.com es el build anterior a 9.8/11.2. Los +5 en depósito esperan a que Pages sirva el build nuevo |
| Motor adaptativo | 55 | 55 | Sin evidencia nueva desde 11.3 |
| Tutor AI | 80 | 80 | Sin cambio desde §7 |
| Gamificación | 40 | 40 | Cero usuarios |
| Bilingüe | 80 | 80 | 202 tildes corregidas — el 80 pasa de afirmado a más ganado |
| PWA / offline | 70 | 70 | Sin medición en Android real |
| Accesibilidad | 75 | 75 | 9.7 bloqueada (H.9) |

### 10.2 El número

```
0,34×5  + 0,14×55 + 0,14×52 + 0,09×80 + 0,07×57
        + 0,06×40 + 0,06×80 + 0,05×70 + 0,05×75   =  42,73
```

**Whetzy ≈ 43 / 100** (≈ 42 en §8). Un punto. Toda la ingeniería de sesiones ay–bb compra exactamente un punto porque la distribución sigue valiendo 5 y pesa 0,34. Eso es la aritmética honesta, no una crítica al trabajo.

### 10.3 Lo que de verdad falta

El análisis de §8.4 no cambia. La tesis de nicho ES/EN + motor auditado + ejecución multi-runtime en navegador es real y se ha fortalecido (tres runtimes reales). Pero el tercio del marcador que mide si alguien *usa* el producto sigue en 5. **H.11** (frontend build) y **H.10** (30 usuarios beta) valen más que todo el backlog técnico pendiente junto.

Lo que cambió en este intervalo: los dos stubs (track13 y track14) demuestran que el pipeline funciona. Son evidencia de velocidad de autoría, no de producto terminado.

---

## 11. Recálculo — 2026-09-18 (sesión bc): H.11 cerrado, Educative.io entra en el set

Mismos pesos de §7.1. Dos cosas nuevas y las dos con evidencia: el frontend de producción
sirve por fin el build actual, y un quinto competidor evaluado **en vivo** (no de memoria).

### 11.1 Qué se movió

| Dimensión | §10 | Ahora | Evidencia — y qué la limita |
|---|---|---|---|
| **Distribución** | 5 | **10** | **H.11 cerrado**: `npx wrangler pages deploy dist --project-name whetzy --branch main` → 153 ficheros, commit `8015fe4`, `https://8c077b9a.whetzy.pages.dev` como Production de `whetzy.com`, verificado en el dashboard de Cloudflare Pages (Production → main). Los «+5 en depósito» de §7.2/§8.1 se cobran: landing, onboarding, `hreflang`, code-splitting, Pyodide autohospedado y el CSS sin `fonts.googleapis.com` (línea roja 5) llegan a quien entre. No sube más porque sigue sin haber usuarios (H.10), sin tiendas (H.2/H.3) y sin TTFQ medido contra prod (11.6, ya desbloqueado) |
| Motor · Contenido · Tutor · Exec · Gamif · Bilingüe · PWA · Acc | = | = | Sin evidencia nueva desde §10 |

### 11.2 El número

```
0,34×10 + 0,14×55 + 0,14×52 + 0,09×80 + 0,07×57
        + 0,06×40 + 0,06×80 + 0,05×70 + 0,05×75   =  44,02
```

**Whetzy ≈ 44 / 100** (≈ 43 en §10). Un punto por cerrar el bloqueo humano más antiguo del ledger: esa es la aritmética con distribución al 34 %.

### 11.3 Educative.io — verificado en vivo el 2026-09-18 (sesión logueada)

Propuesta: cursos de **texto interactivo, sin vídeo**, para desarrolladores con experiencia. Foco en System Design, Interview Prep y AI/ML. Declara 3 M de usuarios, 2.200+ cursos, 330+ proyectos, 330+ Cloud Labs (AWS/GCP reales), AI Mock Interviews (3-7/mes según plan), Code Debugger paso a paso, Breakout Sessions con expertos, plan Business, certificados de finalización y **social login Google / GitHub / Apple / LinkedIn**. Precios anuales: Standard 7 $/mes · Premium 10 $/mes · Premium Plus 13 $/mes. Solo inglés. **Sin app móvil nativa, sin offline, sin gamificación, sin motor adaptativo** (avance lineal por curso). 448 partners de tracking en el banner de privacidad.

| Dimensión | Peso | Educative | Por qué |
|---|---|---|---|
| Distribución | 0,34 | 65 | 3 M de usuarios y marca establecida en su nicho; pierde por no tener app en ninguna tienda |
| Motor adaptativo | 0,14 | 15 | Lineal; ni BKT ni SRS ni diagnóstico de dominio |
| Contenido | 0,14 | 75 | 2.200+ cursos y 330+ proyectos, texto + código ejecutable en servidor |
| Tutor AI | 0,09 | 70 | AI Tutor, Code Feedback, Mock Interviews |
| Ejecución de código | 0,07 | 70 | Ejecución server-side, Cloud Labs reales, debugger |
| Gamificación | 0,06 | 10 | Ninguna |
| Bilingüe | 0,06 | 5 | Solo EN |
| PWA / offline | 0,05 | 20 | Web-only |
| Accesibilidad | 0,05 | 55 | Sin verificar; se asume el estándar del sector |

```
0,34×65 + 0,14×15 + 0,14×75 + 0,09×70 + 0,07×70
        + 0,06×10 + 0,06×5  + 0,05×20 + 0,05×55   =  50,55
```

**Educative ≈ 51 / 100.** Set completo: Duolingo 72 · DataCamp 68 · Brilliant 66 · Codecademy 58 · **Educative 51** · **Whetzy 44**.

**Lectura honesta.** Educative gana en distribución y catálogo y pierde el tercio de la tabla por no tener móvil, y las tres dimensiones donde Whetzy invirtió (adaptativo, bilingüe, PWA) ahí valen cero. La superposición real es pequeña: Educative vende *interview prep y system design a seniors angloparlantes*; Whetzy vende *aprendizaje técnico adaptativo ES/EN con certificaciones cloud y ejecución en navegador*. El riesgo no es que nos quite usuarios; es que un hispanohablante lo encuentre antes por el SEO de «system design interview».

### 11.4 Lo que Educative tiene y Whetzy no — y qué hacer con cada cosa

| Tienen | ¿Lo necesitamos? | Decisión |
|---|---|---|
| Social login (Google / GitHub / Apple / LinkedIn) | **Sí** — fricción de registro; y **App Store 4.8 exige Sign in with Apple** en cuanto haya cualquier otro OAuth | Serie 19: 19.1 web → 19.2 Apple (H.2) → 19.3 Android (ADR-13) |
| Roadmap por rol visible sin cuenta | Sí (conversión) | 19.8 |
| 330+ proyectos guiados | Sí, a escala de nicho: 10/track ejecutable | 18.8 / 19.6 |
| Certificados de finalización | Sí | 17.2 ya lo tiene; falta exponerlo en el listing |
| Plan Business | Más adelante; sin usuarios es una sala vacía | catálogo §9 |
| Cloud Labs reales | **No** — coste de servidor y contrario al diferenciador WASM sin servidor | no se construye |
| AI Mock Interviews | **No ahora** — fuera del nicho (cert prep + Python) y LLM caro | fase ≥ 20 |
| 2.200+ cursos | **No por volumen** — profundidad > amplitud; el techo del catálogo era 27 tracks / ≈ 80 cursos *(histórico; plan actual ADR-53: suelo 50 skills · 800 preguntas por track, ideal por temario — §14)* | catálogo §2 |
| Testimoniales FAANG | No inventar ninguno; prueba social solo con cifras de `/evidence` | 19.8 |

### 11.5 Qué falta para vender en cada canal

| Canal | Bloqueante | Acción |
|---|---|---|
| **Web** (`whetzy.com`, live desde hoy) | Social login ausente; sin prueba social; TTFQ sin medir en prod | 19.1 · 19.8 · 11.6 |
| **App Store** | 3.1.1 IAP (17.14) · **4.8 Sign in with Apple (19.2)** · H.2 · H.14 (macOS) | Ninguna submission sin 17.14 + 19.1 + 19.2 |
| **Play Store** | Google Play Billing (19.3) · Google Sign-In (19.3) · H.3 | Educative **no está** en Play Store: el nicho «aprendizaje técnico ES/EN en Android» está vacío |

### 11.6 El techo, revisado

- Con todo el backlog técnico (Series 17-19) hecho y medido, sin usuarios: **≈ 61** (§8.3, sin cambio — el contenido sigue saliendo solo de fuentes libres, ADR-11, y eso no baja el 55 de Contenido: lo que hace profundo a un track es la verificación, no el precio del libro).
- Con tiendas publicadas, social login y una cohorte de 30 beta midiendo retención (H.10): Distribución ≈ 50 → **≈ 66**. Paridad con Brilliant, por encima de Codecademy y Educative, por debajo de DataCamp y Duolingo.
- Media aritmética de los cinco competidores: **63**. Whetzy hoy está 19 por debajo; con el backlog cerrado, 2 por debajo; con usuarios, 3 por encima. **El marcador global no se gana construyendo**; lo que se gana construyendo es no tener ningún rival en ES/EN + adaptativo + offline.

---

## 13. Recálculo — 2026-09-24: ADR-46 y la corrección de la proyección del catálogo

> **Meta sustituida por ADR-53 el 2026-09-30 (§14).** La escalera de puntos de abajo sigue
> valiendo; lo que cambia es qué significa «catálogo completo».

Mismos pesos de §7.1. **Sin evidencia nueva de mercado: el marcador sigue en ≈ 44.**
Lo que cambia es la meta y una corrección.

- **Meta (ADR-46, histórica; hoy ADR-53, §14):** todos los tracks de la industria (28 del mapa + 14 de
  `CATALOGO_MAESTRO.md` §2.0) con ≥ 50 cursos por track, sobre un corpus abierto
  descargado y verificado. Contenido pasaría de 55 a ≈ 85 cuando esté hecho y
  verificado: **+4,2 puntos** (0,14 × 30). Ni un punto más: el catálogo no toca
  Distribución.
- **Corrección:** `CATALOGO_MAESTRO.md` §12.1 proyectaba «~79 con 1K usuarios» y «~85
  con 10K» y su columna «Hoy» sumaba 49 donde decía 44. Se retira; queda la escalera de
  §11.6 más el catálogo: **44 hoy → ≈ 61 (backlog técnico) → ≈ 66 (tiendas + social login
  + cohorte) → ≈ 70 (catálogo ADR-46 completo)**.
- **Lo que sí puede mover más de 4 puntos** sigue siendo lo de §11.6: usuarios (H.10),
  tiendas (H.2/H.3/H.14/17.14) y distribución (series 26/27, abiertas por ADR-47 para
  redactar; publicar sigue siendo del dueño).
- **Riesgo de ventana:** la fila 37.12 hace el monitoreo trimestral que §11.4 del catálogo
  prometía y nadie tenía asignado.

---

## 9. Catálogo frente al mercado — 2026-09-16 (sesión au)

> **Histórico.** Los objetivos de la tabla (27 tracks, ≈ 80 cursos, ≈ 55 certificaciones) son los
> de aquella fecha; el plan vigente es ADR-54 (2026-10-01; §14 recoge el de ADR-53, sustituido, sin re-puntuar) y la competencia medida está en
> `CATALOGO_MAESTRO.md` §8 (2026-09-30).

El dueño preguntó si Whetzy puede «abarcar todo el mundo informático». La respuesta
completa está en **`CATALOGO_MAESTRO.md`**; aquí sólo lo que afecta al marcador.

**El marcador no cambia.** Mismos pesos de §7.1, ninguna evidencia de mercado
nueva: sigue en **≈ 42** y el techo sin usuarios en **≈ 61** (§8.3). Añadir
tracks mueve *Contenido* (peso 0,14) unos puntos como mucho; no toca *Distribución*
(0,34), que vale 5 mientras el frontend de prod sea un build viejo (H.11).

**Lo que sí queda escrito, porque antes no lo estaba:**

| Dimensión | Whetzy hoy (medido) | Objetivo del catálogo | Liga en la que compite ese objetivo |
|---|---|---|---|
| Tracks / cursos | 15 / 43 (11 completos + 2 stubs) | 27 / ≈ 80 | Boot.dev · Sololearn · Mimo *(≈ 15-40 cursos, estimación sin verificar — 18.12)* |
| Certificaciones | 4 (blueprints corregidos en 18.1) | ≈ 55 | Whizlabs · Tutorials Dojo · KodeKloud |
| Lecciones | 342/342 skills | 1/skill en 27 tracks *(histórico; plan actual ADR-53, §14)* | Codecademy (texto) |
| Ejecución en navegador | Python + SQL + **JS Worker (18.3)** | Python + SQL + JS + shell (v86 descartado, ADR-9) | Brilliant (celdas), DataCamp (IDE) |
| Proyectos | 0 | 10/track ejecutable | Exercism · Boot.dev |
| Vídeo | 0 | explicadores Manim (piloto 18.9) | nadie de la liga objetivo; Platzi/Udemy son otra liga |

**Lectura honesta.** Con el catálogo entero, Whetzy es un **Sololearn/Boot.dev con
motor auditado, ES/EN nativo y ejecución sin servidor** — eso es competir. **No**
es un Platzi (≈ 1.500 cursos, creadores externos, años) ni un Udemy; ese juego no
se gana con agentes. Las cifras de la competencia de esta sección y de
`CATALOGO_MAESTRO.md` §8 son **estimaciones de memoria** hasta que 18.12 las
sustituya por URL + fecha; por eso no se usan para mover ningún número.

## 12. Captura en vivo — 2026-09-24 (sin re-puntuar)

**Qué cambia.** Por primera vez hay precios de la competencia con URL y fecha,
re-descargados a mano: `COMPETENCIA.md` §A.1. Cubre Codecademy, Boot.dev, Platzi y
EDteam, y sustituye en parte las «estimaciones de memoria» de §9 (18.12). Dos
premisas de ADR-21 salen mal (Boot.dev no es $49 sino $59/mes o $399/año;
Codecademy no es $24.99 sino $29.99 mensual o $14.99 anual) y llevan errata en
`DECISIONS.md`.

**Qué no cambia: la puntuación.** No se re-puntúa. Las dimensiones de §11 miden
producto, y lo que se midió hoy son páginas de marketing. Mover un peso con eso
sería el error que §9 advierte. Hay tres hallazgos que sí afectan a la lectura,
pendientes de una re-puntuación con producto medido (34.9):

1. **Lo que diferencia a Whetzy ya está construido, pero no se ve.** Prueba de
   nivel, *readiness* por dominio ponderado y comodín de racha existen en el
   código. Los competidores que los anuncian (Educative, AWS, Duolingo) los
   venden en su portada. Serie 35.
2. **En precio, Whetzy aún no compite: no tiene precio.** La comparativa pública
   lo decía («Aún sin precio») hasta ADR-41, que fijó los mensuales; anual y tarifa regional siguen en H.35.
3. **Hueco en español.** Ninguno de los preparadores de certificación observados
   muestra práctica ni *readiness* en español (informe de agente, §A.2, no
   reproducido).

## 14. Recálculo — 2026-09-30: ADR-53, el catálogo por cobertura

Mismos pesos de §7.1. **El marcador no se mueve: sigue en ≈ 44**, porque no se midió
producto nuevo. Cambia qué cuenta como «catálogo completo» y entra la primera captura de
catálogos de la competencia con URL y fecha (`CATALOGO_MAESTRO.md` §8; 4 descargadas y
leídas por la sesión, el resto por agentes).

> **Sustituida en su meta por ADR-54 (2026-10-01):** forma única 32 skills × 10 preguntas por
> track. Esta sección (§14) no se re-puntúa: lo que sigue es histórico.

- **Meta (ADR-53):** cada track al **suelo** (50 skills · 800 preguntas) y después al
  **ideal** de su temario (4.819 skills · 96.380 preguntas en 45 tracks); certificaciones
  con el 100 % de los objetivos y banco de simulacro reservado; tracks nuevos por demanda.
  Contenido pasa de 55 a ≈ 85 **en el ideal**, igual que antes con ADR-46: **+4,2 puntos**.
  El suelo solo lleva la dimensión Contenido a ≈ 70, es decir +2,1 puntos al marcador
  (0,14 × 15); es una estimación de la sesión, sin medir.
- **Escalera, sin cambios de fondo:** 44 hoy → ≈ 61 (backlog técnico) → ≈ 66 (tiendas +
  social login + cohorte) → ≈ 70 (catálogo en el ideal de ADR-53).
- **Lo que la captura cambia en la lectura, no en los puntos:**
  - en amplitud, Whetzy ya supera a su competencia directa (24 tracks + 11
    certificaciones frente a las 3 rutas y 51 cursos de Boot.dev);
  - en profundidad por track está por debajo (20–30 skills frente a 51 lecciones y 20 h
    del curso mediano de Boot.dev), y eso es lo que corrige el suelo;
  - sus simulacros no tienen banco reservado (el mercado vende 6 simulacros por examen);
  - retención y conversión de apps de educación con fuente (ADR-53 §8): D30 del 2,7–3,2 %,
    conversión freemium del 2,1 %. Nada de eso es de Whetzy: son las referencias a batir.
- **Lo que sí puede mover más de 4 puntos** sigue siendo §11.6: usuarios (H.10), tiendas
  y distribución.

## 15. Rúbrica de interfaz y experiencia re-puntuada — 2026-10-24 (46.6, 34.9)

La rúbrica es la de `PLAN_UI_AVANZADA.md` §0 (pesos fijos, solo interfaz y experiencia; la de §7.1
de este documento mide el producto entero y no se toca). La línea base del 2026-10-17 daba
**≈ 53**. Cada celda nueva cita lo que la sostiene; las notas siguen siendo juicio de la sesión sobre
esa evidencia, **sin usuarios**.

| Dimensión | Peso | 17-10 | 24-10 | Evidencia de la nota nueva |
|---|---|---|---|---|
| Sistema visual | 0,15 | 65 | 85 | un solo juego de tokens (46.4; `src/theme/` ya no existe; 0 `var(--x, #hex)` en `src/`); `tokens.contraste.test.ts` 79/79; axe sin violaciones en los 50 casos de `e2e/axe-rutas.spec.ts` (23 rutas públicas × oscuro/claro; Hoy, 15 pantallas internas y `/admin` sin permiso en es/en × oscuro/claro), 46/46 y las 4 de `/landing` y `/privacy` el 2026-10-24 |
| Animación y pulido | 0,15 | 35 | 75 | feedback dentro de la tarjeta (46.1, #266); movimiento reducido respetado y vigilado (`motionGuard.test.ts`, casos «con movimiento reducido» de `entrada46`, `aprender46`, `competir46`, `progreso46`, `comprar46`); sonido y vibración (`lib/feedbackFx.ts`, `@capacitor/haptics`); tabla §7.5 rehecha contra el código |
| Superficie interactiva | 0,20 | 40 | 45 | tipo `interactive` (40.1) y 3 widgets en código (`frontend/src/widgets/`: búsqueda binaria, CIDR, JOIN) con `e2e/widgets-piloto.spec.ts`; **0 preguntas `interactive` en el banco** (`content/`), así que el alumno aún no ve ninguno |
| IA dentro de la experiencia | 0,15 | 55 | 60 | tutor por modos (¿Por qué? / ¿Cómo? / A fondo; `e2e/tutor-modos.spec.ts`); el tutor que señala y habla (40.5, 40.6) sigue en TODO |
| Accesibilidad e i18n | 0,10 | 85 | 90 | axe en cada ruta y pantalla de `App.tsx`, ES y EN, oscuro y claro, salvo dos huecos: `/admin` con la cuenta del dueño y el Quiz con feedback (solo es/oscuro, `accessibility.spec.ts`); arreglados hoy: `Button` cargando sin nombre, contraste de Evidencia, insignia naranja y pestañas en claro, Reintentar en claro, Restablecer, Verificar correo y perfil público inexistente sin encabezado, ▲▼ de la Liga sin nombre, navegación con etiqueta solo en inglés |
| Rendimiento y sensación nativa | 0,10 | 55 | 60 | vibración nativa (`@capacitor/haptics`); presupuestos de peso (`scripts/check-bundle.mjs`, `e2e/perf-budget.spec.ts`); **LCP en 4G sin medir** esta semana |
| Onboarding y retención | 0,15 | 50 | 50 | embudo de pago y encuesta del primer quiz propios (`GET /analytics/conversion`, 46.6); **sin cohorte de usuarios**, así que nada medido que mueva la nota |
| **Total** | 1,00 | **≈ 53** | **≈ 65** | 0,15·85 + 0,15·75 + 0,20·45 + 0,15·60 + 0,10·90 + 0,10·60 + 0,15·50 = 64,5 |

**Meta ≥ 75: no alcanzada.** Lo que más pesa en lo que falta: superficie interactiva (widgets en
el banco: contenido en pausa, ADR-62) y retención (usuarios).

**Rivales: sin nota.** Las cifras de §0 del plan para Duolingo (≈ 89), Brilliant (≈ 87) y DataCamp
(≈ 72) eran estimación de memoria. La captura de hoy (`COMPETENCIA.md` §A.2e) es de páginas
públicas, no del interior de una lección, y no sostiene una nota por dimensión. Por eso aquí **no
hay ningún «mejor que» ni «peor que»** frente a ellos; 40.13 sigue abierta hasta medir con cuenta y
con usuarios.
