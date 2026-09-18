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
> Última medición: 2026-09-18 (sesión **bg**, 20.2). Estado del banco: ver `## 1`.
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

| Métrica | Valor 2026-09-18 | Comando |
|---|---|---|
| Tracks | **18** (track01–17 + track40) | `python scripts/check_docs.py` |
| Cursos (track × nivel) | **49** | ídem |
| Skills | **378** | ídem |
| Preguntas | **6.233** | `python scripts/check_question_bank.py` |
| Lecciones | 378/378 (100 %) | `pytest tests/content/test_lessons.py` |
| Glosario | **622** | `check_docs.py` |
| Ejecutables | 12 tracks no exentos ≥ 15 % (track16 44,9 %, track17/mod1703 36,7 %, track12 20 %, track13/40 15 %, track14 JS sandbox; track15 exento ADR-9) | `check_question_bank.py` |
| Certificaciones | **5** (CLF-C02, PCEP, SAA-C03, AIF-C01, **ISC2 CC = track40**) — blueprints corregidos en 18.1 (8 passed / 0 xfail) | `pytest tests/content/test_certification_blueprints.py` |
| Proyectos multi-paso | 0 | — |
| Vídeos | 0 | — |

---

## 2. El mapa completo — 26 tracks de aprendizaje

Convención de ids: **tracks de aprendizaje `track12`–`track31`**, **tracks de
certificación `track40`+** (`is_certification: true`, misma forma que track08–11).
Cada track de aprendizaje: **5 módulos × 4 skills = 20 skills · 300 Q · 3 niveles ·
20 lecciones · ≥ 36 términos · ≥ 15 % ejecutable donde el navegador pueda ejecutar
(Python, SQL, JS) o exento con razón (ADR-9)**. Ese es el molde que track12 ya cumple.

