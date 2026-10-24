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
| Backend prod | `https://api.whetzy.com` (#228; Railway sigue activo) |
| Frontend prod | `https://whetzy.com` / `https://whetzy.pages.dev` — **deploy AUTOMÁTICO desde `master`** (Cloudflare Pages conectado a… |
| Repo | `github.com/Neopram/whetzy` branch `master` |
| Autonomía | **ADR-45 (2026-09-24): la sesión trabaja en su rama y abre un PR por oleada; NUNCA `git push origin master` ni fusiona.… |
| DB local | Docker :5433, user `neurium`, pass `neurium_dev`, db `neurium` |
| Modelo LLM | `qwen/qwen3.8-27b` en Groq (llama-3.3-70b NO disponible) |
| Fuentes de contenido | **Solo gratuitas y legales** (ADR-11): reutilizable = MIT / Apache-2 / BSD / CC BY / CC0 / PSF / dominio público;… |
| Railway deploy | **AUTOMÁTICO DESDE `master` — el invariante anterior («MANUAL, sin webhook GitHub») es FALSO y llevaba meses ahí.**… |
| Alembic HEAD | `20261022_perfil_publico` (70 migraciones) |
| Contenido | **12.037 preguntas** / 35 tracks / 730 skills / **730 lecciones (100 %)** / **1.058 términos glosario**. Tracks 09/10/11 =… |

### Gotchas verificados

> → `docs/archive/LEDGER_HISTORY.md` §H

---

## 1. Estado por fase

> Generada desde las filas de `## 2` con `python scripts/ledger.py fases --write`; no se edita
> a mano (`ledger.py check` falla si no cuadra). Series ≤ 16 y 25: `LEDGER_HISTORY.md` §F y §M.

| Serie | Nombre | DONE/Total | % | Abiertas |
|---|---|---|---|---|
| 46 | Experiencia avanzada | 16/20 | 80 % | 46.5, 46.6, 46.14, 46.15 |
| 43 | Flujo del alumno listo para pruebas | 7/8 | 88 % | 43.6 |
| 42 | Ultracode: código tras la sincronización | 7/13 | 54 % | 42.1, 42.3, 42.7, 42.8, 42.10, 42.13 |
| 41 | Documentación al día con el código | 5/6 | 83 % | 41.3 |
| 40 | Superar a Brilliant y Kodree donde hoy ganan | 1/13 | 8 % | 40.2, 40.3, 40.4, 40.5, 40.6, 40.7 +6 |
| 39 | Noche 2026-09-26 — incidente de arranque, deuda de calidad y aprobaci… | 32/41 | 78 % | 39.8, 39.9, 39.10, 39.26, 39.27, 39.33 +1 |
| 38 | Negocio medible — KPIs, pilotos B2B, instructores, afiliados | 6/6 | 100 % | — |
| 37 | Catálogo uniforme 32 × 10, simulacros reservados y prioridad por dema… | 7/23 | 30 % | 37.1, 37.4, 37.5, 37.6, 37.7, 37.8 +10 |
| 35 | Lo que el mercado enseña: competencia verificada → producto | 4/5 | 80 % | 35.6 |
| 34 | Una sola interfaz: todas las pantallas al lenguaje visual de la landi… | 4/11 | 36 % | 34.2, 34.3, 34.4, 34.6, 34.7, 34.8 +1 |
| 33 | Operación medible — SLO, restauración y offline idempotente | 1/1 | 100 % | — |
| 32 | Motor demostrable — calibración y evidencia de aprendizaje | 2/3 | 67 % | 32.2 |
| 31 | Fuente única de cifras, staging y migraciones con datos | 3/7 | 50 % | 31.1, 31.5, 31.6, 31.8 |
| 30 | Integridad del despliegue — incidente de login del 2026-09-24 | 3/4 | 75 % | 30.2 |
| 29 | Economía cerrada y rails — créditos, referidos, códigos, USDC, creden… | 7/8 | 88 % | 29.9 |
| 28 | Marketplace de instructores | 4/9 | 44 % | 28.1, 28.4, 28.5, 28.7, 28.8 |
| 27 | Distribución masiva EN | 0/11 | 0 % | 27.0, 27.1, 27.2, 27.3, 27.4, 27.5 +5 |
| 26 | Distribución masiva ES | 0/11 | 0 % | 26.0, 26.1, 26.2, 26.3, 26.4, 26.5 +5 |
| 24 | Interfaz que venda al verse — UI/UX + competencia en vivo + vídeo | 1/9 | 11 % | 24.0, 24.1, 24.2, 24.3, 24.4, 24.6 +2 |
| 23 | Dos segmentos, un producto — ES y EN sin mezclar | 3/5 | 60 % | 23.2, 23.3 |
| 22 | Blindaje, admin y preparación para un millón — todo a coste cero | 0/1 | 0 % | 22.5 |
| 21 | Legal y fiscal a coste cero — investigación, borradores, gates humanos | 0/4 | 0 % | 21.1, 21.2, 21.5, 21.6 |
| 20 | Verificación masiva código ↔ docs ↔ prod | 1/1 | 100 % | — |
| 19 | Lo que Educative y las tiendas exigen — social login, bootcamps, proy… | 2/9 | 22 % | 19.2, 19.3, 19.7, 19.8, 19.9, 19.10 +1 |
| 18 | Techo de código — todo el catálogo, sin racionar | 1/5 | 20 % | 18.9, 18.10, 18.11, 18.12 |
| 17 | De quiz a escuela + release definitivo | 0/7 | 0 % | 17.5, 17.6, 17.7, 17.10, 17.14, 17.15 +1 |
| 16 | CI en rojo | 0/3 | 0 % | — |
| 14 | La cuña | 0/6 | 0 % | 14.7, 14.8, 14.9, 14.10, 14.13, 14.14 |
| 11 | Superioridad medible | 1/3 | 50 % | 11.8, 11.9 |

---

## 2. Backlog ejecutable

> Orden de ejecución = por `PRI` ascendente, luego por ID. `PRI 0` es lo que
> desbloquea todo lo demás.

### 11 — Superioridad medible (cerrar las brechas honestas)
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 11.6 | 3 | Tiempo hasta primera pregunta < 60 s contra prod con 4G si… | **DONE** | `5e306fb` → §T |
| 11.8 | 3 | **Prueba de aprendizaje real**: cohorte beta ≥ 30 usuarios | HUMAN-BLOCKED (H.10) | Dashboard 5.5 muestra D1 ≥ 40 % / D7 ≥ 20… |
| 11.9 | **2** | 11.9 | **PARCIAL** | **PARCIAL** → §I |

### 14 — La cuña (dirección aprobada 2026-09-14)
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 14.7 | 3 | **PCEP** — primera certificación del carril 1 (decisión #25) | TODO | → LEDGER_HISTORY.md §E |
| 14.8 | 4 | **Predictor beta-binomial de aprobado** con calibración pública | BLOCKED (11.8 · H.10) | → LEDGER_HISTORY.md §E · simulado `5dc7f6b` (#97) → §R |
| 14.9 | 4 | **Informe de dominio verificable** por URL | BLOCKED (11.8 · H.10) | → LEDGER_HISTORY.md §E · aritmética `432bdd2` (#97) → §R |
| 14.10 | 5 | **IRT (θ) — el modelo de Vicks** | BLOCKED (datos) | → LEDGER_HISTORY.md §E · JMLE simulado `b43424c` (#97) → §R |
| 14.13 | 2 | Cuatro tracks nuevos: Linux/CLI · SQL y bases de datos · Framework… | TODO | →… |
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


### 17. De quiz a escuela + release definitivo (web · App Store · Play Store)
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 17.5 | **3** | **Tracks nuevos desde fuentes con licencia permisiva** | PARCIAL | → LEDGER_HISTORY.md §E |
| 17.6 | **2** | **UI de clase mundial, medida** | TODO | → LEDGER_HISTORY.md §E |
| 17.7 | **4** | **Vídeos explicativos generados desde código** | TODO | → LEDGER_HISTORY.md §E |
| 17.10 | **3** | **Re-puntuar frente a la competencia con lo anterior hecho** | TODO | → LEDGER_HISTORY.md §E |
| 17.14 | **1** | Compras dentro de la app (la antigua 7.6, sin fila desde hace mese… | **PARCIAL** | backend hecho (webhook RevenueCat); SDK/UI: Test Store sin consolas, espera decisión del dueño (STORE_LISTING §4) → §T |
| 17.15 | **1** | APK de depuración instalable sin Play Console (D.1) | PARCIAL (preparado, no verificado: smoke en dispositivo) | RUNBOOK «App Android de depuración» |
| 17.16 | **2** | Avisos nativos (FCM/APNs): la app solo tiene Web Push | TODO | RUNBOOK «App Android de depuración» |

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
| 18.4 | **2** | … | DONE — `bec734c` → §T (6) | → §T (6) |
| 18.9 | **4** | **Vídeo explicativo — piloto que decide** | TODO | → LEDGER_HISTORY.md §E |
| 18.10 | **4** | **Resto del catálogo: tracks 24-26, 28-31 y certs P2-P3** | **PARCIAL** | 26/28/29/30 en `1d76762`+`6e2778a` (1.200 Q, 80 lecciones); faltan 24, 25, 31 y relleno a 300 → §E |
| 18.11 | **2** | **Store-ready sin cuenta** | **PARCIAL** | listing, borrado de cuenta y textos hechos; faltan capturas y build iOS (H.14) → §T |
| 18.12 | **3** | **Re-puntuación con URLs fechadas** | TODO | → LEDGER_HISTORY.md §E |

### 19. Lo que Educative y las tiendas exigen — social login, bootcamps, proyectos, autoría con fuentes libres (abierta 2026-09-18, sesión…
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 19.2 | **1** | Sign in with Apple — obligatoria: Google en vivo (21-10)… | PARCIAL (preparado, no verificado: H.2) | Código y tests con claves propias; RUNBOOK «App iOS» |
| 19.3 | **2** | Android: Google Sign-In nativo + Google Play Billing vía RevenueCa… |  | → §I (criterio archivado por 20.10) |
| 19.7 | **2** | **Biblioteca de autoría con fuentes libres + RAG local** | TODO | → LEDGER_HISTORY.md §E |
| 19.8 | **3** | **Landing y SEO de whetzy.com al nivel de Educative** | TODO | → LEDGER_HISTORY.md §E |
| 19.9 | **3** | **Assets de tiendas e iconos de todos los tracks** (plan ADR-53) | TODO | → LEDGER_HISTORY.md §E |
| 19.10 | **4** | **Vídeo: Manim + Remotion (`editor-pro-max`)** — absorbe 18.9 | TODO | → LEDGER_HISTORY.md §E |
| 19.11 | **1** | Moderación de UGC mínima (App Store 1.2/1.2.1) | **DONE** | `395d20f` → §T |
| 19.12 | **2** | Borrado de cuenta con purga real a los 30 días (textos leg… | **DONE** | `b2e3159` → §T |
| 19.13 | **1** | Proyecto de Xcode en git (`frontend/ios/`), iconos y splash de Whetzy | PARCIAL (preparado, no verificado: H.2, sin Mac) | RUNBOOK «App iOS» |

### 20. Verificación masiva código ↔ docs ↔ prod (abierta 2026-09-18, sesión bf — **ABIERTA 2026-09-18 (H.21 ejecutada)**)
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 20.7 | **1** | CI ciego: `verify_ci_local.ps1` replica `ci.yml` paso a paso | **DONE** | `d4de5d2` → §T |

### 21. Legal y fiscal a coste cero — investigación, borradores, gates humanos (abierta 2026-09-18, sesión bf — **H.20 SIGUE ABIERTO** — el…
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 21.1 | **1** | *(Premisa griega suspendida por ADR-47; destino Chipre por ADR-61… | BLOCKED (H.54) | → §I (criterio archivado por 20.10) |
| 21.2 | **1** | *(Premisa griega suspendida por ADR-47; valor por defecto: Merchan… | BLOCKED (H.54) | → §I (criterio archivado por 20.10) |
| 21.5 | **2** | **AI Act, DSA, EAA**: obligaciones de *deployer* del tutor… | **PARCIAL** | **PARCIAL** `5f7bd7b` (2026-09-19) → §I |
| 21.6 | **2** | **Propiedad intelectual**: búsqueda de marca «Whetzy» (EUIPO,… | **PARCIAL** | **PARCIAL** `8e7812a` (2026-09-19) → §I |

### 22. Blindaje, admin y preparación para un millón — todo a coste cero (abierta 2026-09-18, sesión bf — **ABIERTA 2026-09-18 (H.21)**;…
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 22.5 | **2** | Cloudflare free: WAF managed rules, rate limiting rules por ruta… |  | → §I (criterio archivado por 20.10) |

### 23. Dos segmentos, un producto — ES y EN sin mezclar (abierta 2026-09-18, sesión bf — **ABIERTA 2026-09-18 (H.21)**; ADR-17)
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 23.1 | **1** | Auditoría E2E por idioma: cada pantalla, email, push, PDF/… | **DONE** | `c0a5af6` → §T |
| 23.2 | **2** | Landing y SEO por segmento: `/es` y `/en` con copy nativo (no trad… |  | → §I (criterio archivado por 20.10) |
| 23.3 | **2** | Tiendas, emails y soporte por idioma: listings ES/EN en `store/`… | **PARCIAL** | `3497429` (#93) → §S |
| 23.4 | **3** | **Segmento en el admin**: filtrable por idioma | **DONE** | → §N |
| 23.5 | **1** | Las dos guardias de i18n daban números falsos y la que cit… | **DONE** | `d991fe4` → §T |

### 24. Interfaz que venda al verse — UI/UX + competencia en vivo + vídeo (sesión interactiva; **después** de 20-23; absorbe 17.6 y 19.8;…

> **Estado:** `ABIERTA 2026-09-24` (ADR-45/47). Las filas BLOCKED pasan a PARCIAL: hay commits `24.x` en `master` pero son maquetas con…
> **Modo:** rama + PR + preview de Cloudflare (`<rama>.whetzy.pages.dev`); el dueño revisa el preview antes de fusionar, no cada pantalla…
> **Modelo:** Sonnet para código (`frontend/src` es fichero de riesgo); Haiku para inventarios y verificación.
> **Evidencia común a toda fila:** captura fechada en `docs/screenshots/<fecha>/`, `npx tsc -b --force` + `npx vitest run` + `npm run…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 24.0 | **1** | **Investigación competitiva en vivo**: navegar el free tier de los 8… | **PARCIAL** | 7/8 capturadas; faltan las vistas con cuenta y Exercism/Platzi (bloqueados) → §T |
| 24.1 | **1** | **Identidad visual**: tokens de diseño (color con hue propio, tipografía… | **PARCIAL** | 2026-10-16: colores del logo aprobados por el dueño el 2026-10-13 y aplicados (#197) → §T |
| 24.2 | **1** | **Landing que vende** (`/es`, `/en`; absorbe 19.8 y 23.2): hero con el… | **PARCIAL** | Lighthouse (preview): perf 77-89, a11y 94. LCP 3965-4392ms, falla presupuesto 2500ms. Falta: demo 3 preguntas, remedir en prod, copy/A-B del dueño → §I |
| 24.3 | **1** | **Onboarding rediseñado**: 3 preguntas de segmento (`SEGMENTOS.md` §«Cómo… | **PARCIAL** | 2026-10-16: el alta lleva a la primera lección (D-20, #188; e2e en #220). Falta abandono por paso en admin (22.1) → §T |
| 24.4 | **1** | **Dashboard con el motor visible**: mapa de dominio por skill (BKT como… | **PARCIAL** | 2026-10-16: bandas con evidencia en Hoy y Preparación (#189); el Elo solo en DEV (#205, ADR-60) sustituye a «Elo visible». Falta fuente por número → §T |
| 24.6 | **2** | **Gamificación original + wallet de créditos**: racha con identidad… | PARCIAL `601b5bb`: canje e informe en nativo ocultos | saldo = ledger y e2e; decisión del dueño sobre el informe |
| 24.7 | **2** | Panel de certificación: readiness por dominio (18.1), simu… | **DONE** | → §T |
| 24.8 | **2** | **Perfil público** `/u/<handle>` (opt-in): dominio verificado,… | PARCIAL `0e26ec4`, `bbe8ded` (`/u/*` noindex) | e2e; imagen OG (fuera de alcance) |
| 24.9 | **2** | Panel B2B (`SEGMENTOS.md` segmento 5): progreso por empleado, tiem… |  | → §I (criterio archivado por 20.10) |

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

### 26. Distribución masiva ES (ADR-23, ADR-27; spec `DISTRIBUCION.md`)

> **Estado:** `ABIERTA 2026-09-24` — 24.14 es DONE y H.23 queda decidido por defecto (ADR-47: sí). **La sesión redacta y construye todo;…
> **Dependencias:** 24.14 DONE. Ningún dato inventado en ningún activo (30.1/H.31).
> **PRI:** 3. **Modelo:** Sonnet para contenido (ADR-59) y para copy de landing/emails.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 26.0 | **4** | Canal YouTube ES creado: banner, descripción, links, 3 videos demo… |  | → §I (criterio archivado por 20.10) |
| 26.1 | **4** | 5 artículos en Dev.to / Hashnode ES sobre el motor técnico (BKT, F… | **PARCIAL** | `3497429` (#93) → §S |
| 26.2 | **4** | PR en `EbookFoundation/free-programming-books` agregando Whetzy en… | TODO (redactar/construir; publicar… | → §I (criterio archivado por 20.10) |
| 26.3 | **4** | Template de email para universidades LATAM + lista de 50 contactos | TODO (redactar/construir; publicar bajo cuenta nueva… | → §I (criterio archivado por 20.10) |
| 26.4 | **4** | Página de landing para segmento career-switcher ES (dentro de whet… | TODO (redactar/construir; publicar… | → §I (criterio archivado por 20.10) |
| 26.5 | **4** | Página de landing para segmento B2B ES (whetzy.com/es/empresas) | TODO (redactar/construir; publicar bajo cuenta nueva =… | → §I (criterio archivado por 20.10) |
| 26.6 | **4** | Show HN post en español (Hacker News): preparación + activos | TODO (redactar/construir; publicar bajo cuenta nueva =… | → §I (criterio archivado por 20.10) |
| 26.7 | **4** | Perfiles en comunidades ES: Python Argentina Discord, Dev En Españ… | HUMAN-BLOCKED (H.23: perfiles… |  |
| 26.8 | **4** | Superteam LATAM (México, Argentina, Brasil) como canal (ADR-38): p… |  | → §I (criterio archivado por 20.10) |
| 26.9 | **3** | Blog `/blog` ES/EN (SEO orgánico, `archive/SPEC_WEB.md:152`): Mark… | **PARCIAL** | `3497429` (#93) → §S |
| 26.10 | **3** | Newsletter (`archive/EXECUTION_PLAN_25-29.md:87`): alta con doble… | PARCIAL `2975cb2`: envío real depende de H.30 | proveedor de correo (H.30) |

### 27. Distribución masiva EN (ADR-27; spec `DISTRIBUCION.md`)

> **Estado:** `ABIERTA 2026-09-24` (ADR-47). Misma regla que la 26: se redacta y construye todo; publicar bajo cuenta nueva = H.23.
> **Dependencias:** ninguna para redactar; 26.0 DONE antes de grabar vídeo EN.
> **PRI:** 3. **Modelo:** Sonnet para contenido (ADR-59) y para copy.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 27.0 | **4** | Canal YouTube EN creado: banner, descripción, 3 videos EN (mismo c… |  | → §I (criterio archivado por 20.10) |
| 27.1 | **4** | Show HN EN: "I built an adaptive Python→AI learning engine in Span… | TODO (redactar/construir;… | → §I (criterio archivado por 20.10) |
| 27.2 | **4** | 5 artículos en Dev.to / freeCodeCamp News EN sobre motor técnico | **PARCIAL** | `3497429` (#93) → §S |
| 27.3 | **4** | PR en `jwasham/coding-interview-university` y… | TODO (redactar/construir;… | → §I (criterio archivado por 20.10) |
| 27.4 | **4** | Product Hunt preparación: assets, lista de 100 upvoters confirmado… | TODO (redactar/construir; publicar = H.23)… | → §I (criterio archivado por 20.10) |
| 27.5 | **4** | Product Hunt lanzamiento | HUMAN-BLOCKED (H.23) | Top 5 del día en categoría Education |
| 27.6 | **4** | Reddit strategy EN: 10 respuestas de valor en r/learnpython, r/csc… | HUMAN-BLOCKED (H.23: cuenta y karma… |  |
| 27.7 | **4** | Landing page segmento career-switcher EN (whetzy.com/en/career) | TODO (redactar/construir; publicar = H.23) | Lighthouse… |
| 27.8 | **4** | Landing page segmento B2B EN (whetzy.com/en/enterprise) | TODO (redactar/construir; publicar = H.23) | Demo request form… |
| 27.9 | **4** | Superteam global / Solana developer communities EN (ADR-38): Solan… |  | → §I (criterio archivado por 20.10) |
| 27.10 | **3** | Comparativa honesta frente a Coursera/Udemy (`DECISIONS.md` ADR-24… | **PARCIAL** | `3497429` (#93) → §S |

### 28. Marketplace de instructores (ADR-29; spec `MARKETPLACE.md`)

> **Estado:** `ABIERTA 2026-09-24` (ADR-47). El código de 28.0–28.7 ya está en `master` (migración `u1v2w3x4y5z6_admin_tables`,…
> **Dependencias:** 22.1 PARCIAL (basta), 22.3 DONE. Ver spec completo en `docs/MARKETPLACE.md`.
> **PRI:** 3. **Modelo:** Sonnet (toca DB schema y auth — ficheros de riesgo).

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 28.0 | **4** | Schema DB: `instructor_profiles`, `marketplace_courses`,… | DONE `2975cb2` | `test_esquema_instructor.py` 18 passed |
| 28.1 | **4** | API: CRUD cursos instructor, upload contenido JSON, preview; códig… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 28.2 | **4** | Quality gate pipeline para instructores… | **DONE** | → §T |
| 28.3 | **4** | Panel instructor — React: dashboard revenue, cursos, métricas por… | DONE `8435112` (guarda backend y frontend, mutada) | 403 sin `can_create_courses` |
| 28.4 | **4** | Marketplace público: catálogo con filtros, ratings, preview de pri… | **PARCIAL** — Verificado 2026-09-25… | → §I (criterio archivado por 20.10) |
| 28.5 | **4** | Checkout cursos de instructor: Stripe/Paddle, split automático 70/30 | **PARCIAL** — Verificado 2026-09-25 contra el… | → §I (criterio archivado por 20.10) |
| 28.7 | **4** | Payouts mensuales: job día 15 de cada mes, mínimo $50; rail elegid… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 28.8 | **3** | UI del marketplace conectada: `MarketplaceScreen` e… | **PARCIAL** | `cb40bcd` (#100): panel de instructor por API; faltan flag `MARKETPLACE_PUBLIC`, catálogo público y aprobación (criterio en §I) → §S |
| 28.9 | **3** | Kit de reclutamiento de instructores… | **DONE** | → §T |

### 29. Economía cerrada y rails — créditos, referidos, códigos, USDC, credenciales verificables (ADR-33…37; spec `docs/ECONOMIA.md`)

> **Estado:** `ABIERTA` — desbloqueada por el dueño el 2026-09-19 (§1) y H.26 decidido por defecto el 2026-09-24 (ADR-47: la tabla de…
> **Dependencias:** 22.1 (admin), 22.6 (cola de trabajos y `RateLimiter`), 21.7 (ToS para 29.11), 24.6 (UI).
> **PRI:** 3. **Modelo:** Sonnet (migraciones, auth, billing = ficheros de riesgo); Haiku para tests, inventarios y verificación adversaria.
> **Invariante de la serie:** las tres reglas de `ECONOMIA.md` §1 se prueban con tests, no se prometen. Canje solo en web. Ningún «token»…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 29.0 | **1** | Schema: `credit_ledger`, `promo_codes`… | **DONE** | → §T |
| 29.1 | **1** | Servicio de créditos `services/economy/credits.py`: abono… | **DONE** | → §T |
| 29.2 | **1** | Tabla de grifos y sumideros versionada en… | **DONE** | → §T |
| 29.3 | **2** | Referidos: código permanente por usuario, enlace… | **DONE** | `89eb7a7` → §T |
| 29.6 | **2** | Admin (en 22.1): economía (emitidos/gastados/caducados, ra… | **DONE** | → §T |
| 29.7 | **3** | Reactivación automática: job de 14 días de inactividad | **DONE** | → §T |
| 29.8 | **3** | **UI**: wallet, referidos, canje de códigos | **DONE** | → §N |
| 29.9 | **3** | USDC como rail (ADR-36): si H.19 = Stripe → activar *Pay with Cryp… |  | → §I (criterio archivado por 20.10) |


### 30. Integridad del despliegue — incidente de login del 2026-09-24 (PRI 0)

> **Estado:** `ABIERTA`. 30.0/30.7/30.8 DONE en producción (archivo §N). **30.9 solo en rama (PR #34): hasta que se fusione, un login válido en producción vuelve a la landing.**
> **PRI:** 0. **Origen:** captura del dueño — `POST whetzy.com/auth/login` → **405**, pantalla «Incorrect email or password».
> **Invariante de la serie:** un deploy del frontend no está hecho hasta que `node scripts/check-deployed.mjs` sale PASS contra…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 30.2 | **1** | **Se puede publicar sin puerta** (6 commits desde la UI web de GitHub) | **PARCIAL** | puerta del build `5c3ab12` (#90); falta proteger `master` (dueño, RUNBOOK) → §Q |
| 30.4 | **1** | `npm run build` estaba en rojo y nadie lo vio: el prerende… | **DONE** | `be07294` → §T |
| 30.5 | **2** | El script `build` ya no corría `tsc -b` (`8a0dce0`) | **DONE** | `5c3ab12` → §T |
| 30.9 | **0** | Login válido devolvía a la landing (cookie cross-site + ho… | **DONE** | `395e8a1` → §T |

### 31. Fuente única de cifras, staging y migraciones con datos (del plan del 2026-09-24, cuyo fichero no está en el repo: estas filas son…

> **Estado:** `TODO`. **PRI:** 1. **Por qué:** los documentos vivos dan cifras distintas del mismo banco (6.233 frente a 6.305 preguntas)…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 31.1 | **0** | Staging: un preview de Cloudflare Pages y un servicio de Railway d… | HUMAN-BLOCKED… | 2026-09-30: #34 fusiona 2 migraciones directo contra producción sin ensayarlas ahí — sin staging, cada fusión repite ese riesgo |
| 31.4 | **0** | Migración sin datos dejó sin preguntas a los usuarios con… | **DONE** | `1225a29` → §T |
| 31.5 | **0** | Regla del dueño 2026-09-30: PRs pequeños (veto a analítica levantado, ADR-68) | DOING | mismo texto en `ORCHESTRATOR.md` |
| 31.6 | **2** | Tests de analítica sobre Postgres real, no solo SQLite — D1/D7/CUR… | PARCIAL: 48 passed con `WHETZY_PG_TEST_URL`; ningún gate la define | variable en un gate de CI |
| 31.7 | **0** | Pausa de sesiones autónomas y cierre, 2026-09-30 →… | **DONE** | → §T |
| 31.8 | **0** | Lanzamiento piloto (prompt del dueño 2026-10-01): kit… | PARCIAL | kit escrito; invitar, día 4 y recuento = dueño |
| 31.9 | **0** | 229 ejecutables gratis o imposibles reparados; corrige el… | **DONE** | → §T |

### 32. Motor demostrable — calibración y evidencia de aprendizaje (del plan del 2026-09-24; ídem)

> **Estado:** `TODO` (32.2 `BLOCKED` por H.10). **PRI:** 2. **Relación:** complementa 11.8 y 14.8; no las sustituye.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 32.2 | **3** | A/B BKT contra DKT con el framework 24.14 (asignación estable por… | BLOCKED (H.10) | DKT se adopta solo si AUC ≥… · potencia `e7ebd9a` (#97) → §R |
| 32.3 | **2** | «¿Por qué esta pregunta?»: el scheduler devuelve sus razon… | **DONE** | `d92e164` → §T |
| 32.4 | **2** | La lección bloquea el quiz (decisión del dueño 2026-09-27) | **DONE** | `b860e83` → §T |

### 33. Operación medible — SLO, restauración y offline idempotente (del plan del 2026-09-24; ídem)

> **Estado:** `HECHA` (1/1). **PRI:** 2.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 33.1 | **2** | Ensayo de restauración mensual con… | **DONE** | `5cd5ed8` → §T |


### 34. Una sola interfaz: todas las pantallas al lenguaje visual de la landing (abierta 2026-09-24, a petición del dueño)

> **Estado:** `ABIERTA`. **PRI:** 0 para 34.0–34.1 (hoy la app sale **sin estilos**), 1–2 para el resto.
> **Punto de partida medido (2026-09-24):** **276 de 761** referencias `styles.x` apuntan a clases que no existen en su `.module.css` —…
> **Cómo se trabaja (el bucle «tipo Lovable»):** una oleada = una rama y un PR. Cloudflare Pages publica un preview por push…
> **Invariantes de la serie:** (1) se copia el **estilo** de la landing, nunca su contenido inventado (30.1/H.31); (2) cero regresiones de…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 34.11 | **1** | Hallazgos de comportamiento vistos al rediseñar (no son es… | **DONE** | `be2e83b` → §T |
| 34.12 | **2** | Plural e idioma en la UI: `HomeScreen.tsx` sin `count`… | **DONE** | `772fe5d` → §T |
| 34.1 | **0** | Devolver el estilo a las 13 pantallas rotas: por fichero,… | **DONE** | `e58b6b2` → §T |
| 34.2 | **1** | **Un solo juego de tokens**: una sola fuente (`src/theme/tokens.css` o… | **PARCIAL** | 2026-10-16: tokens de los dos temas con los colores del logo (#197) y sin `rgba` en `.module.css` (#222, guarda `tokens.noRgba`) → §T |
| 34.3 | **1** | Componentes base al estilo de la landing: `Button`, `Card`… | **PARCIAL** | 2026-10-16: `Button` común en Auth, Duelo, Perfil y Quiz (#214, #216); botones de icono con nombre (#207) → §T |
| 34.4 | **1** | **Primer uso**: Auth (login, registro, OAuth, olvido/reset), Onboarding,… | **PARCIAL** | 2026-10-16: Auth y olvido/reset con `Button` (#214, #216); «atrás» y `replace` en la entrada (#215). Falta `ttfq-prod.spec.ts` contra producción (dueño) → §T |
| 34.5 | **1** | Aprendizaje: Home, Tracks, Lesson y Quiz (con Monaco, WhyB… | **DONE** | → §T |
| 34.6 | **2** | **Progreso y social**: Profile, Stats, League, Duel, Readiness, MockExam,… | **PARCIAL** | 2026-10-16: Stats con bandas (#204), Perfil por rol (#207), Duelo y Quiz con `Button` (#214, #216) → §T |
| 34.7 | **2** | **Resto**: Admin, Instructor, Marketplace, Legal, Evidence, DeleteAccount | **PARCIAL** | 2026-10-16: Admin solo dueño (#202), Evidence sin notas a terceros (#206), Borrar cuenta con tokens (#209), Marketplace en módulo (#223). Falta revisar Instructor → §T |
| 34.8 | **2** | Regresión visual: Playwright con capturas por ruta (ES/EN × móvil/… | **PARCIAL** | 2026-10-16: E2E 54/56 en local (#220) y selectores por nombre con guarda (#217). D-28 decidida en #327: las capturas aprobadas son las de `e2e/__screenshots__/linux`. Falta axe por ruta → §T |
| 34.9 | **2** | Verificación y re-puntuación: verificador adversario (protocolo §7… |  | → §I (criterio archivado por 20.10) |

### 35. Lo que el mercado enseña: competencia verificada → producto (abierta 2026-09-24, a petición del dueño)

> **Estado:** `ABIERTA`. **PRI:** 1.
> **Origen:** captura en vivo de 33 sitios de competencia directa e indirecta (páginas públicas, sin registro), sintetizada en…
> **Hallazgo que ordena la serie:** varias «ideas nuevas» de los informes **ya existen en el código y no se ven**: la prueba de nivel está…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 35.1 | **1** | Comparativa pública verificada en la landing: solo cifras… | **DONE…** | → §T |
| 35.4 | **2** | Ligas opt-in visible: interruptor en la propia pantalla de… | **DONE** | → §T |
| 35.6 | **2** | Refresco trimestral de §A.1: re-descargar las páginas de precios… | TODO —… | → §I (criterio archivado por 20.10) |
| 35.8 | **2** | Cada deploy de Railway deja ~1 min de 502/503. Medido 2026… | **DONE** | → §T |
| 35.9 | **2** | El nivel 2 (`ci_local.sh`) corría sobre el árbol y quedaba… | **DONE** | `7fe4303` → §T |


### 37. Catálogo uniforme 32 × 10, simulacros reservados y prioridad por demanda (ADR-54, 2026-10-01; antes ADR-53 y ADR-46)

> **Estado:** `ABIERTA`. **PRI:** 1 (detrás de la serie 30). **Modelo:** ADR-59 (escribe Sonnet 5 desde la fuente, revisión completa Sonnet 5, piloto de 10; `PLAN_CONTENIDO.md`).
> **Orden (ADR-59):** en paralelo a 31.8; primero 37.25, luego 37.22, 37.10, 37.6, 37.7 y 37.8. **La guarda 37.0 sigue antes de cualquier pregunta nueva.**
> **Corpus (ADR-46 §4-5, vigente):** `corpus/` está en `.gitignore`. Se descarga con `git clone --depth 1`, dumps oficiales y **torrents solo cuando…
> **Unidad:** la skill. Forma por track: 32 skills · 10 Q (≥ 3 ejecutables) · 1 lección y 1 término por skill (`scripts/metas_catalogo.json`). Suelo e ideal de ADR-53: sustituidos. Cifras: `python scripts/catalog_coverage.py`. Un bloque = un PR verde.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 37.1 | **1** | Temario de referencia por track (ADR-54: solo elige qué 32 skills… | **PARCIAL** | Falta temario de track22, 23, 39, 47, 54, 55 y 56, objetivos de SY0-701 y longitud de examen de Microsoft; `catalog_coverage.py --check` PASS |
| 37.4 | **2** | **Descarga y verificación del corpus por área** (una subfila por área en… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 37.5 | **2** | Generador desde corpus: `scripts/generate_track_content.py` (absor… |  | → §I (criterio archivado por 20.10) |
| 37.6 | **2** | Tracks construidos a la forma 32 × 10: A primero (02, 03, 12, 14… | TODO | `catalog_coverage.py`: el track sin pendientes; 37.0 y puerta §7 en verde; un track = un PR |
| 37.7 | **2** | track24 y track25 reconstruidos con la forma 32 × 10 desde la cuar… | TODO | ídem, fuera de `_quarantine` y `question_diversity.py` sin línea base |
| 37.8 | **2** | Tracks nuevos por demanda (`CATALOGO_MAESTRO.md` §2.0): A (38, 33… | TODO | ídem por track; `metas_catalogo.json` lo pasa a «construido» en el mismo commit |
| 37.9 | **2** | **Glosario ≥ 1 término por skill**, ES y EN nativos (absorbe 25.12) | TODO | `catalog_coverage.py`: términos ≥ skills en cada track |
| 37.10 | **1** | Certificaciones a la regla de ADR-54: 100 % de objetivos, práctica… | PARCIAL (2026-10-16, `catalog_coverage.py` sobre `0de27ad`: faltan +113 de práctica y +821 reservadas) | `catalog_coverage.py`: práctica y reserva al 100 % por certificación; `test_certification_blueprints.py` |
| 37.11 | **3** | **Proyectos multi-paso**: 10 por track ejecutable (hoy 0; catálogo §1) | BLOCKED (37.6) | Cada proyecto con tests de… |
| 37.12 | **3** | Monitoreo trimestral de competencia (`CATALOGO_MAESTRO.md` §11.4 a… |  | → §I (criterio archivado por 20.10) |
| 37.13 | **3** | Scorecard ADR-54 (absorbe 25.13): `scripts/catalog_coverage.py` +… | **PARCIAL** | Hecho 2026-10-01 para ADR-54 (script, metas, 21 tests con mutación). Falta: cifras en `/evidence` y re-puntuar Contenido en el teardown al cambiar de tramo |
| 37.14 | **1** | track13 (ciberseguridad) tiene enunciados repetidos: 87,9 %… | **DONE** | `fbf9baf` → §T |
| 37.15 | **1** | Fuentes sin indexar: 3.906 de 6.305 preguntas… | **PARCIAL** | 3.903 sin indexar de 10.949 (2026-09-29, `Workflow`) → §T |
| 37.16 | **1** | La correcta es la opción más larga. Medido 2026-09-25 sobre… | **DONE** | `46764ff` → §T |
| 37.17 | **1** | Inglés dentro del español y ejecutables con atajo… | **PARCIAL** | 219 de 699 exec revisadas (2026-09-29); quedan ~480 y `q060203ex012` → §T |
| 37.18 | **1** | Banco de simulacro reservado: `"pool": "simulacro"`; ningu… | **DONE** | → §T |
| 37.19 | **1** | Formato de examen del proveedor: AIF-C01 65 Q / 90 min (re… | **DONE** | `764b06b` → §T |
| 37.22 | **1** | ISC2 CC al outline del 2026-09-01 (CAT 100–125 ítems; D2 G… | **DONE** | `84fb47c` → §T |
| 37.20 | **1** | Métricas de producto con meta (ADR-53 §8): D1 ≥ 15 %, D7 ≥… | **DONE** | → §T |
| 37.21 | **3** | Mapa skill → nodo del temario, para elegir las 32 skills de cada t… | TODO (tras 37.6) | cada skill con su nodo |
| 37.23 | **2** | Alineación lección↔quiz (heredera de la 37.1 vieja, antes de ADR-5… | **PARCIAL** | 8 tracks cerrados (2026-09-29); queda la expansión hacia ADR-54 (37.6-37.8) → §T |
| 37.24 | **1** | Poblar el banco de simulacro reservado (2× la longitud del examen… | PARCIAL — 219/1.040 (2026-10-13); flag en `False`; cómo retomar en `scripts/content_qa/reservadas_37_24/README.md` | reservadas ≥ 2 × `exam_question_count` en las 8 con L publicada y flag en `True` → §T |
| 37.25 | **1** | Piloto de autoría (ADR-59): 10 ítems de una skill de track… | **DONE** | → §T |

### 38. Negocio medible — KPIs, pilotos B2B, instructores, afiliados (ADR-47; abierta 2026-09-24)

> **Estado:** `HECHA` (6/6). **PRI:** 2.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 38.1 | **2** | Precios: una sola fuente = ADR-41 (dueño): Pro 14,99 $ · P… | **DONE** | `cf2fc58` → §T |
| 38.2 | **2** | Oferta de 3 pilotos B2B gratuitos (ADR-22): documento ES/EN (qué dam… | DONE | → §O |
| 38.3 | **2** | Dossier de afiliación Python Institute y CompTIA (archive/whetzy_es… | DONE | → §O |
| 38.5 | **3** | Página `/evidence` como única prueba social (19.8, 30.1)… | **DONE** | → §T |
| 38.6 | **2** | Pro Max = tutor IA ilimitado; Pro con cupo diario (ADR-49)… | **DONE** | `843015e` → §T |
| 38.7 | **2** | Certificación a 39,99 $ de pago único (ADR-49). Hoy los tr… | **DONE** | `843015e` → §T |

### 39. Noche 2026-09-26 — incidente de arranque, deuda de calidad y aprobación en bloque (ADR-50)

> **Estado:** `ABIERTA`. Viene del prompt de control total v5 y de `docs/archive/EVALUACION_COMPLETA_WHETZY.md`. Lo que exige cuenta o dinero va a §3.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 39.0 | **0** | Producción caída 09:35–10:48 UTC tras `ec97405`… | **DONE** | → §T |
| 39.1 | **0** | Coletillas de relleno en opciones incorrectas de tracks 26/28/29/30… | DONE | → §O |
| 39.2 | **1** | Fuentes inferidas en 146 lecciones normalizadas en #28 | DONE | → §O |
| 39.3 | **1** | `tests/content` en verde (1.254 fallos en master, 792 tras #28) | DONE | → §O |
| 39.4 | **2** | `content_quota` detrás de flag (ADR-50a) | DONE | → §O |
| 39.5 | **2** | Gamification auditada de punta a punta | DONE | → §O |
| 39.6 | **2** | `audit_ai_traces.py` | DONE | → §M |
| 39.7 | **2** | Detector de originalidad / casi-duplicados | DONE | → §M |
| 39.27 | **2** | Reescribir las 12 parejas casi-duplicadas anotadas en `KNOWN` (tra… | **PARCIAL** | 10/12 reescritas (2026-09-29); las 2 restantes son el ciego de 39.40 → §T |
| 39.28 | **0** | Segunda familia de coletillas («como concepto principal» 9… | **DONE** | → §T |
| 39.29 | **0** | 1.404 explicaciones de plantilla vistas por el alumno en track41 (59… | DONE | → §O |
| 39.30 | **1** | Datos personales en el contenido: `l260101` enseñaba el no… | **DONE** | → §T |
| 39.31 | **2** | `user_meets_tier` no mira `subscription_expires_at` | **DONE** | `749e07f` → §T |
| 39.32 | **3** | `test_rag_self_retrieval` tarda ~28 min (cuadrático en el… | **DONE** | `8934dd2` → §T |
| 39.33 | **1** | Claves sospechosas previas: la explicación se parece más a otra op… | **PARCIAL** | track13 sk130104/204/304 corregidas (`a17a7c8`); falta muestrear el resto del commit masivo → §T |
| 39.34 | **2** | Texto de UI del cupo Free (ES/EN) antes de encender… | **DONE** | `e754b50` → §T |
| 39.35 | **0** | El limitador de peticiones de producción fallaba en abiert… | **DONE** | `95cdfbf` → §T |
| 39.36 | **1** | `options_en` escritas en español en track21 (194 preguntas… | **DONE** | → §T |
| 39.37 | **0** | Relleno de generador en producción: 180 preguntas de track20 mod200… | DONE | → §O |
| 39.38 | **0** | Dos claves falsas de Bicep en track22 (`q220503008`: «using» no… | DONE | → §M |
| 39.39 | **1** | Lección/quiz desalineados: 90 casos en 7 tracks… | **DONE** | (2026-09-29) → §N |
| 39.40 | **2** | `check_originality.py` ciego a `code` (39.27) | **DONE** | (2026-09-29) → §N |
| 39.41 | **1** | 19 `sql_exec` que un alumno con SQL correcto no podía aprobar | **DONE** | → §N |
| 39.42 | **2** | track43 mod4301: 45 de 75 preguntas eran relleno molde… | **DONE** | → §I |
| 39.43 | **2** | Cuarta familia de coletillas: cláusula de marketing cloud pegada a… | **TODO** | Revisión pregunta a pregunta (no regex: ~150 candidatas, la mayoría gerundios legítimos), vía `Workflow` (ADR-52) → §Q |
| 39.8 | **1** | Cerrar el índice de fuentes (37.15) | TODO | 0 % sin indexar o lista exacta de las imposibles |
| 39.9 | **2** | Explicaciones de < 2 frases en tracks 13, 15, 16, 17 | **PARCIAL** | track13 4/4; track15/16/17: 11 reescritas y `q160303005` corregida (`687426f`, #104); sin muestreo de los ~113 «falsos positivos» → §R |
| 39.10 | **3** | Mapa de tracks con rutas y recomendación | TODO | vitest + e2e, ES/EN, a11y |
| 39.11 | **2** | Límite de gasto de Groq por usuario y global | DONE | → §M |
| 39.12 | **3** | LLM de respaldo (ADR-50f) | DONE | → §M |
| 39.13 | **3** | Emails de re-enganche (ADR-50g) | DONE `2975cb2` | flag apagado, baja en un clic, tests |
| 39.14 | **3** | Plantilla de lección con formato (ADR-50d) | **DONE** | `4e8d941` → §T |
| 39.15 | **1** | Fichero `LICENSE` (ADR-50e) | DONE | → §M |
| 39.25 | **1** | MLA-C01 retirado: ampliar track43 sin reestructurar | **DONE** | `a6fe453` → §T |
| 39.26 | **2** | **Security+ V8 hacia el 17-11-2026** (comptia.org, leído 2026-09-26) | TODO | track42 revisado contra el temario V8 al publicarse |
| 39.24 | **1** | AI-900 retirado: track45 a AI-901 | **DONE** | `7522e23` → §T |
| 39.18 | **1** | vitest: 4 fallos (`StatusPage` `/api/v1` relativo, `common.back`,… | DONE | → §M |
| 39.20 | **2** | PostHog en el frontend (ADR-50j) | **DECIDIDO: no** | La analítica ya es propia (`analytics_events` + embudo admin); PostHog en el navegador rompería la promesa de la landing y la CSP (ADR-50j revisada) |
| 39.21 | **2** | Sentry en el frontend (ADR-50k) | **DECIDIDO: no** | Solo backend; privacidad y DPA ES/EN actualizados: Sentry activo desde 2026-09-26, UE, sin PII |
| 39.22 | **2** | Backups: `backup_db.sh` + `restore_check.sh` + runbook | DONE | → §M |
| 39.23 | **1** | H.30 honesto: sin proveedor, 503 `email_not_configured` | DONE | → §M |

### 40. Superar a Brilliant y Kodree donde hoy ganan (abierta 2026-09-28, a petición del dueño; spec `PLAN_EXPERIENCIA.md`)

> **Estado:** `ABIERTA`. **PRI:** 2. Origen: `COMPETENCIA.md` §A.2b. Nada de esto se anuncia hasta 40.13.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 40.1 | **2** | Tipo `interactive`: `{widget, params, target, checker}`; checker e… | DONE — #278 `2409729`, §7 10-20 | esquema en `check_question_bank.py`; test de discrepancia cliente↔servidor en rojo al mutar |
| 40.2 | **2** | **Piloto 3 widgets** (búsqueda binaria, CIDR, JOIN) × 10 ítems ES/EN | PARCIAL — 3 widgets con demostración `5923d5a` (ADR-67 D1: sin los 30 ítems); sin medir peso ni LCP | e2e móvil+escritorio, axe 0, ≤ 30 KB gz/widget, LCP < 2,5 s 4G; sin piloto verde no hay 40.3 |
| 40.3 | **3** | Biblioteca de 15 widgets mapeados a dominios de cert (IAM, Git DAG… | TODO (tras 40.2) | contrato `render/serialize/check` testeado por widget; cada uno suma al readiness |
| 40.4 | **3** | **Widget ↔ código** en los dos sentidos (Pyodide, sql.js, Worker JS) | TODO (tras 40.2) | e2e: editar el widget cambia el código y ejecutar el código anima el widget |
| 40.5 | **3** | Tutor que señala: acciones estructuradas (resaltar línea, marcar n… | TODO (tras 40.2) | acción fuera de esquema rechazada (test); sin grounding lo dice (línea roja 2) |
| 40.6 | **3** | Tutor por voz ES/EN: TTS `speechSynthesis`; STT por Groq… | TODO (tras 40.5) | WER en ES medido con muestras propias; retención de audio de Groq leída con URL; consentimiento ES/EN; cuenta contra 38.6 y 39.11 |
| 40.7 | **3** | Comunidad con contexto: hilos por pregunta/lección, soluciones tra… | TODO (construir; abrir con ≥ 100 activos) | e2e: la solución ajena no se ve antes de resolver; notificación y retirada ES/EN |
| 40.8 | **4** | Grupos de estudio por cert + revisión por pares de proyectos (revi… | TODO (tras 40.7, 37.11) | readiness de grupo sin datos personales (test) |
| 40.9 | **2** | Plan anual junto al mensual; solo esos dos, sin vitalicio ni famil… | TODO | precio anual con su referente citado; cancelar en 2 toques (línea roja 7) y aviso de renovación (21.4) |
| 40.10 | **4** | Ruta Analista de datos ejecutable (pandas en Pyodide + SQL, datase… | TODO | cert confirmada con URL; fuentes ADR-11 |
| 40.11 | **4** | **TypeScript ejecutable** en el Worker, carga perezosa solo en su track | TODO | licencia del compilador verificada; peso fuera del bundle base |
| 40.12 | **4** | **Investigar Java en navegador y UX/UI** (runtime, peso, licencias) | TODO | informe con URL; nada entra sin fuentes H.LIC y línea roja 8 |
| 40.13 | **3** | Medir la superación: tabla criterio a criterio frente a Brilliant… | TODO (cierra la serie) | cada «mejor que» con evidencia ejecutable o URL; sin ella no sale a la landing (línea roja 9) |

### 41. Documentación al día con el código (Oleada 0 del plan ultracode; dueño 2026-10-16; `PLAN_ULTRACODE.md`)

> **Estado:** `ABIERTA`. **PRI:** 0. Antes de la serie 42. Sin contenido (ADR-62 prop.). Prompt: `PROMPT_SINCRONIZACION_DOCS.md`.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 41.1 | **0** | Liberar ≥ 6 KB del ledger (evidencias… | DONE — `643ab4c` → §T (6) | → §T (6) |
| 41.2 | **0** | Inventario y contraste doc ↔ código ↔… | DONE — `643ab4c` → §T (6) | → §T (6) |
| 41.3 | **0** | Corregir en sitio las contradicciones conocidas y las nuevas | PARCIAL (325/441; 116 abiertas en el claims file) | antes/después/`file:line` por cambio; `check_docs.py` verde |
| 41.4 | **0** | Una guarda en `check_docs.py` por cont… | DONE — → §T (6) | → §T (6) |
| 41.5 | **0** | STATUS y CHANGELOG al día; ADR-61/62/6… | DONE — → §T (6) | → §T (6) |
| 41.6 | **0** | Escalar decisiones (H.51…H.57) y archi… | DONE — → §T (6) | → §T (6) |

### 42. Ultracode: código tras la sincronización (oleadas 1-9; dueño 2026-10-16; `PLAN_ULTRACODE.md` §5-§6)

> **Estado:** `ABIERTA`. **PRI:** 1. Sin contenido (ADR-62). Rama + PR, test rojo antes y verde después, verificador §7. Lo ya hecho desde `e85900b`: `PLAN_ULTRACODE.md` §0.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 42.1 | **0** | Prueba de nivel: estimador EAP con prior | PARCIAL (EAP hecho, #219; la siembra pasa a 43.3) | test rojo antes y verde después; simulación de la parada por SE adjunta |
| 42.2 | **0** | Puerta E2E: origen 5199, paso e2e en `ci_local.sh`, guarda de contrato | DONE `b00bb2e`, `8435112` (e2e verde en CI) | `test_e2e_cors_contract.py` 2 passed; CI e2e success |
| 42.3 | **1** | E2E: specs desfasados y `/auth` colgado | PARCIAL: 0 saltados en CI `8435112` | traza de los colgados (no probada) |
| 42.4 | **1** | Duelos 3a: 202 ≠ «Perdiste», feedback, opt-out, cotas, desempate, copy | DONE `fd82efc`, `8435112` | `test_duels.py` 42 passed; 11 rojos con el código anterior |
| 42.5 | **1** | Duelos 3b: el retador reanuda; caducidad | DONE `fd82efc`, `8435112` (H.52 decidido, ADR-69 #6) | reanudación y tercero rechazado con test |
| 42.6 | **1** | Readiness sobre todas las skills del dominio; una definición de do… | DONE `fd82efc` (`app/core/mastery.py`) | guarda de literales en `app/` (mutada) |
| 42.7 | **1** | `exam_pass_predictor`: retirar o conectar tras bandera | TODO (tras H.53) | sin importadores en `backend/app`, o endpoint con test |
| 42.8 | **1** | Prior del onboarding y siembra con encogimiento | BLOCKED (sustituida por 43.3: siembra por módulo, ADR-65 D4) | 1/1 deja de dar 0,94; prior por experiencia con test |
| 42.9 | **1** | Evidencia por fuente: función única y contadores | DONE `fd82efc` | `test_evidence_policy.py`; migración probada en Postgres con datos |
| 42.10 | **2** | Historial de pantallas; atrás de Android | PARCIAL (`pushState`, #218; Android sin probar) | prueba en dispositivo Android (cola humana) |
| 42.11 | **1** | Offline: la cola no se vacía hasta confirmar; `declaredUnknown` | DONE `9e8f018`, `64c721b` | red caída en `flush` conserva la cola; test rojo antes |
| 42.12 | **2** | Blueprint mínimo en `Track` (`code`, `exam_guide`, versión) | DONE `fd82efc` | loader persiste; migración con datos; `content/` sin cambios |
| 42.13 | **2** | Higiene: retirar `getPricingPlans`; jurisdicción según H.54 | TODO (tras H.54) | sin usos; test de precios visibles |

### 43. Flujo del alumno listo para pruebas (anexo del dueño 2026-10-17; `PLAN_FLUJO_ALUMNO.md`; ADR-65)

> **Estado:** `ABIERTA`. **PRI:** 0. Tras la Oleada 0 y antes del resto de la 42. Sin contenido (ADR-62). Puerta: `PLAN_FLUJO_ALUMNO.md` §6.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 43.1 | **0** | Sesión en iPhone: token en memoria +… | DONE — #226 → §T (6) | → §T (6) |
| 43.2 | **0** | Registro sin fricción: errores por cam… | DONE — #227 → §T (6) | → §T (6) |
| 43.3 | **0** | Onboarding D2, prueba de 20 (D3), siem… | DONE — #230 → §T (6) | → §T (6) |
| 43.4 | **0** | Ruta activa (D5) y Hoy filtrado por ella (D6); readiness de 42.6 | DONE — `9bb58d8`, `5a3c2a6`; §7 arreglada en #248 `eefe971` (revisión 10-23) | cambio de ruta persiste; Hoy solo de la ruta activa |
| 43.5 | **0** | Lección primero (D7) | DONE — §7 arreglada en #249 `526f826`; salvo H.60 (prueba de nivel sin lección) (revisión 10-23) | «Estudiar» abre la lección; sin lección vista no hay práctica |
| 43.6 | **1** | Proyectos dentro del track, con progreso y validación en servidor (D8; dueño 2026-10-17: SQL en servidor, Python/JS en navegador sin verificar) | PARCIAL — SQL en servidor (#247 `1fe864d`); Python/JS completan con `passed` del cliente si el código cambia (D8) | progreso sobrevive a salir; `passed=true` sin tests no completa |
| 43.7 | **1** | Playground contextual desde la lección… | DONE — #238 → §T (6) | → §T (6) |
| 43.8 | **0** | Puerta «lista para pruebas»:… | DONE — #239 → §T (6) | → §T (6) |

### Serie 44 — Back-office de soporte (4/4 DONE; detalle en LEDGER_HISTORY §B)

### Serie 45 — Alta con correo (4/4 DONE; detalle en LEDGER_HISTORY §B)

### 46. Experiencia avanzada (dueño 2026-10-18; `PLAN_UI_AVANZADA.md`, #245)

> **Estado:** `ABIERTA`. **PRI:** 1. Orden: 46.0, 46.2, 46.1b, 46.1, 46.3, 46.7, D1–D4, 40.1–40.6, 46.4–46.6.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 46.0 | **0** | Dieta del ledger y alta de la 46 | DONE — #262 `1e4979b`, §7 10-19 | ≤ 59.400 B; checks verdes |
| 46.1 | **1** | Feedback del quiz sin tapar | DONE — #266; e2e «×3» en `e7abd77` | plan §2 y §6.4 |
| 46.1b | **1** | `events[]` en `QuizAnswerResponse` | DONE — #265 `2840689`, §7 10-19 | plan §6.3 |
| 46.2 | **1** | `feedbackFx.ts`: bus, sonido, vibración | DONE — #263 `0449034`, §7 10-19 | plan §6.0–6.1 |
| 46.2b | **2** | `@capacitor/haptics` | DONE — #276 `00e52a5`, §7 10-20 | PR propio (ADR-67 D4) |
| 46.3 | **1** | Estados vacíos y momentos de Home | DONE — #264, #267, #272; e2e de misión en `e7abd77` | plan §2 y §6.2 |
| 46.4 | **2** | Un solo sistema de tokens | DONE `4393460` | 0 `var(--color-`; 0 variables sin definir |
| 46.5 | **2** | Regresión visual en nivel 2 | PARCIAL — 64 capturas `e416b83`; falta la guarda de mutar un token | rojo al mutar un token |
| 46.6 | **2** | Medición y re-puntuación | TODO | tabla con evidencia |
| 46.7 | **1** | Resumen y ceremonias | DONE — #269, #273, #288; e2e nivel 4 en `e7abd77` | plan §6.4 |
| 46.8 | **2** | Mascota: brief para ilustrador | DONE — #277 `b15f062`, §7 10-20 | brief y 3 direcciones (ADR-67 D2) |
| 46.9 | **1** | Sonido encendido por defecto | DONE — #275 `e5f5e5a`, §7 10-20 | sin preferencia → on (ADR-67 D3) |
| 46.6a | **1** | Analítica fx anónima (ADR-68) | DONE — #288; `fx_skipped` del recuento en `4f19ee5` | plan §7.2 |
| 46.10 | **1** | Quiz: opción late/tiembla, «+XP» vuela | DONE — #289, §7 10-21 | plan §7.3 |
| 46.11 | **1** | Llama de racha en 3 tamaños + escudo | DONE — #290, §7 10-21 | plan §7.3 |
| 46.12 | **1** | Home: contadores y banda con `AnimatePresence` | DONE — #291, §7 10-21 | plan §7.3 |
| 46.13 | **2** | Liga y Preparación escalonadas | DONE — #292, §7 10-21 | plan §7.3 |
| 46.14 | **1** | Transiciones de ruta y esqueletos de carga | PARCIAL `601b5bb`: sin spinner «Cargando…» en pantallas | e2e de esqueletos fuera de Stats |
| 46.15 | **2** | Movimiento en las 27 pantallas sin él | DOING — #295–#299; falta tabla §7.5 y check en Restablecer | plan §7.5 |
| 46.16 | **2** | Tokens de movimiento y guarda | DONE — #294, §7 10-21 | plan §7.6 |

## 3. Cola HUMAN-BLOCKED

> → `docs/archive/LEDGER_HISTORY.md` §J

| H.16 | **DECIDIDA** (ADR-50p) — dueño: proteger `master` (PR obligatorio) en GitHub → Branches; staging (31.1) aprobado, alta con coste por el dueño |
| H.12 | PRI 0 de seguridad — rotar la `GROQ_API_KEY`. Estuvo commite… |
| H.13 | **CERRADA** 2026-10-22 (ADR-70): runners de vuelta desde el 2026-10-21; CI verde en #322 |
| H.2 | Apple Developer Program — y desde 2026-09-18 también bloquea… |
| H.3 | Google Play Console |
| H.5 | Submisión a stores |
| H.14 | iOS no se puede generar ni compilar en este PC (Windows, sin… |
| H.6 | Cadena de sesiones |
| H.7 | Rutina remota — única forma de no depender de la app abierta |
| H.9 | Dispositivo físico o emulador con lector de pantalla real pa… |
| H.10 | Cohorte beta ≥ 30 usuarios reales (11.8) |
| H.17 | Ver H.13 |
| H.18 | La cadena solo corre con la app Claude abierta y el PC despi… |
| H.20 | DECIDIDO (ADR-70): se aplaza hasta tener ingresos; textos con marca de borrador |
| H.23 | Abrir la Serie 26 (distribución ES) cuando 24.14 esté DONE |
| H.25 | DECIDIDO (ADR-70): se aplaza a la primera venta de un instructor (28.7) |
| H.27 | DECIDIDO (ADR-70): solo Open Badges, sin cNFT (29.10) |
| H.28 | Grant / bounty de la Solana Foundation o Superteam para trac… |
| H.29 | DECIDIDO 2026-10-01 (web = Paddle, tiendas = RevenueCat, sin Stripe). Web: `/checkout` hecho; falta alta Paddle y dominio. Entidad: ADR-61 §22 (2026-10-09) pasa de Grecia a Chipre como destino, sin entidad constituida; el código sigue en Grecia → H.54. T1: persona física (ADR-70); falta el nombre legal | Dueño |
| H.35 | **DECIDIDO** (ADR-70): anual Pro 149,99 $ y Pro Max 199,99 $ (apagado en piloto); LatAm −40 % en Paddle, España pleno; 80 % tras comisión; Pro 20/día; cert 39,99 $ |
| H.38 | Afiliación con Python Institute y CompTIA (38.3) |
| H.39 | 3 pilotos B2B gratuitos (38.2, ADR-22) |
| H.40 | Reclutar 5 instructores fundadores (28.9) |
| H.42 | **DECIDIDA 2026-09-26** (ADR-50j): analítica = PostHog; Mixpanel no se instrumenta |
| H.44 | Terminar o quitar Firecrawl, Amplitude, Mailchimp y Lusha (a medio conectar) |
| H.45 | Conectar redes (X, LinkedIn…) en Metricool/Typefully para que la distribución deje de ser solo borradores |
| H.46 | ¿Monitor de uptime de Sentry para `/health`? (puede consumir cuota de pago) |
| H.49 | **DECIDIDA 2026-09-28** — dueño: la voz a texto del tutor (40.6) usa el mismo proveedor que el tutor (Groq, `/audio/transcriptions`) |
| H.48 | CERRADA (ADR-70): no hace falta; ningún código llama a la API | Dueño |
| H.47 | ¿Mantener el correo personal del dueño como contacto en la página pública `/evidence` (`EvidenceScreen.tsx:340`)? Por defecto (ADR-47) se deja y se propone un alias tipo `support@whetzy.com` | Dueño |
| H.50 | Descarga del corpus (`scripts/corpus/`) en el setup script del entorno cloud, para que `corpus/` exista en cada sesión de autoría (ADR-59, `PLAN_CONTENIDO.md` §3) | Dueño |
| H.51 | Firmar ADR-63 (evidencia por fuente) y los valores del prior. Recomendado: 0,10/0,20/0,30; k = 4; puerta de 7 solo con práctica | Dueño |
| H.52 | Duelos: opt-out de ligas ⇒ no retar ni ser retado; caducidad a 7 días; sin XP; desempate por tiempo de servidor. El copy ya dice «por turnos» | DECIDIDO por delegación (ADR-69 #6, 2026-10-22) |
| H.53 | `exam_pass_predictor` (sin importadores en `backend/app`): retirarlo a `ml/` (recomendado) o conectarlo tras una bandera | Dueño |
| H.54 | DECIDIDO (ADR-70): ADR-61 fiel, edad mínima 16; titular persona física; Chipre y el código al constituir la entidad | Dueño |
| H.55 | Deuda de contenido de estudio: 12.037 preguntas frente a 730 lecciones y 1.058 términos. Opciones: lecciones largas, ejemplos resueltos, laboratorios guiados; reabre «1 lección por skill» (ADR-54). Sin diseño. Pausa mantenida por el dueño (ADR-70) | Dueño |
| H.56 | «Panel de equipo» prometido en `docs/legal/b2b_pilot_offer_*.md` sin producto. Recomendado: retirar la promesa (S4) | Dueño |
| H.57 | Modelos: CLAUDE.md dice Haiku 4.5 y prohíbe Fable; el entorno ofrece otros. La tabla no se cambia hasta que decidas | Dueño |
| H.58 | Las 119 preguntas del barrido de la Oleada 0 (`docs/archive/verificacion/claims-2026-10-16.md`, «Escalados»), con la opción recomendada primero | Dueño |
| H.62 | **Hecha** 2026-10-17 — verificación en dos pasos activa en la cuenta del dueño (requisito B7 de 44.1; `PLAN_BACKOFFICE.md` §4) | Dueño |

## 5. Bitácora de decisiones

> Decisiones archivadas en `docs/archive/LEDGER_HISTORY.md` §J.
> ADRs formales: `docs/DECISIONS.md`.

---

## 6. Cadena de sesiones

> → `docs/archive/LEDGER_HISTORY.md` §G

- 2026-10-16 · Oleada 0 (serie 41), rama `claude/ultracode-0-docs-sync`
