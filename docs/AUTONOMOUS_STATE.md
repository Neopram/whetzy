# Whetzy — Ledger autónomo de ejecución

> **Este archivo es la fuente de verdad del progreso.** El orquestador lo lee al
> arrancar y lo escribe al cerrar. No lo edites a mano salvo para cambiar prioridades
> o desbloquear un ítem de `HUMAN-BLOCKED`.
>
> Formato de estado: `TODO` · `DOING` · `DONE` · `BLOCKED` · `HUMAN-BLOCKED` · `PARCIAL` · `REFUTADA`
> · `REGRESIÓN` (una fila cerrada que volvió a romperse; `24.5` la usa) · `RESUELTA` / `CORREGIDA` (filas de
> incidente `22x`, `24.5x`, `28x`…). Los cinco últimos los usaban las filas y la cabecera no los declaraba:
> `scripts/ledger.py` los tuvo que descubrir (2026-09-19) y la única PRI 0 abierta no salía en `next`.
>
> _Narrativas de sesión anteriores archivadas en `docs/archive/LEDGER_HISTORY.md`._

---

## 0. Invariantes del sistema (no romper nunca)

| Invariante | Valor |
|---|---|
| Backend prod | `https://api-production-9751.up.railway.app` |
| Frontend prod | `https://whetzy.com` / `https://whetzy.pages.dev` — **deploy AUTOMÁTICO desde `master`** (Cloudflare Pages conectado a… |
| Repo | `github.com/Neopram/whetzy` branch `master` |
| Autonomía | **ADR-45 (2026-09-24): la sesión trabaja en su rama y abre un PR por oleada; NUNCA `git push origin master` ni fusiona.… |
| DB local | Docker :5433, user `neurium`, pass `neurium_dev`, db `neurium` |
| Modelo LLM | `qwen/qwen3.8-27b` en Groq (llama-3.3-70b NO disponible) |
| Fuentes de contenido | **Solo gratuitas y legales** (ADR-11): reutilizable = MIT / Apache-2 / BSD / CC BY / CC0 / PSF / dominio público;… |
| Railway deploy | **AUTOMÁTICO DESDE `master` — el invariante anterior («MANUAL, sin webhook GitHub») es FALSO y llevaba meses ahí.**… |
| Alembic HEAD | `20260926_antifraud` (38 migraciones) |
| Contenido | **6.305 preguntas** / 18 tracks / 378 skills / **378 lecciones (100 %)** / **622 términos glosario**. Tracks 09/10/11 =… |

### Gotchas verificados

> → `docs/archive/LEDGER_HISTORY.md` §H

---

## 1. Estado por fase

> Tabla completa archivada en `docs/archive/LEDGER_HISTORY.md` §F.
> Ver ## 2 para el estado actual de cada tarea.

| Serie | Nombre | DONE/Total | % | Abiertas |
|---|---|---|---|---|
| 38 | Negocio medible — KPIs, pilotos B2B, instructores, afiliados (ADR-47) | 0/6 | 0 % | TODO (abierta 2026-09-24); 38.2, 38.3, 38.4… |
| 37 | Catálogo total — todos los tracks de la industria, ≥ 50 cursos por track, corpus abierto (ADR-46) | 0/14 | 0 % | **PRI 1 ABIERTA… |
| 34 | Una sola interfaz — todas las pantallas al estilo de la landing | 0/12 | 0 % | **Grueso hecho el 2026-09-24 (PR #6):** 276 clases… |
| 33 | Operación medible — SLO, restauración, offline idempotente | 0/3 | 0 % | TODO (abierta 2026-09-24) |
| 32 | Motor demostrable — calibración y evidencia | 0/4 | 0 % | TODO · 32.2 BLOCKED (H.10) |
| 31 | Fuente única de cifras, staging, migraciones con datos | 0/4 | 0 % | TODO · 31.1 HUMAN-BLOCKED (H.16) |
| 30 | Integridad del despliegue — incidente de login 2026-09-24 | 0/9 | 0 % | **PRI 0 ABIERTA.** Login roto en prod (bundle con API = el… |
| 29 | Economía cerrada y rails (créditos, referidos, códigos, USDC, credenciales) — ADR-33…37 | 0/13 (4 PARCIAL) | 0 % | **Recalificada… |
| 28 | Marketplace de instructores | 0/10 (8 PARCIAL) | 0 % | **Recalificada 2026-09-24:** las filas 28.0–28.7 decían BLOCKED mientras esta… |
| 27 | Distribución masiva EN | 0/11 | 0 % | ABIERTA 2026-09-24 (ADR-47): se redacta todo; publicar bajo cuenta nueva = H.23 |
| 26 | Distribución masiva ES | 2/11 | 18 % | ABIERTA 2026-09-24 (ADR-47); 26.9 blog y 26.10 newsletter nuevas. PARCIAL —… |
| 25 | Expansión de contenido — subordinada a la serie 37 (ADR-46) | 0/15 | 0 % | **Reabierta 2026-09-24 tras 37.0.** **NO PASA LA PUERTA… |
| 24 | Interfaz que venda al verse (UI/UX, competencia en vivo, vídeo) | 6/15 | 40 % | **Recalificada 2026-09-24 (ADR-45):** las 9 filas… |
| 23 | Dos segmentos, un producto — ES y EN | 1/5 | 20 % | 23.1 PARCIAL · 23.2, 23.3, 23.4 |
| 22 | Blindaje, admin y preparación para un millón | 7/14 | 50 % | 22.1 y 22.6 PARCIAL · 22.2, 22.4, 22.5, 22.7, 22.13 |
| 21 | Legal y fiscal a coste cero | 1/6 | 17 % | 21.0 DONE · 21.5 PARCIAL (1/4) · 21.6 PARCIAL (2/4) · 21.3, 21.4, 21.8 · **21.1, 21.2 y… |
| 20 | Verificación masiva código↔docs↔prod | 9/11 | 82 % | 20.7 (**REFUTADA 2026-09-19**: `verify_ci_local.ps1` moría en `pip install`;… |
| 19 | Catálogo 27 tracks (histórico; meta actual ADR-46) + cert marketplace | 1/10 | 10 % | 19.2–19.10 |
| 18 | Nuevos tracks (frontend, SQL, linux, algos, redes, certs) | 2/5 | 40 % | 18.3, 18.5 |
| 17 | Plataforma + engine + monetización | mayoría DONE | ~95 % | ver archive §B |
| ≤16 | Fases 1–16 | todas DONE | 100 % | — |

---

## 2. Backlog ejecutable

> Orden de ejecución = por `PRI` ascendente, luego por ID. `PRI 0` es lo que
> desbloquea todo lo demás.

### 11 — Superioridad medible (cerrar las brechas honestas)
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 11.6 | 3 | Tiempo hasta primera pregunta **< 60 s contra prod** con 4G simulado | **DONE** — commit 5e306fb, 2026-09-18 | Playwright con… |
| 11.8 | 3 | **Prueba de aprendizaje real**: cohorte beta ≥ 30 usuarios | HUMAN-BLOCKED (H.10) | Dashboard 5.5 muestra D1 ≥ 40 % / D7 ≥ 20… |
| 11.9 | 4 | k6 contra prod: p95 < 500 ms con 100 VUs | PARCIAL — **no lanzo 100 VUs contra prod sin un humano delante** | →… |

### 14 — La cuña (dirección aprobada 2026-09-14)
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 14.4 | 2 | **Micro-lecciones desde las fuentes** — cerrar la brecha de instrucción sin construir vídeo | TODO | → LEDGER_HISTORY.md §E |
| 14.7 | 3 | **PCEP** — primera certificación del carril 1 (decisión #25) | TODO | → LEDGER_HISTORY.md §E |
| 14.8 | 4 | **Predictor beta-binomial de aprobado** con calibración pública | BLOCKED (11.8 · H.10) | → LEDGER_HISTORY.md §E |
| 14.9 | 4 | **Informe de dominio verificable** por URL | BLOCKED (11.8 · H.10) | → LEDGER_HISTORY.md §E |
| 14.13 | 2 | **Cuatro tracks nuevos: Linux/CLI · SQL y bases de datos · Frameworks web (FastAPI) · Data engineering** | TODO | →… |
| 14.14 | 3 | **~50 animaciones Manim para los conceptos que un texto no explica** | TODO | → LEDGER_HISTORY.md §E |
### 16 — CI en rojo (PRI 0 · sesión ao). Las 3 jobs fallan desde el lote F15–F22
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|


| 16.17 | **2** | 16.17 | **RESUELTA** | **RESUELTA** (2026-09-24) → §I |

| 22x | ~~0~~ | **Sesiones y 2FA estaban escritos, probados y sin registrar** | **RESUELTA 2026-09-19 (sesión bj)** —… |
| 28x | **0** | **El webhook de Paddle aceptaba firmas falsas, y esta publicado en produccion** | **CORREGIDA 2026-09-19 (sesión bj)** —… |
| 25x | ~~0~~ | **`check_docs.py` da 12 fallos y arreglarlos por el camino corto publicaría cifras falsas** | **RESUELTA 2026-09-24** —… | |
| 24.5x | **2** | 24.5x | **RESUELTA** | **RESUELTA** `ed680ef` (2026-09-19) → §I |
| 17.1x | **2** | 17.1x | **RESUELTA** | **RESUELTA** `17dc7b7` (2026-09-24) → §I |

| 14.10 | 5 | **IRT (θ) — el modelo de Vicks** | BLOCKED (datos) | → LEDGER_HISTORY.md §E |

### 17. De quiz a escuela + release definitivo (web · App Store · Play Store)
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 17.2 | **1** | **Examen final de track + certificado + «test-out»** | DONE (76c1897, sesión autónoma) | Backend: MockExamAttempt (kind:… |
| 17.5 | **3** | **Tracks nuevos desde fuentes con licencia permisiva** | PARCIAL | → LEDGER_HISTORY.md §E |
| 17.6 | **2** | **UI de clase mundial, medida** | TODO | → LEDGER_HISTORY.md §E |
| 17.7 | **4** | **Vídeos explicativos generados desde código** | TODO | → LEDGER_HISTORY.md §E |
| 17.10 | **3** | **Re-puntuar frente a la competencia con lo anterior hecho** | TODO | → LEDGER_HISTORY.md §E |
| 17.14 | **1** | **Compras dentro de la app (la antigua 7.6, sin fila desde hace meses; `legal/h21-decision.md:58`)**: RevenueCat +… | | |

**Verdad que condiciona toda la serie:** H.11 cerrado 2026-09-18 (frontend desplegado). Hasta que el dueño cierre **H.SEED** (cargar el…

#### Prompt de arranque — serie 17 (anatomía Fable)

> Copiar tal cual en la próxima sesión. Cada bloque tiene una función: sin uno de ellos la sesión improvisa.

```
[IDENTIDAD] Eres el orquestador autónomo de Whetzy (docs/ORCHESTRATOR.md). Hilo
principal Sonnet/Fable; Haiku para inventarios y autoría por fichero; Opus ≤ 2 y
solo para arquitectura irreversible.

[CONTEXTO] Lee docs/AUTONOMOUS_STATE.md entero antes de tocar nada. La serie 17
(«De quiz a escuela + release definitivo») es el roadmap vigente. Estado de
partida: 4.512 Q, lecciones 15/281, 7 tracks sin ejercicios ejecutables, Android
generado, iOS inexistente, prod con build viejo (H.11) y contenido sin cargar
(H.SEED). CI sin evidencia hasta H.13.

[MISIÓN] Ejecutar la serie 17 en este orden y no en otro: 17.0 → 17.8 → 17.1 →
17.9 → 17.2 → 17.6 → 17.3 → 17.4 → 17.5 → 17.10 → 17.7. Se sale del orden solo
para arreglar una regresión propia o CI en rojo.

[RESTRICCIONES] Líneas rojas del ORCHESTRATOR sin excepción: evidencia o no
pasó; ES/EN nativo; fuente real por cada contenido (inventarla es la falta más
grave); solo licencias permisivas dentro de la app (CC BY-NC se cita, CC BY-SA
espera H.LIC); ningún origen de terceros en prod; nunca create_all; nunca
rotar ni tocar la GROQ_API_KEY de docs/STATUS.md; ningún despliegue, submisión
ni acción de cuenta: eso es del humano y va a la cola HUMAN-BLOCKED con todo
preparado. Autoría siempre por fichero (≤ 32k tokens por agente). Máx. 3
workers en paralelo sobre ficheros disjuntos.

> [EVIDENCIA] → `LEDGER_HISTORY.md` §K

[SALIDA] Al cerrar cada ítem: fila del ledger actualizada con evidencia, commit
con Co-Authored-By, push a master. Al cerrar la sesión: fila en el Scorecard
con números medidos, cola HUMAN-BLOCKED al día, y el prompt de la siguiente
sesión reescrito si el orden cambió.

[CIERRE] Termina siempre recordando al dueño, en una línea cada uno, que H.11,
H.SEED, H.10, H.13, H.LIC, H.2, H.3, H.5 y H.14 son suyos y qué desbloquea cada
uno. Sin H.11 y H.SEED, nada de esta serie existe para un usuario.
```

### 18. Techo de código — todo el catálogo, sin racionar (abierta 2026-09-16, sesión au)
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 18.3 | **1** | **Runtime JS real + track Frontend (track14)** | TODO | → LEDGER_HISTORY.md §E |
| 18.4 | **2** | **Linux (track15) · Algoritmos (track16) · Redes (track17)** | **DONE… | **DONE** | **DONE** (2026-09-18) → §I |
| 18.5 | **2** | **Certificaciones P1: PCAP, MLA-C01, AZ-900, AI-900, DP-900, Security+** | TODO | → LEDGER_HISTORY.md §E |
| 18.6 | **3** | **DevOps y Cloud: Docker/K8s (18), IaC+CI/CD (19), Azure (22), GCP (23)** | TODO | → LEDGER_HISTORY.md §E |
| 18.7 | **3** | **Datos: Data Engineering (20), Data Science (21), NoSQL (27)** | TODO | → LEDGER_HISTORY.md §E |
| 18.8 | **3** | **Proyectos multi-paso con tests en runtime** | TODO | → LEDGER_HISTORY.md §E |
| 18.9 | **4** | **Vídeo explicativo — piloto que decide** | TODO | → LEDGER_HISTORY.md §E |
| 18.10 | **4** | **Resto del catálogo: tracks 24-26, 28-31 y certs P2-P3** | TODO | → LEDGER_HISTORY.md §E |
| 18.11 | **2** | **Store-ready sin cuenta** | TODO | → LEDGER_HISTORY.md §E |
| 18.12 | **3** | **Re-puntuación con URLs fechadas** | TODO | → LEDGER_HISTORY.md §E |

### 19. Lo que Educative y las tiendas exigen — social login, bootcamps, proyectos, autoría con fuentes libres (abierta 2026-09-18, sesión…
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 19.1 | **1** | **Social login web: GitHub + Google (OAuth 2.0 por redirección)** | **DONE** | Backend: `GET /auth/oauth/{provider}/start`… |
| 19.2 | **1** | **Sign in with Apple** — obligatorio por App Store Review 4.8 en cuanto exista 19.1 | HUMAN-BLOCKED (H.2) | Necesita… |
| 19.3 | **2** | **Android: Google Sign-In nativo + Google Play Billing vía RevenueCat** (absorbe la mitad Android de 17.14, la antigua… | | |
| 19.4 | **2** | **Bootcamps: secuencia de tracks con calendario y meta diaria** | TODO | → LEDGER_HISTORY.md §E |
| 19.5 | **2** | **Playground libre (Python · SQL · JS)** | TODO | → LEDGER_HISTORY.md §E |
| 19.6 | **3** | **Proyectos multi-paso** | TODO | → LEDGER_HISTORY.md §E |
| 19.7 | **2** | **Biblioteca de autoría con fuentes libres + RAG local** | TODO | → LEDGER_HISTORY.md §E |
| 19.8 | **3** | **Landing y SEO de whetzy.com al nivel de Educative** | TODO | → LEDGER_HISTORY.md §E |
| 19.9 | **3** | **Assets de tiendas e iconos de todos los tracks** (meta ADR-46) | TODO | → LEDGER_HISTORY.md §E |
| 19.10 | **4** | **Vídeo: Manim + Remotion (`editor-pro-max`)** — absorbe 18.9 | TODO | → LEDGER_HISTORY.md §E |
| 19.11 | **2** | **Confirmación de edad mínima en el registro** («tengo 13 años o más» / por país según 21.3), ES y EN, guardada en el… | | |

### 20. Verificación masiva código ↔ docs ↔ prod (abierta 2026-09-18, sesión bf — **ABIERTA 2026-09-18 (H.21 ejecutada)**)
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 20.0 | **0** | **Cerrojo de sesión + salida limpia** — `.session.lock` (gitignored) + comprobación de `list_task_runs` en el pre-flight… | **DONE** | **DONE** (2026-09-18) → §I |
| 20.1 | **0** | **Inventario de afirmaciones** de los 11 docs vivos + `store/` + `legal/` + `CLAUDE.md` →… | **DONE** | **DONE** (2026-09-18) → §I |
| 20.2 | **0** | **Ledger fila a fila** (protocolo §5): cada `DONE` reejecutado con fecha; `TODO` contrastados con `git log --grep`… | **DONE** | **DONE** `bec734c` (2026-09-18) → §I |
| 20.3 | **1** | **`API.md` ↔ OpenAPI bidireccional = 0 diferencias** (`scripts/check_api_docs.py`); `ARCHITECTURE.md` ↔ árbol real de… | **DONE** | **DONE** (2026-09-18) → §I |
| 20.4 | **1** | `legal/` vs. realidad: errores de hecho en textos legales | **DONE** | `16b4e39` (2026-09-18) CONFIRMADA → §I |
| 20.5 | **1** | **Fuentes**: cada URL de `CATALOGO_MAESTRO.md` §2.1/§2.2 resuelve; para cada repo clonado, `LICENSE` leído == licencia de… | **DONE** | **DONE** (2026-09-18) → §I |
| 20.6 | **1** | **Dieta del ledger**: evidencia histórica de filas `DONE` → `docs/archive/LEDGER_HISTORY.md` (ancla por ID); en la fila… | **DONE** | **DONE** `50d0c18` (2026-09-18) → §I |
| 20.7 | **1** | CI ciego: `verify_ci_local.ps1` replica `ci.yml` paso a paso | **DOING** | Evidencia sesión bg; falta verificador adversario → §I |
| 20.8 | **1** | **Verificador adversario en el loop** (ADR-20): plantilla literal del protocolo §7 usada por el orquestador antes de cada… | **DONE** | **DONE** `b82b377` → §I |
| 20.9 | **2** | **Coherencia final**: README/CLAUDE/ORCHESTRATOR/DECISIONS/CATALOGO/teardown sin contradicciones entre sí ni con el… | **DONE** | **DONE** → §I |
| 20.10 | **2** | REGRESIÓN dieta ledger (20.6). Reducir a <60 KB + guarda mecánica | **DONE** | 221→52 KB. §G/H/I/J/K archivados. `check_docs.py` guarda 61440 testeada ambos sentidos (2026-09-26) |

### 21. Legal y fiscal a coste cero — investigación, borradores, gates humanos (abierta 2026-09-18, sesión bf — **H.20 SIGUE ABIERTO** — el…
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 21.0 | **0** | REGRESIÓN P0 — textos legales con entidad inexistente y decisión no autorizada | **DONE** | `16b4e39`+`ea7707d` (2026-09-19) check_legal_facts.py 21 variantes → §I |
| 21.1 | **1** | *(Premisa griega **suspendida** por ADR-47; la entidad y la jurisdicción están sin decidir, H.29. Se conserva el enunciado… | | |
| 21.2 | **1** | *(Premisa griega **suspendida** por ADR-47; valor por defecto: Merchant of Record + IAP. Enunciado original conservado… | | |
| 21.3 | **1** | **Privacidad multi-jurisdicción**: GDPR/ePrivacy (UE) · UK GDPR · CCPA/CPRA, COPPA, CAN-SPAM, leyes estatales (EE. UU.) ·… | | |
| 21.4 | **2** | **Consumo y suscripciones**: desistimiento UE 14 días para contenido digital (renuncia expresa en checkout), renovación… | | |
| 21.5 | **2** | **AI Act, DSA, EAA**: obligaciones de *deployer* del tutor… | **PARCIAL** | **PARCIAL** `5f7bd7b` (2026-09-19) → §I |
| 21.6 | **2** | **Propiedad intelectual**: búsqueda de marca «Whetzy» (EUIPO,… | **PARCIAL** | **PARCIAL** `8e7812a` (2026-09-19) → §I |
| 21.7 | **2** | **Redacción**: ToS · Privacidad · Cookies (sin banner si solo cookies necesarias — mantenerlo así) · DPA plantilla para… | | |
| 21.8 | **3** | **Procedimientos internos**: brecha de seguridad (72 h, plantilla de notificación), DSAR (export/delete ya existen → SLA y… | | |
| 21.9 | **3** | **Proceso DMCA / retirada de contenido y DPIA** (`legal/README.md:116-127`): página `/legal/dmca` ES/EN con formulario por… | | |

### 22. Blindaje, admin y preparación para un millón — todo a coste cero (abierta 2026-09-18, sesión bf — **ABIERTA 2026-09-18 (H.21)**;…
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 22.0 | **0** | **REGRESIÓN P0 — el backend de producción estuvo 2 h 30 min en 502.** `alembic upgrade head` moría en `u1v2w3x4y5z6`: la… | **DONE** | **DONE** `414e2f6` (2026-09-19) → §I |
| 22.10 | **0** | **`POST /auth/login` devolvía 500 con `created_at` naive** (`check_lockout` restaba un datetime sin zona de… | **DONE** | **DONE** `e9161d7` (2026-09-19) → §I |
| 22.1 | **1** | **Admin sub-app `/admin`** (solo rol `owner`; code-split, fuera del bundle… | **PARCIAL** | **PARCIAL** (2026-09-19) → §I |
| 22.2 | **1** | **Threat model STRIDE** documentado en `ARCHITECTURE.md` + cabeceras de seguridad (CSP sin `unsafe-inline` salvo lo que… | | |
| 22.3 | **2** | **Auth hardening**: lockout progresivo tras N fallos, refresh tokens con rotación y revocación, sesiones por dispositivo… | **DONE** | **DONE** → §I |
| 22.4 | **2** | **Cadena de suministro a €0**: Dependabot (config), `gitleaks` en pre-commit y en `verify_ci_local.ps1`, `bandit` +… | **DONE** | **DONE** → §I |
| 22.5 | **2** | **Cloudflare free**: WAF managed rules, rate limiting rules por ruta (`/auth/*`, `/tutor/*`), Bot Fight Mode, cache rules… | | |
| 22.6 | **2** | **Escala sin coste hoy** (ADR-19): interfaz… | **PARCIAL** | **PARCIAL** `e5efdb7` (2026-09-26) → §I |
| 22.7 | **3** | **Incidentes y estado**: runbook de incidentes (severidades, quién, qué, plantilla de postmortem), página de estado… | | |
| 22.8 | **1** | **Contrastar 22.1, 22.6 y 23.1 con lo que hay en `master`** (protocolo… | **DONE** | **DONE** `f36218f` (2026-09-19) → §I |
| 22.9 | **1** | **Test de frontend rojo en `master`**: `src/test/hooks.useRuntime.test.tsx` falla con `ReferenceError: Worker is not… | **DONE** | **DONE** `7e1b8d4` (2026-09-19) → §I ||
| 22.11 | **1** | **`AdminScreen.tsx` estaba 100 % en inglés** — títulos, pestañas, estados, mensajes de error y unidades eran cadenas… | **DONE** | **DONE** `13d8904` (2026-09-19) → §I |
| 22.12 | **2** | **Deuda de lint y tipos que dejaron las series 22-23**: 21 errores de… | **DONE** | **DONE** `83c6bf1` (2026-09-19) → §I |
| 22.13 | **2** | **Test con presupuesto de tiempo absoluto que falla con la máquina cargada**:… | | |
| 22.14 | **1** | **Arranque en frío de Railway** (`AUDITORIA_EXTERNA_2026-09-19.md:203`): la primera petición tras inactividad devuelve… | | |
| 22.15 | **2** | **Fase 3 del modelo de amenazas** (`design/threat-model-stride.md:157-161`): firma HMAC obligatoria en webhooks internos,… | | |
| 22.16 | **2** | **Cuota de tokens por usuario en `/tutor`** (`ARCHITECTURE.md` riesgos): contador en `analytics_events`, tope diario por… | | |

### 23. Dos segmentos, un producto — ES y EN sin mezclar (abierta 2026-09-18, sesión bf — **ABIERTA 2026-09-18 (H.21)**; ADR-17)
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 23.1 | **1** | **Auditoría E2E por idioma**: cada pantalla, email, push, PDF/certificado,… | **PARCIAL** | **PARCIAL** (2026-09-19) → §I |
| 23.2 | **2** | **Landing y SEO por segmento**: `/es` y `/en` con copy nativo (no traducido), `hreflang` (existe), `sitemap` por idioma,… | | |
| 23.3 | **2** | **Tiendas, emails y soporte por idioma**: listings ES/EN en `store/`, plantillas de email por idioma (P.1) verificadas,… | | |
| 23.4 | **3** | **Segmento en el admin**: todas las métricas de 22.1 filtrables por idioma; cohortes ES vs. EN | TODO | →… |
| 23.5 | **1** | **Las dos guardias de i18n daban números falsos y la que cita el protocolo no existía**: `audit_i18n.py` buscaba… | **DONE** | **DONE** `d991fe4` (2026-09-19) → §I |

### 24. Interfaz que venda al verse — UI/UX + competencia en vivo + vídeo (sesión interactiva; **después** de 20-23; absorbe 17.6 y 19.8;…

> **Estado:** `ABIERTA 2026-09-24` (ADR-45/47). Las filas BLOCKED pasan a PARCIAL: hay commits `24.x` en `master` pero son maquetas con…
> **Modo:** rama + PR + preview de Cloudflare (`<rama>.whetzy.pages.dev`); el dueño revisa el preview antes de fusionar, no cada pantalla…
> **Modelo:** Sonnet para código (`frontend/src` es fichero de riesgo); Haiku para inventarios y verificación.
> **Evidencia común a toda fila:** captura fechada en `docs/screenshots/<fecha>/`, `npx tsc -b --force` + `npx vitest run` + `npm run…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 24.0 | **1** | **Investigación competitiva en vivo**: navegar el free tier de los 8… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 24.1 | **1** | **Identidad visual**: tokens de diseño (color con hue propio, tipografía… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 24.2 | **1** | **Landing que vende** (`/es`, `/en`; absorbe 19.8 y 23.2): hero con el… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 24.3 | **1** | **Onboarding rediseñado**: 3 preguntas de segmento (`SEGMENTOS.md` §«Cómo… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 24.4 | **1** | **Dashboard con el motor visible**: mapa de dominio por skill (BKT como… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 24.5 | **0** | **Sesión adaptativa con BKT visual**: barra de dominio en vivo, «por qué esta pregunta», feedback explicativo (no solo… | **DONE** | **DONE** → §I |
| 24.6 | **2** | **Gamificación original + wallet de créditos**: racha con identidad… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 24.7 | **2** | **Panel de certificación**: readiness por dominio (18.1), simulacros (comprables con créditos), certificado… | | |
| 24.8 | **2** | **Perfil público** `/u/<handle>` (opt-in): dominio verificado,… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 24.9 | **2** | **Panel B2B** (`SEGMENTOS.md` segmento 5): progreso por empleado, tiempo, certificaciones, comparativa anónima, import… | | |
| 24.10 | **3** | **Panel de instructor** (UI de `MARKETPLACE.md` §4) con datos de prueba hasta Serie 28 | DONE (8ad5afd, sesión anterior)… | |
| 24.11 | **3** | **Marketplace UI**: catálogo con filtros, ratings, preview de primera lección; mock hasta 28.4 | DONE (b97c0ee) |… |
| 24.12 | **2** | **Mobile polish**: Capacitor Android, safe areas, gestos, estado offline básico, rendimiento en 4G (11.6) | DONE… | |
| 24.13 | **2** | **Tres vídeos demo, ES y EN nativos**: producto 2 min, motor 5 min, short 60s | DONE (03f7659) | Guiones 6 piezas… |
| 24.14 | **3** | **Framework A/B**: tabla experiments, asignación estable por usuario, flag en frontend | DONE (f39a49d) | Deterministic… |

#### Dependencias

- La serie entera espera a **20.7, 21.7, 22.1 y 23.1** (`DONE`): sin CI local no hay evidencia, sin legales no hay landing, sin admin no…
- **24.1 antes que 24.2–24.12** (todos consumen los tokens).
- 24.6 usa datos reales solo con **29.0–29.2**; 24.7 con **17.2** y **29.10**; 24.9 y 24.14 con **22.1**; 24.10 y 24.11 son mock hasta…
- 24.13 al final (graba las pantallas ya aprobadas). **26.0 y 27.0** esperan a 24.13.

#### Grupos paralelos (ficheros disjuntos, ADR-6)

| Grupo | Tareas | Ficheros |
|---|---|---|
| G-A | 24.2, 24.3 | `LandingScreen*`, `OnboardingScreen*`, `AuthScreen*` |
| G-B | 24.4, 24.5, 24.6 | `HomeScreen*`, `QuizScreen*`, `components/gamification/*`, `components/wallet/*` |
| G-C | 24.7, 24.8 | `CertificationScreen*`, `ProfileScreen*`, `VerifyScreen*` |
| G-D | 24.9, 24.10, 24.11 | `admin-company/*`, `instructor/*`, `MarketplaceScreen*` |
| Secuencial | 24.0 → 24.1 → grupos → 24.12 → 24.13 → 24.14 | — |

### 25. Expansión de contenido — subordinada a la serie 37 (ADR-46 sustituye a ADR-25; ADR-38)

> **Estado:** `ABIERTA 2026-09-24` — reabierta por ADR-46/47 (H.22 decidido por defecto: **no** CC BY-SA; OWASP se cita). **Ninguna fila…
> **Dependencias:** 37.0 DONE; corpus de la área descargado y verificado (37.1–37.3).
> **PRI:** 2 (detrás de 30 y de 37.0–37.3).
> **Modelo:** Haiku para generación de contenido (cada bloque = 1 worker, 1 commit verde). Sonnet solo si toca ficheros de riesgo.
> **Nota:** Esta serie no tiene fecha límite — es la expansión continua del catálogo. Se ejecuta en paralelo con la campaña de distribución…

| ID | PRI | Tarea | Estado | Criterio de aceptación | Deps |
|---|---|---|---|---|---|
| 25.0 | **3** | Infraestructura de generación: script `scripts/generate_track_content.py` que toma track_id + nivel + fuentes y produce… | | | |
| 25.1 | **3** | Completar tracks 1-3 (Python básico/intermedio/avanzado) a 100 cursos por nivel usando PSF docs + exercism/python +… | | | |
| 25.2 | **3** | Completar tracks 6-7 (IA/ML/LLMs) a 100 cursos usando ML-For-Beginners + HF course + fastai + openai/anthropic cookbooks |… | | |
| 25.3 | **3** | Completar tracks 4-5 (Ingeniería + Arquitectura) a 100 cursos usando system-design-primer + aosabook +… | | | |
| 25.4 | **3** | Completar tracks 12, 20, 21, 27 (SQL + Data Eng + DS + NoSQL) usando PostgreSQL docs + DuckDB + Kaggle Learn +… | | | |
| 25.5 | **3** | Completar tracks 13, 24, 25 (Ciberseguridad fundamentos + Pentest + Seguridad cloud) usando NIST + MITRE ATT&CK +… | | | |
| 25.6 | **3** | Completar tracks 8-11, 22-23 (AWS + Azure + GCP) usando AWS docs (cita) + Microsoft Learn CC BY + GCP docs CC BY | BLOCKED… | | |
| 25.7 | **3** | Completar tracks 14, 28 (Frontend JS + Backend FastAPI/Node) usando lydiahallie + Web-Dev-For-Beginners + freeCodeCamp ES… | | | |
| 25.8 | **3** | Completar tracks 15, 17, 26 (Linux + Redes + Git) usando exercism/bash + Peterson/Davie CC BY + github/docs | BLOCKED… | | |
| 25.9 | **3** | Completar tracks 16, 29, 30 (Algoritmos + QA + Agile) usando Erickson CC BY + pytest docs + Scrum Guide cita | BLOCKED… | | |
| 25.10 | **3** | Completar tracks 18, 19 (Docker/K8s + IaC/CI/CD) usando Kubernetes docs CC BY + Docker docs + actions/* | BLOCKED (37.0)… | | |
| 25.11 | **3** | Completar track 31 (Móvil) usando swift-book CC BY + android docs + flutter docs | BLOCKED (37.0) | track31 ≥ 900 Q,… | |
| 25.12 | **3** | Glosario máximo: ≥ 100 términos por track × 28 tracks = 2,800+ términos totales, ES y EN nativos | BLOCKED |… | |
| 25.14 | **3** | **track32 — Solana / Web3 developer** (ADR-38): 5 módulos × 4 skills, JS con `@solana/web3.js` en el Worker (18.3) +… | | | |
| 25.13 | **3** | Scorecard ADR-25: verificar que los 28 tracks pasan §7 quality gate (≥ 15 % exec donde aplica, ≥ 144 términos, BKT… | | | |

**H.22 — Decisión del dueño:** ¿Aceptar [H.LIC] para OWASP CheatSheets/WSTG/ASVS (CC BY-SA 4.0) en tracks de seguridad? Si sí: contenido…

### 26. Distribución masiva ES (ADR-23, ADR-27; spec `DISTRIBUCION.md`)

> **Estado:** `ABIERTA 2026-09-24` — 24.14 es DONE y H.23 queda decidido por defecto (ADR-47: sí). **La sesión redacta y construye todo;…
> **Dependencias:** 24.14 DONE. Ningún dato inventado en ningún activo (30.1/H.31).
> **PRI:** 3. **Modelo:** Haiku para contenido; Sonnet para copy de landing/emails.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 26.0 | **4** | Canal YouTube ES creado: banner, descripción, links, 3 videos demo subidos (grabados en 24.13); **cada vídeo con su código… | | |
| 26.1 | **4** | 5 artículos en Dev.to / Hashnode ES sobre el motor técnico (BKT, FSRS, gap de mercado) | TODO (redactar/construir;… | |
| 26.2 | **4** | PR en `EbookFoundation/free-programming-books` agregando Whetzy en sección Python ES | TODO (redactar/construir; publicar… | |
| 26.3 | **4** | Template de email para universidades LATAM + lista de 50 contactos | TODO (redactar/construir; publicar bajo cuenta nueva… | |
| 26.4 | **4** | Página de landing para segmento career-switcher ES (dentro de whetzy.com/es/carrera) | TODO (redactar/construir; publicar… | |
| 26.5 | **4** | Página de landing para segmento B2B ES (whetzy.com/es/empresas) | TODO (redactar/construir; publicar bajo cuenta nueva =… | |
| 26.6 | **4** | Show HN post en español (Hacker News): preparación + activos | TODO (redactar/construir; publicar bajo cuenta nueva =… | |
| 26.7 | **4** | Perfiles en comunidades ES: Python Argentina Discord, Dev En Español, LatamDevs | HUMAN-BLOCKED (H.23: perfiles… | |
| 26.8 | **4** | **Superteam LATAM (México, Argentina, Brasil) como canal** (ADR-38): presencia en sus Discord/eventos, 1 charla o taller… | | |
| 26.9 | **3** | **Blog `/blog` ES/EN** (SEO orgánico, `archive/SPEC_WEB.md:152`): Markdown en `content/blog/`, prerender en `vite build`… | | |
| 26.10 | **3** | **Newsletter** (`archive/EXECUTION_PLAN_25-29.md:87`): alta con doble opt-in vía Resend (H.30), ES o EN según usuario,… | | |

### 27. Distribución masiva EN (ADR-27; spec `DISTRIBUCION.md`)

> **Estado:** `ABIERTA 2026-09-24` (ADR-47). Misma regla que la 26: se redacta y construye todo; publicar bajo cuenta nueva = H.23.
> **Dependencias:** ninguna para redactar; 26.0 DONE antes de grabar vídeo EN.
> **PRI:** 3. **Modelo:** Haiku para contenido; Sonnet para copy.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 27.0 | **4** | Canal YouTube EN creado: banner, descripción, 3 videos EN (mismo contenido que 24.13 pero grabado en inglés nativo, no… | | |
| 27.1 | **4** | Show HN EN: "I built an adaptive Python→AI learning engine in Spanish because no one else did" | TODO (redactar/construir;… | |
| 27.2 | **4** | 5 artículos en Dev.to / freeCodeCamp News EN sobre motor técnico | TODO (redactar/construir; publicar = H.23) | 5… |
| 27.3 | **4** | PR en `jwasham/coding-interview-university` y `donnemartin/system-design-primer` READMEs | TODO (redactar/construir;… | |
| 27.4 | **4** | Product Hunt preparación: assets, lista de 100 upvoters confirmados, tagline | TODO (redactar/construir; publicar = H.23)… | |
| 27.5 | **4** | Product Hunt lanzamiento | HUMAN-BLOCKED (H.23) | Top 5 del día en categoría Education |
| 27.6 | **4** | Reddit strategy EN: 10 respuestas de valor en r/learnpython, r/cscareerquestions | HUMAN-BLOCKED (H.23: cuenta y karma… | |
| 27.7 | **4** | Landing page segmento career-switcher EN (whetzy.com/en/career) | TODO (redactar/construir; publicar = H.23) | Lighthouse… |
| 27.8 | **4** | Landing page segmento B2B EN (whetzy.com/en/enterprise) | TODO (redactar/construir; publicar = H.23) | Demo request form… |
| 27.9 | **4** | **Superteam global / Solana developer communities EN** (ADR-38): Solana Stack Exchange y Discord oficial con respuestas de… | | |
| 27.10 | **3** | **Comparativa honesta frente a Coursera/Udemy** (`DECISIONS.md` ADR-24, sin fila hasta hoy): página `/en/compare` y… | | |

### 28. Marketplace de instructores (ADR-29; spec `MARKETPLACE.md`)

> **Estado:** `ABIERTA 2026-09-24` (ADR-47). El código de 28.0–28.7 ya está en `master` (migración `u1v2w3x4y5z6_admin_tables`,…
> **Dependencias:** 22.1 PARCIAL (basta), 22.3 DONE. Ver spec completo en `docs/MARKETPLACE.md`.
> **PRI:** 3. **Modelo:** Sonnet (toca DB schema y auth — ficheros de riesgo).

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 28.0 | **4** | Schema DB: `instructor_profiles`, `marketplace_courses`,… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 28.1 | **4** | API: CRUD cursos instructor, upload contenido JSON, preview; **código de… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 28.2 | **4** | Quality gate pipeline para instructores: `scripts/instructor_quality_gate.py` corriendo en upload | **TODO** — Verificado… | |
| 28.3 | **4** | Panel instructor — React: dashboard revenue, cursos, métricas por curso | **PARCIAL** — Verificado 2026-09-25 contra el… | |
| 28.4 | **4** | Marketplace público: catálogo con filtros, ratings, preview de primera lección | **PARCIAL** — Verificado 2026-09-25… | |
| 28.5 | **4** | Checkout cursos de instructor: Stripe/Paddle, split automático 70/30 | **PARCIAL** — Verificado 2026-09-25 contra el… | |
| 28.6 | **4** | Panel admin: aprobación de cursos, moderación, gestión de payouts | **TODO** — Verificado 2026-09-25 contra el criterio:… | | |
| 28.7 | **4** | Payouts mensuales: job día 15 de cada mes, mínimo $50; **rail elegido por… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 28.8 | **3** | **UI del marketplace conectada**: `MarketplaceScreen` e `InstructorScreen` (hoy maquetas, 24.10/24.11) contra… | | |
| 28.9 | **3** | **Kit de reclutamiento de instructores** (`MARKETPLACE.md:161-167`: 5 fundadores → 20 → 50+): oferta escrita ES/EN (70 %,… | | |

### 29. Economía cerrada y rails — créditos, referidos, códigos, USDC, credenciales verificables (ADR-33…37; spec `docs/ECONOMIA.md`)

> **Estado:** `ABIERTA` — desbloqueada por el dueño el 2026-09-19 (§1) y H.26 decidido por defecto el 2026-09-24 (ADR-47: la tabla de…
> **Dependencias:** 22.1 (admin), 22.6 (cola de trabajos y `RateLimiter`), 21.7 (ToS para 29.11), 24.6 (UI).
> **PRI:** 3. **Modelo:** Sonnet (migraciones, auth, billing = ficheros de riesgo); Haiku para tests, inventarios y verificación adversaria.
> **Invariante de la serie:** las tres reglas de `ECONOMIA.md` §1 se prueban con tests, no se prometen. Canje solo en web. Ningún «token»…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 29.0 | **1** | **Schema**: `credit_ledger`, `promo_codes`, `promo_redemptions`, `referral_codes`, `referrals` (`ECONOMIA.md` §2.5, §4.2)… | | |
| 29.1 | **1** | **Servicio de créditos** `services/economy/credits.py`: abono con lote y `expires_at`, gasto FIFO, caducidad diaria (job… | | |
| 29.2 | **1** | **Tabla de grifos y sumideros** versionada en `content/economy/credits.json` (ES/EN en etiquetas) + `GET /economy/prices`… | | |
| 29.3 | **2** | **Referidos**: código permanente por usuario, enlace `/r/<código>` que fija… | **PARCIAL** | **PARCIAL** `89eb7a7` → §I |
| 29.4 | **2** | **Códigos de cinco tipos** (`ECONOMIA.md` §4): generación de lotes (CSV), alfabeto sin `0 O 1 I L`, idioma por código,… | | |
| 29.5 | **2** | **Antifraude**: email verificado, hash propio de dispositivo/IP con sal… | **PARCIAL** | **PARCIAL** (2026-09-26) → §I |
| 29.6 | **2** | **Admin** (en 22.1): economía (emitidos/gastados/caducados, ratio sumidero/grifo, alerta de inflación), referidos… | | |
| 29.7 | **3** | **Reactivación automática**: job (cola 22.6) que a los 14 días de inactividad emite código de 72 h y envía email **ES o EN… | | |
| 29.8 | **3** | **UI**: wallet (saldo, lotes que caducan, historial), escalera de referidos con código y enlace, canje de códigos **solo… | | |
| 29.9 | **3** | **USDC como rail** (ADR-36): si H.19 = Stripe → activar *Pay with Crypto* en **test mode** y documentar en 7.2; payouts de… | | |
| 29.10 | **2** | **Credenciales verificables** (ADR-37): Open Badges 3.0 — JSON-LD firmado (clave en env, nunca versionada), `GET… | | |
| 29.11 | **2** | **Cláusulas legales**: créditos (tres reglas §1), referidos, antifraude, caducidad, clawback — ES y EN nativos → entran… | | |
| 29.12 | **3** | **Scorecard de la serie**: métricas `ECONOMIA.md` §7 visibles en admin con objetivos mes 3/6/12; **verificación… | | |


### 30. Integridad del despliegue — incidente de login del 2026-09-24 (PRI 0)

> **Estado:** `ABIERTA` — el código está en la rama `claude/trusting-franklin-2wwmmr` (PR https://github.com/Neopram/whetzy/pull/6); nada…
> **PRI:** 0. **Origen:** captura del dueño — `POST whetzy.com/auth/login` → **405**, pantalla «Incorrect email or password».
> **Invariante de la serie:** un deploy del frontend no está hecho hasta que `node scripts/check-deployed.mjs` sale PASS contra…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 30.0 | **0** | **Login roto en producción.** Medido 2026-09-24: el bundle servido… | **PARCIAL** | **PARCIAL** (2026-09-24) → §I |
| 30.1 | **0** | **La landing en producción publica testimonios y cifras inventados.** El chunk `LandingScreen-*.js` servido hoy contiene… | **DONE** | **DONE** → §I |
| 30.2 | **1** | **Se puede publicar sin puerta.** `ba686fc`, `50e73ea`, `46789fa`, `f8719b1`, `2efdfb7` y `8a0dce0` entraron en `master`… | | |
| 30.3 | **1** | **Guarda de repo para la configuración de Pages.** Un test (en `pytest tests/content` o en el pre-push) que falle si… | **DONE** | **DONE** → §I |
| 30.4 | **1** | **`npm run build` estaba en rojo y nadie lo vio**: el prerender buscaba… | **PARCIAL** | **PARCIAL** `394c660` → §I |
| 30.5 | **2** | El script `build` ya no corre `tsc -b` (lo quitó `8a0dce0`,… | **PARCIAL** | **PARCIAL** `8a0dce0` (2026-09-24) → §I |
| 30.6 | **1** | **La puerta local no puerta en Linux/macOS.** `.githooks/pre-push` está en git como `100644` (sin bit de ejecución): git… | **DONE** | **DONE** → §I |
| 30.7 | **0** | **El mismo fallo que el login en cinco llamadas más.**… | **PARCIAL** | **PARCIAL** `4c63686` (2026-09-25) → §I |
| 30.8 | **0** | **Producción arrancaba sin contenido y sin cuenta de dueño… | **PARCIAL** | **PARCIAL** `12ff838` (2026-09-22) → §I |

### 31. Fuente única de cifras, staging y migraciones con datos (del plan del 2026-09-24, cuyo fichero no está en el repo: estas filas son…

> **Estado:** `TODO`. **PRI:** 1. **Por qué:** los documentos vivos dan cifras distintas del mismo banco (6.233 frente a 6.305 preguntas)…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 31.0 | **1** | `scripts/project_snapshot.py`: extraer a un módulo el recuento que `check_docs.py` ya hace (preguntas reales, línea ~97) y… | | |
| 31.1 | **1** | Staging: un preview de Cloudflare Pages y un servicio de Railway de staging; `master` solo por PR verde | HUMAN-BLOCKED… | |
| 31.2 | **2** | Migración con datos: fixture de base en la revisión anterior, `upgrade head`, conteos de filas y `downgrade -1` en… | | |
| 31.3 | **2** | Smoke post-deploy de backend: login con cuenta QA, `POST /quiz/start`, `GET /health/ready`, ejecutado tras cada fusión del… | | |

### 32. Motor demostrable — calibración y evidencia de aprendizaje (del plan del 2026-09-24; ídem)

> **Estado:** `TODO` (32.2 `BLOCKED` por H.10). **PRI:** 2. **Relación:** complementa 11.8 y 14.8; no las sustituye.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 32.0 | **2** | Inventario: qué guarda hoy cada respuesta (p_known antes/después, Elo, S/D de FSRS, `expected_p`, tiempo) y qué falta, sin… | | |
| 32.1 | **2** | Curva de fiabilidad de `p_known`: 5 tramos, predicho contra acierto real posterior; script reproducible | DONE |… |
| 32.2 | **3** | A/B BKT contra DKT con el framework 24.14 (asignación estable por usuario) | BLOCKED (H.10) | DKT se adopta solo si AUC ≥… |
| 32.3 | **2** | «¿Por qué esta pregunta?»: el scheduler devuelve sus razones (dominio, repaso vencido, dificultad objetivo 0,75) y el quiz… | | |

### 33. Operación medible — SLO, restauración y offline idempotente (del plan del 2026-09-24; ídem)

> **Estado:** `TODO`. **PRI:** 2. **Relación:** 22.6 y 22.7 cubren cola, caché y página de estado; esto añade objetivos numéricos y ensayos.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 33.0 | **2** | SLO escritos en `RUNBOOK.md` (disponibilidad API ≥ 99,5 %, quiz p95 < 500 ms, `/health/ready` p95 < 500 ms, RPO ≤ 24 h,… | | |
| 33.1 | **2** | Ensayo de restauración mensual con `scripts/db_restore_test.sh` y registro de conteos | DONE | `db_restore_test.sh`… |
| 33.2 | **2** | Cola offline idempotente: `event_id` UUID por respuesta en `frontend/src/services/offlineQueue.ts`; el servidor descarta… | | |


### 34. Una sola interfaz: todas las pantallas al lenguaje visual de la landing (abierta 2026-09-24, a petición del dueño)

> **Estado:** `ABIERTA`. **PRI:** 0 para 34.0–34.1 (hoy la app sale **sin estilos**), 1–2 para el resto.
> **Punto de partida medido (2026-09-24):** **276 de 761** referencias `styles.x` apuntan a clases que no existen en su `.module.css` —…
> **Cómo se trabaja (el bucle «tipo Lovable»):** una oleada = una rama y un PR. Cloudflare Pages publica un preview por push…
> **Invariantes de la serie:** (1) se copia el **estilo** de la landing, nunca su contenido inventado (30.1/H.31); (2) cero regresiones de…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 34.0 | **0** | **Guarda de contrato `.tsx` ↔ `.module.css`** (`src/test/cssModules.contract.test.ts`) en modo trinquete: la deuda de hoy… | **DONE** | **DONE** → §I |
| 34.10 | **0** | **La suite e2e está roja desde el 2026-09-19 y nadie lo vio** (CI ciego por facturación y, después, sin… | **DONE** | **DONE** → §I |
| 34.11 | **1** | **Hallazgos de comportamiento vistos al rediseñar (no son estilo):** (a)… | **PARCIAL** | **PARCIAL** (2026-09-24) → §I |
| 34.1 | **0** | **Devolver el estilo a las 13 pantallas rotas**: por fichero,… | **PARCIAL** | **PARCIAL** `d11db88` (2026-09-25) → §I |
| 34.2 | **1** | **Un solo juego de tokens**: una sola fuente (`src/theme/tokens.css` o… | **PARCIAL** | **PARCIAL** `d11db88` → §I |
| 34.3 | **1** | **Componentes base** al estilo de la landing: `Button`, `Card`, `Badge`, `Modal`,… | **PARCIAL** | **PARCIAL** → §I |
| 34.4 | **1** | **Primer uso**: Auth (login, registro, OAuth, olvido/reset), Onboarding,… | **PARCIAL** | **PARCIAL** `d11db88` → §I |
| 34.5 | **1** | **Aprendizaje**: Home, Tracks, Lesson y Quiz (con Monaco, WhyButton, GlossaryText, TermCard) | **PARCIAL** — pantallas del… | |
| 34.6 | **2** | **Progreso y social**: Profile, Stats, League, Duel, Readiness, MockExam,… | **PARCIAL** | **PARCIAL** `d11db88` → §I |
| 34.7 | **2** | **Resto**: Admin, Instructor, Marketplace, Legal, Evidence, DeleteAccount | **PARCIAL** — pantallas del bloque revisadas… | |
| 34.8 | **2** | **Regresión visual**: Playwright con capturas por ruta (ES/EN × móvil/escritorio)… | **PARCIAL** | **PARCIAL** → §I |
| 34.9 | **2** | **Verificación y re-puntuación**: verificador adversario (protocolo §7) de 34.0–34.8 y fila nueva en el teardown… | | |

### 35. Lo que el mercado enseña: competencia verificada → producto (abierta 2026-09-24, a petición del dueño)

> **Estado:** `ABIERTA`. **PRI:** 1.
> **Origen:** captura en vivo de 33 sitios de competencia directa e indirecta (páginas públicas, sin registro), sintetizada en…
> **Hallazgo que ordena la serie:** varias «ideas nuevas» de los informes **ya existen en el código y no se ven**: la prueba de nivel está…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 35.1 | **1** | **Comparativa pública verificada en la landing**: solo cifras re-descargadas y fechadas, `null` = no comprobado | **DONE**… | |
| 35.2 | **1** | **«Salta lo que ya sabes», explicado**: tras la prueba de nivel, enseñar qué módulos se marcaron como dominados y por qué… | **DONE** | **DONE** → §I |
| 35.3 | **1** | **Racha amable**: 1 comodín gratis por semana ISO (sin acumular; los comprados se conservan), visible en Home, y «perder… | **DONE** | **DONE** → §I |
| 35.4 | **2** | **Ligas opt-in visible**: interruptor en la propia pantalla de ligas («totalmente opcional») | **DONE** — 2026-09-24:… | |
| 35.5 | **1** | ***Readiness* por dominio como producto estrella de las rutas cloud y seguridad**, en ES y EN: visible desde Tracks y la… | **DONE** | **DONE** → §I |
| 35.6 | **2** | **Refresco trimestral de §A.1**: re-descargar las páginas de precios, cambiar cifras y `COMPARISON_CHECKED_ON` | TODO —… | |
| 35.7 | **1** | **Precios del dueño en producto** (ADR-41): landing con 4 planes, perfil, comparativa; tier `creator` (rango sobre `pro`),… | **DONE** | **DONE** → §I |
| 35.8 | **2** | **Cada deploy de Railway deja ~1 min de 502/503.** Medido 2026-09-24: tras los pushes `a6a5a91` y `f2ea9cb`, `/health` dio… | | |
| 35.9 | **2** | **El nivel 2 de la puerta (`ci_local.sh`) corre sobre el árbol… | **PARCIAL** | **PARCIAL** `a021e92` (2026-09-24) → §I |


### 37. Catálogo total — todos los tracks de la industria, ≥ 50 cursos por track, sobre un corpus abierto (ADR-46; abierta 2026-09-24)

> **Estado:** `ABIERTA`. **PRI:** 1 (detrás de la serie 30). **Modelo:** Haiku para descarga, inventario, limpieza y autoría por fichero;…
> **Orden obligatorio:** 37.0 → 37.1 → 37.2 → 37.3 → bloques. **Nadie escribe una pregunta nueva hasta que 37.0 esté DONE**: el intento del…
> **Corpus (ADR-46 §4-5):** `corpus/` está en `.gitignore`. Se descarga con `git clone --depth 1`, dumps oficiales y **torrents solo cuando…
> **Unidad:** curso = módulo = 4 skills · 60 Q · 4 lecciones · ≥ 8 términos · ≥ 15 % ejecutable donde aplique. Un bloque = un PR verde con…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 37.0 | **1** | **Guarda de diversidad semántica** en `scripts/check_question_bank.py`: por track, enunciados distintos ≥ 90 %, opciones… | **DONE** | **DONE** → §I |
| 37.1 | **1** | **Inventario de la industria vs catálogo**: contrastar… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 37.2 | **1** | **Recuento por módulos**: `check_docs.py` y `lib/catalog.ts` pasan de «curso = track × nivel» a «curso = módulo» en el… | **DONE** | **DONE** → §I |
| 37.3 | **1** | **Pipeline de corpus** `scripts/corpus/`: `fetch.py` (git/dump/torrent oficial), `verify_license.py` (lee… | **DONE** | **DONE** → §I |
| 37.4 | **2** | **Descarga y verificación del corpus por área** (una subfila por área en… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 37.5 | **2** | **Generador desde corpus**: `scripts/generate_track_content.py` (absorbe 25.0) toma track + módulo + fragmentos del corpus… | | |
| 37.6 | **2** | **Bloques de tracks existentes a 50 cursos** — orden: track01-03 → 12 → 06-07 → 04-05 → 13/24/25 (reescribiendo las 800… | | |
| 37.7 | **2** | **Tracks del mapa sin construir** (18-23, 26-27, 29-32) al molde mínimo primero (20 skills · 300 Q) y luego a 50 cursos —… | | |
| 37.8 | **2** | **Tracks nuevos de §2.0** (Java/JVM, C#/.NET, Go, Rust, C/C++ y sistemas, TypeScript, SRE/observabilidad, MLOps,… | | |
| 37.9 | **2** | **Glosario ≥ 400 términos por track**, ES y EN nativos (absorbe 25.12) | BLOCKED (37.6) | `check_docs.py`: 0 términos sin… |
| 37.10 | **2** | **Certificaciones: blueprints de las 55 del catálogo §3** con simulacro por dominio, pesos verificados contra la guía… | | |
| 37.11 | **3** | **Proyectos multi-paso**: 10 por track ejecutable (hoy 0; catálogo §1) | BLOCKED (37.6) | Cada proyecto con tests de… |
| 37.12 | **3** | **Monitoreo trimestral de competencia** (`CATALOGO_MAESTRO.md` §11.4 apuntaba a una fila que no existía; complementa… | | |
| 37.13 | **3** | **Scorecard ADR-46** (absorbe 25.13): tracks × cursos × 37.0 verde; re-puntuación de Contenido en el teardown con… | | |
| 37.14 | **1** | **track13 (ciberseguridad) tiene enunciados repetidos: 87,9 % distintos**, por debajo del 90 % de ADR-46 (medido por… | | |
| 37.15 | **1** | **Fuentes sin indexar:** 3.906 de 6.305 preguntas (62 %) no llevan URL en… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 37.16 | **1** | **La correcta es la opción más larga.** Medido 2026-09-25 sobre… | **PARCIAL** | **PARCIAL** `2041992` (2026-09-25) → §I |

### 38. Negocio medible — KPIs, pilotos B2B, instructores, afiliados (ADR-47; abierta 2026-09-24)

> **Estado:** `ABIERTA`. **PRI:** 2. Todo lo que aquí exige hablar con personas o crear cuentas lo prepara la sesión y lo ejecuta el dueño…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 38.0 | **2** | **KPIs de `DISTRIBUCION.md` §10 y ADR-32 en el admin** (22.1): registrados, pagos, MRR, D30, NPS, K-factor, % referidos,… | | |
| 38.1 | **2** | **Precios: una sola fuente = ADR-41 (dueño)**: Pro 14,99 $ · Pro Max 19,99 $ · Creador 99,99 $, 80/20. 35.7 ya los puso en… | | |
| 38.2 | **2** | **Oferta de 3 pilotos B2B gratuitos** (ADR-22): documento ES/EN (qué damos, qué pedimos: testimonio y datos de uso, 90… | | |
| 38.3 | **2** | **Dossier de afiliación** Python Institute y CompTIA (`archive/whetzy_estrategia_definitiva_v3.md:392`): condiciones,… | | |
| 38.4 | **3** | **Kit de reclutamiento de instructores** — es la fila 28.9; aquí solo para que la serie 38 lo tenga a la vista | DONE… | |
| 38.5 | **3** | **Página `/evidence` como única prueba social** (19.8, 30.1): cifras del banco y del motor calculadas en build, cero… | | |
| 38.6 | **2** | **Pro Max = tutor IA ilimitado; Pro con cupo diario** (ADR-49). `POST /tutor/explain` cuenta las explicaciones por usuario… | | |
| 38.7 | **2** | **Certificación a 39,99 $ de pago único** (ADR-49). Hoy los tracks `is_certification` no emiten certificado… | | |

## 3. Cola HUMAN-BLOCKED

> → `docs/archive/LEDGER_HISTORY.md` §J

| H.16 | PRI 0 — `git push` a `master` DESPLIEGA A PRODUCCIÓN, y el c… |
| H.15 | PRI 0 - el proxy de `vite` apunta a la API de PRODUCCION en … |
| H.12 | PRI 0 de seguridad — rotar la `GROQ_API_KEY`. Estuvo commite… |
| H.13 | PRI 0 - GitHub Actions dejo de ejecutar jobs por facturacion… |
| H.2 | Apple Developer Program — y desde 2026-09-18 también bloquea… |
| H.3 | Google Play Console |
| H.4 | Stripe cuenta live |
| H.5 | Submisión a stores |
| H.14 | iOS no se puede generar ni compilar en este PC (Windows, sin… |
| H.6 | Cadena de sesiones |
| H.7 | Rutina remota — única forma de no depender de la app abierta |
| H.8 | `GROQ_API_KEY` ausente localmente |
| H.9 | Dispositivo físico o emulador con lector de pantalla real pa… |
| H.10 | Cohorte beta ≥ 30 usuarios reales (11.8) |
| H.17 | CI ciego por facturación de GitHub (continuación de H.13, a … |
| H.18 | La cadena solo corre con la app Claude abierta y el PC despi… |
| H.19 | Decidir rail de pagos y entidad (ADR-16) — ahora depende de … |
| H.20 | Revisión profesional de los textos legales antes de publicar… |
| H.22 | ¿Aceptar [H.LIC] para OWASP (CheatSheets/WSTG/ASVS, CC BY-SA… |
| H.23 | Abrir la Serie 26 (distribución ES) cuando 24.14 esté DONE |
| H.24 | Abrir la Serie 28 (marketplace) cuando 22.1 y 22.3 estén DON… |
| H.25 | Activar payouts de instructores en producción (28.7) |
| H.26 | Abrir la Serie 29 (economía cerrada) cuando 24.6 esté DONE: … |
| H.27 | cNFT de certificados en Solana (29.10, opcional; ADR-37): wa… |
| H.28 | Grant / bounty de la Solana Foundation o Superteam para trac… |
| H.29 | ABIERTO 2026-09-19 — Decisión: Grecia + 3 rails de pagos + a… |
| H.30 | PRI 0 — el correo no sale de la maquina, y la pantalla dice … |
| H.31 | PRI 0 — la landing de producción publica testimonios con nom… |
| H.32 | **2** | H.32 | **RESUELTA** | **RESUELTA** `e40ba75` (2026-09-24) → §I |
| H.33 | Variables del dueño en Railway (30.8) |
| H.34 | Conector de Railway para Claude (verificación de 30.8 sin ad… |
| H.35 | **2** | H.35 | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| H.38 | Afiliación con Python Institute y CompTIA (38.3) |
| H.39 | 3 pilotos B2B gratuitos (38.2, ADR-22) |
| H.40 | Reclutar 5 instructores fundadores (28.9) |

## 5. Bitácora de decisiones

> Decisiones archivadas en `docs/archive/LEDGER_HISTORY.md` §J.
> ADRs formales: `docs/DECISIONS.md`.

---

## 6. Cadena de sesiones

> → `docs/archive/LEDGER_HISTORY.md` §G