Licencias: en la app entra solo contenido propio o MIT / Apache-2 / BSD / CC BY /
CC0 / PSF / dominio público (NIST, RFC, docs de gobierno de EE. UU.). **CC BY-SA
espera a H.LIC; CC BY-NC y docs propietarias (AWS, CompTIA, ISC2, Cisco) se citan,
nunca se copian.** Certificaciones: **nunca dumps**; preguntas propias sobre los
dominios oficiales, con los pesos verificados contra la guía del proveedor (lección
de 17.13). **Desde el 2026-09-18 (ADR-11): solo fuentes gratuitas y legales — no se
compran libros para parafrasearlos y los PDFs pirateados no entran ni como cita.** El
camino con cualquier fuente es el mismo: leer → escribir lección/pregunta original en
ES y EN → citar. Los hechos son libres; la redacción no.

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
| 9 | Seguridad | Ciberseguridad — fundamentos | track13 | stub ✅ (18.2) — 326 Q, 15 % exec, ≥15 Q/skill | NIST SP 800-53/61/63 (dominio público), MITRE ATT&CK (atribución), RFC; OWASP solo cita (BY-SA) | Python `fix_bug`/`fill_blank_exec` (hashlib, hmac, secrets, html, re, ipaddress) | ISC2 CC, Security+ |
| 10 | Web | Frontend (JS/TS/React) | track14 | stub ✅ (18.3) — 12 Q, 2 js_exec, 1 lección, 6 términos | `lydiahallie/javascript-questions` MIT, `Web-Dev-For-Beginners` MIT, MDN (CC BY-SA → cita) | **JS Worker sandbox real (18.3)** | JSE-1 |
| 11 | Fundamentos | Linux / shell | track15 | ❌ | `exercism/bash` MIT, man-pages (cita), *The Linux Command Line* (cita) | exento (fill_blank de comandos) | LPIC-1, Linux+, LFCS |
| 12 | Fundamentos | Algoritmos y estructuras | track16 | ❌ | `TheAlgorithms/Python` MIT, `tech-interview-handbook` MIT; `coding-interview-university` (BY-SA → H.LIC) | Python (≥ 30 %) | — |
| 13 | Fundamentos | Redes | track17 | ❌ | RFCs (IETF), *Computer Networking* (cita), Cisco docs (cita) | Python (`socket`, `ipaddress`) | CCNA, Network+ |
| 14 | DevOps | Docker y Kubernetes | track18 | ❌ | Docs Kubernetes CC BY 4.0, Docker docs (cita) | exento (escenario + decisión) | KCNA, CKA, CKAD, CKS |
| 15 | DevOps | IaC y CI/CD (Terraform, GitHub Actions) | track19 | ❌ | Terraform docs (cita), GitHub Actions docs (cita), `actions/*` MIT | exento | Terraform Associate, GitHub Actions |
| 16 | Datos | Data Engineering | track20 | ❌ | `Data-Science-For-Beginners` MIT, PostgreSQL docs, DuckDB docs MIT | SQL (duckdb-wasm o sql.js) | DP-203, GCP PDE, Databricks DE |
| 17 | Datos | Data Science / Analytics | track21 | ❌ | Kaggle Learn Apache-2, *Python Data Science Handbook* (cita) | Python stdlib (`statistics`, `csv`) | DP-100, Google Data Analytics |
| 18 | Cloud | Azure | track22 | ❌ | Microsoft Learn (cita; propietario) | exento | AZ-900, AZ-104, AZ-204, AI-900, DP-900 |
| 19 | Cloud | GCP | track23 | ❌ | Google Cloud docs (cita; propietario) | exento | Digital Leader, ACE, PCA, PMLE |
| 20 | Seguridad | Ofensiva / pentest | track24 | ❌ | MITRE ATT&CK, NIST SP 800-115 (dominio público), OWASP WSTG (cita) | Python stdlib | eJPT, PenTest+, CEH (cita), OSCP (cita) |
| 21 | Seguridad | Seguridad en la nube | track25 | ❌ | AWS Well-Architected (cita), CIS Benchmarks (cita), NIST 800-144 | exento | AWS Security Specialty, CCSP |
| 22 | Fundamentos | Git y herramientas de desarrollo | track26 | ❌ | Pro Git (CC BY-NC-SA → cita), git docs (GPL → cita), GitHub docs | exento | GitHub Foundations |
| 23 | Datos | NoSQL | track27 | ❌ | MongoDB docs (cita), Redis docs (cita) | exento | MongoDB Associate |
| 24 | Web | Backend (FastAPI / Node) | track28 | ❌ | FastAPI docs MIT, *Full Stack Python* MIT, Node docs MIT | Python stdlib (`http.server`, `json`) | — |
| 25 | Ingeniería | QA y testing | track29 | ❌ | pytest docs MIT, ISTQB syllabus (cita), Playwright docs Apache-2 | Python (`unittest`, `assert`) | ISTQB CTFL |
| 26 | Ingeniería | Agile y producto | track30 | ❌ | Scrum Guide (CC BY-SA → cita), Agile Manifesto (cita) | exento | PSM I |
| 27 | Móvil | Móvil (Android/Kotlin · iOS/Swift · Flutter/RN) | track31 | ❌ (último: sin runtime en navegador) | Android docs Apache-2, Flutter docs BSD, Apple docs (cita) | exento | — |

