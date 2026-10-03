# Whetzy — Catálogo maestro: todo el mundo informático, medido

> **Qué es este documento.** La única lista de tracks, certificaciones, fuentes y
> volúmenes que Whetzy se compromete a construir, con el estado real de cada fila.
> Sustituye a la tabla de la Parte II de la estrategia v3 (hoy en
> `archive/whetzy_estrategia_definitiva_v3.md`) y a la tabla §5 del plan «de quiz a
> escuela». Cuando este doc y otro choquen, manda éste.
>
> **Regla de honestidad.** Cada fila «HECHO» tiene un comando que lo reproduce
> (`python scripts/check_question_bank.py`, `python scripts/check_docs.py`,
> `pytest tests/content`). Cada cifra de la competencia marcada *(estimación)* es
> memoria del modelo, no una captura: la tarea **18.12** la sustituye por URL + fecha
> o la borra. Un número sin comando ni URL es un bug de este doc.
>
> Última medición: 2026-10-01 (`python scripts/catalog_coverage.py` sobre `80cd3ad`). Estado del banco: ver `## 1`.
> **Plan vigente desde el 2026-10-01 (ADR-54; sustituye el suelo y el ideal de ADR-53, que a su
> vez sustituyó la meta de volumen de ADR-46):** cada track de aprendizaje tiene **una sola
> forma**: 32 skills (8 módulos × 4) · 10 preguntas por skill, ≥ 3 de ellas ejecutables donde el
> navegador ejecute · 1 lección y 1 término por skill. Nada se borra: lo que pase de esa forma se
> conserva. Cada certificación: el 100 % de sus objetivos oficiales, práctica ≥ máx(300, 3 × las
> preguntas del examen) y un **banco de simulacro reservado** de 2 × el examen, que no sale en
> práctica («pendiente» si el proveedor no publica la longitud). Los tracks nuevos entran por
> **demanda medida** (Stack Overflow 2025, niveles A/B/C de ADR-53). **Ningún contenido antes
> del piloto** (`LANZAMIENTO_PILOTO.md`); después, primero los tracks que usen los pilotos. Las
> metas, con URL y fecha, están en `scripts/metas_catalogo.json`. Ejecución: serie 37 del
> ledger. Siguen de ADR-46 el corpus abierto fuera del repo y la guarda 37.0 antes de
> cualquier pregunta nueva.
> Política de fuentes desde el 2026-09-18 (ADR-11): **solo gratuitas y legales** — ver §2.1.

---

## 0. Por qué existe

El dueño preguntó tres cosas el 2026-09-16: si el catálogo cubre «todo el mundo
informático» (no: 12 tracks de 26), si estamos «a años luz» de la competencia
(en catálogo sí, en motor no) y si el plan de una tarea por sesión era capacidad o
racionamiento (racionamiento por presupuesto semanal, disfrazado de estrategia).
Este doc es la respuesta ejecutable: el mapa entero, lo que cuesta cerrarlo, y el
orden.

Lo que **no** cambia: el techo del marcador competitivo sin usuarios sigue siendo
**≈ 61/100** (`competitive-teardown.md` §8.3). Cerrar este catálogo entero no lo
mueve por encima; lo mueven H.11, H.SEED y H.10. Este doc mide *amplitud y
profundidad de producto*, no adquisición.

---

## 1. Estado del banco hoy (fuente: `check_question_bank.py` + `check_docs.py`)

| Métrica | Valor 2026-10-01 | Comando |
|---|---|---|
| Tracks | **35** (track01–23 + track26–30 + track40–46) | `python scripts/check_docs.py` |
| Módulos (unidad de presentación en la web; el plan mide skills, ADR-54) | **174** | ídem |
| Skills | **730** | ídem |
| Preguntas | **11.005** | `python scripts/check_question_bank.py` |
| Lecciones | **730** (una por skill: las 730 skills tienen lección) | `python scripts/catalog_coverage.py --json` |
| Glosario | **1.044** | `check_docs.py` |
| Ejecutables | **7** tracks ≥ 15 % (01, 02, 04, 06, 07, 09 y 12 — este, 20 %); track03 13,4 %, track13 4,8 %, track14 4,5 %, track40 1,4 %, track16 y track17 0 %; exentos track05, 08, 10, 11 y 15 (ADR-9). El 2026-10-01 se quitaron 216 «ejecutables» que daban correcto sin escribir nada (sin hueco `___` o con el hueco vacío válido) y pasaron a `fill_blank`, que es lo que eran: track16 decía 44,9 % y track17 36,7 %. El 2026-10-02, 24 que pasaban en CPython no podían resolverse en el navegador (hilos, `asyncio.run`, `sqlite3`, `tempfile`): 7 se reescribieron para el sandbox, 3 pasaron a `sql_exec` y 14 a `mcq`; `frontend/scripts/check-exec-pyodide.mjs` los corre en Pyodide | `check_question_bank.py`, `check-exec-pyodide.mjs` |
| Certificaciones | **11** (CLF-C02, PCEP, SAA-C03, AIF-C01, ISC2 CC, **PCAP**, **Security+**, **MLA-C01**, **AZ-900**, **AI-901** (antes AI-900, retirado por Microsoft el 30-06-2026; blueprint migrado 39.24, 2026-10-02), **DP-900**) | `pytest tests/content/test_certification_blueprints.py` |
| Proyectos multi-paso | 0 | — |
| Vídeos | 0 | — |
| Plan ADR-54: tracks construidos ya en la forma 32 × 10 | 0 de 24 | `python scripts/catalog_coverage.py` |
| Lo que falta en los 24 tracks construidos | +261 skills · +261 lecciones · +266 términos · +2.610 preguntas | ídem |
| Lo que falta en las 11 certificaciones | +872 de práctica · +1.040 reservadas (AZ-900, AI-901 y DP-900: «pendiente», sin longitud publicada) | ídem |
| Total y ritmo | 4.522 preguntas ≈ 9 sesiones a 518/sesión (estimación) | ídem |

---

## 2. El mapa — 28 tracks de aprendizaje (+ 17 de la ampliación por demanda, §2.0 y §2.0.1)

Convención de ids: **tracks de aprendizaje `track12`–`track39` y `track47`–`track59`**,
**tracks de certificación `track40`–`track46` y, los nuevos, `track60`–`track99`**
(`is_certification: true`, misma forma que track08–11). El número de track va con dos
cifras dentro de los ids de módulo y skill (`mod4601`, `sk460101`): pasar de `track99`
exige antes un ADR. Un id planificado nunca reutiliza uno de `content/curriculum/tracks.json`
(renumeración del 2026-09-29: los planificados track41–46 chocaban con las certificaciones
PCAP, Security+, MLA-C01, AZ-900, AI-900 y DP-900, y pasaron a track51–56).
Cada track de aprendizaje (ADR-54):
- **Forma única:** 32 skills (8 módulos × 4) · 10 preguntas por skill (320 por track), ≥ 3
  ejecutables por skill donde el navegador pueda ejecutar (Python, SQL, JS) o exento con razón
  escrita · 1 lección y 1 término de glosario por skill · guarda 37.0 en verde.
- **Nada se borra:** un track por encima de 32 skills o de 10 preguntas por skill conserva lo
  que tiene (track01: 52 skills, 867 preguntas).
- **roadmap.sh** solo sirve para elegir qué 32 skills entran; sus recuentos siguen en
  `scripts/metas_catalogo.json` como referencia, no como meta.
- El molde antiguo de 20 skills · 300 preguntas (track12) queda 12 skills por debajo de la
  forma: es el punto de partida de 13 de los 24 tracks construidos.

Licencias: en la app entra solo contenido propio o MIT / Apache-2 / BSD / CC BY /
CC0 / PSF / dominio público (NIST, RFC, docs de gobierno de EE. UU.). **CC BY-SA
espera a H.LIC; CC BY-NC y docs propietarias (AWS, CompTIA, ISC2, Cisco) se citan,
nunca se copian.** Certificaciones: **nunca dumps**; preguntas propias sobre los
dominios oficiales, con los pesos verificados contra la guía del proveedor (lección
de 17.13). **Desde el 2026-09-18 (ADR-11): solo fuentes gratuitas y legales — no se
compran libros para parafrasearlos y los PDFs pirateados no entran ni como cita.** El
camino con cualquier fuente es el mismo: leer → escribir lección/pregunta original en
ES y EN → citar. Los hechos son libres; la redacción no.

**Meta por track (ADR-54):** la forma de arriba. Las anteriores quedan sustituidas: ADR-53
(suelo de 50 skills · 800 preguntas e ideal por temario, sustituido el 2026-10-01) y ADR-46 (50
cursos = 200 skills · 3.000 preguntas · 200 lecciones · ≥ 400 términos por track, histórico).

