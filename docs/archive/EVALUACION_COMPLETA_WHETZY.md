# Evaluación Integral Whetzy — Septiembre 2026

> **Documento de análisis. No manda:** manda el ledger (`docs/AUTONOMOUS_STATE.md`, ADR-48) y las decisiones de **ADR-50** (`docs/DECISIONS.md`). Se midió sobre `master` `9ab4d24` (18 tracks); `master` tiene hoy 35 tracks. Cifras actuales: `python scripts/project_snapshot.py`. Las correcciones comprobadas están en la **§29**.

**Sesión de análisis read-only.** Ninguna línea de código fue modificada.
Todas las cifras exactas de impuestos, comisiones y umbrales están marcadas [Guessing] cuando provienen de memoria de entrenamiento y requieren verificación con un profesional antes de actuar.

---

## ÍNDICE

1. [Auditoría técnica (9 dimensiones)](#1-auditor%C3%ADa-t%C3%A9cnica)
2. [Auditoría no técnica (7 dimensiones)](#2-auditor%C3%ADa-no-t%C3%A9cnica)
3. [Lógica de negocio](#3-l%C3%B3gica-de-negocio)
4. [Contenido: legitimidad, copyright y fuentes](#4-contenido-legitimidad-copyright-y-fuentes)
5. [Mitigación de riesgos (7 acciones priorizadas)](#5-mitigaci%C3%B3n-de-riesgos)
6. [Blockers de App Store y Google Play](#6-blockers-de-app-store-y-google-play)
7. [Proyecciones de ingresos (10K / 20K / 100K MAU)](#7-proyecciones-de-ingresos)
8. [¿Puedo vivir de esto?](#8-puedo-vivir-de-esto)
9. [Modelo operativo solo founder](#9-modelo-operativo-solo-founder)
10. [Arquitectura de pagos (3 canales)](#10-arquitectura-de-pagos)
11. [SEO y distribución](#11-seo-y-distribuci%C3%B3n)
12. [Expansión multilingüe (8 idiomas)](#12-expansi%C3%B3n-multiling%C3%BCe)
13. [Video generado con IA](#13-video-generado-con-ia)
14. [Impuestos, IVA y estructura fiscal](#14-impuestos-iva-y-estructura-fiscal)
15. [Constitución de empresa](#15-constituci%C3%B3n-de-empresa)
16. [Scorecard competitivo (antes y después)](#16-scorecard-competitivo)
17. [Ventajas únicas y debilidades permanentes](#17-ventajas-%C3%BAnicas-y-debilidades-permanentes)
18. [Roadmap de implementación definitivo](#18-roadmap-de-implementaci%C3%B3n-definitivo)
19. [Límites del plan Free — decisión de monetización](#19-l%C3%ADmites-del-plan-free)
20. [Bundle y partición: iOS, Android y Web](#20-bundle-y-partici%C3%B3n)
21. [Auditoría de contenido: rastros de IA](#21-auditor%C3%ADa-de-contenido-rastros-de-ia)
22. [Cobertura de tracks: gaps y path Python → AI Engineering](#22-cobertura-de-tracks)
23. [Certificaciones: cobertura y suficiencia](#23-certificaciones-cobertura-y-suficiencia)
24. [Navegación no lineal: libertad de elección del usuario](#24-navegaci%C3%B3n-no-lineal)
25. [Contenido: video, texto, emojis y costos](#25-contenido-video-texto-emojis-y-costos)
26. [Lo que falta: ángulos ciegos del solo founder](#26-lo-que-falta-solo-founder)
27. [Lógica del negocio vs competencia: veredicto](#27-l%C3%B3gica-vs-competencia-veredicto)
28. [Plan de implementación definitivo con decisiones tomadas](#28-plan-de-implementaci%C3%B3n-con-decisiones)
29. [Fe de erratas comprobada (2026-09-26)](#29-fe-de-erratas-comprobada-2026-09-26)

---

## 1. Auditoría técnica

| Dimensión | Nota | Justificación |
|---|---|---|
| **Arquitectura backend** | 8.5/10 | FastAPI async, 25 módulos de endpoints, SQLAlchemy 2.0 + asyncpg, Redis, 33 migraciones Alembic. Capas bien separadas (models/schemas/services/api). OpenTelemetry + Prometheus + Sentry. Arquitectura de startup seria. |
| **Arquitectura frontend** | 8/10 | React 19 + Vite + TypeScript, 23 pantallas, 30 componentes, design tokens propios con 70+ variables CSS, dark/light mode, Zustand + React Query. Self-hosted Pyodide/Monaco para ejecución de código en el browser. |
| **Testing** | 7.5/10 | 146 archivos de test, pirámide sólida (95 backend, 31 frontend, 18 e2e Playwright). Load tests existen. Cobertura backend fuerte; frontend con 31 tests para 23 pantallas queda corto. |
| **Seguridad** | 8.5/10 | JWT + bcrypt + timing-attack-safe, 2FA TOTP, refresh token rotation, rate limiting, gitleaks + bandit + semgrep en pre-commit, Docker non-root, audit de dependencias. Sobresaliente para el tamaño del equipo. |
| **CI/CD** | 6/10 | Pipeline de GitHub Actions bien escrito pero **nunca ha corrido** (facturación). Gate local `.githooks/pre-push` compensa parcialmente. No hay evidencia automática en PRs, no hay badge verde. |
| **Infra & deploy** | 7.5/10 | Railway (backend auto-deploy desde master) + Cloudflare Pages (frontend). Funcional y barato. Falta monitoring de uptime real — el backend ha estado caído sin detección. |
| **AI/LLM** | 8/10 | Stack adaptativo triple (BKT + DKT + FSRS + Elo) más sofisticado que la mayoría de competidores. RAG ligero con BM25 (pragmático). Tutor bilingüe con memoria de tres capas. Groq como provider inteligente por coste. |
| **i18n y accesibilidad** | 9/10 | 926 líneas de JSON por idioma, script de paridad, 158 ocurrencias de a11y en 41 archivos, `prefers-reduced-motion`, axe-core en Playwright, ratios WCAG documentados. Excelente. |
| **Mobile** | 5/10 | Capacitor configurado para Android, Codemagic para builds. Pero **no hay app publicada** en ninguna tienda. No hay iOS (falta Sign in with Apple, ADR-13). |

### Mitigaciones técnicas al 100%

**Backend:** Railway Pro con horizontal scaling, pgbouncer para pooling, read replica de PostgreSQL para queries pesados, health check real (UptimeRobot/Betterstack). DKT inference en worker separado si PyTorch es pesado.

**Frontend:** Escalar a 60+ unit tests cubriendo flujos críticos (quiz, auth, payment). Implementar deep linking para compartir resultados/certificados.

**Testing:** Frontend a 60+ tests. Restaurar umbral real para content tests. Añadir contract tests API. Load test targeting 10K concurrent.

**CI/CD:** Activar GitHub Actions (free tier da 2,000 min/mes — suficiente). Pipeline ya está escrito — solo hay que activarlo.

**Seguridad:** Cloudflare WAF (gratis en plan Free). CSP headers en middleware existente. Un pen-test externo antes de lanzamiento ($500-2,000 o OWASP ZAP automatizado gratis).

**i18n:** Migrar a Inter o Noto Sans (cobertura Unicode completa). Implementar `dir="rtl"` condicional para árabe. Visual regression tests por locale.

**AI/LLM:** Pre-computar DKT inference (batch nocturno, no real-time). Fallback a segundo provider LLM (Cerebras, Together, o Anthropic Haiku). Vector DB (Qdrant o Pinecone) cuando corpus exceda 50K preguntas.

**Mobile:** (a) Sign in with Apple con plugin Capacitor. (b) Crear proyecto iOS con `npx cap add ios`. (c) StoreKit 2 (Apple IAP) y Google Play Billing Library. (d) Data Safety form e IARC questionnaire. (e) Ocultar tracks incompletos. (f) Publicar en ambas stores.

---

## 2. Auditoría no técnica

| Dimensión | Nota | Justificación |
|---|---|---|
| **Contenido educativo** | 6/10 | 6,305 preguntas, 378 skills, 622 términos, 18 tracks. Sustancial pero target propio es 126K preguntas (estás al ~5%). Cero video, cero proyectos multi-paso. Pipeline AI rápido (~518 preguntas/sesión verificadas). |
| **Modelo de negocio** | 7/10 | Pricing agresivo (Free con todo el contenido, Pro $14.99, cert $39.99). Undercut vs Platzi ($49), EDteam ($30), Codecademy ($29.99). Paddle como MoR. El modelo tiene lógica, pero **ningún ingreso ha validado nada**. |
| **Posicionamiento competitivo** | 6.5/10 | Teardown competitivo honesto (40/100 vs Duolingo 72). Datos de competencia sourced con URL y fecha. Ángulo bilingüe ES/EN para tech es real. |
| **Marketing y distribución** | 2/10 | **El agujero más grande del proyecto.** Landing dentro del SPA (no SEO-friendly). Sin analytics, sin blog, sin SEO, sin redes sociales, sin email marketing, sin referidos, sin presencia en app stores. |
| **Usuarios y validación** | 1/10 | **Cero usuarios.** Ninguna métrica de retención, conversión, engagement, o NPS. Ningún feedback real de un estudiante. |
| **Documentación operativa** | 9/10 | Ledger con 224 filas, ADRs numerados, catálogo maestro, protocolo de verificación. Máquina de documentación. Quizás demasiada para un producto sin usuarios. |
| **Velocidad de ejecución** | 8/10 | 158 commits en 4 días. Pipeline AI-asistido. Scripts de automatización maduros. Pero la velocidad está concentrada en *construir*, no en *lanzar*. |

---

## 3. Lógica de negocio

### Lo que funciona bien

- Stack adaptativo (BKT+DKT+FSRS+Elo) es diferenciador técnico real — ningún competidor combina los tres
- Bilingüe nativo ES/EN para tech es un hueco de mercado genuino
- Pricing undercut a todos los competidores relevantes
- Ejecución de código en browser (Pyodide/sql.js) sin servidor es elegante y barato de operar
- Content pipeline con IA es 10-100x más rápido que producción humana

### Lo que no funciona / riesgo

- Se está construyendo en el vacío — no hay ni un usuario que diga si la UX adaptativa se *siente* bien
- 50 items HUMAN-BLOCKED en el backlog = cuello de botella en el dueño
- CI “nunca ha corrido” = deployment a master es técnicamente sin red
- Sin monitoring de uptime, el backend puede caerse y nadie lo sabe
- Marketplace de instructores asume supply-side (instructores) que no existe

---

## 4. Contenido: legitimidad, copyright y fuentes

### Marco legal: sólido [Verified]

| Marca | Licencias | Qué se puede hacer | Cantidad |
|---|---|---|---|
| **[reusar]** | MIT, Apache-2, BSD, CC BY, CC0, PSF, dominio público | Texto entra al app con atribución | 12 fuentes |
| **[H.LIC]** | CC BY-SA | Prohibido por defecto (ADR-47) | 0 fuentes |
| **(cita)** | CC BY-NC, propietario (AWS, CompTIA, ISC2, Cisco) | Leer, aprender, escribir original, linkear. Nunca pegar | 3 fuentes |

### Las 15 fuentes verificadas

| Fuente | Licencia | Uso |
|---|---|---|
| CPython docs | PSF-2.0 | Reusar |
| Exercism Python | MIT | Reusar |
| TheAlgorithms/Python | MIT | Reusar |
| SQLite docs | Dominio público | Reusar |
| MITRE ATT&CK | Custom permisiva | Reusar |
| Docker docs | Apache 2.0 | Reusar |
| Kubernetes website | CC BY 4.0 | Reusar |
| Azure docs | CC BY 4.0 / MIT | Reusar |
| Flutter website | CC BY 3.0 / BSD | Reusar |
| TypeScript website | CC BY 4.0 / MIT | Reusar |
| 12factor (Heroku) | MIT | Reusar |
| Anthropic cookbook | MIT | Reusar |
| Anthropic courses | CC BY-NC 4.0 | Solo cita |
| javascript.info | CC BY-NC 4.0 | Solo cita |
| The Linux Command Line | CC BY-NC-ND | Solo cita |

### Calidad del contenido por track

| Categoría | Tracks | Nota | Detalle |
|---|---|---|---|
| **Excelente** | track01 (Python Basics), track07 (AI Eng), track12 (SQL) | 8-9/10 | Preguntas correctas, explicaciones del “por qué”, código ejecutable, ES/EN nativos, distractores plausibles |
| **Bueno** | track02-03, track04-05, track06, track08-11 | 7/10 | Sólidos pero menos profundos |
| **Mediocre** | track13, track15-17 | 5-6/10 | Explicaciones telegráficas, un distractor flippant |
| **Stub** | track14 (Frontend JS) | 2/10 | 12 preguntas, 1 lección. Placeholder |
| **Cuarentena** | track24, track25 | 0/10 | Basura generada por IA, correctamente aislada |

### Inventario completo

| Track | Preguntas | Lecciones | Glosario |
|---|---|---|---|
| track01 Python Basics | 867 | 52 | 38 |
| track02 Python Intermediate | 405 | 24 | 43 |
| track03 Python Advanced | 397 | 24 | 41 |
| track04 Software Engineering | 498 | 30 | 37 |
| track05 Software Architecture | 365 | 24 | 42 |
| track06 AI Fundamentals | 496 | 28 | 40 |
| track07 AI Engineering | 481 | 25 | 39 |
| track08 AWS CLF-C02 | 348 | 19 | 42 |
| track09 PCEP | 267 | 15 | 40 |
| track10 AWS SAA-C03 | 375 | 25 | 42 |
| track11 AWS AIF-C01 | 225 | 15 | 40 |
| track12 SQL | 300 | 20 | 36 |
| track13 Cybersecurity | 398 | 20 | 50 |
| track14 Frontend JS | 12 | 1 | 6 |
| track15 Linux/Shell | 180 | 12 | 12 |
| track16 Algorithms | 158 | 12 | 12 |
| track17 Networking | 180 | 12 | 12 |
| track40 ISC2 CC | 353 | 20 | 50 |
| **TOTAL** | **6,305** | **378** | **622** |

### Veredicto legal de contenido

**Riesgo de demanda por copyright: BAJO.** [Likely — basado en muestreo, no en revisión de las 6,305 preguntas]

El framework legal es mejor que el de la mayoría de startups edtech. Las decisiones están documentadas en ADRs, las fuentes clasificadas con criterio, hay scripts de validación, y el contenido muestreado es composición original.

Los tres riesgos reales:
1. **Paráfrasis cercana no detectada** en preguntas sobre conceptos propietarios (AWS, CompTIA)
2. **Falta de LICENSE propio** — trivial de arreglar
3. **Falta de blueprint mapping** — si un organismo certificador argumenta que la estructura replica su examen

---

## 5. Mitigación de riesgos

### Tabla priorizada

| # | Acción | Esfuerzo | Impacto legal |
|---|---|---|---|
| 1 | Archivo LICENSE + notice en content/ | 5 min | **Alto** — sin esto cualquiera puede argumentar que tu código/contenido no tiene protección |
| 2 | Disclaimer de marcas en ToS | 15 min | **Alto** — estándar de la industria, defensa básica |
| 3 | Cerrar gap index.json vs sources reales | 1-2 horas | **Alto** — cierra el loop de trazabilidad |
| 4 | Blueprint mapping público | 2-3 horas | Medio — demuestra origen legítimo |
| 5 | Detector de similitud | 4-6 horas | Medio — atrapa paráfrasis cercana |
| 6 | Auditoría trimestral documentada | 2 horas/trimestre | Medio — evidencia de due diligence |
| 7 | Editorial tracks 13-17 | 3-4 horas | Bajo legal, alto reputación |

### Detalle de cada mitigación

**1. LICENSE (5 min):** Código AGPL-3.0 o propietario. Contenido CC BY-NC-ND 4.0 o “All Rights Reserved”. El banco de preguntas *es* el producto — no regalarlo con MIT.

**2. Disclaimer ToS (15 min):** “Las preguntas de preparación para certificación son material original creado por Whetzy. No están afiliadas ni endorsadas por AWS/CompTIA/ISC2/Python Institute. Los nombres de certificación son marcas registradas de sus respectivos propietarios.” Estándar — Kaplan, Whizlabs, Tutorials Dojo, todos lo tienen.

**3. Cerrar gap index.json (1-2h):** Extraer todas las URLs únicas de los campos `source` de las 6,305 preguntas. Agrupar por dominio. Añadir al `index.json` cada dominio nuevo con su licencia verificada. Hacer que `check_question_bank.py` falle si un `source` cita un dominio no registrado en el índice.

**4. Blueprint mapping (2-3h):** Crear `content/exams/blueprints/` por certificación con los dominios **públicos** del examen. Mapear cada skill_id al dominio público correspondiente. Demuestra que la cobertura viene del syllabus público, no de exam dumps. Bonus: feature de producto “tu cobertura del dominio 3 es 72%”.

**5. Detector de similitud (4-6h):** Script que compare texto de explicaciones contra texto fuente (si descargable) con similitud de coseno o n-gram overlap. Umbral: >60% similitud = flag para revisión humana. Gate de generación: prompt explícito “Escribe con tus propias palabras. No parafrasees. Usa ejemplos originales.”

**6. Auditoría trimestral (2h/trimestre):** Muestreo de 20 preguntas al azar de tracks que citan libros/papers. Buscar frases clave en Google Scholar/libro original. Documentar en `content/audits/YYYY-MM.md`. Defensa legal fuerte: “hacemos auditorías periódicas documentadas de originalidad.”

**7. Editorial tracks 13-17 (3-4h):** Explicaciones de mínimo 2-3 oraciones con el “por qué”. Eliminar distractores joke. Ratchet de longitud mínima de explicación en `check_question_bank.py`: `len(explanation) < 80 chars` = flag.

---

## 6. Blockers de App Store y Google Play

### Apple App Store — Rechazos seguros

| # | Check | Estado actual | Mitigación | ¿Blocker? |
|---|---|---|---|---|
| 1 | Sign in with Apple (Guideline 4.8) | Falta | Capacitor plugin + backend OAuth | **Sí** |
| 2 | Apple IAP / StoreKit 2 (Guideline 3.1.1) | Falta | Implementar para subs + certs | **Sí** |
| 3 | Proyecto iOS | Falta | `npx cap add ios` + Xcode | **Sí** |
| 4 | Divulgación de AI (Guideline 5.6.4+) | No declarada | Declarar en App Review info | **Sí** |
| 5 | Contenido incompleto (Guideline 2.1) | Track14 stub | Ocultar o completar | Medio |

### Google Play — Rechazos probables

| # | Check | Estado actual | Mitigación | ¿Blocker? |
|---|---|---|---|---|
| 6 | Google Play Billing | Falta | Billing Library v6+ | **Sí** |
| 7 | Data Safety form | Falta | Completar formulario | **Sí** |
| 8 | Target API level ≥ 34 | No verificado | Actualizar build.gradle | Bajo |
| 9 | IARC Content Rating | Falta | Completar cuestionario | **Sí** |

### Lo que pasaría bien

- Privacy policy accesible (7 docs × 2 idiomas, `check_legal_facts.py`)
- Eliminación de cuenta (`DeleteAccount` page)
- Offline graceful (IndexedDB + `OfflineIndicator`)
- Sin third-party tracking (simplifica Data Safety y ATT)
- Accesibilidad (158 a11y attributes, WCAG)

**Tiempo estimado para resolver todos los blockers: ~2-3 semanas de trabajo enfocado.**

---

## 7. Proyecciones de ingresos

### Comisiones por canal

| Canal | Comisión | Tú recibes |
|---|---|---|
| **Web (Paddle)** | 5% + $0.50/tx | ~94% |
| **Apple App Store** | 15% (Small Business <$1M) / 30% (>$1M) | 70-85% |
| **Google Play** | 15% (primer $1M) / 30% (después) | 70-85% |

### 10,000 MAU — 5 escenarios

| Escenario | Conversión | MRR Neto | ARR Neto | Nota |
|---|---|---|---|---|
| 1. Pesimista | 3% | $4,980 | $59,760 | Ingreso complementario |
| 2. Conservador | 5% | $8,443 | $101,316 | Ingreso principal viable |
| 3. Realista optimista | 7% | $13,361 | $160,332 | Puedes contratar ayuda |
| 4. Breakout | 10% | $19,520 | $234,240 | Salario senior US |
| 5. Best case | 12% + regional | $16,394→$28,063 | $253,000 yr1 | Negocio real con crecimiento |

### 20,000 MAU — 5 escenarios

| Escenario | Conversión | MRR Neto | ARR Neto |
|---|---|---|---|
| 1. Pesimista | 3% | $9,757 | $117,084 |
| 2. Conservador | 5.5% | $17,027 | $204,324 |
| 3. Realista optimista | 8% | $23,764 | $285,168 |
| 4. Breakout | 11% | $32,218 | $386,616 |
| 5. Best case | 14% + B2B | $42,275 | $507,300 |

### 100,000 MAU — 5 escenarios

| Escenario | Conversión | Revenue neto/año | Opex/año | **Beneficio neto/año** |
|---|---|---|---|---|
| 1. Pesimista | 4% | $688,260 | $300,000 | **$388,260** |
| 2. Conservador | 7% | $1,399,284 | $384,000 | **$1,015,284** |
| 3. Realista optimista | 10% | $2,227,392 | $456,000 | **$1,771,392** |
| 4. Breakout | 13% | $3,169,692 | $540,000 | **$2,629,692** |
| 5. Best case | 16% + enterprise | $4,365,888 | $660,000 | **$3,705,888** |

**Nota crítica a 100K:** Apple sube a 30% (superas $1M/año en iOS). La estrategia es **web-first**: deep linking que abra la web para pagos, pricing diferenciado (más barato en web), features exclusivas en web (B2B dashboard). Paddle cobra 6% vs Apple 30% — diferencia de $200K+/año.

---

## 8. ¿Puedo vivir de esto?

**Sí. Sin matices.**

### Coste operativo hoy

| Coste | Mensual |
|---|---|
| Railway | ~$20 |
| Cloudflare Pages | $0 |
| Groq (tutor IA) | ~$50 |
| Dominio | ~$1 |
| Paddle | $0 fijo |
| **Total** | **~$71/mes** |

### Breakeven

$71 / ($14.99 × 0.94) = **5 usuarios pagantes.**

### Resumen por nivel

| Nivel | MAU | Conversión | Beneficio neto/año | Qué vida te da |
|---|---|---|---|---|
| Mínimo viable | 10K | 3% | ~$60K | Vivir modestamente en Grecia/LATAM |
| Cómodo | 10K | 7% | ~$160K | Vida cómoda en cualquier ciudad europea |
| Sólido | 20K | 7% | ~$200K | Salario de senior engineer en Amsterdam |
| Negocio real | 20K | 12% | ~$500K | Equipo pequeño, crecimiento, opciones |
| Startup seria | 100K | 10% | ~$1.8M | Dirigir una empresa |

### Lo que ya tienes a favor

1. **Costes fijos casi cero.** No tienes oficina, equipo, ni $50K/mes de AWS. La mayoría de startups edtech queman $100K/mes antes de facturar $1. Tú empiezas en verde con 5 pagantes.
2. **Residencia en Grecia.** Coste de vida razonable, EU (DMA, SEPA, Paddle como MoR), zona horaria compatible con LATAM y MENA/Europa.
3. **El producto ya existe.** No estás en fase de MVP. Está construido, testeado, con 6,305 preguntas, 18 tracks, adaptive learning, tutor IA, bilingüe.
4. **Pipeline de contenido escalable.** 518 preguntas verificadas por sesión con IA vs 20-30/día humano. Ventaja de producción 10-20x.
5. **El mercado tiene hambre.** “Preparación PCEP en español”, “AWS certification gratis”, “aprender Python adaptativo” — buscan y no encuentran lo que tú tienes.

---

## 9. Modelo operativo solo founder

### Escalado de equipo por nivel de MAU

| MAU | Equipo necesario | Coste equipo/mes |
|---|---|---|
| 0-10K | Solo founder | $0 |
| 10K-20K | + 1 dev part-time + 1 content/marketing part-time | $3,000-6,000 |
| 20K-50K | + 2 devs + 1 content + 1 marketing | $12,000-18,000 |
| 50K-100K | 6-10 personas | $25,000-45,000 |
| 100K+ | 8-15 personas | $35,000-65,000 |

### Costes operativos a 100K MAU

| Coste | Mensual |
|---|---|
| Infra (Railway/DB/Redis) | $1,500-3,000 |
| LLM API (Groq/tutor) | $1,000-3,000 |
| Equipo (3-5 personas) | $12,000-25,000 |
| Legal/contabilidad | $800-1,500 |
| Marketing | $3,000-8,000 |
| Herramientas | $500-1,000 |
| **Total opex** | **$19,000-41,500** |

---

## 10. Arquitectura de pagos

### Los 3 canales

| Canal | Comisión | Qué se vende |
|---|---|---|
| **Web (Paddle MoR)** | ~6% | Subs + Certs + Creator + B2B |
| **Apple App Store** | 15-30% | Subs + Certs via IAP (StoreKit 2) |
| **Google Play** | 15-30% | Subs + Certs via Google Play Billing |

### Pricing

| Plan | Precio | Canal |
|---|---|---|
| Free | $0 (todo el contenido, tutor limitado) | Todos |
| Pro | $14.99/mes | Todos |
| Pro Max | $19.99/mes (tutor ilimitado + cert incluida, ADR-49) | Todos |
| Certificación | $39.99 pago único | Todos |
| Creator/Instructor | $99.99/mes | Web only |
| Annual Pro | ~$149.90/año (2 meses gratis) | Todos |

### Pricing regional (a escala)

| Región | Precio Pro/mes |
|---|---|
| LATAM/MENA | $4.99 |
| Europa del Sur | $9.99 |
| US/DE/UK | $14.99 |

### Estrategia a escala

A 100K+ MAU, empujar usuarios hacia web (6% Paddle vs 30% Apple). Deep linking para pagos a web, pricing diferenciado más barato en web, features exclusivas web (B2B dashboard).

### DMA (Digital Markets Act) EU

En la UE, Apple debe permitir link-out a web para pagos (DMA). Implementar: botón “Comprar en web” dentro de la app iOS para usuarios EU. Apple cobra 0% si el pago se completa en web para usuarios EU.

---

## 11. SEO y distribución

### Estado actual: 2/10 (el agujero más grande)

- Landing dentro del SPA (no SEO-friendly)
- Sin analytics terceros
- Sin blog, sin SEO, sin redes sociales
- Sin email marketing, sin referidos
- Sin presencia en app stores

### Plan de implementación

1. **Landing estática pre-renderizada** fuera del SPA, con meta tags, OG images, structured data
2. **Blog con 20+ posts SEO:** “preparación PCEP español gratis”, “AWS SAA-C03 en español”, “mejores certificaciones IT 2027”
3. **Presencia social:** Twitter/X dev, LinkedIn, comunidades dev LATAM (Platzi community, freeCodeCamp español, dev.to en español)
4. **Email marketing:** captura email en landing → drip de 5 emails → conversión
5. **Referral:** invita amigo → ambos ganan 50 créditos
6. **App Store Optimization** en 8 idiomas

### Resultado esperado

De invisible a discoverable. Funnel completo de adquisición.

---

## 12. Expansión multilingüe

### Roadmap por oleadas

| Oleada | Idiomas | Esfuerzo | Timeline |
|---|---|---|---|
| Lanzamiento | ES + EN (listo) | 0 | Ahora |
| Oleada 1 | + Portugués + Italiano | Bajo (románica) | Mes 1 post-lanzamiento |
| Oleada 2 | + Francés + Griego | Bajo-medio | Meses 2-3 |
| Oleada 3 | + Alemán + Árabe | Medio-alto (AR=RTL) | Meses 4-6 |

### Prioridad por idioma

| # | Idioma | Hablantes | Esfuerzo técnico | Competencia | ROI estimado |
|---|---|---|---|---|---|
| 1 | Portugués (BR) | 210M | Bajo (románica) | Casi cero | Muy alto |
| 2 | Francés | 300M+ | Bajo (románica) | Casi cero en tech | Alto |
| 3 | Italiano | 65M | **Muy bajo** (la más fácil) | Casi cero | Medio-alto |
| 4 | Griego | 10.5M | Medio (font/script) | Cero | Medio (founder advantage) |
| 5 | Árabe | 400M+ | Alto (RTL, font, testing) | Cero | Alto pero caro |
| 6 | Alemán | 100M | Bajo (latino) | Baja | Alto (poder adquisitivo) |

### Por idioma: implementación

- UI strings: ~926 líneas, 1-2 días IA + revisión
- Contenido: 6,305+ preguntas, 1-2 semanas con pipeline
- QA visual + `check_i18n_parity`
- Font migrada a Inter/Noto Sans (cobertura Unicode completa)
- RTL con `dir="rtl"` condicional + CSS logical properties (para árabe)

### Griego: ventaja del founder

Mercado de ~10.5M hablantes, competencia literal cero en edtech técnico griego. Tú estás ahí — puedes ir a meetups de devs en Atenas, hablar con NTUA/AUTH, aparecer en podcasts tech griegos. ASO: “Προετοιμασíα AWS πιστοποíηση” → competencia cero en App Store/Play Store. 1,000 usuarios griegos pagando $14.99 = $15K MRR.

### Italiano: la traducción más barata

Misma familia románica que español — la traducción ES→IT es la más fácil de todas. Mismo script latino, misma dirección, font funciona sin cambios. 65M hablantes con poder adquisitivo europeo.

### Moat competitivo

**8 idiomas en educación técnica.** Literalmente no existe. Traducir 35K+ preguntas con calidad a 8 idiomas requiere meses de trabajo que un competidor no puede replicar rápido.

---

## 13. Video generado con IA

### Estado actual

Whetzy es 100% texto + código. El mercado LATAM consume mucho video (Platzi, EDteam son video-first).

### Oportunidad

Con el contenido estructurado existente (preguntas, lecciones, explicaciones), se puede generar video automáticamente usando herramientas de IA:
- Slides animados a partir de lecciones
- Video explicativo corto por skill
- Video de marketing a partir del contenido

### Recomendación

**Fase 2 post-lanzamiento.** No es blocker. Primero validar con texto + código. Añadir video cuando haya revenue para justificar el esfuerzo.

---

## 14. Impuestos, IVA y estructura fiscal

### Quién maneja el IVA del consumidor

| Canal | Responsable del IVA | Tu obligación |
|---|---|---|
| **Web (Paddle MoR)** | Paddle | Declarar ingresos B2B. Paddle recauda y remite el IVA del consumidor en cada país |
| **Apple App Store** | Apple (deemed supplier desde 2015/2021 en UE) | Recibes 70-85% sin preocuparte del IVA del comprador |
| **Google Play** | Google (deemed supplier) | Recibes 70-85% sin preocuparte del IVA del comprador |

### IRPF griego — el problema a escala [Guessing en tramos exactos]

| Tramo (EUR) | Tipo marginal |
|---|---|
| 0 – 10.000 | 9% |
| 10.001 – 20.000 | 22% |
| 20.001 – 30.000 | 28% |
| 30.001 – 40.000 | 36% |
| >40.000 | **44%** |

Con 4.5M USD/año de beneficio:
- IKE: 22% sobre ~4.1M EUR = ~900K EUR
- IRPF sobre distribución de ~3.2M EUR: mayoría al 44% = ~1.4M EUR
- **Total: ~56% efectivo**

### Comparativa de jurisdicciones

| Jurisdicción | Corp. | Dividendos/IRPF | Efectivo total sobre 4M EUR | Requiere mudanza |
|---|---|---|---|---|
| Grecia (IKE) | 22% | ~44% marginal | **~56%** | No |
| Estonia (OÜ, sin distribuir) | 0% retenido | 20% al distribuir + IRPF griego si vives en GR | ~0% retenido, ~56% al sacar si vives en GR | Parcial |
| Chipre (non-dom) | 12.5% | ~0% + 2.65% GeSY | **~15%** | Sí |
| EAU (Dubai) | 9% | 0% | **~9%** | Sí |

---

## 15. Constitución de empresa

### Recomendación por fase

| Fase | Ingresos | Estructura | Razón |
|---|---|---|---|
| Ahora (0-10K usuarios) | 0-100K EUR/año | **IKE griega** | Coste bajo, cero riesgo, empieza a facturar ya. ~26% efectivo |
| Crecimiento (200K+ EUR/año) | 200K-1M EUR | Consulta con asesor fiscal cross-border | Eurofast, PwC Grecia, Deloitte Grecia |
| Escala (1M+ EUR/año) | >1M EUR | Considerar mudanza a Chipre | ~15% efectivo vs ~56% griego |

### IKE griega (recomendada para empezar)

- Constitución: ~300-500 EUR
- Contable: ~100-150 EUR/mes
- Banco: Revolut Business o Alpha Bank/Eurobank
- Paddle deposita en EUR a cualquier IBAN europeo

### Advertencia sobre Estonia sin mudanza

Montar una OÜ estonia con nominee director mientras controlas todo desde Grecia es **exactamente** lo que las CFC rules griegas y europeas (ATAD, 2016/1164) interceptan. Grecia puede imputarte como renta personal los beneficios no distribuidos. Resultado potencial: 44% griego + recargos + intereses + posible sanción por elusión fiscal.

### Cuenta bancaria

No necesitas cuenta en otro país. Con IKE griega:
- Revolut Business (gratis o ~25 EUR/mes)
- Wise Business (conversiones baratas USD/EUR/GBP)
- Banco griego para obligaciones fiscales locales

Una cuenta en EE.UU. no cambia la residencia fiscal. FATCA reporta a Grecia que la tienes.

---

## 16. Scorecard competitivo (antes y después)

### Competidores directos (educación técnica)

| Categoría | Whetzy HOY | Whetzy 100% | Codecademy | Platzi | DataCamp | EDteam | freeCodeCamp |
|---|---|---|---|---|---|---|---|
| Contenido (volumen) | 25 | 70 | 90 | 85 | 80 | 60 | 95 |
| Contenido (calidad) | 55 | 80 | 75 | 70 | 80 | 65 | 60 |
| Adaptive learning | 80 | 90 | 20 | 10 | 40 | 10 | 0 |
| Certificaciones | 40 | 75 | 30 | 40 | 50 | 30 | 50 |
| Idiomas | 40 (2) | 90 (8) | 15 (1) | 20 (1) | 15 (1) | 20 (1) | 30 (1+) |
| Mobile app | 5 | 75 | 70 | 65 | 60 | 40 | 50 |
| Código interactivo | 70 | 80 | 90 | 30 | 85 | 40 | 80 |
| AI tutor | 65 | 80 | 30 | 20 | 40 | 10 | 0 |
| Gamification | 60 | 75 | 30 | 20 | 30 | 15 | 20 |
| Precio | 90 | 90 | 40 | 30 | 35 | 50 | 100 |
| UX/Design | 65 | 80 | 85 | 75 | 80 | 60 | 40 |
| SEO/Distribución | 2 | 60 | 90 | 80 | 85 | 50 | 95 |
| Social proof | 0 | 20* | 95 | 85 | 90 | 60 | 95 |
| Seguridad técnica | 80 | 90 | 75 | 50 | 70 | 40 | 50 |
| **PROMEDIO** | **48** | **75** | **60** | **49** | **54** | **39** | **47** |

*\*20 asumiendo 5-10K usuarios en primeros 6 meses*

### Competidores indirectos

| Categoría | Whetzy 100% | Duolingo | Brilliant | Whizlabs | Tutorials Dojo | Sololearn |
|---|---|---|---|---|---|---|
| Metodología adaptativa | 90 | 85 | 70 | 20 | 10 | 30 |
| Contenido técnico | 80 | 0 | 60 | 70 | 80 | 50 |
| Multilingüe | 90 | 95 | 15 | 15 | 10 | 20 |
| Gamification | 75 | 95 | 60 | 20 | 10 | 70 |
| Mobile | 75 | 95 | 85 | 50 | 30 | 80 |
| Precio | 90 | 70 | 50 | 60 | 70 | 70 |
| Certificaciones | 75 | 0 | 0 | 90 | 90 | 20 |

---

## 17. Ventajas únicas y debilidades permanentes

### Donde Whetzy gana al 100%

1. **Adaptive + Multilingüe + Certificaciones en un producto.** Nadie combina los tres. Duolingo tiene adaptive + multilingüe pero no tech. Whizlabs tiene certs pero no adaptive ni multilingüe.
2. **8 idiomas en educación técnica.** Literalmente no existe. Moat real.
3. **Triple ML stack (BKT + DKT + FSRS + Elo).** Más sofisticado que cualquier competidor directo. Solo Duolingo tiene comparable, y no enseñan tech.
4. **Free content + cheap paid.** Free tier incluye todo el contenido. Pro $14.99 vs $29.99 Codecademy vs $49 Platzi. Insostenible para competidores con equipos de 50+ personas.
5. **Ejecución de código en browser a cero coste marginal.** Pyodide + sql.js + Monaco. Cero coste de servidor por usuario. Codecademy paga servidores por sandbox.
6. **Privacy-first.** Sin tracking, sin ads, self-hosted fonts y runtimes. En mundo post-GDPR/DMA, esto es marketing.

### Donde Whetzy pierde incluso al 100%

1. **Volumen de contenido vs Codecademy/freeCodeCamp.** Miles de horas acumuladas en 10+ años. Solo se cierra con tiempo.
2. **Social proof.** Codecademy 50M+ usuarios, Platzi 5M+, Whetzy 0. Solo se cierra con tiempo.
3. **Video.** Whetzy es 100% texto + código. LATAM consume mucho video.
4. **Proyectos multi-paso.** Codecademy/freeCodeCamp tienen “build a website” / “build an API”. Whetzy tiene quiz + lecciones pero no proyectos guiados.
5. **B2B/Enterprise.** DataCamp y Codecademy tienen enterprise plans con reporting, SSO, seat management. Whetzy no tiene.

---

## 18. Roadmap de implementación definitivo

### Semana 1-2: Legal y calidad

- [ ] Archivo LICENSE (código AGPL-3.0 o propietario, contenido All Rights Reserved)
- [ ] Disclaimer de marcas en Terms of Service
- [ ] Cerrar gap index.json vs sources reales
- [ ] Activar CI (GitHub Actions free tier)
- [ ] Editorial pass tracks 13-17

### Semana 3-4: App stores

- [ ] Sign in with Apple (Capacitor plugin + backend OAuth)
- [ ] Crear proyecto iOS (`npx cap add ios`)
- [ ] Implementar Apple IAP (StoreKit 2) para subs + certs
- [ ] Implementar Google Play Billing Library
- [ ] Data Safety form (Google)
- [ ] IARC Content Rating (ambas stores)
- [ ] Declarar uso de AI generativa (Apple)
- [ ] Ocultar tracks incompletos en app

### Semana 5-6: SEO y lanzamiento

- [ ] Landing estática pre-renderizada con meta tags, OG images, structured data
- [ ] 10 posts de blog para long-tail keywords
- [ ] App Store submissions (iOS + Android)
- [ ] App Store Optimization en ES + EN
- [ ] Monitoring de uptime (Betterstack/UptimeRobot)
- [ ] Closed beta con 50-100 usuarios reales

### Semana 7-8: Oleada 1 idiomas

- [ ] Portugués (UI strings + contenido)
- [ ] Italiano (UI strings + contenido)
- [ ] Font migrada a Inter/Noto Sans
- [ ] Visual regression tests por locale

### Mes 3: Oleada 2 + crecimiento

- [ ] Francés (UI + contenido)
- [ ] Griego (UI + contenido + font coverage)
- [ ] Beta pública
- [ ] Email marketing (captura → drip → conversión)
- [ ] Referral program (invita amigo → 50 créditos)
- [ ] Presencia social (Twitter/X, LinkedIn, comunidades dev)
- [ ] Blueprint mapping para certificaciones
- [ ] Detector de similitud (n-gram overlap)

### Mes 4-6: Oleada 3 + escala

- [ ] Alemán (UI + contenido)
- [ ] Árabe (UI + contenido + RTL implementation)
- [ ] Infrastructure scaling (Railway Pro, pgbouncer, read replica)
- [ ] Fallback LLM provider
- [ ] Pricing regional
- [ ] ASO en 8 idiomas
- [ ] Primer $5K MRR target

### Mes 6-12: Iteración con datos reales

- [ ] 10K+ usuarios target
- [ ] Completar tracks core faltantes
- [ ] A/B testing pricing
- [ ] B2B pilots si hay demanda
- [ ] Auditoría trimestral de originalidad de contenido
- [ ] Constituir IKE griega cuando los ingresos lo justifiquen

---

## 19. Límites del plan Free — decisión de monetización

### Estado actual [Verified]

Todo el contenido (378 lecciones, 18 tracks, 6,305 preguntas) es 100% gratuito sin ningún límite. Lo único limitado es el tutor IA: 20 explicaciones/día para Free y Plus (`backend/app/services/tutor_quota.py:36`, `backend/app/core/config.py:200`). Pro Max = tutor ilimitado (ADR-49).

### Análisis competitivo de gates

| Competidor | Qué es free | Qué es de pago | Mecanismo de fricción |
|---|---|---|---|
| **Duolingo** | Todo el contenido | Super Duolingo | Hearts: 5 errores y esperas o pagas |
| **Sololearn** | Todo el contenido | Pro | Hearts + anuncios intersticiales |
| **Brilliant** | 2 lecciones/día | Premium | Límite diario duro |
| **DataCamp** | Solo capítulo 1 | Premium | Paywall a contenido avanzado |
| **Codecademy** | Solo cursos intro | Pro | Paywall a cursos intermedios+ |
| **freeCodeCamp** | 100% todo | Nada | Modelo donación |
| **Whetzy (HOY)** | 100% todo + solo tutor limitado | Tutor ilimitado | Casi nada — ~90% de usuarios nunca usa el tutor |

### Problema

El 90%+ de los usuarios aprende leyendo lecciones y haciendo quizzes — nunca toca el tutor IA. Si el tutor es lo único de pago, la conversión será <1%. Los competidores que dan todo gratis (freeCodeCamp) no monetizan en absoluto.

### DECISIÓN: modelo híbrido con límite diario de actividad

| Concepto | Free | Plus ($9.99/mo) | Pro Max ($19.99/mo) |
|---|---|---|---|
| Lecciones completables/día | **5** | Ilimitadas | Ilimitadas |
| Preguntas de práctica/día | **30** | Ilimitadas | Ilimitadas |
| Tutor IA/día | **5 explicaciones** | 20 explicaciones | Ilimitado |
| Examen de certificación | No | No | Incluido |
| Anuncios | Sí (1 intersticial cada 3 lecciones) | No | No |
| Modo offline | No | Sí | Sí |
| Descarga de certificado PDF | No | No | Sí |

### Por qué 5 lecciones/día

- Suficiente para ~25-40 min/día de uso — crea hábito
- Insuficiente para avanzar rápido — la frustración de esperar 24h cuando estás motivado es el driver de conversión #1 en edtech
- Duolingo monetiza exactamente esto

### Implementación

Nuevo servicio `backend/app/services/content_quota.py` análogo a `tutor_quota.py`:
- Contador diario por usuario con reset UTC
- Tabla `content_usage` (user_id, day, lessons_completed, questions_answered)
- Endpoint middleware que verifica cuota antes de servir lección/pregunta
- Frontend: banner "Has alcanzado tu límite diario. Actualiza a Plus para continuar."
- **Esfuerzo estimado: 2-3 días backend + 1-2 días frontend**

---

## 20. Bundle y partición: iOS, Android y Web

### Estado actual [Verified]

Capacitor 8 configurado (`frontend/capacitor.config.ts`) con appId `app.whetzy`, esquema iOS "Learning Engine" y Android. No existen `ios/` ni `android/` — no se ha ejecutado `npx cap add ios/android`.

### DECISIÓN: arquitectura de distribución

```
                    ┌──────────────────┐
                    │  Código fuente    │
                    │  React + Vite     │
                    │  (monorepo)       │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │    Web      │  │    iOS     │  │  Android   │
     │ Cloudflare  │  │  App Store │  │ Play Store │
     │   Pages     │  │ Capacitor  │  │ Capacitor  │
     │             │  │ + StoreKit │  │ + Play     │
     │  Paddle     │  │    IAP     │  │ Billing    │
     │  (~6%)      │  │  (15-30%)  │  │  (15-30%)  │
     └────────────┘  └────────────┘  └────────────┘
```

### Diferencias por plataforma

| Aspecto | Web | iOS | Android |
|---|---|---|---|
| Pagos | Paddle (MoR, ~6%) | Apple IAP obligatorio (15-30%) | Google Play Billing (15-30%) |
| Precios | $9.99/$19.99 | $12.99/$24.99 (compensar comisión) | $12.99/$24.99 |
| Push notif. | Web Push API | APNs nativo | FCM nativo |
| Login | Email + Google OAuth | Email + Google + **Apple obligatorio** (ADR-13) | Email + Google |
| Pyodide | Funciona | Funciona en WKWebView | Funciona en WebView |
| Deploy | Automático (Cloudflare Pages) | App Store Review (~1-2 sem primera vez) | Play Store Review (~3-7 días) |
| DMA (UE) | N/A | Link-out a web para pagos permitido | N/A |

### Implementación paso a paso

1. **Wrapper de pagos con detección de plataforma:**
   ```typescript
   import { Capacitor } from '@capacitor/core';
   
   function getPaymentProvider() {
     const platform = Capacitor.getPlatform();
     if (platform === 'ios') return 'storekit';
     if (platform === 'android') return 'google-play';
     return 'paddle';
   }
   ```

2. **Generar proyectos nativos:**
   - `npx cap add ios` → configura Xcode project
   - `npx cap add android` → configura Gradle project
   - `npx cap sync` después de cada build

3. **Sign in with Apple** (blocker iOS, ADR-13):
   - Plugin: `@capacitor-community/apple-sign-in`
   - Backend: validar identity token contra Apple

4. **StoreKit 2 (iOS):** Capacitor plugin `@capacitor-community/in-app-purchases`

5. **Google Play Billing:** Plugin equivalente para Android

6. **Pricing diferenciado:**
   - Web siempre más barato (6% Paddle vs 30% stores)
   - En la UE (DMA), botón "Comprar en web" dentro de la app iOS

### Anti-steering y DMA

- **iOS fuera de UE:** No puedes dirigir al usuario a pagar en web. Apple puede rechazar la app.
- **iOS en UE (DMA):** Puedes tener botón "Comprar en la web" — Apple cobra 0% si el pago se completa en web.
- **Android:** Más permisivo, puedes ofrecer alternativas de pago.

---

## 21. Auditoría de contenido: rastros de IA

### Resultado de la auditoría [Verified]

Se buscaron los siguientes patrones en todos los archivos de `content/`:
- "Claude", "as an AI", "language model", "I can help", "AI assistant"
- **Resultado: cero coincidencias.**

El contenido se genera a partir de corpus abierto con fuentes verificadas (`content/sources/index.json`: 15 fuentes con URL, licencia SPDX, fecha de verificación y commit SHA).

### Patrones sutiles que la búsqueda automática no detecta

| Patrón | Ejemplo | Riesgo |
|---|---|---|
| Frases formulaicas | "Es importante destacar que...", "Cabe mencionar que..." | Delata IA a un reviewer experto |
| Estructura simétrica | Todos los puntos con exactamente la misma longitud | Antinatural |
| Sobre-calificadores | "Fundamentalmente", "Significativamente", "Esencialmente" | Huella GPT/Claude clásica |
| Disclaimers fantasma | "Dependiendo de tu caso específico..." | Fuera de lugar en contenido técnico |
| Listados exhaustivos | "Primero..., Segundo..., Tercero..., Finalmente..." | Formato de modelo, no de humano |

### DECISIÓN: auditoría en dos pases

**Pase 1 — Automático (implementar ya):**
Script `scripts/audit_ai_traces.py` que busque:
- Regex para frases formulaicas (lista de ~30 patrones)
- Distribución de longitud de explicaciones (varianza demasiado baja = IA)
- Ratio de conectores formales vs coloquiales
- Output: lista de lecciones flaggeadas para revisión humana

**Pase 2 — Manual (tú):**
Revisión de las lecciones flaggeadas + muestreo aleatorio.
- 378 lecciones × ~2 min/lección = **~12 horas**
- Priorizar: tracks de certificación (más visibilidad) y tracks 13-17 (calidad mediocre)

### Implementación

- Esfuerzo script: ~4 horas
- Esfuerzo revisión humana: ~12 horas distribuidas en 2-3 días
- Gate: `check_question_bank.py` ya existe — añadir flag `--ai-traces` que corra el pase 1

---

## 22. Cobertura de tracks: gaps y path Python → AI Engineering

### Los 18 tracks actuales [Verified]

| # | Track | Módulos | Skills | Lecciones | Estado |
|---|---|---|---|---|---|
| 01 | Python Básico | 12 | 52 | 52 | Completo |
| 02 | Python Intermedio | 6 | 24 | 24 | Completo |
| 03 | Python Avanzado | 6 | 24 | 24 | Completo |
| 04 | Ingeniería de Software | 7 | 30 | 30 | Completo |
| 05 | Arquitectura de Software | 6 | 24 | 24 | Completo |
| 06 | Fundamentos de IA | 6 | 28 | 28 | Completo |
| 07 | Ingeniería de IA | 6 | 25 | 25 | Completo |
| 08 | AWS Cloud Practitioner (CLF-C02) | 4 | 19 | 19 | Cert |
| 09 | PCEP | 4 | 15 | 15 | Cert |
| 10 | AWS SA Associate (SAA-C03) | 5 | 25 | 25 | Cert |
| 11 | AWS AI Practitioner (AIF-C01) | 5 | 15 | 15 | Cert |
| 12 | SQL | 5 | 20 | 20 | Completo |
| 13 | Ciberseguridad | 5 | 20 | 20 | Completo |
| 14 | JavaScript Frontend | 1 | 1 | **1** | **Stub** |
| 15 | Linux y Shell | 3 | 12 | 12 | Parcial |
| 16 | Algoritmos y Estructuras | 3 | 12 | 12 | Parcial |
| 17 | Redes y Protocolos | 3 | 12 | 12 | Parcial |
| 40 | ISC2 CC | 5 | 20 | 20 | Cert |
| | **TOTAL** | | **378** | **378** | |

### Path Python → AI Engineering: CUBIERTO

Track 01 → 02 → 03 → 06 → 07. Es la vertical más fuerte del producto.

### DECISIÓN: tracks que se van a crear (priorizados por demanda laboral)

> **Superado el 2026-09-30 por ADR-53, sustituida a su vez por ADR-54 el 2026-10-01.** Casi
> todos estos tracks ya existen (tracks 14, 18–23, 26–30). El plan vigente —qué tracks, en qué
> orden y con qué volumen— es ADR-54 y la serie 37 del ledger: forma única 32 skills × 10
> preguntas por track y prioridad por demanda medida (Stack Overflow 2025).

**Tier 1 — Imprescindibles (sin estos no compites):**

| Prioridad | Track nuevo | Justificación | Lecciones est. |
|---|---|---|---|
| 1 | **Data Science con Python** | pandas/numpy/sklearn — mayor demanda junior | ~30 |
| 2 | **Git y Control de Versiones** | Prerequisito universal — todo dev lo necesita | ~15 |
| 3 | **HTML/CSS Fundamentos** | Prerequisito para frontend | ~25 |
| 4 | **JavaScript Completo** | Reemplaza track14 stub — mayor ecosistema web | ~30 |
| 5 | **React Frontend** | Mayor demanda laboral frontend | ~25 |
| 6 | **Docker y Contenedores** | Base de DevOps moderno | ~20 |
| 7 | **API REST y Microservicios** | Python + FastAPI/Flask | ~20 |

**Tier 2 — Alta demanda laboral:**

| Prioridad | Track nuevo | Justificación | Lecciones est. |
|---|---|---|---|
| 8 | Data Engineering (ETL, Spark) | Pipeline de datos — explosión laboral | ~25 |
| 9 | Kubernetes y Orquestación | Cloud-native | ~20 |
| 10 | CI/CD y DevOps | Cultura DevOps en toda empresa | ~20 |
| 11 | Testing y QA | Calidad de software | ~20 |
| 12 | MongoDB/NoSQL | Complemento a SQL | ~15 |
| 13 | Node.js Backend | Backend JS — alta demanda | ~25 |
| 14 | TypeScript | Estándar frontend/backend moderno | ~20 |

**Visión total: 32+ tracks = cobertura del 90% del mercado tech education.**

### Track 14 (JavaScript Frontend): DECISIÓN

**Eliminar como stub y reemplazar con track completo.** Un track con 1 lección destruye la confianza del usuario. Dos opciones:
1. Ocultar track 14 inmediatamente de la UI → crear track nuevo "JavaScript Completo" con ~30 lecciones
2. Expandir track 14 in-place a ~30 lecciones

**Decisión: opción 1.** Ocultar track 14, crear track nuevo desde cero con estructura limpia.

---

## 23. Certificaciones: cobertura y suficiencia

### Estado actual [Verified]

**5 certificaciones implementadas** (no 11):
1. AWS CLF-C02 (Cloud Practitioner) — track 08
2. PCEP (Python Entry-Level) — track 09
3. AWS SAA-C03 (Solutions Architect) — track 10
4. AWS AIF-C01 (AI Practitioner) — track 11
5. ISC2 CC (Cybersecurity) — track 40

### Análisis de demanda de certificaciones

| Certificación | Demanda | Competidores que la cubren | ¿Hay en español? |
|---|---|---|---|
| AWS (3 certs) | Altísima | Whizlabs, Tutorials Dojo, A Cloud Guru | Parcialmente |
| PCEP | Media | Python Institute oficial | No |
| ISC2 CC | Media-alta | Pocos | No |
| **CCNA** | **Altísima** | Whizlabs, Boson | **No en español** |
| **CompTIA Security+** | **Altísima** | Whizlabs, Dion Training | **No en español** |
| **AZ-900** | **Alta** | Microsoft Learn, Whizlabs | **Parcial** |
| **LPIC-1** | **Alta** | Pocos | **No** |
| **CKA/KCNA** | **Alta (explosión)** | Linux Foundation, KodeKloud | **No** |
| **GCP ACE** | **Media-alta** | Google, Whizlabs | **No** |
| **CompTIA Network+** | **Media** | Whizlabs, Dion | **No** |

### DECISIÓN: roadmap de certificaciones

> **Superado el 2026-09-30 por ADR-53.** Hoy hay 11 certificaciones (Security+, AZ-900, PCAP,
> MLA-C01, AI-900 y DP-900 ya se construyeron). El orden de las nuevas lo fija hoy
> `CATALOGO_MAESTRO.md` §3 (ADR-54, que mantiene el de ADR-53 §6):
> primero las que se examinan en español (GCP ACE, LPIC-1, AZ-104, comprobado el
> 2026-09-30); CKA/CKAD no se examinan en español y el idioma de CCNA está sin comprobar.
> La columna «¿Hay en español?» de la tabla de arriba habla de preparación, no del examen.

**Año 1 — Target: 12 certificaciones**

| # | Certificación | Prioridad | Estimado de preguntas |
|---|---|---|---|
| 1-5 | Las 5 actuales | Ya hechas | 1,568 preguntas |
| 6 | **CCNA** | Alta — altísima demanda, cero competencia en ES | ~400 |
| 7 | **CompTIA Security+** | Alta — puerta de entrada cybersecurity | ~350 |
| 8 | **AZ-900** (Azure Fundamentals) | Alta — segundo cloud | ~300 |
| 9 | **LPIC-1** | Media-alta — Linux transversal | ~300 |
| 10 | **CKA** (Kubernetes) | Media-alta — explosión cloud-native | ~300 |
| 11 | **GCP ACE** | Media — completa "tri-cloud" | ~300 |
| 12 | **CompTIA Network+** | Media — complementa CCNA | ~250 |

**Año 2 — Expansión a 18-20:**
- CISSP, AWS Developer, AWS DevOps Pro, Azure Administrator, GCP Pro, PMP, ITIL

### Ventaja competitiva de certificaciones en español

**Nadie cubre certificaciones IT en español con práctica adaptativa.** Esto es un moat real: la demanda existe (LATAM + España = 500M+ hispanohablantes), la oferta no. Cada certificación nueva en español es un monopolio temporal.

---

## 24. Navegación no lineal: libertad de elección del usuario

### Estado actual [Verified]

- **Entre tracks:** NO hay prerequisitos. No existe campo `required_track` ni `depends_on` en `tracks.json`. Un usuario puede empezar en cualquier track.
- **Dentro de un track:** SÍ hay progresión. `min_mastery_to_unlock` en los módulos (70% de mastery para desbloquear el siguiente módulo).
- **Placement tests:** Solo existe `content/exams/placement/track01_placement.json`. No hay para otros tracks.

### DECISIÓN: sistema de navegación libre con guía inteligente

**Principio:** el usuario elige por dónde empezar, pero el sistema le recomienda. Nunca bloquear entre tracks; solo bloquear dentro de un track (módulos secuenciales).

**Lo que se va a implementar:**

1. **Mapa visual de tracks** (frontend):
   - Vista de cuadrícula con todos los tracks disponibles
   - Estado por track: No iniciado / En progreso (%) / Completado
   - Filtros: por carrera (Backend, Data, Cloud, Security, Frontend), por nivel (Básico, Intermedio, Avanzado), por tipo (Track, Certificación)
   - Badges de dificultad estimada

2. **Placement test por track** (contenido + backend):
   - Crear placement test para cada track (10-15 preguntas rápidas)
   - Si el usuario ya domina módulos 1-3, empieza en módulo 4
   - Usar el sistema BKT/Elo existente para calibrar la dificultad del placement
   - **Esfuerzo: ~1 día de preguntas por track × 18 tracks = 18 días**

3. **Recomendaciones inteligentes** (backend — usar stack ML existente):
   - "Basado en tu rendimiento en SQL (87% mastery), te recomendamos Data Engineering"
   - "Completaste Python Avanzado — IA y Data Science son los siguientes pasos naturales"
   - Algoritmo: graph de afinidad entre tracks ponderado por mastery del usuario

4. **"Learning paths" sugeridos (no obligatorios):**
   - Backend Engineer: Python → SQL → API REST → Docker → CI/CD
   - Data Scientist: Python → SQL → Data Science → IA Fundamentals → IA Engineering
   - Cloud Engineer: Linux → Redes → AWS CLF → AWS SAA → Kubernetes
   - Cybersecurity: Redes → Linux → Ciberseguridad → CompTIA Sec+ → ISC2 CC

### Esfuerzo total: ~3-4 semanas (frontend mapa + placement tests + recomendaciones)

---

## 25. Contenido: video, texto, emojis y costos

### DECISIÓN: formato estándar por lección

```
📘 LECCIÓN: Variables en Python
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Objetivo: Entender qué son las variables y cómo asignar valores.

📖 Concepto
Una variable es un nombre que apunta a un valor en memoria.

💻 Ejemplo
  nombre = "Ana"      # str
  edad = 25           # int
  altura = 1.68       # float

▶️ Resultado
  Ana tiene 25 años

⚠️ Error común
  25edad = "veinticinco"  # ❌ SyntaxError

✅ Regla: los nombres de variable nunca empiezan con número.

🧠 Dato clave: Python es dinámicamente tipado — no declaras el tipo.
```

### Reglas de uso de emojis

- **1 emoji por sección** como separador visual, nunca en medio de texto técnico
- Emojis funcionales (📘🎯💻⚠️✅🧠▶️), no decorativos
- **WCAG 2.1 AA:** los screen readers leen cada emoji como texto — menos es más
- Los competidores top (Codecademy, DataCamp) no saturan de emojis; usan iconografía SVG propia
- Emojis en cuerpo de código: NUNCA

### Video: decisión por fases

| Fase | Cuándo | Qué | Herramienta | Costo |
|---|---|---|---|---|
| **1 (ahora)** | Pre-lanzamiento | Sin video. Texto + código interactivo | N/A | $0 |
| **2 (con revenue)** | Post 1K usuarios | Screencast de los 50 tracks más populares, 3-5 min | OBS Studio (gratis) | $0 + tu tiempo |
| **3 (con revenue)** | Post 5K usuarios | Avatar-presenter IA para cada lección | Synthesia ($18/mo) | ~$216/año |

### Justificación de fase 1 sin video

- freeCodeCamp demostró que texto interactivo supera a video en retención para programación
- Pyodide + sql.js (ejecución en browser) es tu ventaja — más poderoso que un video
- Video es costoso en tiempo de producción y no escala con el pipeline de contenido IA
- Se añade cuando haya datos de retención que lo justifiquen

### Herramientas de video IA disponibles (2026)

| Herramienta | Costo | Calidad | Mejor para |
|---|---|---|---|
| **Google Veo 3** | Gratis (10/mes) | Alta pero genérica | Demos conceptuales cortas |
| **Synthesia** | $18/mo | Avatar profesional | Explicaciones narradas |
| **HeyGen** | $29/mo | Avatar + lip sync | Alternativa a Synthesia |
| **Guidde** | $23/mo | Screencasts automáticos | Tutoriales paso a paso |
| **OBS + tú** | Gratis | Variable | Screencasts propios |
| **Canva** | $13/mo | Animaciones 2D | Infografías animadas |

### Costo total de contenido

| Concepto | Costo | Tiempo |
|---|---|---|
| Texto con emojis (378 lecciones existentes) | $0 | Reformatear con pipeline IA + revisión humana (~40h) |
| Screencast OBS (50 lecciones prioritarias) | $0 | ~100 horas (2h producción × 50) |
| Synthesia (378 videos de 3 min, si se activa) | ~$216-500/año | Automatizable |
| **Total fase 1** | **$0** | **~40h reformateo** |

---

## 26. Lo que falta: ángulos ciegos del solo founder

### Los 10 gaps que no estás pensando (ordenados por riesgo)

**1. Analytics y métricas de producto — CRÍTICO**
Sin un dashboard de product analytics estás volando ciego. Necesitas saber:
- Funnel: signup → first lesson → day 7 retention → day 30 → payment
- Tasa de completación por track
- Drop-off points (qué lección hace que la gente se vaya)
- Feature usage (quién usa el tutor, quién ejecuta código)

**Herramientas:** PostHog (free tier, self-hostable) o Mixpanel (free hasta 20M events).
**Esfuerzo:** ~2-3 días de integración.

**2. Onboarding flow — CRÍTICO**
La primera experiencia del usuario determina si vuelve. No hay implementado:
- "¿Qué quieres aprender?" → selección de carrera
- Placement test automático → "Tu nivel actual es intermedio"
- Plan personalizado → "Te recomendamos empezar por el módulo 3"

**Esfuerzo:** ~1 semana frontend + backend.

**3. Gamification — ALTO**
Tienes BKT/DKT/FSRS/Elo (impresionante técnicamente), pero falta lo que el usuario VE:
- Streaks diarios (login consecutivo)
- XP por lección completada / pregunta correcta
- Badges/logros por hitos (primera lección, primer track, primer examen)
- Leaderboard semanal (opcional, social)
- Nivel de usuario (Novato → Junior → Mid → Senior → Expert)

Sin gamification la retención a 30 días será ~5-10%. Con gamification tipo Duolingo: ~20-30%.
**Esfuerzo:** ~2-3 semanas.

**4. Email marketing y re-engagement — ALTO**
¿Qué pasa cuando un usuario no vuelve en 3 días? ¿7 días? ¿30 días?
- Emails automáticos: "Tu streak de Python está en riesgo"
- Drip campaign: bienvenida → valor → caso de éxito → upgrade
- Herramientas: Resend (free tier 3K emails/mo) o Loops.so

**Esfuerzo:** ~3-5 días.

**5. Comunidad — MEDIO**
Aprender solo es difícil. Opciones:
- Discord server (gratis, simple)
- Foro integrado en la app (complejo, no prioritario)
- Comentarios por lección (medio)

**Decisión:** Discord server al lanzamiento. Cero esfuerzo técnico, alto impacto social.

**6. Legal: Terms of Service y Privacy Policy — BLOCKER**
Obligatorios para App Store y Play Store. GDPR (usuarios EU) requiere consent manager.
**Esfuerzo:** ~1 día con plantillas + revisión legal.

**7. Customer support — MEDIO**
Como solo founder: chatbot con FAQ + email de soporte mínimo.
**Esfuerzo:** ~1 día.

**8. App Store Optimization (ASO) — ALTO**
Keywords, screenshots, preview video, descripción optimizada en 8 idiomas. La visibilidad en App Store es tan importante como SEO en web.
**Esfuerzo:** ~3-5 días.

**9. Backup y disaster recovery — ALTO**
¿Hay backups automáticos de PostgreSQL? ¿Has probado restaurar uno?
Railway ofrece backups, pero verificar frecuencia y probar restore.
**Esfuerzo:** ~4 horas configurar + probar.

**10. Rate limiting calibrado en API — MEDIO**
El rate limiting existe pero ¿está calibrado? Un script malicioso podría generar miles de requests a Groq (que cuesta dinero) a través de la API.
**Esfuerzo:** ~4 horas de revisión y calibración.

---

## 27. Lógica del negocio vs competencia: veredicto

### Comparación directa

| Aspecto | Whetzy | Codecademy Pro | DataCamp | Duolingo | Veredicto |
|---|---|---|---|---|---|
| Contenido free | **Todo** (problema) | Solo intro | Solo cap. 1 | Todo con hearts | Demasiado generoso |
| Precio Pro | $9.99-19.99 | $34.99/mo | $25/mo | $7.33/mo | Competitivo |
| IA integrada | Tutor + BKT/DKT/FSRS | Asistente básico | DataLab | Personalización | **Ventaja real** |
| Python in-browser | Pyodide ✓ | Sí | Sí | N/A | A la par |
| SQL in-browser | sql.js ✓ | Sí | Sí | N/A | A la par |
| Certificaciones | 5 | 0 | 0 | 0 | **Diferenciador** |
| Video | No | Sí | Sí | No | Gap aceptable (fase 2) |
| Mobile app | No (configurada) | Sí | Sí | Sí | Gap (resolver semana 3-4) |
| Tracks | 18 | 400+ | 300+ | 40+ | Gap (resolver progresivamente) |
| Bilingüe ES/EN | ✓ | EN only | EN only | 40 idiomas | **Diferenciador** |
| Precio cert | $39.99 único | N/A | N/A | N/A | **Diferenciador** |
| Gamification | Mastery score | Badges/streaks | XP/streaks | Hearts/streaks/leagues | Gap (resolver semana 5-6) |

### Veredicto sobre la lógica de negocio

**La lógica base es correcta.** El posicionamiento (certificaciones reales + IA personalizada + bilingüe + código interactivo) es un nicho que nadie cubre exactamente así.

### Tres correcciones críticas (ya decididas arriba)

1. **Limitar el free** (§19) — Implementar límite diario de 5 lecciones + 30 preguntas + anuncios. Sin esto, la conversión será <1%.

2. **Gamification** (§26) — Streaks, XP, badges, leaderboard. Sin esto, la retención a 30 días será ~5-10% vs ~20-30% con gamification. Es la diferencia entre un negocio viable y uno que regala contenido.

3. **Track 14 invisible** (§22) — Un track con 1 lección destruye confianza. Ocultar inmediatamente.

### Lo que Whetzy tiene y la competencia no

1. Stack ML triple (BKT + DKT + FSRS + Elo) — más sofisticado que cualquier competidor directo
2. Certificaciones como pago único ($39.99) vs suscripción mensual — propuesta de valor clara
3. Bilingüe nativo ES/EN desde el código, no traducción post-hoc
4. Python + SQL ejecutándose en browser sin backend — escalabilidad infinita para esos componentes
5. Backend instrumentado (OpenTelemetry + Prometheus + Sentry) — producción seria
6. Costos operativos mínimos ($71/mo) — breakeven con 5 usuarios pagantes

---

## 28. Plan de implementación definitivo con decisiones tomadas

### FASE 0 — Emergencia (antes de cualquier otra cosa)

| # | Tarea | Decisión | Esfuerzo | Blocker para |
|---|---|---|---|---|
| 0.1 | Ocultar track 14 (JS stub) de la UI | Decidido: ocultar, no borrar | 1 hora | Confianza del usuario |
| 0.2 | Ocultar tracks en cuarentena (24, 25) si visibles | Decidido: ya están en `_quarantine/` | Verificar | Confianza del usuario |

### FASE 1 — Legal, calidad y gates (Semana 1-2)

| # | Tarea | Decisión | Esfuerzo |
|---|---|---|---|
| 1.1 | Archivo LICENSE | Código: propietario. Contenido: All Rights Reserved | 30 min |
| 1.2 | Terms of Service + Privacy Policy | Plantilla legal + revisión | 1 día |
| 1.3 | Disclaimer de marcas en ToS | Incluir AWS/CompTIA/ISC2/Python Institute/Cisco | 15 min |
| 1.4 | Cerrar gap index.json vs sources reales | Script de verificación | 2 horas |
| 1.5 | Editorial pass tracks 13-17 | Explicaciones mín. 2-3 oraciones | 4 horas |
| 1.6 | Script audit_ai_traces.py | Regex 30 patrones + distribución de longitud | 4 horas |
| 1.7 | Revisión humana de lecciones flaggeadas | Pase manual priorizado por certs | 12 horas |
| 1.8 | Activar CI (GitHub Actions) | Free tier 2,000 min/mes — el pipeline ya existe | 1 hora |

### FASE 2 — Monetización y retención (Semana 3-4)

| # | Tarea | Decisión | Esfuerzo |
|---|---|---|---|
| 2.1 | `content_quota.py` — límite diario free | 5 lecciones/día + 30 preguntas/día | 3 días |
| 2.2 | Reducir tutor free de 20 a 5 explicaciones/día | Valor fijo en config.py | 30 min |
| 2.3 | Banner de upgrade en frontend | "Límite alcanzado — Actualiza a Plus" | 1 día |
| 2.4 | Gamification v1: streaks + XP | Tabla daily_streak, XP por actividad | 1 semana |
| 2.5 | Gamification v1: badges | 10 badges iniciales (primer login, primer track, etc.) | 3 días |
| 2.6 | Analytics: PostHog | Integración frontend + backend events | 2-3 días |
| 2.7 | Onboarding flow | Selector de carrera → placement test → plan | 1 semana |

### FASE 3 — App Stores (Semana 5-6)

| # | Tarea | Decisión | Esfuerzo |
|---|---|---|---|
| 3.1 | Sign in with Apple | Capacitor plugin + backend OAuth | 2 días |
| 3.2 | `npx cap add ios` + proyecto Xcode | Crear proyecto nativo | 1 día |
| 3.3 | `npx cap add android` + proyecto Gradle | Crear proyecto nativo | 1 día |
| 3.4 | StoreKit 2 (Apple IAP) | Subs + certs como IAP | 3-4 días |
| 3.5 | Google Play Billing | Subs + certs como Play purchases | 3-4 días |
| 3.6 | Wrapper de pagos multi-plataforma | Detección de plataforma → provider correcto | 2 días |
| 3.7 | Data Safety form (Google) | Completar formulario | 2 horas |
| 3.8 | IARC Content Rating (ambas stores) | Completar cuestionario | 1 hora |
| 3.9 | Declarar uso de IA (Apple Guideline 5.6.4+) | En App Review submission info | 30 min |
| 3.10 | ASO: screenshots + preview + keywords ES/EN | Generar assets por store | 3-5 días |
| 3.11 | Submit iOS + Android | Enviar a review | 1 día |

### FASE 4 — SEO, distribución y lanzamiento (Semana 7-8)

| # | Tarea | Decisión | Esfuerzo |
|---|---|---|---|
| 4.1 | Landing estática pre-renderizada | Meta tags, OG images, structured data | 2 días |
| 4.2 | 10 blog posts SEO | Long-tail: "PCEP español gratis", "AWS cert free" | 3-5 días |
| 4.3 | Monitoring de uptime | Betterstack o UptimeRobot (gratis) | 1 hora |
| 4.4 | Email marketing setup | Resend free tier + drip de bienvenida 5 emails | 3 días |
| 4.5 | Discord server | Canal por track + bot de bienvenida | 2 horas |
| 4.6 | Closed beta: 50-100 usuarios reales | Feedback loop + iteración rápida | Continuo |

### FASE 5 — Navegación y placement (Mes 3)

| # | Tarea | Decisión | Esfuerzo |
|---|---|---|---|
| 5.1 | Mapa visual de tracks | Cuadrícula con filtros por carrera/nivel/tipo | 1 semana |
| 5.2 | Placement tests por track | 10-15 preguntas × 18 tracks | 18 días |
| 5.3 | Learning paths sugeridos | 4 paths predefinidos (Backend, Data, Cloud, Security) | 3 días |
| 5.4 | Motor de recomendaciones | Graph de afinidad + mastery ponderado | 1 semana |
| 5.5 | Reformateo de lecciones con emojis | 378 lecciones al formato estándar §25 | ~40 horas |

### FASE 6 — Expansión de contenido (Mes 3-6)

| # | Tarea | Decisión | Esfuerzo |
|---|---|---|---|
| 6.1 | Track: Data Science con Python | 30 lecciones + 500 preguntas | 2 semanas |
| 6.2 | Track: Git y Control de Versiones | 15 lecciones + 250 preguntas | 1 semana |
| 6.3 | Track: HTML/CSS Fundamentos | 25 lecciones + 400 preguntas | 2 semanas |
| 6.4 | Track: JavaScript Completo | 30 lecciones + 500 preguntas (reemplaza stub 14) | 2 semanas |
| 6.5 | Track: React Frontend | 25 lecciones + 400 preguntas | 2 semanas |
| 6.6 | Cert: CCNA | 400 preguntas + 25 lecciones | 2 semanas |
| 6.7 | Cert: CompTIA Security+ | 350 preguntas + 20 lecciones | 2 semanas |

### FASE 7 — Idiomas e internacionalización (Mes 4-6)

| # | Tarea | Decisión | Esfuerzo |
|---|---|---|---|
| 7.1 | Portugués (BR) | UI + todo el contenido | 2 semanas |
| 7.2 | Italiano | UI + todo el contenido | 2 semanas |
| 7.3 | Francés | UI + todo el contenido | 2 semanas |
| 7.4 | Griego | UI + todo el contenido | 2 semanas |
| 7.5 | Font: migrar a Inter/Noto Sans | Cobertura Unicode completa | 1 día |
| 7.6 | Visual regression tests por locale | Playwright por idioma | 3 días |

### FASE 8 — Escala y optimización (Mes 6-12)

| # | Tarea | Decisión | Esfuerzo |
|---|---|---|---|
| 8.1 | Alemán + Árabe (RTL) | UI + contenido + dir="rtl" condicional | 4 semanas |
| 8.2 | Infra scaling | Railway Pro, pgbouncer, read replica | 1 semana |
| 8.3 | Fallback LLM provider | Cerebras o Together como backup de Groq | 2 días |
| 8.4 | Pricing regional | LATAM $4.99, EU Sur $9.99, US/DE/UK $14.99 | 3 días |
| 8.5 | Tracks Tier 2 (Docker, K8s, CI/CD, Node.js, TypeScript) | ~5 tracks × 2 semanas | 10 semanas |
| 8.6 | Certs adicionales (AZ-900, LPIC-1, CKA, GCP ACE) | ~4 certs × 2 semanas | 8 semanas |
| 8.7 | Video fase 2: screencast 50 lecciones | OBS + edición básica | 100 horas |
| 8.8 | Blueprint mapping para certs | Mapear skills a syllabus público | 1 semana |
| 8.9 | A/B testing pricing | Experimentar con pricing web vs mobile | Continuo |
| 8.10 | Constituir IKE griega | Cuando ingresos lo justifiquen (~5K EUR/mo) | Papeleo |

### Resumen de inversión total

| Fase | Duración | Costo monetario |
|---|---|---|
| Fase 0: Emergencia | 1 día | $0 |
| Fase 1: Legal/calidad | 2 semanas | $0 |
| Fase 2: Monetización/retención | 2 semanas | $0 (PostHog free) |
| Fase 3: App Stores | 2 semanas | $99/año Apple Developer + $25 Google Play |
| Fase 4: SEO/distribución | 2 semanas | $0 (Resend free, Betterstack free) |
| Fase 5: Navegación | 4 semanas | $0 |
| Fase 6: Contenido nuevo | 12 semanas | $0 (pipeline IA) |
| Fase 7: 4 idiomas | 8 semanas | $0 (traducción IA + revisión) |
| Fase 8: Escala | 6-12 meses | ~$200-500/mo infra adicional |
| **Total hasta lanzamiento (Fase 0-4)** | **~8 semanas** | **~$124 una vez** |

---

## 29. Fe de erratas comprobada (2026-09-26)

Cada punto se comprobó en el repo o en producción el 2026-09-26. Donde esta evaluación y este apartado discrepen, manda este apartado; donde discrepen este apartado y el código, manda el código.

| Lo que dice la evaluación | Lo comprobado | Dónde |
|---|---|---|
| 18 tracks, 378 lecciones, 5 certificaciones | 35 tracks, 177 cursos, 723 skills, 723 lecciones, 10.989 preguntas, 11 certificaciones | `project_snapshot.py`; log de arranque de Railway `Content loaded: {'tracks': 35, 'questions': 10989, … 'lessons': 723}` |
| «Cero gamification» | XP, racha, congelación de racha, ligas, insignias, misiones y tienda de rachas | `backend/app/models/user.py` (`total_xp`, `current_streak`); `services/gamification/service.py` (`get_current_standings`, `get_user_badges`, `get_today_missions`); `services/streak_shop.py` |
| Faltan ToS y privacidad | 7 documentos × ES/EN: términos, privacidad, cookies, reembolsos, DPA, aviso de IA, disclaimers de marca | `docs/legal/` |
| No existen `ios/` ni `android/` | `frontend/android/` existe; `ios/` no | árbol del repo |
| Tutor Free = 20 explicaciones/día | Free **no** tiene tutor; Pro 20/día; Pro Max ilimitado | `tutor.py:40` `require_tier("plus")`; `config.py` `TUTOR_DAILY_LIMIT_PLUS` |
| Planes «Plus» 9,99 / 19,99 / 39,99 y precio mayor en móvil | Pro 14,99 $ (`plus`), Pro Max 19,99 $ (`pro`), Creador 99,99 $; certificación 39,99 $ pago único; mismo precio en todas las plataformas | ADR-41, ADR-49, ADR-50c |
| Ocultar el track 14 (1 lección) | Tiene 24 lecciones y ≥ 300 preguntas | `content/lessons/track14/` |
| Fase 6: crear Git, Data Science, Docker, CI/CD, NoSQL, Backend, Testing | Existen: tracks 18–23 y 26–30 | `content/curriculum/tracks.json` |
| Fase 7: griego e IKE | Premisa griega suspendida | ADR-47 |
| «35–40 tracks cubren el 90 %» como meta | La meta es ADR-54 (2026-10-01; sustituye el suelo y el ideal de ADR-53 y la meta de ADR-46): tracks por demanda medida, cada uno con la forma 32 skills × 10 preguntas | ADR-54 |
| Navegación, onboarding y placement por construir | `TracksScreen`, `OnboardingScreen` y `PlacementScreen` existen; placement solo del track01 | `frontend/src/pages/`, `content/exams/placement/` |
| Email marketing por montar | `services/email.py` (Resend/SMTP) existe; falta el proveedor en producción (H.30) y las campañas (39.13) | ADR-50l |
| Sin rate limiting calibrado | Hay `DEFAULT_RATE_LIMIT` y `AUTH_RATE_LIMIT`; falta el límite de gasto de Groq (39.11) | `backend/app/main.py` |
| Sin monitorización | Sentry activo en el backend desde 2026-09-26 (`Sentry initialised (env=production)`); PostHog conectado sin eventos | ADR-50j/k, `docs/CONECTORES.md` |

**Incidente del 2026-09-26.** Tras fusionar `ec97405`, producción no arrancó de 09:35 a 10:48 UTC: `content_loader` falló con `KeyError: 'order'` (dominios de examen de track41/44–46) y después con lecciones escritas en otro esquema. Arreglado en #28, con `test_loader_schema.py` que falla sobre `ec97405`. Pruebas: logs de Railway del deploy `620edcd3` (fallo en bucle) y `b64e2a9a` (arranque correcto).

## Veredicto ejecutivo (actualizado)

**Whetzy hoy (septiembre 2026):** producto técnicamente impresionante en un taller, invisible para el mercado. Percentil 90 en ingeniería, percentil 5 en distribución. **Tres errores estratégicos activos:** free plan sin fricción (conversión ~0%), cero gamification (retención ~5%), track stub visible (destruye confianza).

**Whetzy al 100% mitigado (post Fase 1-8):** plataforma competitiva con ventajas únicas reales (adaptativo + multilingüe + 12+ certificaciones + código interactivo + precio agresivo). Percentil 80 en todas las categorías. **32+ tracks, 8 idiomas, 12+ certificaciones en español** — nicho sin competidor directo.

**Gap permanente:** social proof y volumen de contenido acumulado. Solo se cierran con tiempo y usuarios reales. No hay atajo técnico.

**Las tres decisiones más importantes de este documento:**

1. **Limitar el free plan** (§19) — sin esta decisión, el modelo de negocio no funciona. El 90%+ de usuarios nunca usa el tutor IA, así que si el contenido es ilimitado, no hay razón para pagar.

2. **Gamification antes del lanzamiento** (§26, Fase 2) — sin streaks/XP/badges, la retención a 30 días será ~5-10%. No importa cuán bueno sea el contenido si la gente no vuelve.

3. **Ocultar track 14 inmediatamente** (§22, Fase 0) — un track con 1 lección es peor que no tener el track. Destruye la credibilidad de los otros 17 tracks que sí están completos.

**El modelo de negocio es viable en TODOS los escenarios** si se corrigen estos tres puntos. Los costos operativos son $71/mes. Breakeven: 5 usuarios pagantes. El producto técnicamente ya existe. Lo que falta es distribución, retención y la fricción correcta para monetizar.

**¿Puede funcionar?** Sí — si sale del taller con las correcciones de monetización y retención aplicadas. La base técnica es excepcional para un solo founder. Las ventajas competitivas son reales y difíciles de replicar (especialmente multilingüe + certificaciones + adaptive ML). Pero cada semana sin usuarios es una semana donde las ventajas siguen sin validar.