**Cobertura hoy: 10 de 27 filas (37 %).** 8 tracks completados + track13 ciberseg (326 Q, 15 % exec) + track14 Frontend JS (stub, 12 Q). Faltan **17**: Linux (15), Algoritmos (16), Redes (17), Docker/K8s (18), IaC+CI/CD (19), Data Eng (20), Data Science (21), Azure (22), GCP (23), Pentest (24), Seguridad cloud (25), Git (26), NoSQL (27), Backend (28), QA (29), Agile (30), Móvil (31).

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
| Python | `github.com/python/peps` | dominio público / Open Publication (cabecera de cada PEP) | [reusar] verificar por PEP | PEP 8, 20, 484, 557, 3107… |
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
| Arquitectura | `github.com/heroku/12factor` | verificar (MIT probable) | verificar | doce factores |
| Arquitectura | `microservices.io` · AWS Well-Architected | propietario | (cita) | patrones |
| IA / ML | `github.com/microsoft/ML-For-Beginners` · `AI-For-Beginners` · `Data-Science-For-Beginners` · `generative-ai-for-beginners` | MIT (con `translations/es`) | [reusar] | **cursos completos con español nativo** |
| IA / ML | Google *ML Crash Course* (developers.google.com/machine-learning) | CC BY 4.0 (contenido) · Apache-2.0 (código) | [reusar] | curso, también en ES |
| IA / ML | `github.com/huggingface/course` | Apache-2.0 | [reusar] | NLP/LLM (tiene ES) |
| IA / ML | `github.com/probml/pml-book` (Murphy, *Probabilistic ML*) | MIT | [reusar] | libro completo |
| IA / ML | `github.com/d2l-ai/d2l-en` · `d2l-es` | CC BY-SA 4.0 (texto) · MIT (código) | [H.LIC] texto · [reusar] código | deep learning |
| IA / ML | `github.com/dair-ai/Prompt-Engineering-Guide` · `github.com/mlabonne/llm-course` | MIT · Apache-2.0 | [reusar] | prompting, LLM engineering |
| IA / ML | `github.com/Kaggle/learntools` | Apache-2.0 | [reusar] | ejercicios Kaggle Learn |
| IA / ML | `github.com/scikit-learn/scikit-learn` · `pandas-dev/pandas` · `numpy/numpy` · `pytorch/tutorials` · `keras-team/keras-io` (docs) | BSD-3 · BSD-3 · BSD-3 · BSD-3 · Apache-2.0 | [reusar] | referencia y tutoriales |
| IA / ML | `github.com/openai/openai-cookbook` · `anthropics/anthropic-cookbook` · `anthropics/courses` · `langchain-ai/langchain` (docs) | MIT · verificar · verificar · MIT | [reusar] / verificar | agentes, tool use, RAG |
| IA / ML | `github.com/fastai/fastbook` · *UDL* (Prince) · *Deep Learning* (Goodfellow) · *MML* · *ISLP* · *SLP* (Jurafsky) · Nielsen | GPL-3 código / © texto · CC BY-NC-ND · © · © · © · © · CC BY-NC | (cita) | ideas, no prosa |
| SQL / Datos | `github.com/postgres/postgres` (`doc/`) · sqlite.org/docs | PostgreSQL License · dominio público | [reusar] | referencia SQL |
| SQL / Datos | `github.com/duckdb/duckdb-web` | MIT | [reusar] | SQL analítico |
| SQL / Datos | `github.com/wesm/pydata-book` | MIT (código) · CC BY-NC-ND (texto) | [reusar] código · (cita) texto | pandas |
| SQL / Datos | `github.com/redis/redis-doc` · MongoDB docs | CC BY-SA 4.0 · CC BY-NC-SA 3.0 | [H.LIC] · (cita) | NoSQL |
| SQL / Datos | *Use The Index, Luke* · pgexercises | CC BY-NC-ND · © | (cita) | índices, ejercicios |
| Datasets | UCI ML Repository · Eurostat · Our World in Data · `datos.gob.es` · data.gov | CC BY 4.0 · CC BY 4.0 · CC BY 4.0 · CC BY 4.0 · dominio público | [reusar] verificar por dataset | datos para `sql_exec` y DS |
| Datasets | `github.com/mwaskom/seaborn-data` · `github.com/vega/vega-datasets` | BSD-3 | [reusar] | datasets pequeños |
| Seguridad | NIST CSRC (SP 800-53/61/63/115/144) · CISA | dominio público (US gov) | [reusar] | controles, respuesta a incidentes |
| Seguridad | `github.com/OWASP/CheatSheetSeries` · `OWASP/wstg` · `OWASP/Top10` · `OWASP/ASVS` | CC BY-SA 4.0 (ASVS 3.0) | [H.LIC] | checklists |
| Seguridad | `github.com/mitre-attack/attack-stix-data` | Apache-2.0 (datos) · términos ATT&CK | [reusar] verificar términos | tácticas y técnicas |
| Seguridad | `github.com/juice-shop/juice-shop` · `swisskyrepo/PayloadsAllTheThings` | MIT | [reusar] (uso defensivo/educativo) | laboratorios |
| Seguridad | *Crypto 101* · *Handbook of Applied Cryptography* · CIS Controls · Security+ SY0-701 · ISC2 CC outline | (cita) | (cita) | temarios |
| Frontend / Backend | `github.com/mdn/content` · `mdn/translated-content` (`files/es`) | CC BY-SA 2.5 (prosa) · CC0 (código) | [H.LIC] prosa · [reusar] código | web, **ES nativo** |
| Frontend / Backend | `github.com/freeCodeCamp/freeCodeCamp` | BSD-3 | [reusar] | currículo completo, **tiene ES** |
| Frontend / Backend | `github.com/reactjs/react.dev` · `reactjs/es.react.dev` | CC BY 4.0 (contenido) · MIT (código) | [reusar] | React, **ES nativo** |
| Frontend / Backend | `github.com/fastapi/fastapi` (`docs/es`) · `django/django` (`docs/`) · `pallets/flask` (`docs/`) · `nodejs/node` (`doc/`) | MIT · BSD-3 · BSD-3 · MIT | [reusar] | backend |
| Frontend / Backend | `github.com/microsoft/TypeScript-Website` | MIT (código) · verificar (handbook) | verificar | TypeScript |
| Frontend / Backend | `github.com/GoogleChrome/web.dev` | CC BY 4.0 (contenido) · Apache-2.0 (código) | [reusar] | rendimiento, PWA |
| Frontend / Backend | `github.com/lydiahallie/javascript-questions` · `microsoft/Web-Dev-For-Beginners` · `mattmakai/fullstackpython.com` | MIT | [reusar] | preguntas JS (tiene ES), curso web (tiene ES) |
| Frontend / Backend | `github.com/expressjs/expressjs.com` | CC BY-SA 3.0 | [H.LIC] | Express |
| Frontend / Backend | javascript.info · *Eloquent JavaScript* · *YDKJS* · The Odin Project | CC BY-NC-SA (verificar) · CC BY-NC · CC BY-NC-ND · CC BY-NC-SA | (cita) | ideas |
| Frontend / Backend | RFC 9110-9114 (IETF) | IETF Trust (reproducción con atribución) | [reusar] | HTTP |
| Linux / Redes | `github.com/SystemsApproach/book` (Peterson/Davie) | CC BY 4.0 | [reusar] | redes, libro completo |
| Linux / Redes | `github.com/obonaventure/cnp3` (*CNP3*) | CC BY 3.0/4.0 | [reusar] | redes |
| Linux / Redes | `github.com/exercism/bash` | MIT | [reusar] | ejercicios shell |
| Linux / Redes | ArchWiki (`wiki.archlinux.org`) | GFDL 1.3 | [H.LIC] | administración |
| Linux / Redes | *Beej's Guide* · *HPBN* · man-pages (varias) · *TLCL* (Shotts) · Cobbaut · LPI Learning Materials · *OSTEP* · `missing-semester` | © · CC BY-NC-ND · mixtas · CC BY-NC-ND · © · CC BY-NC-ND · © · CC BY-NC-SA | (cita) | temarios, ideas |
| DevOps / Cloud | `github.com/kubernetes/website` (`content/es`) | CC BY 4.0 | [reusar] | Kubernetes, **ES nativo** |
| DevOps / Cloud | `github.com/docker/docs` | Apache-2.0 | [reusar] | Docker |
| DevOps / Cloud | `github.com/prometheus/docs` · `github.com/actions/*` · `github.com/github/docs` | Apache-2.0 · MIT · CC BY 4.0 | [reusar] | observabilidad, CI/CD |
| DevOps / Cloud | `github.com/MicrosoftDocs/azure-docs` (archivado; `learn.microsoft.com` ES) | CC BY 4.0 (contenido) · MIT (código) | [reusar] verificar por página | Azure, AZ-900/AI-900/DP-900 |
| DevOps / Cloud | `cloud.google.com/docs` · `github.com/GoogleCloudPlatform/*` (samples) | CC BY 4.0 · Apache-2.0 | [reusar] | GCP |
| DevOps / Cloud | `github.com/awsdocs/*` (archivados 2023) · docs.aws.amazon.com | CC BY-SA 4.0 · propietario | [H.LIC] · (cita) | AWS |
| DevOps / Cloud | `github.com/cncf/curriculum` · HashiCorp docs · Ansible docs · Grafana docs | verificar · verificar (MPL/©) · GPL-3 · AGPL | verificar / (cita) | KCNA/CKA, IaC |
| Móvil | `github.com/swiftlang/swift-book` · `developer.android.com` · `github.com/JetBrains/kotlin-web-site` · `github.com/flutter/website` · `github.com/facebook/react-native-website` | CC BY 4.0 · CC BY 2.5 · Apache-2.0 · CC BY 4.0 (verificar) · MIT | [reusar] | móvil |
| Español nativo (transversal) | `python-docs-es` · `*-For-Beginners/translations/es` · `mdn/translated-content` · `kubernetes/website/content/es` · `es.react.dev` · `fastapi/docs/es` · freeCodeCamp ES · `d2l-es` · Microsoft Learn ES · ML Crash Course ES | ver filas | ver filas | **fuentes en español que no son traducción automática**; prioridad para la línea roja 3 |
| Español (cita) | *Aprende con Alf* · *El Libro de Python* · *Python para todos* (González Duque) · Wikipedia/Wikilibros ES (CC BY-SA → [H.LIC]) | CC BY-NC-SA · verificar · CC BY-NC-SA 2.5 · CC BY-SA | (cita) / [H.LIC] | terminología y enfoque en español |

