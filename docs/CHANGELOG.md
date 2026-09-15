# Changelog — Whetzy

Formato: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)  
Versioning: [Semantic Versioning](https://semver.org/)

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

- **1.1.0**: editor Monaco en preguntas de código, fill_blank con validación de fragmento.
- **1.2.0**: track Frontend (JavaScript, React, CSS) y track Algoritmos.
- **2.0.0**: vídeos explicativos generados con Manim, proyectos multi-paso con tests.
