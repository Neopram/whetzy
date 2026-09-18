# Changelog — Whetzy

Formato: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)  
Versioning: [Semantic Versioning](https://semver.org/)

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