---

## 3. Certificaciones — 55 objetivo, 4 construidas

Un track de certificación = módulos que son **los dominios oficiales con su peso
verificado** (`exam_domain` + `exam_weight_pct`, suma 100 — `_domain_allocation`
lo valida desde 17.13), ≥ 15 Q/skill, simulacro en formato real (nº de ítems,
minutos, corte), informe por dominio, y **readiness** (18.1): BKT por dominio ×
peso → «listo / no listo» con evidencia. Sin dumps. Sin adivinar pesos.

| Proveedor | Certificación | Track de aprendizaje | Estado | Prioridad |
|---|---|---|---|---|
| Python Institute | **PCEP-30-02** | track01 | ✅ track09 — 4 bloques verificados (18.1) | — |
| Python Institute | PCAP-31-03 | track02 | ❌ | P1 (cuña, siguiente escalón) |
| Python Institute | PCPP1 | track03 | ❌ | P3 |
| AWS | **CLF-C02** | track08 (propio) | ✅ 300 Q, 4 dominios verificados | — |
| AWS | **SAA-C03** | track10 | ✅ — 4 dominios, suma 100 (18.1) | — |
| AWS | **AIF-C01** | track11 / track07 | ✅ — 5 dominios completos (18.1) | — |
| AWS | DVA-C02 | track28 | ❌ | P2 |
| AWS | MLA-C01 | track07 | ❌ | P1 |
| AWS | SOA-C02 · DOP-C02 · SAP-C02 | track18/19 | ❌ | P3 |
| AWS | Security Specialty (SCS-C02) | track25 | ❌ | P2 |
| ISC2 | **CC** (Certified in Cybersecurity, examen gratuito) | track13 | ✅ **track40** — 353 Q, 5 dominios con pesos verificados, 15 % exec, `correct_index` auditado (18.2 / 18.14) | — |
| ISC2 | SSCP · CCSP · CISSP | track13/25 | ❌ | P3 |
| CompTIA | **Security+ SY0-701** | track13 | ❌ (48 % de ofertas cyber, estrategia v3) | P1 |
| CompTIA | Network+ · Linux+ · PenTest+ · CySA+ | track17/15/24 | ❌ | P2 |
| Microsoft | AZ-900 · AI-900 · DP-900 | track22/06/12 | ❌ | P1 (fundamentals: 3 exámenes, un molde) |
| Microsoft | AZ-104 · AZ-204 · AI-102 · DP-100 · DP-203 · AZ-305 | track22/07/21/20 | ❌ | P2 |
| Google Cloud | Digital Leader · ACE · PCA · PDE · PMLE | track23/20/07 | ❌ | P2 |
| CNCF | KCNA · CKA · CKAD · CKS | track18 | ❌ | P2 (CKA/CKAD son prácticos: solo teoría + escenario) |
| HashiCorp | Terraform Associate 003 | track19 | ❌ | P2 |
| GitHub | Foundations · Actions | track26/19 | ❌ | P2 |
| Linux Foundation / LPI | LFCS · LPIC-1 | track15 | ❌ | P3 |
| Cisco | CCNA 200-301 | track17 | ❌ | P2 |
| EC-Council / OffSec | CEH · OSCP | track24 | solo cita (propietario, práctico) | — |
| Databricks | DE Associate · ML Associate | track20/21 | ❌ | P3 |
| MongoDB | Associate Developer | track27 | ❌ | P3 |
| PostgreSQL (EDB) | Associate | track12 | ❌ | P3 |
| Oracle | 1Z0-071 SQL | track12 | ❌ | P3 |
| ISTQB | CTFL v4 | track29 | ❌ | P3 |
| Scrum.org | PSM I | track30 | ❌ | P3 |
| JS Institute | JSE-1 | track14 | ❌ | P3 |
| The Open Group | TOGAF Foundation | track05 | ❌ | P3 |