| # | Área | Track | Id | Estado | Fuentes con licencia | Runtime | Certs asociadas (→ §3) |
|---|---|---|---|---|---|---|---|
| 1 | Fundamentos | Python básico | track01 | ✅ | PSF docs | Python | PCEP |
| 2 | Fundamentos | Python intermedio | track02 | ✅ | PSF docs | Python | PCAP |
| 3 | Fundamentos | Python avanzado | track03 | ✅ | PSF docs, PEPs | Python | PCPP1 |
| 4 | Ingeniería | Ingeniería de software | track04 | ✅ | `faif/python-patterns` MIT, Pro Git (cita) | Python + SQL | GitHub Foundations |
| 5 | Ingeniería | Arquitectura de software | track05 | ✅ | `system-design-primer` CC BY | exento | TOGAF (cita) |
| 6 | IA | Fundamentos de IA/ML | track06 | ✅ | `microsoft/ML-For-Beginners` MIT, Google MLCC CC BY | Python stdlib | AI-900 |
| 7 | IA | Ingeniería de IA / LLMs | track07 | ✅ | `generative-ai-for-beginners` MIT, `dair-ai/PEG` MIT, arXiv | Python stdlib | AIF-C01 ✅, AI-102 |
| 8 | Datos | SQL | track12 | ✅ (18.0 lo deja verde) | SQLite docs (dominio público), PostgreSQL docs | **SQL (sql.js)** | PostgreSQL Associate, DP-900 |
| 9 | Seguridad | Ciberseguridad — fundamentos | track13 | ✅ (25.0: scaffolding + 500 Q mock, 15 % exec) | NIST SP 800-53/61/63 (PD) + OWASP CheatSheets (CC BY-SA) | Python `fix_bug_exec` (hashlib, hmac, secrets, html, re, ipaddress) | ISC2 CC, Security+ |
| 10 | Web | Frontend (JS/TS/React) | track14 | ✅ (18.3: 6 módulos, 24 skills, 24 lecciones, 40 términos glosario, JS Worker sandbox) | `lydiahallie/javascript-questions` MIT, `Web-Dev-For-Beginners` MIT, MDN (CC BY-SA → cita) | **JS Worker sandbox real (18.3)** | JSE-1 |
| 11 | Fundamentos | Linux / shell | track15 | ✅ (18.4, `bec734c`: 180 Q, 3 módulos, 12 lecciones, exento ADR-9) | `exercism/bash` MIT, man-pages (cita), *The Linux Command Line* (cita) | exento (fill_blank de comandos) | LPIC-1, Linux+, LFCS |
| 12 | Fundamentos | Algoritmos y estructuras | track16 | ✅ (18.4: 158 Q, 44,9 % exec, 12 lecciones) | `TheAlgorithms/Python` MIT, `tech-interview-handbook` MIT; `coding-interview-university` (BY-SA → H.LIC) | Python (≥ 30 %) | — |
| 13 | Fundamentos | Redes | track17 | ✅ (18.4: 180 Q, mod1703 36,7 % exec, 12 lecciones) | RFCs (IETF), *Computer Networking* (cita), Cisco docs (cita) | Python (`socket`, `ipaddress`) | CCNA, Network+ |
| 14 | DevOps | Docker y Kubernetes | track18 | ✅ (18.6: 300 Q, 5 módulos, 20 lecciones) | Docs Kubernetes CC BY 4.0, Docker docs (cita) | exento (escenario + decisión) | KCNA, CKA, CKAD, CKS |
| 15 | DevOps | IaC y CI/CD (Terraform, GitHub Actions) | track19 | ✅ (18.6: 300 Q, 5 módulos, 20 lecciones) | Terraform docs (cita), GitHub Actions docs (cita), `actions/*` MIT | exento | Terraform Associate, GitHub Actions |
| 16 | Datos | Data Engineering | track20 | ✅ (18.7: 300 Q, 5 módulos, 20 lecciones) | `Data-Science-For-Beginners` MIT, PostgreSQL docs, DuckDB docs MIT | SQL (duckdb-wasm o sql.js) | DP-203, GCP PDE, Databricks DE |
| 17 | Datos | Data Science / Analytics | track21 | ✅ (18.7: 300 Q, 5 módulos, 20 lecciones) | Kaggle Learn Apache-2, *Python Data Science Handbook* (cita) | Python stdlib (`statistics`, `csv`) | DP-100, Google Data Analytics |
| 18 | Cloud | Azure | track22 | ✅ (18.6: 300 Q, 5 módulos, 20 lecciones) | Microsoft Learn (cita; propietario) | exento | AZ-900, AZ-104, AZ-204, AI-900, DP-900 |
| 19 | Cloud | GCP | track23 | ✅ (18.6: 300 Q, 5 módulos, 20 lecciones) | Google Cloud docs (cita; propietario) | exento | Digital Leader, ACE, PCA, PMLE |
| 20 | Seguridad | Ofensiva / pentest | track24 | ⚠️ en cuarentena (25.0): no está en `tracks.json`; se reconstruye en 37.7 (nivel B, ADR-53) | OWASP WSTG (CC BY-SA) + MITRE ATT&CK (PD) + NIST SP 800-115 (PD) | Python stdlib | eJPT, PenTest+, CEH (cita) |
| 21 | Seguridad | Seguridad en la nube | track25 | ⚠️ en cuarentena (25.0): no está en `tracks.json`; se reconstruye en 37.7 (nivel B, ADR-53) | NIST SP 800-144 (PD) + OWASP ASVS (CC BY-SA) + CIS Benchmarks (cita) | exento | AWS Security Specialty, CCSP |
| 22 | Fundamentos | Git y herramientas de desarrollo | track26 | ✅ (18.10: 300 Q, 5 módulos, 20 lecciones) | Pro Git (CC BY-NC-SA → cita), git docs (GPL → cita), GitHub docs | exento | GitHub Foundations |
| 23 | Datos | NoSQL | track27 | ✅ (18.7: 300 Q, 5 módulos, 20 lecciones) | MongoDB docs (cita), Redis docs (cita) | exento | MongoDB Associate |
| 24 | Web | Backend (FastAPI / Node) | track28 | ✅ (18.10: 300 Q, 5 módulos, 20 lecciones) | FastAPI docs MIT, *Full Stack Python* MIT, Node docs MIT | Python stdlib (`http.server`, `json`) | — |
| 25 | Ingeniería | QA y testing | track29 | ✅ (18.10: 300 Q, 5 módulos, 20 lecciones) | pytest docs MIT, ISTQB syllabus (cita), Playwright docs Apache-2 | Python (`unittest`, `assert`) | ISTQB CTFL |
| 26 | Ingeniería | Agile y producto | track30 | ✅ (18.10: 300 Q, 5 módulos, 20 lecciones) | Scrum Guide (CC BY-SA → cita), Agile Manifesto (cita) | exento | PSM I |
| 27 | Móvil | Móvil (Android/Kotlin · iOS/Swift · Flutter/RN) | track31 | ❌ (nivel B de demanda, Kotlin 10,8 %; sin runtime en navegador) — 37.8 | Android docs Apache-2, Flutter docs BSD, Apple docs (cita) | exento | — |
| 28 | Web3 | Solana / Web3 developer (ADR-38) | track32 | ❌ (nivel C de demanda, sin medida; 37.8) | `solana-labs/solana` y `solana-program-library` Apache-2, `solana-developers` cookbook/docs MIT, `@solana/web3.js` MIT, Anchor Apache-2 — confirmar `LICENSE` en 37.3 antes de reutilizar texto | **JS (`@solana/web3.js` en el Worker de 18.3)** + Python stdlib (hash, base58, serialización); Rust/Anchor = escenario + decisión (exento ADR-9) | — (sin cert oficial; evidencia = bounties Superteam Earn resueltos) |

**Cobertura hoy (2026-09-30, `catalog_coverage.py`):** 24 de las 28 filas están construidas
(faltan track24 y track25, en cuarentena; track31, móvil; track32, Solana). De los 45 tracks
del plan, solo track01 está en el suelo; la tabla por track sale de
`python scripts/catalog_coverage.py`.

### 2.0 Ampliación por demanda medida (ADR-53; antes ADR-46) — 14 tracks, más 3 de §2.0.1

Áreas que el mapa de 28 no cubría. Desde ADR-53 todas están en el plan
(`scripts/metas_catalogo.json`) y **el orden lo decide la demanda medida**: uso en Stack Overflow
Developer Survey 2025, All Respondents (leído el 2026-09-30). **A ≥ 25 %** y **B 10–25 %**
llegan al suelo primero; **C (< 10 % o sin medida)** solo cuando todos los A y B estén en el
suelo. Licencias de las fuentes: se comprueban en 37.3 leyendo `LICENSE` (nada aquí se da por
libre sin leerlo). Runtime: solo Python, SQL y JS ejecutan en el navegador; el resto va exento
con razón (ADR-9), como Linux.

| Nivel | Tracks (dato de demanda) |
|---|---|
| **A** | track38 TypeScript (43,6 %) · track33 Java (29,4 %) · track34 C# (27,8 %) |
| **B** | track37 C/C++ (C++ 23,5 %) · track47 PowerShell (23,2 %) · track48 PHP (18,9 %) · track35 Go (16,4 %) · track36 Rust (14,8 %) · track39 SRE (Prometheus 11,8 %) · track31 móvil (Kotlin 10,8 %) · track24/25 seguridad, por reconstrucción y segmento estratégico (sin medida en la encuesta) |
| **C** | track49 Ruby (6,4 %) · track50 R (4,9 %) · track53 videojuegos (GDScript 3,3 %) · track54 IoT (MicroPython 2,3 %) · track32 Solana, track52 Solidity, track51 MLOps, track55 Matemáticas para CS y track56 Soporte IT (sin medida) |

| # | Área | Track | Id | Fuentes candidatas (licencia a comprobar en 37.3) | Runtime | Certs asociadas |
|---|---|---|---|---|---|---|
| 29 | Lenguajes | Java / JVM (Kotlin backend) | track33 | OpenJDK docs (GPL+CE → cita), `TheAlgorithms/Java` MIT, Spring guides Apache-2 | exento | OCA/OCP (cita) |
| 30 | Lenguajes | C# / .NET | track34 | `dotnet/docs` CC BY 4.0, `TheAlgorithms/C-Sharp` MIT | exento | AZ-204 (con track22) |
| 31 | Lenguajes | Go | track35 | `golang/go` BSD, Go by Example CC BY, `TheAlgorithms/Go` MIT | exento | — |
| 32 | Lenguajes | Rust | track36 | The Rust Book MIT/Apache-2, Rustlings MIT, `TheAlgorithms/Rust` MIT | exento | — |
| 33 | Sistemas | C / C++ y sistemas | track37 | `TheAlgorithms/C` y `C-Plus-Plus` MIT, cppreference (CC BY-SA → cita), OSTEP (CC BY-NC → cita) | exento | — |
| 34 | Web | TypeScript avanzado | track38 | `microsoft/TypeScript` docs Apache-2, `type-challenges` MIT | **JS Worker** (18.3) | — |
| 35 | DevOps | SRE y observabilidad | track39 | Google SRE books (CC BY-NC → cita), Prometheus/Grafana docs Apache-2, OpenTelemetry docs Apache-2 | exento | — |
| 36 | IA | MLOps y despliegue de modelos | track51 | `mlflow` Apache-2, Kubeflow docs Apache-2, `madewithml` MIT | Python stdlib | — |
| 37 | Web3 | Solidity / EVM | track52 | Solidity docs GPL (→ cita), `OpenZeppelin` MIT, `ethereum.org` docs MIT | JS Worker (`ethers` MIT) | — |
| 38 | Juegos | Desarrollo de videojuegos (Godot, Unity) | track53 | Godot docs CC BY 3.0, `godotengine/godot-demo-projects` MIT | exento | — |
| 39 | Sistemas | Embebidos e IoT | track54 | MicroPython MIT, Zephyr docs Apache-2, Arduino docs CC BY-SA (→ cita) | Python stdlib (MicroPython-compatible) | — |
| 40 | Fundamentos | Matemáticas para CS | track55 | OpenStax (CC BY 4.0), `3b1b/manim` MIT (explicadores) | Python stdlib | — |
| 41 | Soporte | Soporte IT y hardware | track56 | CompTIA A+ / ITF+ objetivos (cita), Wikipedia (CC BY-SA → cita), docs de Microsoft (cita) | exento | A+, ITF+ |
| 42 | Sistemas | Administración Windows / PowerShell | track47 | `PowerShell/PowerShell-Docs` CC BY 4.0, `MicrosoftDocs` (CC BY 4.0 en repos públicos) | exento | — |

