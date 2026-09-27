# Changelog — Whetzy

Formato: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)  
Versioning: [Semantic Versioning](https://semver.org/)

---

## [Unreleased] — 2026-09-26 (noche tardía, control total — rama `claude/gallant-tesla-fnzy1g`, PR #34)

**ES**

- **Cupo diario del plan Free, apagado por defecto** (39.4, ADR-50a/51): 30 preguntas nuevas y 5 lecciones al día (UTC); el repaso espaciado, el placement y los exámenes no cuentan. Se enciende con `FREE_DAILY_QUOTA_ENABLED` cuando abra el cobro.
- **La insignia «Perfeccionista» ya se concede** (39.5): nunca se otorgaba, y en la décima respuesta perfecta llegaba tarde. Prueba de punta a punta con capturas de XP, racha, liga e insignia.
- **Pruebas e2e**: el registro de prueba no marcaba la casilla de «13 años o más» y dejaba rotos todos los recorridos que crean un usuario.
- **Inicio de sesión social**: sus pruebas exigen ahora la sesión en cookies HttpOnly y ningún token en la URL.
- **Lecciones al listón** en JavaScript (14), Ciencia de Datos (21), Azure (22), Google Cloud (23) y PCAP (41), con fuentes oficiales comprobadas.
- **Guarda de coletillas ampliada** a una tercera familia de relleno en las opciones.
- **Tracks 18-22 sin coletillas** (39.28): 18, 19, 20, 21 y 22 a cero, con revisión adversaria completa por módulo. Varias claves falsas encontradas y corregidas en su sitio: un comando de Docker que no existe, una pregunta de Gradle que se citaba a sí misma, una desventaja de PCA al revés y dos comandos de Bicep inventados.
- **El limitador de peticiones ya no falla en abierto** (39.35): si Redis no responde, limita en memoria en vez de dejar pasar todo — el login en producción no tenía límite.
- **Política de modelos actualizada** (ADR-52): el hilo de una sesión interactiva pasa a Sonnet 5.

**EN**

- **Free plan daily quota, off by default** (39.4, ADR-50a/51): 30 new questions and 5 lessons per UTC day; spaced review, placement and exams do not count. Turned on with `FREE_DAILY_QUOTA_ENABLED` once billing opens.
- **The "Perfectionist" badge is now awarded** (39.5): it was never granted, and on the tenth perfect answer it arrived late. End-to-end test with screenshots of XP, streak, league and badge.
- **E2E tests**: the test sign-up did not tick the "13 or older" box, which broke every journey that creates a user.
- **Social login**: its tests now require the session in HttpOnly cookies and no token in the URL.
- **Lessons brought up to the bar** in JavaScript (14), Data Science (21), Azure (22), Google Cloud (23) and PCAP (41), with official sources checked.
- **Filler-ending guard extended** to a third family of padding in answer options.
- **Tracks 18-22 free of filler endings** (39.28): 18, 19, 20, 21 and 22 at zero, each with a full adversarial review. Several false keys found and fixed in place: a non-existent Docker command, a Gradle question that quoted itself, a PCA disadvantage stated backwards, and two invented Bicep commands.
- **The rate limiter no longer fails open** (39.35): when Redis is unreachable it now limits in memory instead of letting every request through — production login had no limit.
- **Model policy updated** (ADR-52): an interactive session's main thread moves to Sonnet 5.

## [Unreleased] — 2026-09-26 (noche, control total)

**ES**

- **Producción recuperada** (#28): el backend no arrancaba desde `ec97405` por contenido fuera del esquema del loader; test nuevo `test_loader_schema.py`.
- **Deploy web recuperado** (#29 y siguientes): dependencias de dependabot revertidas (`@vitejs/plugin-react` 4.x, pyodide 0.26.2) y prerender compatible con Node 20.
- **Sentry activo** en el backend (ADR-50k).
- **Recuperar contraseña ya no finge**: sin proveedor de correo, la API responde 503 y la pantalla lo dice (H.30).
- **ADR-50**: aprobación en bloque del dueño (Free, anuncios, precios, analítica PostHog, staging, protección de `master`).
- **Conectores de Claude** documentados en `docs/CONECTORES.md`.
- **Track42: claves de verdadero/falso corregidas** (153) y 110 duplicadas reescritas; guarda `test_tf_consistency.py`.
- **1.404 explicaciones de plantilla sustituidas** por explicaciones reales (track41-46, track23); 0 huellas de generador en el banco vivo.
- **Distractores reales** en tracks 26, 28, 29 y 30 (sin coletillas de relleno; la correcta ya no es casi siempre la más larga).
- **Lecciones de 18, 19, 20 y 26-30** al listón (150-300 palabras por idioma, fuente real, código que imprime lo que dice); fallos de `tests/content` 792 → 440.
- **Guardas nuevas**: coletillas por track, casi-duplicados, huellas de generador, verdadero/falso coherente y datos personales en el contenido.
- **Herramientas de revisión de contenido** en `scripts/content_qa/`.

**EN**

- **Production restored** (#28): the backend failed to boot after `ec97405` because content did not match the loader schema; new `test_loader_schema.py`.
- **Web deploy restored** (#29 onward): dependabot majors reverted and the prerender made Node 20 safe.
- **Sentry live** on the backend (ADR-50k).
- **Password reset stops pretending**: with no email provider, the API answers 503 and the page says so (H.30).
- **ADR-50**: owner's blanket approval (Free tier, ads, pricing, PostHog analytics, staging, `master` protection).
- **Claude connectors** documented in `docs/CONECTORES.md`.
- **Track42 true/false answer keys fixed** (153) and 110 duplicates rewritten; new `test_tf_consistency.py` guard.
- **1,404 placeholder explanations replaced** with real ones (track41-46, track23); 0 generator traces left in the live bank.
- **Real distractors** in tracks 26, 28, 29 and 30 (no filler endings; the correct option is no longer usually the longest).
- **Lessons for tracks 18, 19, 20 and 26-30** meet the bar (150-300 words per language, real source, code prints what it claims); `tests/content` failures 792 → 440.
- **New guards**: per-track filler endings, near-duplicates, generator traces, consistent true/false keys and personal data in content.
- **Content review tools** in `scripts/content_qa/`.

---

## [Unreleased] — 2026-09-18 (sesión bc)

**ES**

- **Frontend desplegado a producción** (H.11 cerrado): `whetzy.com` sirve el build `8015fe4` vía `wrangler pages deploy --branch main`.
- **Documentación unificada**: estrategia v3 y runbook de backups a `docs/archive/`; ARCHITECTURE, README, RELEASE, ORCHESTRATOR y CLAUDE sincronizados; tabla de invariantes del ledger restaurada.
- **Política de fuentes** (ADR-11): solo gratuitas y legales; biblioteca por área en `CATALOGO_MAESTRO.md` §2.1.
- **Teardown §11**: Educative.io evaluado en vivo (≈ 51/100); Whetzy 44/100; qué falta para vender en web, App Store y Play Store.
- **Serie 19** abierta: social login (Sign in with Apple obligatorio — ADR-13), bootcamps, playground, biblioteca RAG de autoría, landing, assets, vídeo con Remotion.

**EN**

- **Frontend deployed to production** (H.11 closed): `whetzy.com` serves build `8015fe4` via `wrangler pages deploy --branch main`.
- **Docs unified**: v3 strategy and backup runbook moved to `docs/archive/`; ARCHITECTURE, README, RELEASE, ORCHESTRATOR and CLAUDE synced; ledger invariants table restored.
- **Sources policy** (ADR-11): free and legal only; per-area library in `CATALOGO_MAESTRO.md` §2.1.
- **Teardown §11**: Educative.io assessed live (≈ 51/100); Whetzy 44/100; what each sales channel (web, App Store, Play Store) still needs.
- **Serie 19** opened: social login (Sign in with Apple mandatory — ADR-13), bootcamps, playground, authoring RAG library, landing, store assets, Remotion video post-production.

---

## [1.2.0] — 2026-09-18

### Sesiones ay–bb

**ES**

- **Runtime JavaScript real**: sandbox Web Worker (Blob URL, sin eval en el hilo principal, console capturado, timeout via `terminate()`). Tipo `js_exec` añadido al banco; EXEC_FLOOR ratchet para track14.
- **Track14 Frontend JS** (stub): 12 preguntas bilingües (10 MCQ + 2 `js_exec`), 1 lección, 6 términos de glosario. Habilidades: variables, tipos de datos y alcance. Fuente: MDN Web Docs.
- **Track13 Ciberseguridad + track40**: 79 preguntas `fill_blank_exec` nuevas (Python stdlib: `hashlib`, `hmac`, `secrets`, `html`, `re`, `ipaddress`). Ambos tracks alcanzan ≥ 15 % ejecutable.
- **Blueprints certificaciones corregidos**: PCEP (4 dominios correctos), SAA-C03 (4 dominios sin duplicado), AIF-C01 (5 dominios). `test_certification_blueprints.py` 8 passed / 0 xfail.
- **Readiness por dominio**: `GET /exams/certification/{track_id}/readiness` — «listo / no listo» por dominio × peso oficial.
- **Niveles de curso**: cada módulo gana `level 1|2|3`; `TracksScreen` agrupa en Fundamentos/Intermedio/Avanzado.
- **Tildes en todo el catálogo**: 202 cadenas corregidas en `tracks.json`, preguntas, lecciones y glosario. Guard `test_spanish_accents.py` extendido a `tracks.json`.
- **Banco**: 5.715 preguntas / 15 tracks / 342 skills / 342 lecciones / 586 términos. Deploy automático verificado (H.16).

**EN**

- **Real JavaScript runtime**: Blob-URL Web Worker sandbox (no eval on main thread, console captured, timeout via `terminate()`). `js_exec` type added to bank; EXEC_FLOOR ratchet for track14.
- **Track14 Frontend JS** (stub): 12 bilingual questions (10 MCQ + 2 `js_exec`), 1 lesson, 6 glossary terms. Skills: variables, data types and scope. Source: MDN Web Docs.
- **Track13 Cybersecurity + track40**: 79 new `fill_blank_exec` questions (Python stdlib: `hashlib`, `hmac`, `secrets`, `html`, `re`, `ipaddress`). Both tracks reach ≥ 15% executable.
- **Certification blueprints fixed**: PCEP (4 correct domains), SAA-C03 (4 domains, no duplicate), AIF-C01 (5 domains). `test_certification_blueprints.py` 8 passed / 0 xfail.
- **Domain readiness**: `GET /exams/certification/{track_id}/readiness` — "ready / not ready" per domain × official weight.
- **Course levels**: each module gains `level 1|2|3`; `TracksScreen` groups under Fundamentals/Intermediate/Advanced.
- **Spanish accents across catalog**: 202 strings fixed in `tracks.json`, questions, lessons, and glossary. `test_spanish_accents.py` guard extended to `tracks.json`.
- **Bank**: 5,715 questions / 15 tracks / 342 skills / 342 lessons / 586 terms. Auto-deploy verified (H.16).

---

## [1.0.0] — 2026-09-15

### Primera versión pública

**ES — Lo que incluye esta versión**

- **Motor adaptativo**: BKT (Bayesian Knowledge Tracing) + FSRS para programar las repeticiones, Elo para la dificultad por pregunta, UCB1 para el bandido multi-brazo de selección de preguntas, y DKT (Deep Knowledge Tracing) con fallback automático.
- **Banco de contenido**: 4.512 preguntas bilingües (ES/EN) en 11 tracks — Python avanzado, arquitectura de software, IA/ML, AWS CLF-C02, SAA-C03, AIF-C01, PCEP, y más. Todas con fuente canónica y al menos el 15 % ejecutables en CPython o sqlite3.
- **Lecciones**: 281 lecciones (una por habilidad) con ejemplo ejecutable y salida verificada automáticamente en CI.
- **Glosario**: 443 términos bilingües con definición y fuente.
- **Ejecución en navegador**: Python (Pyodide/WASM) y SQL (sqlite3 vía WASM) corren localmente — sin servidor, sin latencia, sin pérdida de datos de aprendizaje durante la ejecución.
- **Certificaciones**: simulacros cronometrados de 65 preguntas para AWS CLF-C02, SAA-C03, AIF-C01 y PCEP.
- **Gamificación**: XP, ligas semanales, rachas, misiones, duelos 1v1.
- **Tutor IA**: explicaciones por Groq (qwen3.8-27b) con RAG BM25 sobre el contenido del track.
- **Accesibilidad**: WCAG 2.2 AA, axe 0 violaciones en todas las rutas, `prefers-reduced-motion` respetado.
- **Modo oscuro**: respeta `prefers-color-scheme`; toggle en ajustes.
- **Bilingüe nativo**: ES e IN escritos por separado, con guardia de paridad en CI.
- **Offline**: las respuestas se encolan en IndexedDB y se sincronizan al reconectar.
- **GDPR**: exportación de datos, borrado de cuenta, política de privacidad, sin terceros en el bundle.
- **Android** (Google Play — pendiente H.3): APK/AAB generado con Capacitor. Target API 35. Deep links `https://whetzy.com`.
- **iOS** (App Store — pendiente H.2 + H.14): proyecto Capacitor preparado. PrivacyInfo.xcprivacy incluido. Requiere macOS para compilar.

---

**EN — What this version includes**

- **Adaptive engine**: BKT + FSRS for spaced repetition, Elo for per-question difficulty, UCB1 multi-armed bandit for question selection, and DKT (Deep Knowledge Tracing) with automatic fallback.
- **Content bank**: 4,512 bilingual (ES/EN) questions across 11 tracks — advanced Python, software architecture, AI/ML, AWS CLF-C02, SAA-C03, AIF-C01, PCEP, and more. All with canonical sources and at least 15% runnable in CPython or sqlite3.
- **Lessons**: 281 lessons (one per skill) with runnable examples whose output is verified automatically in CI.
- **Glossary**: 443 bilingual terms with definition and source.
- **In-browser execution**: Python (Pyodide/WASM) and SQL (sqlite3 via WASM) run locally — no server, no latency, no learning data loss during execution.
- **Certifications**: timed 65-question mock exams for AWS CLF-C02, SAA-C03, AIF-C01, and PCEP.
- **Gamification**: XP, weekly leagues, streaks, missions, 1v1 duels.
- **AI tutor**: explanations via Groq (qwen3.8-27b) with BM25 RAG over the track's content.
- **Accessibility**: WCAG 2.2 AA, axe 0 violations on all routes, `prefers-reduced-motion` respected.
- **Dark mode**: respects `prefers-color-scheme`; toggle in settings.
- **Natively bilingual**: ES and EN written separately, with CI parity guard.
- **Offline**: answers queued in IndexedDB and synced on reconnect.
- **GDPR**: data export, account deletion, privacy policy, no third parties in the bundle.
- **Android** (Google Play — pending H.3): APK/AAB built with Capacitor. Target API 35. Deep links `https://whetzy.com`.
- **iOS** (App Store — pending H.2 + H.14): Capacitor project prepared. PrivacyInfo.xcprivacy included. Requires macOS to build.

---

## Versiones futuras / Future versions

- **1.3.0**: social login (GitHub + Google web; Sign in with Apple tras H.2), bootcamps, playground libre, TTFQ medido en prod (Serie 19 / 11.6).
- **1.4.0**: Linux, Algoritmos y Redes (18.4, con Erickson y Peterson/Davie CC BY), certificaciones P1 (18.5).
- **2.0.0**: proyectos multi-paso con tests en runtime (18.8), vídeos Manim + Remotion (19.10), resto del catálogo de 27 tracks.