**Cobertura hoy: 5 de ~55 (9 %), las cinco con blueprint verificado.**

Programas de afiliado (estrategia v3, Parte II): Python Institute, CompTIA, ISC2 —
**sin verificar**; siguen siendo *guessing* hasta que el dueño contacte.

---

## 4. Las capas que faltan en todos los tracks

| Capa | Hoy | Objetivo | Cómo se verifica |
|---|---|---|---|
| Lección por skill (150-300 palabras ES+EN, ejemplo ejecutado) | 281/301 → 301/301 (18.0) | 1/skill en los 27 tracks | `test_lessons.py` (ratchet `MIN_LESSONS`) |
| Ejemplo resuelto + problema de completar (fading) | solo la lección | 1 secuencia por skill | test de estructura |
| Práctica adaptativa (quiz) | ✅ 5.024 Q | ≥ 15 Q/skill en 27 tracks (≈ 8.100 Q) | `check_question_bank.py` |
| **Proyectos multi-paso con tests en runtime** | **0** | 10 por track ejecutable (`exercism/*` MIT como semilla) — tipo `project` + `ProjectScreen` | e2e 1 proyecto por runtime |
| Examen de nivel + certificado verificable | ✅ 17.2 (spec e2e sin correr) | igual | `track-exam.spec.ts` |
| Simulacro de certificación en formato real | ✅ 4 (3 mal) | 55 | `test_certification_blueprints.py` sin xfail |
| **Readiness por dominio** | **0** | «P(aprobar)» por cert con BKT × peso oficial | 18.1 |
| Glosario | 444 + 36 | ≥ 36/track | `check_docs.py` |
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
  para individuos y empresas de ≤ 3 personas; si la IKE crece, se paga o se cambia.

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