`track40`–`track46` ya existen (certificaciones ISC2 CC, PCAP, Security+, MLA-C01, AZ-900,
AI-900 y DP-900); por eso la numeración salta de `track39` a `track47`, y `track48`–`track50`
quedan para los propuestos de §2.0.1 (PHP, Ruby, R).

### 2.0.1 Inventario de la industria frente al catálogo (37.1, 2026-09-25)

Fuentes descargadas por la sesión, sin registrarse. La hora es la de la descarga (UTC).
Los recuentos se reproducen con el comando indicado; no se copian a mano en otros docs.

| Fuente | URL | Descarga | Estado | Qué se leyó |
|---|---|---|---|---|
| roadmap.sh | https://roadmap.sh | 2026-09-25T00:39:21Z | 200 | slugs de roadmap (`grep -oE 'href="/[a-z0-9-]+"'`, sin navegación) |
| Stack Overflow Survey 2025 | https://survey.stackoverflow.co/2025/technology | 2026-09-25T00:39:56Z | 200 | lenguajes y frameworks por nombre |
| ISC2 | https://www.isc2.org/certifications | 2026-09-25T00:39:21Z | 200 | CISSP, CCSP, CSSLP, CGRC… |
| Linux Foundation | https://training.linuxfoundation.org/certification-catalog/ | 2026-09-25T00:39:21Z | 200 | KCNA, CKA, CKAD, CKS, CGOA… |
| CompTIA | https://www.comptia.org/certifications | 2026-09-25T00:39:21Z | 200 | catálogo de certificaciones |
| Microsoft Learn | https://learn.microsoft.com/en-us/credentials/browse/?credential_types=certification | 2026-09-28T16:11Z | 200 | Playwright (arreglado el TLS del proxy de sandbox esta sesión, sin bypass): 74 certificaciones, 3 páginas paginadas, `innerText` completo |
| Google Cloud | https://cloud.google.com/learn/certification | 2026-09-28T16:11Z | 200 | Playwright: catálogo completo por nivel (Foundational/Associate/Professional) |

**Microsoft Learn (74 certificaciones, 2026-09-28) y Google Cloud, ya legibles.**
Ninguna certificación de las dos listas abre una categoría de track que no exista ya:
Microsoft es sobre todo Azure (AI/cloud/seguridad/datos, ya cubierto por 06-08/10/11/13/
20-25/41), GitHub (track26), Power BI/Fabric (track20/21) y una franja grande de Dynamics
365 y Office Specialist (aplicaciones de negocio, fuera del foco actual del catálogo —
no se propone track). Google Cloud: Cloud Digital Leader/Engineer/Architect/Database
Engineer/DevOps Engineer/Security Engineer/Network Engineer/ML Engineer/Data
Practitioner/Workspace Administrator, todas dentro de tracks existentes. `Azure AI
Fundamentals` sigue en la lista como nombre de certificación aunque el examen debajo
cambió a AI-901 (39.24) — el nombre de marca no cambia con el código del examen.

**Área → track** (roadmap.sh como índice, contrastado con la encuesta y los catálogos):

| Área de la industria (slug de roadmap.sh) | Track de Whetzy |
|---|---|
| python, python-data-analysis | track01–03, track21 |
| ai-engineer, ai-agents, prompt-engineering, machine-learning, ai-data-scientist, ai-product-builder, claude-code, vibe-coding | track06, track07 |
| mlops | track51 |
| frontend, html, css, javascript, react, vue, angular, nextjs, design-system, frontend-performance-best-practices | track14 |
| typescript | track38 |
| backend, nodejs, django, api-design, graphql, backend-performance-best-practices, full-stack | track28 (+ track14) |
| java, spring-boot, kotlin, scala | track33 (JVM; Scala se absorbe aquí) |
| aspnet-core | track34 |
| golang · rust · c, cpp | track35 · track36 · track37 |
| android, ios, swift-ui, flutter, react-native | track31 |
| devops, docker, kubernetes, terraform, cloudflare | track18, track19 (CGOA/GitOps de Linux Foundation → track19) |
| linux, shell-bash | track15 |
| aws, aws-best-practices | track08, track10, track11 |
| cyber-security, api-security-best-practices, devsecops, ai-red-teaming | track13, track24, track25 (CSSLP de ISC2 → track13 + track29) |
| data-analyst, bi-analyst, power-bi · data-engineer | track21 · track20 |
| sql, postgresql-dba · mongodb, redis, elasticsearch | track12 · track27 |
| datastructures-and-algorithms, leetcode, computer-science | track16, track55 |
| system-design, software-architect, software-design-architecture | track05 |
| qa, code-review, code-review-best-practices | track29, track04 |
| git-github | track26 |
| network-engineer | track17 |
| blockchain | track32, track52 |
| game-developer, server-side-game-developer | track53 |
| product-manager | track30 (parcial: Agile y producto) |
| **php, laravel, wordpress** | **SIN TRACK** → propuesto `track48` PHP (Laravel, WordPress) |
| **ruby, ruby-on-rails** | **SIN TRACK** → propuesto `track49` Ruby (Rails) |
| **r-programming** | **SIN TRACK** → propuesto `track50` R para datos |
| ux-design, product-design · technical-writer, devrel · engineering-manager · seo | sin track, **una sola fuente** (roadmap.sh): no se proponen todavía |

**Propuestos** (≥ 2 fuentes: roadmap.sh + Stack Overflow Survey 2025, donde PHP, Ruby, R,
Laravel, Ruby on Rails y WordPress aparecen por nombre): `track48` PHP, `track49` Ruby,
`track50` R. Entran en el plan por ADR-53 con su nivel de demanda: PHP en B (18,9 %), Ruby y
R en C (6,4 % y 4,9 %). Las fuentes libres
de cada uno se buscan con el pipeline de 37.3 antes de escribir una sola pregunta (37.0).

### 2.1 Biblioteca de fuentes libres por área (ADR-11 — solo gratis y legal)

Tres marcas, y solo la primera permite reutilizar texto:

- **[reusar]** — licencia permisiva (MIT / Apache-2 / BSD / CC BY / CC0 / PSF / dominio público): puede entrar en la app con atribución.
- **[H.LIC]** — CC BY-SA: solo si el dueño acepta que lo derivado herede la licencia.
- **(cita)** — gratis online pero CC BY-NC-* o propietario: se lee, se aprende, se escribe original y se enlaza. Nunca se pega.

Sin libros de pago. Sin PDFs pirateados. Toda fuente citada en una pregunta o lección debe resolver por URL (`scripts/check_content_sources.py`), y la tarea 19.7 construye el índice local `content/sources/index.json` con URL, licencia y fecha de captura.

| Área | Tracks | [reusar] | [H.LIC] | (cita) |
|---|---|---|---|---|
| Python | 01, 02, 03, 09, PCAP | Tutorial y docs de Python (PSF) · PEPs · `exercism/python` (MIT) | *A Byte of Python* · *Composing Programs* | *Think Python* 3e · *Automate the Boring Stuff* · *Python for Everybody* (py4e) · syllabus PCEP/PCAP |
| Algoritmos | 16 | *Algorithms* (Jeff Erickson, **CC BY 4.0**) · *Open Data Structures* (CC BY) · `TheAlgorithms/Python` (MIT) · `tech-interview-handbook` (MIT) | `coding-interview-university` | *Problem Solving with Algorithms and DS using Python* (Miller/Ranum) · *Competitive Programmer's Handbook* |
| Ingeniería, Git, QA, Agile | 04, 26, 29, 30 | *The Architecture of Open Source Applications* (CC BY) · `faif/python-patterns` (MIT) · pytest y Playwright docs · `actions/*` (MIT) | Scrum Guide | *Pro Git* · *Software Engineering at Google* · *SRE Book* · ISTQB CTFL v4 syllabus · GitHub docs |
| Arquitectura | 05 | `system-design-primer` (CC BY) · *AOSA* vol. 1-2 (CC BY) | — | 12factor.net · microservices.io · AWS Well-Architected |
| IA / ML / LLMs | 06, 07, 11, MLA-C01, AI-900/AI-102 | `ML-For-Beginners`, `AI-For-Beginners`, `generative-ai-for-beginners` (MIT, con ES) · Google ML Crash Course (CC BY) · Hugging Face Course y fast.ai (Apache-2) · `dair-ai/Prompt-Engineering-Guide` (MIT) · Kaggle Learn (Apache-2) · `mlabonne/llm-course` (Apache-2) | *Dive into Deep Learning* | *Understanding Deep Learning* (Prince) · *Deep Learning* (Goodfellow) · *Probabilistic ML* (Murphy) · *Mathematics for ML* · *ISLP* · *Speech and Language Processing* (Jurafsky) · *The Little Book of Deep Learning* · *Neural Networks and Deep Learning* (Nielsen) |
| SQL, NoSQL, Data Eng, Data Science | 12, 20, 21, 27 | SQLite docs (dominio público) · PostgreSQL docs (PostgreSQL License) · DuckDB docs (MIT) · `Data-Science-For-Beginners` (MIT) · Kaggle Learn (Apache-2) | — | *Python for Data Analysis* 3e (open access) · *Python Data Science Handbook* · *Think Stats* · *Think Bayes* · *Use The Index, Luke* · MongoDB University · Redis docs |
| Seguridad | 13, 24, 25, 40, Security+ | NIST SP 800-53/61/63/115/144 (dominio público) · MITRE ATT&CK (atribución) · RFCs · *Crypto 101* · *Handbook of Applied Cryptography* (online gratis, uso académico: verificar) | OWASP Top 10 · WSTG · Cheat Sheets | CIS Controls · *Security Engineering* 3e (Anderson) · ISC2 CC curso oficial + exam outline · Security+ SY0-701 objectives |
| Frontend y Backend | 14, 28, JSE-1, DVA-C02 | `lydiahallie/javascript-questions` (MIT) · `Web-Dev-For-Beginners` (MIT) · React docs (CC BY 4.0) · TypeScript Handbook · FastAPI docs (MIT) · *Full Stack Python* (MIT) · Node docs (MIT) · RFC 9110 | MDN | *Eloquent JavaScript* 4e · *You Don't Know JS Yet* · javascript.info |
| Linux y Redes | 15, 17, LPIC-1, CCNA/Network+ | *Computer Networks: A Systems Approach* (Peterson/Davie, **CC BY 4.0**) · RFCs (IETF) · `exercism/bash` (MIT) | — | *Beej's Guide to Network Programming* · *High Performance Browser Networking* · man-pages · *The Linux Command Line* 5e · *Linux Fundamentals* (Cobbaut) · LPI Learning Materials · *OSTEP* · *The Missing Semester* |
| DevOps | 18, 19, CKA/CKAD/KCNA, Terraform | Kubernetes docs (**CC BY 4.0**) · `actions/*` (MIT) · 12factor.net | — | currículos CKA/CKAD/KCNA (CNCF) · *The Site Reliability Workbook* · Docker docs · Terraform docs · GitHub Actions docs |
| AWS, Azure, GCP | 08, 10, 11, 22, 23, 25 | — (**ninguna nube publica docs con licencia libre**) | — | guías de examen, whitepapers y Well-Architected de AWS · AWS Skill Builder (cursos gratis) · Microsoft Learn · Azure Architecture Center · Google Cloud docs · Cloud Skills Boost · Architecture Framework |
| Móvil | 31 | *The Swift Programming Language* (swift.org, **CC BY 4.0**) · Android developer docs (**CC BY 2.5**) · Kotlin docs (Apache-2) · Flutter y Dart docs (BSD / CC BY) · React Native docs (MIT) | — | Apple Human Interface Guidelines |

