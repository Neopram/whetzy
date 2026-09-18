# Whetzy — Catálogo maestro: todo el mundo informático, medido

> **Qué es este documento.** La única lista de tracks, certificaciones, fuentes y
> volúmenes que Whetzy se compromete a construir, con el estado real de cada fila.
> Sustituye a la tabla de la Parte II de `whetzy_estrategia_definitiva_v3.md` y a
> la tabla §5 del plan «de quiz a escuela». Cuando este doc y otro choquen, manda éste.
>
> **Regla de honestidad.** Cada fila «HECHO» tiene un comando que lo reproduce
> (`python scripts/check_question_bank.py`, `python scripts/check_docs.py`,
> `pytest tests/content`). Cada cifra de la competencia marcada *(estimación)* es
> memoria del modelo, no una captura: la tarea **18.12** la sustituye por URL + fecha
> o la borra. Un número sin comando ni URL es un bug de este doc.
>
> Última medición: 2026-09-18 (sesión **bb**). Estado del banco: ver `## 1`.

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
| Tracks | **15** (11 + SQL + ciberseg + JS stub) | `python scripts/check_docs.py` |
| Cursos (track × nivel) | **43** | ídem |
| Skills | **342** | ídem |
| Preguntas | **5.715** | `python scripts/check_question_bank.py` |
| Lecciones | 342/342 (100 %) | `pytest tests/content/test_lessons.py` |
| Glosario | **586** (444 + track12 36 + track13 + track14 6) | `check_docs.py` |
| Ejecutables | 10 tracks no exentos ≥ 15 % (track12 20 %, track13/40 15 %, track14 JS sandbox) | `check_question_bank.py` |
| Certificaciones | 4 (CLF-C02, PCEP, SAA-C03, AIF-C01) — **3 con blueprint incorrecto (17.13, PRI 0)** | `pytest tests/content/test_certification_blueprints.py` |
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
de 17.13).

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

**Cobertura hoy: 11 de 27 filas (41 %).** 8 tracks completados + track13 ciberseg (stub, 326 Q) + track14 Frontend JS (stub, 12 Q). Linux, Redes,
DevOps, Azure/GCP, Data Eng, Móvil: **cero**.

---

## 3. Certificaciones — 55 objetivo, 4 construidas

Un track de certificación = módulos que son **los dominios oficiales con su peso
verificado** (`exam_domain` + `exam_weight_pct`, suma 100 — `_domain_allocation`
lo valida desde 17.13), ≥ 15 Q/skill, simulacro en formato real (nº de ítems,
minutos, corte), informe por dominio, y **readiness** (18.1): BKT por dominio ×
peso → «listo / no listo» con evidencia. Sin dumps. Sin adivinar pesos.

| Proveedor | Certificación | Track de aprendizaje | Estado | Prioridad |
|---|---|---|---|---|
| Python Institute | **PCEP-30-02** | track01 | ✅ track09 — **blueprint 3 bloques, el real tiene 4 (17.13)** | P0 corregir |
| Python Institute | PCAP-31-03 | track02 | ❌ | P1 (cuña, siguiente escalón) |
| Python Institute | PCPP1 | track03 | ❌ | P3 |
| AWS | **CLF-C02** | track08 (propio) | ✅ 300 Q, 4 dominios verificados | — |
| AWS | **SAA-C03** | track10 | ✅ — **5 dominios que suman 120 (17.13)** | P0 corregir |
| AWS | **AIF-C01** | track11 / track07 | ✅ — **faltan 2 dominios = 28 % del examen (17.13)** | P0 corregir |
| AWS | DVA-C02 | track28 | ❌ | P2 |
| AWS | MLA-C01 | track07 | ❌ | P1 |
| AWS | SOA-C02 · DOP-C02 · SAP-C02 | track18/19 | ❌ | P3 |
| AWS | Security Specialty (SCS-C02) | track25 | ❌ | P2 |
| ISC2 | **CC** (Certified in Cybersecurity, examen gratuito) | track13 | ❌ | **P1 — entrada más barata a cyber** |
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

**Cobertura hoy: 4 de ~55 (7 %), y 3 de las 4 con blueprint incorrecto.**

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
| **Total** | **≈ 22 k Q · 700 lecciones · 120 proyectos · 55 certs** | **≈ 25 M** | **≈ 18-20 sesiones** |

- **Al ritmo de presupuesto de esta semana** (85 % del cupo consumido por una
  sesión larga): 1-2 tracks/semana → **≈ 9-12 meses**.
- **Con cupo sin racionar y Workflow paralelo**: **≈ 6-8 semanas**.
- La diferencia es el plan de Claude del dueño, no la capacidad del agente. Esto
  se dice aquí para que ninguna sesión vuelva a vender racionamiento como plan.

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

Cada bloque de contenido corre como **Workflow paralelo** (autoría Haiku por
fichero → verificador propio → QA Sonnet → `pytest tests/content` →
`check_question_bank.py` → `check_docs.py` → commit). Un bloque = un commit
verde. Nunca un track a medias en `master` otra vez.