## 6. Cuánto cuesta cerrar el mapa — aritmética, no fe

Rendimiento demostrado (track12, sesión `at`+`au`): 300 Q + 20 lecciones + 36
términos + verificación = **4 agentes Haiku de autoría + 6 de reparación +
verificador propio**, ≈ 0,5 M tokens Haiku y ≈ 60 k Sonnet/Fable de orquestación.
**Y aun así salió roto a `master`** (schema distinto, fills sin ejecutar, 20
lecciones y 36 términos sin escribir): la puerta de QA no es opcional, ver §7.

| Bloque | Volumen | Tokens (Haiku) | Sesiones con Workflow paralelo |
|---|---|---|---|
| 19 tracks de aprendizaje nuevos | 5.700 Q · 380 lecciones · 684 términos | ≈ 10 M | ≈ 5 (4 tracks/sesión) |
| 51 certificaciones nuevas (≈ 225 Q, 4-5 dominios) | ≈ 11.500 Q | ≈ 10 M | ≈ 8 |
| Corregir 3 blueprints (17.13) + readiness (18.1) | código + ≈ 150 Q AIF | ≈ 0,5 M + Sonnet | 1 |
| Proyectos 10/track ejecutable (≈ 12 tracks) | 120 | ≈ 2 M (Sonnet) | 2 |
| Runtime JS real + sandbox | código | Sonnet | 1 |
| Vídeo piloto → escala | 10 → 300 | render local | 1 + N |
| Serie 19: social login (web/Apple/Android), bootcamps, playground, biblioteca RAG, landing, assets, vídeo post | código | Sonnet | ≈ 5 |
| **Total** | **≈ 22 k Q · 700 lecciones · 120 proyectos · 55 certs + Serie 19** | **≈ 25 M** | **≈ 23-25 sesiones** |