Lo que esta tabla cambia en el coste: **los tres tracks de 18.4 (Linux, Algoritmos, Redes) tienen fuente [reusar] de libro completo** (Erickson, Peterson/Davie) y ya no dependen de H.LIC; los de cloud (22, 23) y certificaciones de proveedor siguen siendo cita + preguntas propias, como siempre fue.

### 2.2 Repositorios y fuentes a clonar (sesión bf, 2026-09-18 — alimenta 19.7 y la Serie 20)

Reglas de uso, por encima de la tabla:

1. **Clonar fuera del repo**: `git clone --depth 1 <url> C:\Users\feder\whetzy-sources\<nombre>` (fuera de Desktop/Documents por *Controlled Folder Access*; la carpeta no se versiona).
2. **La licencia que manda es el fichero `LICENSE`/`NOTICE` del commit clonado**, no esta tabla. Al clonar se anota `sha`, fecha y licencia leída en `content/sources/index.json` (19.7). Si difiere de la columna «Licencia», gana el fichero y se corrige la tabla **en el mismo commit**. `scripts/check_source_licenses.py` (20.5) lo comprueba.
3. Muchos repos tienen **código y prosa con licencias distintas** (columna «Qué extraer»). Código MIT/BSD/Apache es [reusar] aunque el texto sea (cita).
4. Docs de proveedor (AWS, Azure, GCP, CompTIA, ISC2) son (cita) salvo donde se indique CC BY: se leen, se escribe original, se enlaza.
5. Marca `verificar` = licencia probable pero no confirmada por esta sesión; **no se extrae nada** hasta que 20.5 la confirme.