- **Al ritmo de presupuesto de esta semana** (85 % del cupo consumido por una
  sesión larga): 1-2 tracks/semana → **≈ 10-14 meses**.
- **Con cupo sin racionar y Workflow paralelo**: **≈ 8-10 semanas** para todo el
  backlog técnico (Series 17-19). Las 17 filas de tracks que faltan y las 50
  certificaciones son el grueso; la Serie 19 entera cabe en ≈ 5 sesiones.
- Lo que **no** entra en ningún calendario de agente: H.2, H.3, H.4, H.10, H.14.
  Sin ellos el marcador se queda en ≈ 61; con ellos, ≈ 66 (teardown §11.6).
- La diferencia es el plan de Claude del dueño, no la capacidad del agente. Esto
  se dice aquí para que ninguna sesión vuelva a vender racionamiento como plan.
- **Restricción de fuentes (ADR-11) y coste:** trabajar solo con fuentes libres no
  encarece nada — la autoría siempre fue original y citada. Lo único que cambia es
  que los tracks de cloud y certificaciones de proveedor se escriben contra docs
  propietarias *citadas*, que es exactamente como se hicieron track08-11.

---

## 7. Puerta de calidad — obligatoria por bloque (lección de track12)

Ninguna autoría en masa entra en `master` sin pasar **las cinco**:

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

Modelo por tarea: **autoría → Haiku; verificación y código → Sonnet; el hilo
principal el que fije `settings.json`**. Un bloque que no pasa la puerta no
existe: no se cuenta, no se anota, no se despliega.

---

## 8. Competencia — catálogo, con la honestidad que exige la línea roja 9