| Área | Repositorio / fuente | Licencia (esperada) | Marca | Qué extraer |
|---|---|---|---|---|
| Python | `github.com/python/cpython` (`Doc/`) | PSF-2.0 | [reusar] | tutorial, referencia de biblioteca, ejemplos |
| Python | `github.com/python/python-docs-es` | PSF-2.0 | [reusar] | **la misma docs en español nativo** |
| Python | `github.com/python/peps` | dominio público / Open Publication License (cabecera de cada PEP) | [reusar] (confirmar licencia en cabecera del PEP específico; la mayoría PSF/dominio público) | PEP 8, 20, 484, 557, 3107… |
| Python | `github.com/exercism/python` | MIT | [reusar] | ejercicios con tests (moldes de `fill_blank_exec`) |
| Python | `github.com/TheAlgorithms/Python` | MIT | [reusar] | implementaciones de referencia |
| Python | `github.com/realpython/materials` | MIT (código) | [reusar] código · (cita) artículos | snippets ejecutables |
| Python | `github.com/fluentpython/example-code-2e` | MIT (código) | [reusar] código · (cita) libro | ejemplos avanzados |
| Python | `github.com/swaroopch/byte-of-python` | CC BY-SA 4.0 | [H.LIC] | prosa introductoria |
| Python | OpenStax *Introduction to Python Programming* (openstax.org) | CC BY 4.0 | [reusar] | capítulos completos, ejercicios |
| Python | `github.com/AllenDowney/ThinkPython` · `github.com/csev/py4e` | CC BY-NC-SA | (cita) | estructura pedagógica, ideas de ejercicios |
| Algoritmos | `jeffe.cs.illinois.edu/teaching/algorithms` (`github.com/jeffgerickson/algorithms`) | CC BY 4.0 | [reusar] | libro completo |
| Algoritmos | `github.com/patmorin/ods` (*Open Data Structures*) | CC BY 2.5 | [reusar] | estructuras de datos con código |
| Algoritmos | `github.com/keon/algorithms` · `github.com/TheAlgorithms/Python` | MIT | [reusar] | implementaciones |
| Algoritmos | `github.com/yangshun/tech-interview-handbook` | MIT | [reusar] | patrones de entrevista |
| Algoritmos | `github.com/jwasham/coding-interview-university` | CC BY-SA 4.0 | [H.LIC] | plan de estudio |
| Ingeniería / Git / QA | `github.com/aosabook/aosabook` | CC BY 3.0 | [reusar] | arquitectura de proyectos reales |
| Ingeniería / Git / QA | `github.com/google/eng-practices` | CC BY 3.0 | [reusar] | code review |
| Ingeniería / Git / QA | `github.com/github/docs` | CC BY 4.0 (contenido) · MIT (código) | [reusar] | Git, Actions, PRs |
| Ingeniería / Git / QA | `github.com/faif/python-patterns` | MIT | [reusar] | patrones con código |
| Ingeniería / Git / QA | `github.com/pytest-dev/pytest` (`doc/`) · `github.com/microsoft/playwright` (`docs/`) | MIT · Apache-2.0 | [reusar] | testing |
| Ingeniería / Git / QA | `github.com/progit/progit2` · `progit2-es` · `github.com/git/git` (`Documentation/`, GPL-2) | CC BY-NC-SA 3.0 · GPL-2.0 | (cita) | conceptos; nunca prosa |
| Arquitectura | `github.com/donnemartin/system-design-primer` | CC BY 4.0 | [reusar] | diseño de sistemas (tiene ES parcial) |
| Arquitectura | `github.com/heroku/12factor` | MIT | [reusar] | doce factores |
| Arquitectura | `microservices.io` · AWS Well-Architected | propietario | (cita) | patrones |
| IA / ML | `github.com/microsoft/ML-For-Beginners` · `AI-For-Beginners` · `Data-Science-For-Beginners` · `generative-ai-for-beginners` | MIT (con `translations/es`) | [reusar] | **cursos completos con español nativo** |
| IA / ML | Google *ML Crash Course* (developers.google.com/machine-learning) | CC BY 4.0 (contenido) · Apache-2.0 (código) | [reusar] | curso, también en ES |
| IA / ML | `github.com/huggingface/course` | Apache-2.0 | [reusar] | NLP/LLM (tiene ES) |
| IA / ML | `github.com/probml/pml-book` (Murphy, *Probabilistic ML*) | MIT | [reusar] | libro completo |
| IA / ML | `github.com/d2l-ai/d2l-en` · `d2l-es` | CC BY-SA 4.0 (texto) · MIT (código) | [H.LIC] texto · [reusar] código | deep learning |
| IA / ML | `github.com/dair-ai/Prompt-Engineering-Guide` · `github.com/mlabonne/llm-course` | MIT · Apache-2.0 | [reusar] | prompting, LLM engineering |
| IA / ML | `github.com/Kaggle/learntools` | Apache-2.0 | [reusar] | ejercicios Kaggle Learn |
| IA / ML | `github.com/scikit-learn/scikit-learn` · `pandas-dev/pandas` · `numpy/numpy` · `pytorch/tutorials` · `keras-team/keras-io` (docs) | BSD-3 · BSD-3 · BSD-3 · BSD-3 · Apache-2.0 | [reusar] | referencia y tutoriales |
| IA / ML | `github.com/openai/openai-cookbook` · `anthropics/anthropic-cookbook` · `langchain-ai/langchain` (docs) | MIT | [reusar] | agentes, tool use, RAG |
| IA / ML | `github.com/anthropics/courses` | CC BY-NC 4.0 | (cita) | prompt engineering interactivo Anthropic — no comercial |
| IA / ML | `github.com/fastai/fastbook` · *UDL* (Prince) · *Deep Learning* (Goodfellow) · *MML* · *ISLP* · *SLP* (Jurafsky) · Nielsen | GPL-3 código / © texto · CC BY-NC-ND · © · © · © · © · CC BY-NC | (cita) | ideas, no prosa |
| SQL / Datos | `github.com/postgres/postgres` (`doc/`) · sqlite.org/docs | PostgreSQL License · dominio público | [reusar] | referencia SQL |
| SQL / Datos | `github.com/duckdb/duckdb-web` | MIT | [reusar] | SQL analítico |
| SQL / Datos | `github.com/wesm/pydata-book` | MIT (código) · CC BY-NC-ND (texto) | [reusar] código · (cita) texto | pandas |
| SQL / Datos | `github.com/redis/redis-doc` · MongoDB docs | CC BY-SA 4.0 · CC BY-NC-SA 3.0 | [H.LIC] · (cita) | NoSQL |
| SQL / Datos | *Use The Index, Luke* · pgexercises | CC BY-NC-ND · © | (cita) | índices, ejercicios |
| Datasets | UCI ML Repository · Eurostat · Our World in Data · `datos.gob.es` · data.gov | CC BY 4.0 · CC BY 4.0 · CC BY 4.0 · CC BY 4.0 · dominio público | [reusar] (confirmar licencia del dataset específico antes de usar — la política varía por dataset) | datos para `sql_exec` y DS |
| Datasets | `github.com/mwaskom/seaborn-data` · `github.com/vega/vega-datasets` | BSD-3 | [reusar] | datasets pequeños |
| Seguridad | NIST CSRC (SP 800-53/61/63/115/144) · CISA | dominio público (US gov) | [reusar] | controles, respuesta a incidentes |
| Seguridad | `github.com/OWASP/CheatSheetSeries` · `OWASP/wstg` · `OWASP/Top10` · `OWASP/ASVS` | CC BY-SA 4.0 (ASVS 3.0) | [H.LIC] | checklists |
| Seguridad | `github.com/mitre-attack/attack-stix-data` | MITRE custom (permisiva; investigación y uso comercial con atribución a MITRE ATT&CK®) | [reusar] atribuir a MITRE | tácticas y técnicas |
| Seguridad | `github.com/juice-shop/juice-shop` · `swisskyrepo/PayloadsAllTheThings` | MIT | [reusar] (uso defensivo/educativo) | laboratorios |
| Seguridad | *Crypto 101* · *Handbook of Applied Cryptography* · CIS Controls · Security+ SY0-701 · ISC2 CC outline | (cita) | (cita) | temarios |
| Frontend / Backend | `github.com/mdn/content` · `mdn/translated-content` (`files/es`) | CC BY-SA 2.5 (prosa) · CC0 (código) | [H.LIC] prosa · [reusar] código | web, **ES nativo** |
| Frontend / Backend | `github.com/freeCodeCamp/freeCodeCamp` | BSD-3 | [reusar] | currículo completo, **tiene ES** |
| Frontend / Backend | `github.com/reactjs/react.dev` · `reactjs/es.react.dev` | CC BY 4.0 (contenido) · MIT (código) | [reusar] | React, **ES nativo** |
| Frontend / Backend | `github.com/fastapi/fastapi` (`docs/es`) · `django/django` (`docs/`) · `pallets/flask` (`docs/`) · `nodejs/node` (`doc/`) | MIT · BSD-3 · BSD-3 · MIT | [reusar] | backend |
| Frontend / Backend | `github.com/microsoft/TypeScript-Website` | CC BY 4.0 (contenido handbook) · MIT (código) | [reusar] | TypeScript |
| Frontend / Backend | `github.com/GoogleChrome/web.dev` | CC BY 4.0 (contenido) · Apache-2.0 (código) | [reusar] | rendimiento, PWA |
| Frontend / Backend | `github.com/lydiahallie/javascript-questions` · `microsoft/Web-Dev-For-Beginners` · `mattmakai/fullstackpython.com` | MIT | [reusar] | preguntas JS (tiene ES), curso web (tiene ES) |
| Frontend / Backend | `github.com/expressjs/expressjs.com` | CC BY-SA 3.0 | [H.LIC] | Express |
| Frontend / Backend | javascript.info · *Eloquent JavaScript* · *YDKJS* · The Odin Project | CC BY-NC 4.0 · CC BY-NC · CC BY-NC-ND · CC BY-NC-SA | (cita) | ideas |
| Frontend / Backend | RFC 9110-9114 (IETF) | IETF Trust (reproducción con atribución) | [reusar] | HTTP |
| Linux / Redes | `github.com/SystemsApproach/book` (Peterson/Davie) | CC BY 4.0 | [reusar] | redes, libro completo |
| Linux / Redes | `github.com/obonaventure/cnp3` (*CNP3*) | CC BY 3.0/4.0 | [reusar] | redes |
| Linux / Redes | `github.com/exercism/bash` | MIT | [reusar] | ejercicios shell |
| Linux / Redes | ArchWiki (`wiki.archlinux.org`) | GFDL 1.3 | [H.LIC] | administración |
| Linux / Redes | *Beej's Guide* · *HPBN* · man-pages (varias) · *TLCL* (Shotts) · Cobbaut · LPI Learning Materials · *OSTEP* · `missing-semester` | © · CC BY-NC-ND · mixtas · CC BY-NC-ND · © · CC BY-NC-ND · © · CC BY-NC-SA | (cita) | temarios, ideas |
| DevOps / Cloud | `github.com/kubernetes/website` (`content/es`) | CC BY 4.0 | [reusar] | Kubernetes, **ES nativo** |
| DevOps / Cloud | `github.com/docker/docs` | Apache-2.0 | [reusar] | Docker |
| DevOps / Cloud | `github.com/prometheus/docs` · `github.com/actions/*` · `github.com/github/docs` | Apache-2.0 · MIT · CC BY 4.0 | [reusar] | observabilidad, CI/CD |
| DevOps / Cloud | `github.com/MicrosoftDocs/azure-docs` (archivado; `learn.microsoft.com` ES) | CC BY 4.0 (contenido) · MIT (código) | [reusar] (confirmar CC BY 4.0 en cada página de learn.microsoft.com antes de usar) | Azure, AZ-900/AI-900/DP-900 |
| DevOps / Cloud | `cloud.google.com/docs` · `github.com/GoogleCloudPlatform/*` (samples) | CC BY 4.0 · Apache-2.0 | [reusar] | GCP |
| DevOps / Cloud | `github.com/awsdocs/*` (archivados 2023) · docs.aws.amazon.com | CC BY-SA 4.0 · propietario | [H.LIC] · (cita) | AWS |
| DevOps / Cloud | `github.com/cncf/curriculum` · HashiCorp docs · Ansible docs · Grafana docs | CC BY (CNCF) · BSL-1.1 (HashiCorp, desde 2023) · GPL-3 · AGPL-3 | (cita) | KCNA/CKA, IaC |
| Móvil | `github.com/swiftlang/swift-book` · `developer.android.com` · `github.com/JetBrains/kotlin-web-site` · `github.com/flutter/website` · `github.com/facebook/react-native-website` | CC BY 4.0 · CC BY 2.5 · Apache-2.0 · CC BY 3.0 · MIT | [reusar] | móvil |
| Español nativo (transversal) | `python-docs-es` · `*-For-Beginners/translations/es` · `mdn/translated-content` · `kubernetes/website/content/es` · `es.react.dev` · `fastapi/docs/es` · freeCodeCamp ES · `d2l-es` · Microsoft Learn ES · ML Crash Course ES | ver filas | ver filas | **fuentes en español que no son traducción automática**; prioridad para la línea roja 3 |
| Español (cita) | *Aprende con Alf* · *El Libro de Python* · *Python para todos* (González Duque) · Wikipedia/Wikilibros ES (CC BY-SA → [H.LIC]) | CC BY-NC-SA · CC BY-NC-SA (probable) · CC BY-NC-SA 2.5 · CC BY-SA | (cita) / [H.LIC] | terminología y enfoque en español |

---

## 3. Certificaciones — 11 construidas; práctica, banco de simulacro reservado y orden por idioma (ADR-54)

Un track de certificación = módulos que son **los dominios oficiales con su peso
verificado** (`exam_domain` + `exam_weight_pct`, suma 100 — `_domain_allocation`
lo valida desde 17.13), simulacro en formato real (nº de ítems, minutos, corte, **el que
publica el proveedor**, con URL y fecha), informe por dominio, y **readiness** (18.1): BKT por
dominio × peso → «listo / no listo» con evidencia. Sin dumps. Sin adivinar pesos.

- **Regla única (ADR-54):** 100 % de los objetivos oficiales cubiertos · práctica
  ≥ máx(300, 3 × L) · **banco de simulacro reservado de 2 × L** (`"pool": "simulacro"`), que no
  sale en práctica ni repaso; L = preguntas del examen. Sin L publicada (AZ-900, AI-901,
  DP-900), las reservadas quedan «pendiente». Sustituye el suelo y el ideal de ADR-53 (15 y
  20 preguntas por skill, banco de 6 × L).
- **El banco reservado existe desde 37.18** (`pool` en `questions`, migración
  `20260930_question_pool`), pero está vacío: 0 reservadas hoy, meta 1.040 para las 8
  certificaciones con L publicada.
- **Orden de las nuevas:** primero las que se examinan en español (comprobado el 2026-09-30:
  GCP Associate Cloud Engineer, LPIC-1, AZ-104); CKA/CKAD/CKS solo se examinan en inglés,
  chino y japonés; CCNA, idioma sin comprobar (la página de Cisco no se pudo leer).

| Proveedor | Certificación | Track de aprendizaje | Estado | Prioridad |
|---|---|---|---|---|
| Python Institute | **PCEP-30-02** | track01 | ✅ track09 — 4 bloques verificados (18.1) | — |
| Python Institute | **PCAP-31-03** | track02 | ✅ track41 — 21 objetivos, 300 Q | — |
| Python Institute | PCPP1 | track03 | ❌ | P3 |
| AWS | **CLF-C02** | track08 (propio) | ✅ 300 Q, 4 dominios verificados | — |
| AWS | **SAA-C03** | track10 | ✅ — 4 dominios, suma 100 (18.1) | — |
| AWS | **AIF-C01** | track11 / track07 | ✅ — 5 dominios completos (18.1) | — |
| AWS | DVA-C02 | track28 | ❌ | P2 |
| AWS | **MLA-C01** → MLA-C02 | track07 | ✅ track43 — 12 task statements, 169 Q (45 de relleno retiradas en 39.42; +49 de GenAI/RAG/agentes/Bedrock/IA responsable en 39.25, mismos 4 dominios); MLA-C01 dejó de ofrecerse en inglés el 2026-09-28, MLA-C02 en beta desde el 29-09 (39.25, verificado 2026-10-02); formato C01 (65 preguntas, 130 min) fijado en 37.19 | — |
| AWS | SOA-C02 · DOP-C02 · SAP-C02 | track18/19 | ❌ | P3 |
| AWS | Security Specialty (SCS-C02) | track25 | ❌ | P2 |
| ISC2 | **CC** (Certified in Cybersecurity, examen gratuito) | track13 | ✅ **track40** — 374 Q, `correct_index` auditado (18.2/18.14); migrado al **outline de 2026-09-01** en 37.22 (2026-10-02): 5 dominios nuevos (24/17,3/20/21,3/17,3, examen adaptativo de 100–125 ítems), 20 skills reetiquetadas + 3 nuevas (GRC/métricas, nube, monitoreo/pruebas) | — |
| ISC2 | SSCP · CCSP · CISSP | track13/25 | ❌ | P3 |
| CompTIA | **Security+ SY0-701** | track13 | ✅ track42 — 300 Q; V8 (SY0-801, solo inglés) el 2026-11-17 (39.26) | — |
| CompTIA | Network+ · Linux+ · PenTest+ · CySA+ | track17/15/24 | ❌ | P2 |
| Microsoft | **AZ-900 · AI-901 · DP-900** | track44/45/46 | ✅ AZ-900 95 Q, AI-901 76 Q, DP-900 96 Q (faltan 205/224/204 de práctica para 300 cada una); AI-901 migrado de AI-900 (39.24, 2026-10-02): 2 dominios, 12 skills, 76 Q, 12 lecciones | — |
| Microsoft | AZ-104 · AZ-204 · AI-102 · DP-100 · DP-203 · AZ-305 | track22/07/21/20 | ❌ | **AZ-104: siguiente** (examen en español) · resto P2 |
| Google Cloud | Digital Leader · ACE · PCA · PDE · PMLE | track23/20/07 | ❌ | **ACE: siguiente** (examen en español) · resto P2 |
| CNCF | KCNA · CKA · CKAD · CKS | track18 | ❌ | P2 (sin examen en español; CKA/CKAD son prácticos: solo teoría + escenario) |
| HashiCorp | Terraform Associate 003 | track19 | ❌ | P2 |
| GitHub | Foundations · Actions | track26/19 | ❌ | P2 |
| Linux Foundation / LPI | LFCS · LPIC-1 | track15 | ❌ | **LPIC-1: siguiente** (examen en español) · LFCS P3 |
| Cisco | CCNA 200-301 | track17 | ❌ | P2 (idioma sin comprobar; v2.0 anunciada) |
| EC-Council / OffSec | CEH · OSCP | track24 | solo cita (propietario, práctico) | — |
| Databricks | DE Associate · ML Associate | track20/21 | ❌ | P3 |
| MongoDB | Associate Developer | track27 | ❌ | P3 |
| PostgreSQL (EDB) | Associate | track12 | ❌ | P3 |
| Oracle | 1Z0-071 SQL | track12 | ❌ | P3 |
| ISTQB | CTFL v4 | track29 | ❌ | P3 |
| Scrum.org | PSM I | track30 | ❌ | P3 |
| JS Institute | JSE-1 | track14 | ❌ | P3 |
| The Open Group | TOGAF Foundation | track05 | ❌ | P3 |

**Hoy: 11 construidas.** Lo que falta por la regla de ADR-54 (`catalog_coverage.py`,
2026-10-03): +872 preguntas de práctica (PCEP +33, AIF-C01 +75, MLA-C01 +131, AZ-900 +205,
AI-901 +224, DP-900 +204) y +1.040 reservadas. Sin objetivos contados: Security+ SY0-701. Sin
longitud de examen publicada: AZ-900, AI-901 y DP-900. La cobertura de objetivos se mide hoy
con un proxy (una skill por objetivo): no hay mapa objetivo → skill. La lista de
arriba es el universo candidato, no una meta de «55»: cada nueva entra por el orden de este §3.

Programas de afiliado (estrategia v3, Parte II): Python Institute, CompTIA, ISC2 —
**sin verificar**; siguen siendo *guessing* hasta que el dueño contacte.

---

## 4. Las capas que faltan en todos los tracks

| Capa | Hoy (2026-10-01) | Objetivo (ADR-54 salvo donde se dice) | Cómo se verifica |
|---|---|---|---|
| Lección por skill (150-300 palabras ES+EN, ejemplo ejecutado) | 730/730 skills con lección | 1 lección por skill en todos los tracks del plan | `test_lessons.py` (ratchet `MIN_LESSONS`) + `catalog_coverage.py` |
| Ejemplo resuelto + problema de completar (fading) | solo la lección | 1 secuencia por skill | test de estructura |
| Práctica adaptativa (quiz) | ✅ 11.005 Q · 15,1 por skill | 10 por skill, ≥ 3 ejecutables donde el navegador ejecute (320 por track de 32 skills) | `check_question_bank.py` + `catalog_coverage.py` |
| **Proyectos multi-paso con tests en runtime** | **0** | 10 por track ejecutable (`exercism/*` MIT como semilla) — tipo `project` + `ProjectScreen` | e2e 1 proyecto por runtime |
| Examen de nivel + certificado verificable | ✅ 17.2 (spec e2e sin correr) | igual | `track-exam.spec.ts` |
| Simulacro de certificación en formato real | ✅ 11; formato del proveedor fijado por test en AIF-C01, MLA-C01, AZ-900, DP-900 (37.19) e ISC2 CC (37.22, 2026-10-02: outline 2026-09-01); Microsoft no publica el número de preguntas, así que AZ-900, AI-901 y DP-900 no tienen simulacro cronometrado | formato del proveedor + **banco reservado 2 × examen** (0/1.040 hoy) | `test_certification_blueprints.py` + 37.18 |
| **Readiness por dominio** | 18.1 | «P(aprobar)» por cert con BKT × peso oficial, calibrado frente al examen real con n publicado | 18.1 + métricas de ADR-53 §8 |
| Glosario | 1.044 términos | 1 término por skill (32 por track de la forma) | `check_docs.py` |
| **Vídeo explicativo** | **0** | 1 animación de 30-90 s por skill donde aporte (algoritmos, redes, arquitectura, SQL) | 18.9 |
| Runtimes en navegador | Python (Pyodide) ✅ · SQL (sql.js) ✅ · **JS (Worker sandbox) ✅ (18.3)** · shell ❌ | shell = `fill_blank` (v86 descartado por peso, línea roja 8) | `useRuntime` + e2e por runtime |
| **Social login** | **0** (email-only) | GitHub + Google (web) · **Sign in with Apple (obligatorio, App Store 4.8)** · Google nativo (Android) | 19.1 / 19.2 / 19.3, e2e con proveedor simulado |
| **Bootcamps** (secuencia de tracks + calendario + meta diaria) | **0** | 3 iniciales sobre contenido existente (Python→PCEP, Cloud, IA); cohortes en vivo solo tras H.10 | 19.4 |
| **Playground libre** | **0** | Python · SQL · JS sin servidor, historial local | 19.5 |
| Roadmap por rol visible sin cuenta + prueba social reproducible | landing con hero | como Educative, con cifras de `/evidence` | 19.8, Lighthouse SEO 100 |

---

## 5. Vídeo — lo que es real

- **Manim Community (MIT)** + **Piper TTS (MIT)**: animación de concepto desde un
  script Python, voz sintética ES/EN, subtítulos, WebM autohospedado (línea roja 5),
  `preload="none"` para no tocar el LCP. Requiere ffmpeg + LaTeX en el PC de
  render; Controlled Folder Access obliga a renderizar en el scratchpad y copiar.
- **Qué NO es:** un profesor a cámara. Es un explicador tipo 3Blue1Brown-lite.
  Vale para algoritmos, redes, SQL, arquitectura; vale poco para «cómo configurar
  IAM». Para eso, lección + escenario.
- Volumen: 1/skill donde aporte ≈ 300-400 vídeos. Piloto 17.7 (10 en track01)
  decide si escala. Sin piloto verificado en navegador, no se autora en masa.
- **Post-producción (19.10):** `Hainrixz/editor-pro-max` (MIT) sobre Remotion —
  títulos, subtítulos ES/EN con Whisper, export para redes. Remotion es gratuita
  para individuos y empresas de ≤ 3 personas; si la entidad (sin decidir, H.29; ADR-47 suspende la premisa griega) crece, se paga o se cambia.

---

## 5b. Herramientas externas de autoría — fuera de la app, nunca en el bundle (ADR-12)

Evaluadas el 2026-09-18 con URL. Ninguna toca el runtime (línea roja 5).

| Herramienta | Qué es | Licencia | Uso en Whetzy |
|---|---|---|---|
| `hainrixz/claude-webkit` | Skills de Claude Code que generan una landing Next.js y despliegan a Vercel | MIT | **Referencia** para 19.8 (skills de design system y SEO). No se adopta Next.js ni Vercel: seguimos en Vite + Cloudflare Pages |
| `AgriciDaniel/banana-claude` | Skill de Claude Code para generar/editar imágenes con Gemini, con aprobación de coste | MIT (API de pago) | **Sí, 19.9**: iconos de tracks, feature graphic, banners de tiendas. **Nunca** diagramas técnicos de lecciones (SVG/Manim) |
| `Hainrixz/editor-pro-max` | Editor de vídeo por lenguaje natural sobre Remotion, local, Whisper + FFmpeg | MIT (Remotion: gratis ≤ 3 personas) | **Sí, 19.10**: post-producción del piloto Manim |
| Maia (Matillion) | Plataforma comercial de pipelines de datos | Propietaria, de pago | **No.** Whetzy no tiene ETL; como mucho, cita en track20 |
| `PleasePrompto/notebooklm-mcp` | Servidor MCP que rasca NotebookLM con Chrome + Patchright (evasión de detección) | MIT — **archivado sept-2026** | **No se instala.** Sin mantenimiento, zona gris de ToS de Google, no crea cuadernos. El grounding con cita se hace con el BM25 propio sobre fuentes libres (19.7) |

---

## 6. Cuánto cuesta el plan — aritmética, no fe (ADR-54, 2026-10-01)

Cifras de `python scripts/catalog_coverage.py` sobre `80cd3ad`. El ritmo es el único medido:
**518 preguntas verificadas por sesión** (sesión 18.4, `bec734c`). Todo lo demás es división.