| Plataforma | Catálogo | Fuente |
|---|---|---|
| Platzi | ≈ 1.500 cursos | *(estimación sin verificar — 18.12)* |
| Pluralsight | ≈ 7.000 cursos | *(estimación sin verificar — 18.12)* |
| DataCamp | ≈ 500 cursos | *(estimación sin verificar — 18.12)* |
| Codecademy | ≈ 300 cursos | *(estimación sin verificar — 18.12)* |
| Brilliant | ≈ 100 cursos | *(estimación sin verificar — 18.12)* |
| Boot.dev | ≈ 40 cursos | *(estimación sin verificar — 18.12)* |
| Sololearn | ≈ 30 cursos | *(estimación sin verificar — 18.12)* |
| Mimo | ≈ 15 rutas | *(estimación sin verificar — 18.12)* |
| **Educative** | **2.200+ cursos · 330+ proyectos · 330+ Cloud Labs · 3 M usuarios** | **verificado en vivo 2026-09-18** (educative.io, sesión logueada; teardown §11.3) |
| **Whetzy** | **15 tracks · 43 cursos · 5.715 Q** | `check_docs.py` |

Lectura honesta: con 27 tracks × 3 niveles ≈ 80 cursos, Whetzy queda en la liga
de **Boot.dev / Sololearn / Mimo** — que son exactamente las apps que monetizan
catálogos pequeños con motor y móvil — y **no** en la de Platzi/Udemy, que viven de
creadores externos y años. La tesis defendible sigue siendo la de §8.4 del
teardown: *el mejor en un nicho que los grandes ignoran* (ES/EN nativo + motor
auditado + ejecución en navegador), no «abarcar todo».

---

## 9. Lo que no se construye (y por qué)

- **Marketplace de creadores** (estrategia v3, Parte III-IV): **no hasta ≥ 100
  usuarios activos verificados.** Con 0 usuarios es una sala vacía; ninguna de
  las apps de la liga objetivo tiene uno. La fase 10 del ledger queda en 10.1-10.3
  (schema, contenido, simulacro); 10.4 espera Stripe live (H.4) *y* usuarios.
- **Shell real en navegador (v86)**: imagen Alpine ≈ 20 MB en móvil, línea roja 8.
  Linux se enseña con `fill_blank` de comandos + salida real ilustrativa (ADR-9).
- **Vídeo filmado**: no hay cámara ni presentador. Manim o nada.
- **Certificación propia de Whetzy**: no vale nada todavía (v3, Parte XI).
- **Tracks sin runtime ni cert** (móvil) van los últimos.

---

## 10. Orden de ejecución — ver Serie 18 en `AUTONOMOUS_STATE.md`

Urgente × difícil primero: **18.0** dejar `master` verde (track12 completo) →
**18.1** blueprints correctos + readiness (PRI 0, es la cuña) → **18.2**
Ciberseguridad + ISC2 CC → **18.3** Frontend + runtime JS → **18.4** Linux ·
Algoritmos · Redes → **18.5** certificaciones P1 (PCAP, MLA-C01, AZ-900/AI-900/DP-900,
Security+) → **18.6** DevOps/Cloud (Docker/K8s, IaC, Azure, GCP) → **18.7** Datos
(Data Eng, DS, NoSQL) → **18.8** proyectos multi-paso → **18.9** vídeo piloto →
**18.10** resto de tracks y certs P2-P3 → **18.11** store-ready sin cuenta →
**18.12** re-puntuación con URLs fechadas.

**Serie 19 en paralelo, sin esperar a la 18** (es código, no contenido): **19.1**
social login web antes que nada — es lo que convierte y lo que las tiendas exigen —,
**19.7** biblioteca de fuentes libres (alimenta cada bloque de la 18), **19.4** y
**19.5** cuando haya sesión interactiva para la captura.

Cada bloque de contenido corre como **Workflow paralelo** (autoría Haiku por
fichero → verificador propio → QA Sonnet → `pytest tests/content` →
`check_question_bank.py` → `check_docs.py` → commit). Un bloque = un commit
verde. Nunca un track a medias en `master` otra vez.