| Qué | Preguntas que faltan | Sesiones (≈ Q / 518) |
|---|---|---|
| Antes de nada: el piloto (`LANZAMIENTO_PILOTO.md`) | 0 | — |
| 11 certificaciones: práctica ≥ máx(300, 3 × L) (+872) y banco reservado de 2 × L (+1.040; sin AZ-900, AI-901 y DP-900, cuya longitud no se publica) | 1.912 | ≈ 4 |
| 24 tracks construidos a la forma 32 × 10: 12 de nivel A (+1.280) · 2 de B (+240) · 10 de C (+1.090) | 2.610 | ≈ 5 |
| **Total del plan** | **4.522** | **≈ 9** |
| *Solo cuando la demanda los active (no cuentan en el total):* track24/25 reconstruidos (2 × 320) · nuevos A (3 × 320) · B (7 × 320) · C (9 × 320) | 640 · 960 · 2.240 · 2.880 | ≈ 1 · 2 · 4 · 6 |

- Además de preguntas: +261 skills, +261 lecciones y +266 términos en los tracks construidos.
- Ejecutables (≥ 3 por skill): 13 tracks (16, 17, 18-23 y 26-30) salen «sin medir» porque no
  tienen preguntas ejecutables ni exención escrita en `scripts/metas_catalogo.json`. track16 y
  track17 entraron en esa lista el 2026-10-01, al convertir en `fill_blank` sus «ejecutables» sin hueco.
- Sustituye la aritmética de ADR-53 (suelo 31.056 preguntas ≈ 60 sesiones; ideal 94.611 ≈ 183).
- La autoría la hace Haiku 4.5 con revisión completa de Sonnet 5 (ADR-52). El piloto de
  track28 dio 7 de 10 malas: si se repite, el ritmo real será menor que 518 por sesión.
- Lo que **no** entra en ningún calendario de agente: H.2, H.3, H.4, H.10, H.14. Sin
  distribución el marcador competitivo se queda donde esté el contenido (teardown §14).
- **Restricción de fuentes (ADR-11) y coste:** trabajar solo con fuentes libres no
  encarece nada — la autoría siempre fue original y citada. Los tracks de cloud y
  certificaciones de proveedor se escriben contra docs propietarias *citadas*.

---

## 7. Puerta de calidad — obligatoria por bloque (lección de track12)

Ninguna autoría en masa entra en `master` sin pasar **las siete**:

1. **Schema canónico**: `tracks.json` con `name_es/name_en/order/color/icon`,
   módulos con `level` y skills con `name_*` — nunca `title_*`. El loader hace
   `data["name_es"]` y **revienta** con otra forma (y `start.sh` se lo traga).
2. **Ejecutado, no descrito**: cada `sql_exec`/`fill_blank_exec`/`fix_bug` con su
   fill en el sidecar correcto (`sql_exec_reference_fills.json` /
   `exec_reference_solutions.json`) y `pytest tests/content` en verde; la
   `correct_answer` es lo que imprimió el motor, no lo que escribió el modelo.
3. **Verificador fuera del scratchpad compartido** (`orch-private/`): un worker
   sobrescribió el verificador de la sesión `ar` y tres comprobaciones pasaron
   sobre el script equivocado.
4. **Español con tildes y sin mojibake**: `test_spanish_accents.py` +
   `test_no_double_encoded_text` + relectura del fichero por el worker.
5. **Sesgo de posición y opciones repetidas**: `check_question_bank.py` PASS
   (Haiku entrega el 100 % en la posición A si no se rebalancea).
6. **Diversidad (37.0)**: `scripts/question_diversity.py` PASS: enunciados distintos,
   opciones de más de una palabra, ejecutables con código, fuente indexada.
7. **Plan y catálogo en el mismo mundo (ADR-54)**: `python scripts/catalog_coverage.py
   --check` PASS; y ninguna pregunta `"pool": "simulacro"` sale en práctica ni repaso (37.18).

Modelo por tarea (ADR-52, 2026-09-27): **autoría masiva → Haiku 4.5; revisión adversaria
completa y corrección → Sonnet 5; lecturas e inventarios → Haiku 4.5; hilo interactivo →
Sonnet 5; nunca Fable ni Opus 4.x**. Herramientas del lote: `scripts/content_qa/`. Un bloque que no pasa la puerta no
existe: no se cuenta, no se anota, no se despliega.

---

## 8. Competencia — catálogo, con la honestidad que exige la línea roja 9

Captura del 2026-09-30. **[S]** = descargado y leído por la sesión; **[A]** = leído por un
agente y no reproducido (probable); el resto de cifras antiguas se retiraron.

| Plataforma | Catálogo | Unidad | Fuente |
|---|---|---|---|
| **Boot.dev** | 51 cursos · 2.823 lecciones · 1.053 h; mediana 51 lecciones y 20 h por curso | curso de horas | [S] boot.dev/courses |
| **Kodree** | 42 tarjetas de curso en la home (algunas repetidas) · 687 lecciones · 2.559 tareas; «60+ COURSES» en App Store | curso corto | [S] kodree.com; App Store (2026-09-28, COMPETENCIA §A.2b) |
| **Exercism** | 83 lenguajes; Python: 146 ejercicios en 17 conceptos | ejercicio | [S] exercism.org |
| **Pocket Prep** (ISC2 CC) | 800 preguntas | pregunta de práctica | [S] pocketprep.com |
| Educative | 2.200+ cursos · 330+ proyectos | curso | verificado en vivo 2026-09-18 (teardown §11.3) |
| DataCamp | 776 cursos · 32 career tracks; Intro to Python: 4 h, 46 ejercicios | curso de horas | [A] datacamp.com (antibot a la descarga directa) |
| Codecademy | 846 resultados de catálogo; Full-Stack Engineer 51 cursos / 150 h | curso | [A] codecademy.com/catalog |
| Platzi | «+2000 cursos, 30 rutas»; Python: 32 clases, 4 h de vídeo + 12 h de práctica | curso de vídeo | [A] platzi.com |
| EDteam | 41 rutas, mediana 5 cursos y 33 h por ruta | ruta | [A] ed.team/especialidades |
| Brilliant | 14 cursos de CS, 35 de matemáticas | curso | [A] brilliant.org/topics/coding |
| Mimo | 4 rutas de carrera + 8 cursos; lecciones de 5 min | ruta | [A] mimo.org |
| Tutorials Dojo / Udemy (AWS) | 6 simulacros × 65 = 390 preguntas por examen (Maarek, Bonso); TD: 7–9 simulacros cronometrados | pregunta | [A] (Udemy devolvió 403) |
| **Whetzy** | 24 tracks de aprendizaje + 11 certificaciones · 730 skills · 11.005 preguntas | skill | `catalog_coverage.py` |

**Lectura honesta (2026-10-01, ADR-54):**
- En **amplitud** Whetzy ya supera a su competencia directa: Boot.dev enseña en 3 rutas y
  Kodree en unas 7, frente a 24 tracks y 11 certificaciones.
- En **profundidad por track** está por debajo: 20 de los 24 tracks tienen 20–30 skills y 3
  tienen 12 (track15-17); solo track01 pasa de 50. La forma de ADR-54 (32 skills · 320
  preguntas) **no** iguala las horas de un curso mediano de Boot.dev (51 lecciones, 20 h): es
  un límite escrito en ADR-54, que compite en práctica adaptativa, ES/EN y ejecución.
- Frente a los **bancos de certificación**, Whetzy está por debajo (90–375 preguntas de
  práctica por examen contra 390–800) y **sin banco de simulacro reservado** todavía.
- «Curso» no es una unidad comparable: el de Platzi o Boot.dev son horas, el módulo de Whetzy
  son 4 skills. Por eso el plan mide skills, no cursos.
- La tesis defendible sigue siendo la de §8.4 del teardown: *el mejor en un nicho que los
  grandes ignoran* (ES/EN nativo + motor auditado + ejecución en navegador).

---

## 9. Lo que no se construye (y por qué)

- **Marketplace de creadores** (estrategia v3, Parte III-IV): **no hasta ≥ 100
  usuarios activos verificados.** Con 0 usuarios es una sala vacía; ninguna de
  las apps de la liga objetivo tiene uno. El marketplace es la **serie 28** (se
  construye entera; no se abre al público antes de ≥ 100 usuarios activos, ADR-47).
  Precio del plan Creador y reparto 80/20: ADR-41. La antigua «fase 10» (10.1-10.3,
  simulacro de certificación) no es el marketplace.
- **Shell real en navegador (v86)**: imagen Alpine ≈ 20 MB en móvil, línea roja 8.
  Linux se enseña con `fill_blank` de comandos + salida real ilustrativa (ADR-9).
- **Vídeo filmado**: no hay cámara ni presentador. Manim o nada.
- **Certificación propia de Whetzy**: no vale nada todavía (v3, Parte XI).
- **Los tracks de nivel C de demanda** (§2.0) van después de los A y B, con la misma forma 32 × 10 (ADR-54).

---

## 10. Orden de ejecución — serie 37 en `AUTONOMOUS_STATE.md` (ADR-54)

1. **Antes de cualquier contenido: el piloto** (fila 31.8, `LANZAMIENTO_PILOTO.md`). Lo que
   rompan o pidan los pilotos va primero.
2. **Hecho (código):** 37.18 banco de simulacro reservado y 37.19 formatos de examen del
   proveedor. 37.20 (métricas de producto) está DONE pero vetada en lo nuevo hasta ≥ 100
   registrados reales (31.5).
3. **Después del piloto, primero los tracks y certificaciones que usen los pilotos.** Para el
   resto: 37.22 ISC2 CC al outline de 2026 y 37.10 las 11 certificaciones a la regla de
   ADR-54 (MLA-C01 y Microsoft primero, las más lejos); 37.6 los 24 tracks construidos a la
   forma 32 × 10, **A primero**, luego B y C; 37.7 track24/25.
4. **Tracks nuevos:** 37.8 por demanda (A → B → C), con la misma forma. La fase 4 de ADR-53
   (el ideal por temario) quedó sustituida; 37.21 se reduce a elegir las 32 skills de cada
   track con roadmap.sh como referencia.

Cada bloque de contenido corre como **Workflow paralelo** (autoría Haiku 4.5 por
fichero → revisor y corrector Sonnet 5, ADR-52 → `scripts/content_qa/` → `pytest tests/content` →
`check_question_bank.py` → `question_diversity.py` → `catalog_coverage.py --check` →
`check_docs.py` → commit). Un bloque = un commit verde. Nunca un track a medias en `master`.

---

## 11. Validación de mercado externa (2026-09-18)

> **Fuente:** Estudio independiente *"The Edtech / Learning Platform Market, 2025–2026: A Data-Driven Map With a Spanish-Language Whitespace"*, revisado por el dueño el 2026-09-18. No encargado por Whetzy — validación externa no sesgada.

### 11.1 El gap confirmado

La frase literal del estudio:

> *"No dedicated Spanish-language, AI-native adaptive learning platform for Python/AI/cybersecurity was identified."*

Whetzy es exactamente eso. El estudio confirma que el gap existe y que los incumbentes (Platzi, EDteam, Desafío Latam, KeepCoding) están agregando "chatbot/AI-tutor overlays on top of video/cohort content — not genuine adaptive engines."

**Lo que esto significa para el catálogo:** El motor BKT+FSRS+Elo+DKT no es una ventaja técnica abstracta — es la diferenciación que el mercado de $350B no tiene en español. Llevar el catálogo a la forma 32 × 10 de ADR-54 (antes el suelo y el ideal de ADR-53, sustituidos, y la meta histórica de ADR-46 y «2,700 cursos», ADR-25) refuerza esa diferenciación; el plan vigente no promete superar a nadie en volumen (límites escritos en ADR-54).

### 11.2 Benchmarks del mercado (según el estudio; no reproducidos)

> Las cifras de esta tabla son las que cita el estudio; la sesión no las reprodujo. Las que sí
> se descargaron y leyeron el 2026-09-30 (retención y conversión de apps de educación,
> Duolingo, edX) están en ADR-53 §8 y sustituyen a estas donde choquen.

| Métrica | Valor | Fuente |
|---|---|---|
| Conversión freemium edtech | 2.6% | First Page Sage 2025 |
| Conversión trial-to-paid edtech | ~24.8% | dataset B2C edtech |
| Retención Day-30 education apps | ~2% | Business of Apps 2026 |
| Precio medio suscripción education app | $8.13/mo o $56.09/yr | Business of Apps 2026 |
| Boot.dev ARR | ~$10M | 25K paying × $348/yr |
| Boot.dev equipo | ~13 personas | bootstrapped |
| DataCamp ARR | ~$100M (proyectado) | cashflow positive |
| Platzi estudiantes | 7M+ | YC profile |
| Mercado LATAM e-learning 2024 | ~$30.5B | Arizton |
| Crecimiento LATAM e-learning | ~9.3% CAGR | Arizton |
| Gap AI engineers (demanda/oferta) | ~3.2:1 | 365 Data Science 2026 |
| Python en job postings AI engineer | 71% | 365 Data Science 2026 |

### 11.3 El comparable directo: Boot.dev

Boot.dev es el modelo de negocio más cercano a Whetzy:
- Bootstrapped / indie
- Technical skills (backend: Python, Go, SQL)
- Gamificado
- Career-outcome focused
- $10M ARR con 13 personas y 25,000 paying members *(cifras del estudio, sin reproducir)*

**Diferencias a favor de Whetzy:**
- Motor adaptativo real (Boot.dev es lineal)
- 24 tracks construidos + 11 certificaciones frente a 51 cursos en 3 rutas de Boot.dev (boot.dev, 2026-09-30)
- Español nativo (Boot.dev es solo inglés)
- 11 simulacros de certificación con pesos oficiales (Boot.dev no tiene)
- Bootcamps async (Boot.dev no tiene)

**Diferencias a favor de Boot.dev (para aprender):**
- 3 años de ventaja en comunidad y marca
- Canal YouTube con 100K+ suscriptores
- Modelo LTV claro y documentado (~$348/yr × 25K)

**Conclusión:** Si Boot.dev llegó a $10M ARR con un producto más simple y solo en inglés, Whetzy tiene el techo técnico para superar ese número en el nicho español donde no existe competencia adaptativa.

### 11.4 Riesgo de ventana — qué monitorear

El estudio advierte explícitamente:

> *"If Platzi, DataCamp, or a well-funded entrant ships genuinely adaptive Spanish content at scale, the window narrows quickly — monitor Platzi's Leap integration and any DataCamp Spanish localization."*

**Acción en el ledger:** fila **37.12** (monitoreo trimestral; hasta el 2026-09-24 este párrafo apuntaba a una fila que no existía). Si Platzi anuncia motor adaptativo real o DataCamp anuncia localización al español con motor, escalar a HUMAN-BLOCKED para decisión del dueño sobre aceleración o pivot a nicho de ciberseguridad.

---

## 12. Proyección competitiva con el plan de ADR-53 (antes ADR-46 y ADR-25) — histórica

> **Sustituida en su meta por ADR-54 (2026-10-01).** Esta proyección se hizo con el ideal de
> ADR-53 (Contenido 55 → 85). Con la forma 32 × 10 de ADR-54 **no se ha re-puntuado** con el
> método de `competitive-teardown.md` §7.1: no la cites como meta vigente ni como marcador
> esperado. Lo que sigue es histórico.

### 12.1 Score competitivo proyectado

Los pesos fijos del `competitive-teardown.md` §7.1 no cambian. Lo que cambia es la puntuación en cada dimensión:

| Dimensión | Peso | Hoy (44/100) | Al 100% técnico (~66) | Con el ideal de ADR-53 | Con usuarios |
|---|---|---|---|---|---|
| Distribución | 0.34 | 0 | 0 | 0 | Variable |
| Motor adaptativo | 0.14 | 12 | 14 | 14 | 14 |
| Contenido/alcance | 0.14 | 6 | 8 | 14 | 14 |
| Tutor AI | 0.09 | 8 | 9 | 9 | 9 |
| Ejecución técnica | 0.07 | 7 | 7 | 7 | 7 |
| Gamificación | 0.06 | 5 | 6 | 6 | 6 |
| Bilingüe | 0.06 | 4 | 6 | 6 | 6 |
| PWA/móvil | 0.05 | 4 | 5 | 5 | 5 |
| Accesibilidad | 0.05 | 3 | 5 | 5 | 5 |
| **Total sin distribución** | | **44** | **~60** | **~66** | **~66** |

> **Corregido el 2026-09-24:** la tabla anterior sumaba 49 en la columna «Hoy» donde decía 44, y proyectaba «~79 con 1K usuarios» y «~85 con 10K» sin ninguna aritmética detrás (para 85 haría falta Distribución = 100). Se retiran. Con los pesos de `competitive-teardown.md` §7.1 y las notas de §11: hoy **44**; con el backlog técnico cerrado y sin usuarios **≈ 61**; con tiendas, social login y cohorte beta **≈ 66**; y el catálogo en el ideal de ADR-53 (Contenido 55 → 85; antes se atribuía a ADR-46) añade **+4,2** → **≈ 70**. Por encima de eso solo mueve Distribución, que pesa 0,34 y no se construye.

**La única variable que mueve el marcador más allá de 66 es la distribución.** El ideal de ADR-53 cierra la dimensión de contenido, pero no toca distribución. El dueño la activa con la campaña (YouTube, B2B, comunidades Python en español).

### 12.2 Comparativa final vs competencia directa

| | Platzi | DataCamp | Boot.dev | Educative | **Whetzy (ADR-53 en el ideal + usuarios)** |
|---|---|---|---|---|---|
| Motor adaptativo | ❌ video/cohort | ✅ Optima (EN/AR) | ❌ lineal | Parcial | **✅ BKT+FSRS+Elo+DKT** |
| Español nativo | ✅ | ❌ | ❌ | ❌ | **✅ + EN separado** |
| Cursos/contenido (§8, 2026-09-30) | +2.000 cursos [A] | 776 cursos [A] | 51 cursos [S] | 2.200+ cursos | **(histórico, sustituido por ADR-54) 45 tracks al suelo (50 skills · 800 Q) y al ideal por temario (4.819 skills · 96.380 Q)** |
| Certificaciones | ❌ | ❌ | ❌ | ❌ | **✅ 11 hoy + las que se examinan en español (§3)** |
| Ciberseguridad | ❌ | ❌ | ❌ | Parcial | **✅ 3 tracks** |
| Cloud (AWS/Azure/GCP) | ❌ | ❌ | ❌ | ❌ | **✅ 6 tracks** |
| Móvil (Android/iOS) | ❌ | ❌ | ❌ | ❌ | **✅** |
| Tutor AI con memoria | ❌ | ❌ | ❌ | ❌ | **✅ 3 capas** |
| Créditos cerrados + referidos por activación | sin datos | XP (sin referidos por activación) | gemas | ❌ | **✅ Serie 29 (ADR-34/35)** |
| Pago en USDC liquidado en fiat (LATAM) | ❌ | ❌ | ❌ | ❌ | **✅ tras H.19 (ADR-36)** |
| Credenciales verificables (Open Badges 3.0) | ❌ | ❌ | ❌ | ❌ | **✅ 29.10 (ADR-37)** |
| Token / cripto propia | ❌ | ❌ | ❌ | ❌ | **❌ a propósito (ADR-33)** |
| B2B ready | ✅ | ✅ | ❌ | ✅ | **✅ (Serie 22)** |
| Precio base (verificado 2026-09-24 salvo DataCamp/Educative; COMPETENCIA §A) | $49/mo · $249/año | ~$39/mo (sin verificar) | $59/mo · $399/año | ~$20/mo (sin verificar) | **Pro $14.99/mo (ADR-41; cobro sin abrir, H.19)** |
| Empleabilidad real | Bajo (70% no termina) | Medio | Alto | Medio | **sin dato hasta H.10 (objetivo ADR-32: completion > 50 %)** |

**Whetzy con ADR-53 en el ideal sería técnicamente superior en todas las dimensiones relevantes para el nicho Python→AI Engineer en español.** La única ventaja que los incumbentes mantienen es brand recognition — y eso se construye con distribución, no con código.

### 12.3 El argumento de venta cuando el producto esté completo

> "La única plataforma que adapta el camino a cómo aprendes tú — no al promedio — para llegar de cero a AI Engineer en español, con certificaciones que los empleadores reconocen."

Eso no lo puede decir ningún competidor hoy. Ninguno podrá decirlo en 12-18 meses si la ventana se aprovecha.
