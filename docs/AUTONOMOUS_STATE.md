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
| Alembic HEAD | `20261004_tracks_is_active` (54 migraciones) |
| Contenido | **11.416 preguntas** / 35 tracks / 730 skills / **730 lecciones (100 %)** / **1.058 términos glosario**. Tracks 09/10/11 =… |

### Gotchas verificados

> → `docs/archive/LEDGER_HISTORY.md` §H

---

## 1. Estado por fase

> Generada desde las filas de `## 2` con `python scripts/ledger.py fases --write`; no se edita
> a mano (`ledger.py check` falla si no cuadra). Series ≤ 16 y 25: `LEDGER_HISTORY.md` §F y §M.

| Serie | Nombre | DONE/Total | % | Abiertas |
|---|---|---|---|---|
| 40 | Superar a Brilliant y Kodree donde hoy ganan | 0/13 | 0 % | 40.1, 40.2, 40.3, 40.4, 40.5, 40.6 +7 |
| 39 | Noche 2026-09-26 — incidente de arranque, deuda de calidad y aprobaci… | 31/41 | 76 % | 39.8, 39.9, 39.10, 39.13, 39.26, 39.27 +2 |
| 38 | Negocio medible — KPIs, pilotos B2B, instructores, afiliados | 6/6 | 100 % | — |
| 37 | Catálogo uniforme 32 × 10, simulacros reservados y prioridad por dema… | 7/23 | 30 % | 37.1, 37.4, 37.5, 37.6, 37.7, 37.8 +10 |
| 35 | Lo que el mercado enseña: competencia verificada → producto | 4/5 | 80 % | 35.6 |
| 34 | Una sola interfaz: todas las pantallas al lenguaje visual de la landi… | 4/11 | 36 % | 34.2, 34.3, 34.4, 34.6, 34.7, 34.8 +1 |
| 33 | Operación medible — SLO, restauración y offline idempotente | 1/1 | 100 % | — |
| 32 | Motor demostrable — calibración y evidencia de aprendizaje | 2/3 | 67 % | 32.2 |
| 31 | Fuente única de cifras, staging y migraciones con datos | 3/7 | 50 % | 31.1, 31.5, 31.6, 31.8 |
| 30 | Integridad del despliegue — incidente de login del 2026-09-24 | 3/4 | 75 % | 30.2 |
| 29 | Economía cerrada y rails — créditos, referidos, códigos, USDC, creden… | 7/8 | 88 % | 29.9 |
| 28 | Marketplace de instructores | 2/9 | 22 % | 28.0, 28.1, 28.3, 28.4, 28.5, 28.7 +1 |
| 27 | Distribución masiva EN | 0/11 | 0 % | 27.0, 27.1, 27.2, 27.3, 27.4, 27.5 +5 |
| 26 | Distribución masiva ES | 0/11 | 0 % | 26.0, 26.1, 26.2, 26.3, 26.4, 26.5 +5 |
| 24 | Interfaz que venda al verse — UI/UX + competencia en vivo + vídeo | 1/9 | 11 % | 24.0, 24.1, 24.2, 24.3, 24.4, 24.6 +2 |
| 23 | Dos segmentos, un producto — ES y EN sin mezclar | 3/5 | 60 % | 23.2, 23.3 |
| 22 | Blindaje, admin y preparación para un millón — todo a coste cero | 0/1 | 0 % | 22.5 |
| 21 | Legal y fiscal a coste cero — investigación, borradores, gates humanos | 0/4 | 0 % | 21.1, 21.2, 21.5, 21.6 |
| 20 | Verificación masiva código ↔ docs ↔ prod | 1/1 | 100 % | — |
| 19 | Lo que Educative y las tiendas exigen — social login, bootcamps, proy… | 2/8 | 29 % | 19.2, 19.3, 19.7, 19.8, 19.9, 19.10 |
| 18 | Techo de código — todo el catálogo, sin racionar | 1/5 | 20 % | 18.9, 18.10, 18.11, 18.12 |
| 17 | De quiz a escuela + release definitivo | 0/5 | 0 % | 17.5, 17.6, 17.7, 17.10, 17.14 |
| 16 | CI en rojo | 0/4 | 0 % | 14.10 |
| 14 | La cuña | 0/5 | 0 % | 14.7, 14.8, 14.9, 14.13, 14.14 |
| 11 | Superioridad medible | 1/3 | 50 % | 11.8, 11.9 |

---

## 2. Backlog ejecutable

> Orden de ejecución = por `PRI` ascendente, luego por ID. `PRI 0` es lo que
> desbloquea todo lo demás.

### 11 — Superioridad medible (cerrar las brechas honestas)
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 11.6 | 3 | Tiempo hasta primera pregunta **< 60 s contra prod** con 4G simulado | **DONE** — `5e306fb` | → §N |
| 11.8 | 3 | **Prueba de aprendizaje real**: cohorte beta ≥ 30 usuarios | HUMAN-BLOCKED (H.10) | Dashboard 5.5 muestra D1 ≥ 40 % / D7 ≥ 20… |
| 11.9 | **2** | 11.9 | **PARCIAL** | **PARCIAL** → §I |

### 14 — La cuña (dirección aprobada 2026-09-14)
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 14.7 | 3 | **PCEP** — primera certificación del carril 1 (decisión #25) | TODO | → LEDGER_HISTORY.md §E |
| 14.8 | 4 | **Predictor beta-binomial de aprobado** con calibración pública | BLOCKED (11.8 · H.10) | → LEDGER_HISTORY.md §E · simulado `5dc7f6b` (#97) → §R |
| 14.9 | 4 | **Informe de dominio verificable** por URL | BLOCKED (11.8 · H.10) | → LEDGER_HISTORY.md §E · aritmética `432bdd2` (#97) → §R |
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

| 14.10 | 5 | **IRT (θ) — el modelo de Vicks** | BLOCKED (datos) | → LEDGER_HISTORY.md §E · JMLE simulado `b43424c` (#97) → §R |

### 17. De quiz a escuela + release definitivo (web · App Store · Play Store)
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 17.5 | **3** | **Tracks nuevos desde fuentes con licencia permisiva** | PARCIAL | → LEDGER_HISTORY.md §E |
| 17.6 | **2** | **UI de clase mundial, medida** | TODO | → LEDGER_HISTORY.md §E |
| 17.7 | **4** | **Vídeos explicativos generados desde código** | TODO | → LEDGER_HISTORY.md §E |
| 17.10 | **3** | **Re-puntuar frente a la competencia con lo anterior hecho** | TODO | → LEDGER_HISTORY.md §E |
| 17.14 | **1** | **Compras dentro de la app (la antigua 7.6, sin fila desde hace meses; `legal/h21-decision.md:58`)**: RevenueCat +… | **PARCIAL** | **PARCIAL** (2026-09-27): mitad backend — `POST /billing/revenuecat/webhook` (sandbox, auth verificado en vivo contra doc de RevenueCat), mismo entitlement que Stripe, `subscription_provider` nuevo. Falta: SDK/UI nativa (Capacitor) — HUMAN-BLOCKED (H.2, H.3) → §I |

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
| 18.4 | **2** | **Linux (track15) · Algoritmos (track16) · Redes (track17)** | **DONE… | **DONE** | **DONE** (2026-09-18) → §I |
| 18.9 | **4** | **Vídeo explicativo — piloto que decide** | TODO | → LEDGER_HISTORY.md §E |
| 18.10 | **4** | **Resto del catálogo: tracks 24-26, 28-31 y certs P2-P3** | **PARCIAL** | 26/28/29/30 en `1d76762`+`6e2778a` (1.200 Q, 80 lecciones); faltan 24, 25, 31 y relleno a 300 → §E |
| 18.11 | **2** | **Store-ready sin cuenta** | **PARCIAL** | `docs/STORE_LISTING.md` consolidado (iOS + Android), precios IAP actualizados a ADR-41/49, checklist actualizado (A3 age gate DONE por 19.11). Cuenta delete: endpoint + pantalla DONE. Privacy/Terms: DONE. Falta: screenshots con Playwright (necesita backend local), `codemagic.yaml` iOS build (H.14 macOS runner). |
| 18.12 | **3** | **Re-puntuación con URLs fechadas** | TODO | → LEDGER_HISTORY.md §E |

### 19. Lo que Educative y las tiendas exigen — social login, bootcamps, proyectos, autoría con fuentes libres (abierta 2026-09-18, sesión…
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 19.2 | **1** | **Sign in with Apple** — 19.1 (GitHub/Google OAuth) ya está en vivo sin flag (confirmado 2026-09-30: `oauth.py`, botones en `AuthScreen.tsx`), así que 4.8 exige esto **ahora**, no «en cuanto exista 19.1» | HUMAN-BLOCKED (H.2) | Necesita… |
| 19.3 | **2** | **Android: Google Sign-In nativo + Google Play Billing vía RevenueCat** (absorbe la mitad Android de 17.14, la antigua… | | → §I (criterio archivado por 20.10) |
| 19.7 | **2** | **Biblioteca de autoría con fuentes libres + RAG local** | TODO | → LEDGER_HISTORY.md §E |
| 19.8 | **3** | **Landing y SEO de whetzy.com al nivel de Educative** | TODO | → LEDGER_HISTORY.md §E |
| 19.9 | **3** | **Assets de tiendas e iconos de todos los tracks** (plan ADR-53) | TODO | → LEDGER_HISTORY.md §E |
| 19.10 | **4** | **Vídeo: Manim + Remotion (`editor-pro-max`)** — absorbe 18.9 | TODO | → LEDGER_HISTORY.md §E |
| 19.11 | **1** | **Moderación de UGC mínima (App Store 1.2/1.2.1)** | **DONE** | `395d20f`+`62353e6` (#92): filtro de nombres, reportar/bloquear, liga y duelos; 150 passed (2026-10-03, en `c6d0545`) → §R |
| 19.12 | **2** | **Borrado de cuenta con purga real a los 30 días** (textos legales §4/§8.3) | **DONE** | **DONE** `b2e3159`+`025aa0b` (2026-10-01; verificador 2.ª ronda CONFIRMADA): `services/account_deletion.py` — solicitud en `gdpr_requests`, gracia de 30 días (login, OAuth o panel la cancelan), purga cada 6 h que borra datos personales y de aprendizaje y anonimiza `users` (sin migración). 13 tests, 10 mutaciones en rojo, purga probada en Postgres 16 real |

### 20. Verificación masiva código ↔ docs ↔ prod (abierta 2026-09-18, sesión bf — **ABIERTA 2026-09-18 (H.21 ejecutada)**)
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 20.7 | **1** | CI ciego: `verify_ci_local.ps1` replica `ci.yml` paso a paso | **DONE** | `d4de5d2`, verificador CONFIRMADA: pin de ruff, oxlint y `check:i18n` verificados por `grep`; 6/6 backend, 10/10 frontend → §I |

### 21. Legal y fiscal a coste cero — investigación, borradores, gates humanos (abierta 2026-09-18, sesión bf — **H.20 SIGUE ABIERTO** — el…
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 21.1 | **1** | *(Premisa griega **suspendida** por ADR-47; la entidad y la jurisdicción están sin decidir, H.29. Se conserva el enunciado… | | → §I (criterio archivado por 20.10) |
| 21.2 | **1** | *(Premisa griega **suspendida** por ADR-47; valor por defecto: Merchant of Record + IAP. Enunciado original conservado… | | → §I (criterio archivado por 20.10) |
| 21.5 | **2** | **AI Act, DSA, EAA**: obligaciones de *deployer* del tutor… | **PARCIAL** | **PARCIAL** `5f7bd7b` (2026-09-19) → §I |
| 21.6 | **2** | **Propiedad intelectual**: búsqueda de marca «Whetzy» (EUIPO,… | **PARCIAL** | **PARCIAL** `8e7812a` (2026-09-19) → §I |

### 22. Blindaje, admin y preparación para un millón — todo a coste cero (abierta 2026-09-18, sesión bf — **ABIERTA 2026-09-18 (H.21)**;…
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 22.5 | **2** | **Cloudflare free**: WAF managed rules, rate limiting rules por ruta (`/auth/*`, `/tutor/*`), Bot Fight Mode, cache rules… | | → §I (criterio archivado por 20.10) |

### 23. Dos segmentos, un producto — ES y EN sin mezclar (abierta 2026-09-18, sesión bf — **ABIERTA 2026-09-18 (H.21)**; ADR-17)
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 23.1 | **1** | **Auditoría E2E por idioma**: cada pantalla, email, push, PDF/certificado,… | **DONE** | `c0a5af6`: Forgot/ResetPassword y `/evidence` sin i18n, push racha/duelo fijo en inglés → `push_service.localize()` → §I |
| 23.2 | **2** | **Landing y SEO por segmento**: `/es` y `/en` con copy nativo (no traducido), `hreflang` (existe), `sitemap` por idioma,… | | → §I (criterio archivado por 20.10) |
| 23.3 | **2** | **Tiendas, emails y soporte por idioma**: listings ES/EN en `store/`, plantillas de email por idioma (P.1) verificadas,… | **PARCIAL** | `3497429` (#93) → §S |
| 23.4 | **3** | **Segmento en el admin**: filtrable por idioma | **DONE** | → §N |
| 23.5 | **1** | **Las dos guardias de i18n daban números falsos y la que cita el protocolo no existía**: `audit_i18n.py` buscaba… | **DONE** | **DONE** `d991fe4` (2026-09-19) → §I |

### 24. Interfaz que venda al verse — UI/UX + competencia en vivo + vídeo (sesión interactiva; **después** de 20-23; absorbe 17.6 y 19.8;…

> **Estado:** `ABIERTA 2026-09-24` (ADR-45/47). Las filas BLOCKED pasan a PARCIAL: hay commits `24.x` en `master` pero son maquetas con…
> **Modo:** rama + PR + preview de Cloudflare (`<rama>.whetzy.pages.dev`); el dueño revisa el preview antes de fusionar, no cada pantalla…
> **Modelo:** Sonnet para código (`frontend/src` es fichero de riesgo); Haiku para inventarios y verificación.
> **Evidencia común a toda fila:** captura fechada en `docs/screenshots/<fecha>/`, `npx tsc -b --force` + `npx vitest run` + `npm run…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 24.0 | **1** | **Investigación competitiva en vivo**: navegar el free tier de los 8… | **PARCIAL** | 21 capturas landing+precios de 7/8. Reintento Platzi: firewall nuevo, tratado como bloqueo. Falta: onboarding/dashboard/gamificación (cuenta), Exercism/Platzi (bloqueados), `decisiones-24.0.md` → §I |
| 24.1 | **1** | **Identidad visual**: tokens de diseño (color con hue propio, tipografía… | **PARCIAL** | 6/51 `.module.css` con hex literal → 0/51, guarda mutada; `docs/design/identidad.md` escrito. Falta: aprobación del dueño → §I |
| 24.2 | **1** | **Landing que vende** (`/es`, `/en`; absorbe 19.8 y 23.2): hero con el… | **PARCIAL** | Lighthouse (preview): perf 77-89, a11y 94. LCP 3965-4392ms, falla presupuesto 2500ms. Falta: demo 3 preguntas, remedir en prod, copy/A-B del dueño → §I |
| 24.3 | **1** | **Onboarding rediseñado**: 3 preguntas de segmento (`SEGMENTOS.md` §«Cómo… | **PARCIAL** | e2e en inglés (`onboarding.en.spec.ts`), bug propio hallado y arreglado (`getByLabel('Name')` ambigua). Mutado rojo/verde. Falta: abandono por paso en admin (22.1) → §I
| 24.4 | **1** | **Dashboard con el motor visible**: mapa de dominio por skill (BKT como… | **PARCIAL** | Elo real visible (el nivel mostrado era XP); sin intentos no se muestra nada (evita el 1500 inventado). 4 tests, mutado. Falta: fuente por número, vista por segmento → §I |
| 24.6 | **2** | **Gamificación original + wallet de créditos**: racha con identidad… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 24.7 | **2** | **Panel de certificación**: readiness por dominio (18.1), simulacros (comprables con créditos), certificado… | **DONE** | ReadinessScreen + MockExamScreen + CertificateScreen + CertificateCard, endpoints, i18n ES/EN → §I |
| 24.8 | **2** | **Perfil público** `/u/<handle>` (opt-in): dominio verificado,… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 24.9 | **2** | **Panel B2B** (`SEGMENTOS.md` segmento 5): progreso por empleado, tiempo, certificaciones, comparativa anónima, import… | | → §I (criterio archivado por 20.10) |

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
| 26.0 | **4** | Canal YouTube ES creado: banner, descripción, links, 3 videos demo subidos (grabados en 24.13); **cada vídeo con su código… | | → §I (criterio archivado por 20.10) |
| 26.1 | **4** | 5 artículos en Dev.to / Hashnode ES sobre el motor técnico (BKT, FSRS, gap de mercado) | **PARCIAL** | `3497429` (#93) → §S |
| 26.2 | **4** | PR en `EbookFoundation/free-programming-books` agregando Whetzy en sección Python ES | TODO (redactar/construir; publicar… | → §I (criterio archivado por 20.10) |
| 26.3 | **4** | Template de email para universidades LATAM + lista de 50 contactos | TODO (redactar/construir; publicar bajo cuenta nueva… | → §I (criterio archivado por 20.10) |
| 26.4 | **4** | Página de landing para segmento career-switcher ES (dentro de whetzy.com/es/carrera) | TODO (redactar/construir; publicar… | → §I (criterio archivado por 20.10) |
| 26.5 | **4** | Página de landing para segmento B2B ES (whetzy.com/es/empresas) | TODO (redactar/construir; publicar bajo cuenta nueva =… | → §I (criterio archivado por 20.10) |
| 26.6 | **4** | Show HN post en español (Hacker News): preparación + activos | TODO (redactar/construir; publicar bajo cuenta nueva =… | → §I (criterio archivado por 20.10) |
| 26.7 | **4** | Perfiles en comunidades ES: Python Argentina Discord, Dev En Español, LatamDevs | HUMAN-BLOCKED (H.23: perfiles… | |
| 26.8 | **4** | **Superteam LATAM (México, Argentina, Brasil) como canal** (ADR-38): presencia en sus Discord/eventos, 1 charla o taller… | | → §I (criterio archivado por 20.10) |
| 26.9 | **3** | **Blog `/blog` ES/EN** (SEO orgánico, `archive/SPEC_WEB.md:152`): Markdown en `content/blog/`, prerender en `vite build`… | **PARCIAL** | `3497429` (#93) → §S |
| 26.10 | **3** | **Newsletter** (`archive/EXECUTION_PLAN_25-29.md:87`): alta con doble opt-in vía Resend (H.30), ES o EN según usuario,… | | → §I (criterio archivado por 20.10) |

### 27. Distribución masiva EN (ADR-27; spec `DISTRIBUCION.md`)

> **Estado:** `ABIERTA 2026-09-24` (ADR-47). Misma regla que la 26: se redacta y construye todo; publicar bajo cuenta nueva = H.23.
> **Dependencias:** ninguna para redactar; 26.0 DONE antes de grabar vídeo EN.
> **PRI:** 3. **Modelo:** Sonnet para contenido (ADR-59) y para copy.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 27.0 | **4** | Canal YouTube EN creado: banner, descripción, 3 videos EN (mismo contenido que 24.13 pero grabado en inglés nativo, no… | | → §I (criterio archivado por 20.10) |
| 27.1 | **4** | Show HN EN: "I built an adaptive Python→AI learning engine in Spanish because no one else did" | TODO (redactar/construir;… | → §I (criterio archivado por 20.10) |
| 27.2 | **4** | 5 artículos en Dev.to / freeCodeCamp News EN sobre motor técnico | **PARCIAL** | `3497429` (#93) → §S |
| 27.3 | **4** | PR en `jwasham/coding-interview-university` y `donnemartin/system-design-primer` READMEs | TODO (redactar/construir;… | → §I (criterio archivado por 20.10) |
| 27.4 | **4** | Product Hunt preparación: assets, lista de 100 upvoters confirmados, tagline | TODO (redactar/construir; publicar = H.23)… | → §I (criterio archivado por 20.10) |
| 27.5 | **4** | Product Hunt lanzamiento | HUMAN-BLOCKED (H.23) | Top 5 del día en categoría Education |
| 27.6 | **4** | Reddit strategy EN: 10 respuestas de valor en r/learnpython, r/cscareerquestions | HUMAN-BLOCKED (H.23: cuenta y karma… | |
| 27.7 | **4** | Landing page segmento career-switcher EN (whetzy.com/en/career) | TODO (redactar/construir; publicar = H.23) | Lighthouse… |
| 27.8 | **4** | Landing page segmento B2B EN (whetzy.com/en/enterprise) | TODO (redactar/construir; publicar = H.23) | Demo request form… |
| 27.9 | **4** | **Superteam global / Solana developer communities EN** (ADR-38): Solana Stack Exchange y Discord oficial con respuestas de… | | → §I (criterio archivado por 20.10) |
| 27.10 | **3** | **Comparativa honesta frente a Coursera/Udemy** (`DECISIONS.md` ADR-24, sin fila hasta hoy): página `/en/compare` y… | **PARCIAL** | `3497429` (#93) → §S |

### 28. Marketplace de instructores (ADR-29; spec `MARKETPLACE.md`)

> **Estado:** `ABIERTA 2026-09-24` (ADR-47). El código de 28.0–28.7 ya está en `master` (migración `u1v2w3x4y5z6_admin_tables`,…
> **Dependencias:** 22.1 PARCIAL (basta), 22.3 DONE. Ver spec completo en `docs/MARKETPLACE.md`.
> **PRI:** 3. **Modelo:** Sonnet (toca DB schema y auth — ficheros de riesgo).

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 28.0 | **4** | Schema DB: `instructor_profiles`, `marketplace_courses`,… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 28.1 | **4** | API: CRUD cursos instructor, upload contenido JSON, preview; **código de… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 28.2 | **4** | Quality gate pipeline para instructores: `scripts/instructor_quality_gate.py` corriendo en upload | **DONE** | → §N |
| 28.3 | **4** | Panel instructor — React: dashboard revenue, cursos, métricas por curso | **PARCIAL** — Verificado 2026-09-25 contra el… | → §I (criterio archivado por 20.10) |
| 28.4 | **4** | Marketplace público: catálogo con filtros, ratings, preview de primera lección | **PARCIAL** — Verificado 2026-09-25… | → §I (criterio archivado por 20.10) |
| 28.5 | **4** | Checkout cursos de instructor: Stripe/Paddle, split automático 70/30 | **PARCIAL** — Verificado 2026-09-25 contra el… | → §I (criterio archivado por 20.10) |
| 28.7 | **4** | Payouts mensuales: job día 15 de cada mes, mínimo $50; **rail elegido por… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 28.8 | **3** | **UI del marketplace conectada**: `MarketplaceScreen` e `InstructorScreen` (hoy maquetas, 24.10/24.11) contra… | **PARCIAL** | `cb40bcd` (#100): panel de instructor por API; faltan flag `MARKETPLACE_PUBLIC`, catálogo público y aprobación (criterio en §I) → §S |
| 28.9 | **3** | **Kit de reclutamiento de instructores** (`MARKETPLACE.md:161-167`: 5 fundadores → 20 → 50+): oferta escrita ES/EN (70 %,… | **DONE** | `docs/legal/instructor_recruitment_kit_{es,en}.md` → §I |

### 29. Economía cerrada y rails — créditos, referidos, códigos, USDC, credenciales verificables (ADR-33…37; spec `docs/ECONOMIA.md`)

> **Estado:** `ABIERTA` — desbloqueada por el dueño el 2026-09-19 (§1) y H.26 decidido por defecto el 2026-09-24 (ADR-47: la tabla de…
> **Dependencias:** 22.1 (admin), 22.6 (cola de trabajos y `RateLimiter`), 21.7 (ToS para 29.11), 24.6 (UI).
> **PRI:** 3. **Modelo:** Sonnet (migraciones, auth, billing = ficheros de riesgo); Haiku para tests, inventarios y verificación adversaria.
> **Invariante de la serie:** las tres reglas de `ECONOMIA.md` §1 se prueban con tests, no se prometen. Canje solo en web. Ningún «token»…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 29.0 | **1** | **Schema**: `credit_ledger`, `promo_codes`, `promo_redemptions`,… | **DONE** | **DONE** (2026-09-25) → §I |
| 29.1 | **1** | **Servicio de créditos** `services/economy/credits.py`: abono con lote y… | **DONE** | **DONE** (2026-09-25) → §I |
| 29.2 | **1** | **Tabla de grifos y sumideros** versionada en `content/economy/credits.json`… | **DONE** | **DONE** (2026-09-25) → §I |
| 29.3 | **2** | **Referidos**: código permanente por usuario, enlace `/r/<código>` que fija… | **DONE** | **DONE** `89eb7a7`: modelo+endpoint+frontend /r/ ruta+servicio con ladder de créditos → §I · 2026-10-01 (ADR-57): nada activaba ni abonaba; cableados job, 4 condiciones, abono a 7 días, escalera §3.3 y `granted_tier` |
| 29.6 | **2** | **Admin** (en 22.1): economía (emitidos/gastados/caducados, ratio sumidero/grifo, alerta de inflación), referidos… | **DONE** | 3 endpoints: `/economy/credits`, `/economy/referrals`, `/economy/k-factor` → §I |
| 29.7 | **3** | **Reactivación automática**: job de 14 días de inactividad | **DONE** | → §N · 2026-10-02: nada encolaba el job; ahora `periodic_jobs_loop`, 200 créditos/60 días (ECONOMIA §2.2), baja de un clic |
| 29.8 | **3** | **UI**: wallet, referidos, canje de códigos | **DONE** | → §N |
| 29.9 | **3** | **USDC como rail** (ADR-36): si H.19 = Stripe → activar *Pay with Crypto* en **test mode** y documentar en 7.2; payouts de… | | → §I (criterio archivado por 20.10) |


### 30. Integridad del despliegue — incidente de login del 2026-09-24 (PRI 0)

> **Estado:** `ABIERTA`. 30.0/30.7/30.8 DONE en producción (archivo §N). **30.9 solo en rama (PR #34): hasta que se fusione, un login válido en producción vuelve a la landing.**
> **PRI:** 0. **Origen:** captura del dueño — `POST whetzy.com/auth/login` → **405**, pantalla «Incorrect email or password».
> **Invariante de la serie:** un deploy del frontend no está hecho hasta que `node scripts/check-deployed.mjs` sale PASS contra…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 30.2 | **1** | **Se puede publicar sin puerta** (6 commits desde la UI web de GitHub) | **PARCIAL** | puerta del build `5c3ab12` (#90); falta proteger `master` (dueño, RUNBOOK) → §Q |
| 30.4 | **1** | **`npm run build` estaba en rojo y nadie lo vio**: el prerender buscaba… | **DONE** | `be07294`, verificador CONFIRMADA: Node 22 tiene `navigator.language` real; `detectLanguage()` fuerza `es` sin `window` → §I |
| 30.5 | **2** | El script `build` ya no corría `tsc -b` (`8a0dce0`) | **DONE** | `5c3ab12` (#90): `vite build` con error de tipos → exit 1; restaurado 0 (2026-10-03, en `01a200c`) → §Q |
| 30.9 | **0** | Login válido devolvía a la landing (cookie cross-site + host-only; `logout()` no llamaba a `/auth/logout`) → STATUS.md | **DONE** | `395e8a1`, verificador CONFIRMADA. Safari (ITP) sin probar → §I |

### 31. Fuente única de cifras, staging y migraciones con datos (del plan del 2026-09-24, cuyo fichero no está en el repo: estas filas son…

> **Estado:** `TODO`. **PRI:** 1. **Por qué:** los documentos vivos dan cifras distintas del mismo banco (6.233 frente a 6.305 preguntas)…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 31.1 | **0** | Staging: un preview de Cloudflare Pages y un servicio de Railway de staging; `master` solo por PR verde | HUMAN-BLOCKED… | 2026-09-30: #34 fusiona 2 migraciones directo contra producción sin ensayarlas ahí — sin staging, cada fusión repite ese riesgo |
| 31.4 | **0** | **Migración sin datos dejó sin preguntas a los usuarios con historial** (dueño, 2026-09-30) | **DONE** | `1225a29` (push directo a `master`, excepción ADR-45) → §N |
| 31.5 | **0** | **Regla del dueño 2026-09-30**: PRs pequeños, veto a analítica hasta ≥ 100 registrados reales, ningún `DONE` sin verificador de §7 → texto completo §N | DOING | mismo texto en `ORCHESTRATOR.md`; cumplido desde esta fila |
| 31.6 | **2** | **Tests de analítica sobre Postgres real**, no solo SQLite — D1/D7/CURR (2026-09-30): SQLite oculta diferencias de dialecto que los tests nunca vieron. Espera a que 31.5 libere analítica | TODO | `test_product_metrics.py` también contra Postgres real, en verde |
| 31.7 | **0** | **Pausa de sesiones autónomas y cierre**, 2026-09-30 → `docs/CIERRE_2026-09-30.md` | **DONE** | `check_docs.py` [11] exige PAUSA+cita, mutado rojo/verde |
| 31.8 | **0** | **Lanzamiento piloto** (prompt del dueño 2026-10-01): kit `docs/LANZAMIENTO_PILOTO.md`; PRs #45-#49 | PARCIAL | kit escrito; invitar, día 4 y recuento = dueño |
| 31.9 | **0** | 229 ejecutables gratis o imposibles reparados; corrige el servidor | DONE | `TestNoFreeAnswers` |

### 32. Motor demostrable — calibración y evidencia de aprendizaje (del plan del 2026-09-24; ídem)

> **Estado:** `TODO` (32.2 `BLOCKED` por H.10). **PRI:** 2. **Relación:** complementa 11.8 y 14.8; no las sustituye.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 32.2 | **3** | A/B BKT contra DKT con el framework 24.14 (asignación estable por usuario) | BLOCKED (H.10) | DKT se adopta solo si AUC ≥… · potencia `e7ebd9a` (#97) → §R |
| 32.3 | **2** | «¿Por qué esta pregunta?»: el scheduler devuelve sus razones (dominio, repaso… | **DONE** | **DONE** `d92e164` → §I |
| 32.4 | **2** | **La lección bloquea el quiz** (decisión del dueño 2026-09-27) | **DONE** | `b860e83` → §N |

### 33. Operación medible — SLO, restauración y offline idempotente (del plan del 2026-09-24; ídem)

> **Estado:** `TODO`. **PRI:** 2. **Relación:** 22.6 y 22.7 cubren cola, caché y página de estado; esto añade objetivos numéricos y ensayos.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 33.1 | **2** | Ensayo de restauración mensual con `scripts/db_restore_test.sh` y registro de… | **DONE** | **DONE** `5cd5ed8` → §I |


### 34. Una sola interfaz: todas las pantallas al lenguaje visual de la landing (abierta 2026-09-24, a petición del dueño)

> **Estado:** `ABIERTA`. **PRI:** 0 para 34.0–34.1 (hoy la app sale **sin estilos**), 1–2 para el resto.
> **Punto de partida medido (2026-09-24):** **276 de 761** referencias `styles.x` apuntan a clases que no existen en su `.module.css` —…
> **Cómo se trabaja (el bucle «tipo Lovable»):** una oleada = una rama y un PR. Cloudflare Pages publica un preview por push…
> **Invariantes de la serie:** (1) se copia el **estilo** de la landing, nunca su contenido inventado (30.1/H.31); (2) cero regresiones de…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 34.11 | **1** | **Hallazgos de comportamiento vistos al rediseñar (no son estilo):** (a)… | **DONE** | `be2e83b`, verificador CONFIRMADA (2ª ronda; 1ª REFUTADA por (b) sin test) → §I |
| 34.12 | **2** | Plural e idioma en la UI: `HomeScreen.tsx` sin `count`, `/evidence` en inglés fijo | **DONE** | `772fe5d`, verificador CONFIRMADA: plurales `_one`/`_other`, `/evidence` traducida (~60 cadenas) → §I |
| 34.1 | **0** | **Devolver el estilo a las 13 pantallas rotas**: por fichero,… | **DONE** | `e58b6b2` → §N |
| 34.2 | **1** | **Un solo juego de tokens**: una sola fuente (`src/theme/tokens.css` o… | **PARCIAL** | **PARCIAL** (2026-09-28): 0 `var(--x, #hex)` en `src/` (era 1, `--color-cyan` no existía en ningún fichero, caía al respaldo) → `var(--color-primary)` real. Guarda `tokens.noHexFallback` mutada. Falta: modo claro por el dueño → §I |
| 34.3 | **1** | **Componentes base** al estilo de la landing: `Button`, `Card`, `Badge`, `Modal`,… | **PARCIAL** | Foco visible y objetivos táctiles arreglados y verificados (`touchTargets.spec.ts`, 0 <44px). Detalle → §I |
| 34.4 | **1** | **Primer uso**: Auth (login, registro, OAuth, olvido/reset), Onboarding,… | **PARCIAL** | **PARCIAL** (2026-09-28): 390px sin scroll horizontal en Auth/Onboarding/Home ES+EN (5 e2e, mutado); TTFQ ES 14.7s, EN 12.9s (esta rama, local). `ttfq-prod.spec.ts` NO se corrió contra producción (cuenta real, fuera de alcance sin el dueño) → §I
| 34.5 | **1** | **Aprendizaje**: Home, Tracks, Lesson y Quiz (con Monaco, WhyButton, GlossaryText, TermCard) | **DONE** | **DONE** (2026-09-29) → §N |
| 34.6 | **2** | **Progreso y social**: Profile, Stats, League, Duel, Readiness, MockExam,… | **PARCIAL** | **PARCIAL** `d11db88` → §I |
| 34.7 | **2** | **Resto**: Admin, Instructor, Marketplace, Legal, Evidence, DeleteAccount | **PARCIAL** — pantallas del bloque revisadas… | (2026-09-29) `ProfileTab`/`CourseTab`: mismo bug de 34.3 fuera de `pages/`, invisible al guard hex-only (`rgba` no hex) — `:focus`→`:focus-visible`+`color-mix` 35%, verificado en Chromium real → §I |
| 34.8 | **2** | **Regresión visual**: Playwright con capturas por ruta (ES/EN × móvil/escritorio)… | **PARCIAL** | **PARCIAL** → §I |
| 34.9 | **2** | **Verificación y re-puntuación**: verificador adversario (protocolo §7) de 34.0–34.8 y fila nueva en el teardown… | | → §I (criterio archivado por 20.10) |

### 35. Lo que el mercado enseña: competencia verificada → producto (abierta 2026-09-24, a petición del dueño)

> **Estado:** `ABIERTA`. **PRI:** 1.
> **Origen:** captura en vivo de 33 sitios de competencia directa e indirecta (páginas públicas, sin registro), sintetizada en…
> **Hallazgo que ordena la serie:** varias «ideas nuevas» de los informes **ya existen en el código y no se ven**: la prueba de nivel está…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 35.1 | **1** | **Comparativa pública verificada en la landing**: solo cifras re-descargadas y fechadas, `null` = no comprobado | **DONE**… | |
| 35.4 | **2** | **Ligas opt-in visible**: interruptor en la propia pantalla de ligas («totalmente opcional») | **DONE** — 2026-09-24:… | |
| 35.6 | **2** | **Refresco trimestral de §A.1**: re-descargar las páginas de precios, cambiar cifras y `COMPARISON_CHECKED_ON` | TODO —… | → §I (criterio archivado por 20.10) |
| 35.8 | **2** | **Cada deploy de Railway deja ~1 min de 502/503.** Medido 2026-09-24: tras los pushes `a6a5a91` y `f2ea9cb`, `/health` dio… | **DONE** | railway.toml healthcheckPath=/health 120s + lifespan shutdown handler con close_db() → §I |
| 35.9 | **2** | El nivel 2 (`ci_local.sh`) corría sobre el árbol y quedaba «CORRIENDO» | **DONE** | `7fe4303` (#90): TERM → `INTERRUMPIDO`; KILL → `--estado` lo detecta (2026-10-03, en `01a200c`) → §Q |


### 37. Catálogo uniforme 32 × 10, simulacros reservados y prioridad por demanda (ADR-54, 2026-10-01; antes ADR-53 y ADR-46)

> **Estado:** `ABIERTA`. **PRI:** 1 (detrás de la serie 30). **Modelo:** ADR-59 (escribe Sonnet 5 desde la fuente, revisión completa Sonnet 5, piloto de 10; `PLAN_CONTENIDO.md`).
> **Orden (ADR-59):** en paralelo a 31.8; primero 37.25, luego 37.22, 37.10, 37.6, 37.7 y 37.8. **La guarda 37.0 sigue antes de cualquier pregunta nueva.**
> **Corpus (ADR-46 §4-5, vigente):** `corpus/` está en `.gitignore`. Se descarga con `git clone --depth 1`, dumps oficiales y **torrents solo cuando…
> **Unidad:** la skill. Forma por track: 32 skills · 10 Q (≥ 3 ejecutables) · 1 lección y 1 término por skill (`scripts/metas_catalogo.json`). Suelo e ideal de ADR-53: sustituidos. Cifras: `python scripts/catalog_coverage.py`. Un bloque = un PR verde.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 37.1 | **1** | **Temario de referencia por track** (ADR-54: solo elige qué 32 skills entran): `scripts/metas_catalogo.json`, 45 tracks y 11 certificaciones, leídos el 2026-09-30 | **PARCIAL** | Falta temario de track22, 23, 39, 47, 54, 55 y 56, objetivos de SY0-701 y longitud de examen de Microsoft; `catalog_coverage.py --check` PASS |
| 37.4 | **2** | **Descarga y verificación del corpus por área** (una subfila por área en… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 37.5 | **2** | **Generador desde corpus**: `scripts/generate_track_content.py` (absorbe 25.0) toma track + módulo + fragmentos del corpus… | | → §I (criterio archivado por 20.10) |
| 37.6 | **2** | **Tracks construidos a la forma 32 × 10**: A primero (02, 03, 12, 14, 15, 18, 22, 26, 27, 28, 30), luego B (19, 23) y C | TODO | `catalog_coverage.py`: el track sin pendientes; 37.0 y puerta §7 en verde; un track = un PR |
| 37.7 | **2** | **track24 y track25 reconstruidos con la forma 32 × 10** desde la cuarentena (nivel B) | TODO | ídem, fuera de `_quarantine` y `question_diversity.py` sin línea base |
| 37.8 | **2** | **Tracks nuevos por demanda** (`CATALOGO_MAESTRO.md` §2.0): A (38, 33, 34) → B (37, 47, 48, 35, 36, 39, 31) → C (49, 50, 53, 54, 32, 52, 51, 55, 56) solo con todos los A y B en el suelo | TODO | ídem por track; `metas_catalogo.json` lo pasa a «construido» en el mismo commit |
| 37.9 | **2** | **Glosario ≥ 1 término por skill**, ES y EN nativos (absorbe 25.12) | TODO | `catalog_coverage.py`: términos ≥ skills en cada track |
| 37.10 | **1** | **Certificaciones a la regla de ADR-54**: 100 % de objetivos, práctica ≥ máx(300, 3 × L), reservadas 2 × L; primero MLA-C01 y las 3 de Microsoft; nuevas en español: GCP ACE → LPIC-1 → AZ-104 | TODO | `catalog_coverage.py`: práctica y reserva al 100 % por certificación; `test_certification_blueprints.py` |
| 37.11 | **3** | **Proyectos multi-paso**: 10 por track ejecutable (hoy 0; catálogo §1) | BLOCKED (37.6) | Cada proyecto con tests de… |
| 37.12 | **3** | **Monitoreo trimestral de competencia** (`CATALOGO_MAESTRO.md` §11.4 apuntaba a una fila que no existía; complementa… | | → §I (criterio archivado por 20.10) |
| 37.13 | **3** | **Scorecard ADR-54** (absorbe 25.13): `scripts/catalog_coverage.py` + `scripts/metas_catalogo.json` + `backend/tests/test_cobertura_plan.py` | **PARCIAL** | Hecho 2026-10-01 para ADR-54 (script, metas, 21 tests con mutación). Falta: cifras en `/evidence` y re-puntuar Contenido en el teardown al cambiar de tramo |
| 37.14 | **1** | **track13 (ciberseguridad) tiene enunciados repetidos: 87,9 %… | **DONE** | **DONE** `fbf9baf` (2026-09-25) → §I |
| 37.15 | **1** | Fuentes sin indexar: 3.906 de 6.305 preguntas… | **PARCIAL** | (2026-09-29, `Workflow` 10 agentes) 4.450→3.903 sin indexar (10.949 preguntas). 267 citas RFC/PEP con URL canónica verificada en vivo; 8 dominios nuevos en `index.json` (peps.python.org reusar/CC0, Wikipedia/Deep Learning book/OWASP cheatsheets cita). `tests/content` 70.057 verde → STATUS.md |
| 37.16 | **1** | **La correcta es la opción más larga.** Medido 2026-09-25 sobre… | **DONE** | `46764ff` (2026-09-26) → §N |
| 37.17 | **1** | Inglés dentro del español y ejecutables con atajo… | **PARCIAL** | (2026-09-29, `Workflow`) recuento real: 699 preguntas exec (no ~2.900, cifra vieja errónea). 219 revisadas a fondo en 4 tracks, 10 bugs de ambigüedad reales arreglados y verificados, 1 estructural sin arreglar (`q060203ex012`). Quedan ~480 sin revisar → STATUS.md |
| 37.18 | **1** | **Banco de simulacro reservado**: `"pool": "simulacro"`; ninguna vía fuera del simulacro lo sirve | **DONE** | `20260930_question_pool`, corregido 2026-09-30 (incondicional en las 4 vías) → §N |
| 37.19 | **1** | **Formato de examen del proveedor**: AIF-C01 65 Q / 90 min (repo 85/120); MLA-C01 65/130 (repo lleva el de C02, 85/170); duración de AZ-900 y DP-900 | **DONE** | **DONE** `764b06b` (2026-09-30) → §N |
| 37.22 | **1** | **ISC2 CC al outline del 2026-09-01** (CAT 100–125 ítems; D2 Governance nuevo; `mod4002` BC/DR no mapea 1:1) | **DONE** | `84fb47c` (#102): 5 `exam_domains` del outline 2026, 23 skills con dominio, test ISC2 pasa; dominio por skill, no por módulo (dueño, 2026-10-03) → §S |
| 37.20 | **1** | **Métricas de producto con meta** (ADR-53 §8): D1 ≥ 15 %, D7 ≥ 7 %, D30 ≥ 4 %, conversión D35 ≥ 2,1 %, CURR, ≥ 30 min/semana, completion de pago, calibración del simulacro | **DONE** | (2026-09-30) D30/CURR/conversion_d35/30min-pagadores en `analytics.py`; corregido ×2 (CURR a la definición literal de Duolingo, días UTC completos) → §N, STATUS.md |
| 37.21 | **3** | **Mapa skill → nodo del temario**, para elegir las 32 skills de cada track (el ideal por temario quedó sustituido, ADR-54) | TODO (tras 37.6) | cada skill con su nodo |
| 37.23 | **2** | **Alineación lección↔quiz** (heredera de la 37.1 vieja, antes de ADR-53; los commits `22a01a8`…`4f1ab26` dicen «37.1» por ese motivo — ver STATUS.md): `audit_lesson_quiz_alignment.py` sobre 8 tracks señalados el 2026-09-28 | **PARCIAL** | (2026-09-29) 8 tracks revisados, track08+22+11+23+10+44+45+46 cerrados (39.39 DONE). 4/4 bugs de contenido corregidos. track44: `l440202`/`l440204` reasignados (skill_id), 5 preguntas nuevas. Queda la expansión de catálogo hacia ADR-53 (37.6-37.8), no una corrección → STATUS.md |
| 37.24 | **1** | **Poblar el banco de simulacro reservado** (2× la longitud del examen, ADR-54; `"pool": "simulacro"`) y encender `MOCK_EXAM_RESERVED_POOL_ENABLED` (mecanismo DONE en 37.18, apagado por defecto) | TODO | 8 certificaciones con L publicada con reservadas ≥ 2× su `exam_question_count`; flag en `True`; `catalog_coverage.py` pasa de 0/1.040 reservadas a la meta — autoría de contenido (ADR-59), no una tarea de código |
| 37.25 | **1** | **Piloto de autoría (ADR-59)**: 10 ítems de una skill de track44, escritos por Sonnet desde un fragmento `reusar` | DONE | puerta §7 PASS; ≤ 3/10 `blocker`/`major` tras revisión; coste por ítem aceptado anotado en `PLAN_CONTENIDO.md` §7 |

### 38. Negocio medible — KPIs, pilotos B2B, instructores, afiliados (ADR-47; abierta 2026-09-24)

> **Estado:** `ABIERTA`. **PRI:** 2. Todo lo que aquí exige hablar con personas o crear cuentas lo prepara la sesión y lo ejecuta el dueño…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 38.1 | **2** | **Precios: una sola fuente = ADR-41 (dueño)**: Pro 14,99 $ · Pro Max 19,99 $ ·… | **DONE** | **DONE** `cf2fc58` → §I |
| 38.2 | **2** | Oferta de 3 pilotos B2B gratuitos (ADR-22): documento ES/EN (qué dam… | DONE | → §O |
| 38.3 | **2** | Dossier de afiliación Python Institute y CompTIA (archive/whetzy_es… | DONE | → §O |
| 38.5 | **3** | **Página `/evidence` como única prueba social** (19.8, 30.1): cifras del banco y del motor calculadas en build, cero… | **DONE** | **DONE**: EvidenceScreen.tsx + CSS module + ruta registrada en App.tsx → §I |
| 38.6 | **2** | **Pro Max = tutor IA ilimitado; Pro con cupo diario** (ADR-49). `POST`… | **DONE** | `843015e` (2026-09-25) → §I |
| 38.7 | **2** | **Certificación a 39,99 $ de pago único** (ADR-49). Hoy los tracks… | **DONE** | `843015e` (2026-09-25) → §I |

### 39. Noche 2026-09-26 — incidente de arranque, deuda de calidad y aprobación en bloque (ADR-50)

> **Estado:** `ABIERTA`. Viene del prompt de control total v5 y de `docs/archive/EVALUACION_COMPLETA_WHETZY.md`. Lo que exige cuenta o dinero va a §3.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 39.0 | **0** | **Producción caída 09:35–10:48 UTC tras `ec97405`**: `content_loader`… | DONE | → §M |
| 39.1 | **0** | Coletillas de relleno en opciones incorrectas de tracks 26/28/29/30… | DONE | → §O |
| 39.2 | **1** | Fuentes inferidas en 146 lecciones normalizadas en #28 | DONE | → §O |
| 39.3 | **1** | `tests/content` en verde (1.254 fallos en master, 792 tras #28) | DONE | → §O |
| 39.4 | **2** | `content_quota` detrás de flag (ADR-50a) | DONE | → §O |
| 39.5 | **2** | Gamification auditada de punta a punta | DONE | → §O |
| 39.6 | **2** | `audit_ai_traces.py` | DONE | → §M |
| 39.7 | **2** | Detector de originalidad / casi-duplicados | DONE | → §M |
| 39.27 | **2** | Reescribir las 12 parejas casi-duplicadas anotadas en `KNOWN` (track01 ×3, track09 ×5, track41 ×4) | **PARCIAL** | (2026-09-29) 10/12 reescritas y verificadas en Python real, quitadas de `KNOWN`. 2 nunca fueron duplicados: ciego del checker (solo `question_es`, ignora `code`) → 39.40. `tests/content` 70.277; guarda mutada rojo/verde → §I |
| 39.28 | **0** | Segunda familia de coletillas («como concepto principal» 982, «sin e… | DONE | → §O |
| 39.29 | **0** | 1.404 explicaciones de plantilla vistas por el alumno en track41 (59… | DONE | → §O |
| 39.30 | **1** | Datos personales en el contenido: `l260101` enseñaba el nombre y correo del dueño | DONE | → §M |
| 39.31 | **2** | `user_meets_tier` no mira `subscription_expires_at` | **DONE** | `749e07f`: cancelación no reseteaba `subscription_tier`; vencido → «free». Verificador CONFIRMADA, mutado → §I |
| 39.32 | **3** | `test_rag_self_retrieval` tarda ~28 min (cuadrático en el banco) | **DONE** | `8934dd2` (#111): 186 s, 95,60/95,33 %; suite + lento ≈ 12,8 min, aceptado por el dueño el 2026-10-03 (`[COORD]` en #89) → §R, §S |
| 39.33 | **1** | Claves sospechosas previas: la explicación se parece más a otra opción (`check_expl_key`) | **PARCIAL** | 86 + 26 más (`a17a7c8`, ya en esta rama): sk130104/204/304 (track13) tenían >50% mal — RACI inventado, "menor privilegio" al revés. Verificadas leyendo las 60 preguntas de las 3 skills en vivo esta sesión: ninguna queda mal. Tracks hermanos del mismo commit masivo: solo `q120302mc002` revisado. TODO: resto sin muestrear |
| 39.34 | **2** | Texto de UI del cupo Free (ES/EN) antes de encender `FREE_DAILY_QUOTA_ENABLED` | **DONE** | `e754b50` → §N |
| 39.35 | **0** | El limitador de peticiones de producción fallaba en abierto:… | DONE | → §M. Post-DONE `95cdfbf`: `except` no cazaba `RuntimeError`/`OSError` — 204 tests rotos → 0 |
| 39.36 | **1** | `options_en` escritas en español en track21 (194 preguntas) y track44-46 (46, 33, 49) | **DONE** | 295 preguntas → §N |
| 39.37 | **0** | Relleno de generador en producción: 180 preguntas de track20 mod200… | DONE | → §O |
| 39.38 | **0** | Dos claves falsas de Bicep en track22 (`q220503008`: «using» no… | DONE | → §M |
| 39.39 | **1** | Lección/quiz desalineados: 90 casos en 7 tracks… | **DONE** | (2026-09-29) → §N |
| 39.40 | **2** | `check_originality.py` ciego a `code` (39.27) | **DONE** | (2026-09-29) → §N |
| 39.41 | **1** | 19 `sql_exec` que un alumno con SQL correcto no podía aprobar | **DONE** | → §N |
| 39.42 | **2** | track43 mod4301: 45 de 75 preguntas eran relleno molde… | **DONE** | → §I |
| 39.43 | **2** | **Cuarta familia de coletillas**: cláusula de marketing cloud pegada a opciones cortas (track10 98, track06 18…) | **TODO** | Revisión pregunta a pregunta (no regex: ~150 candidatas, la mayoría gerundios legítimos), vía `Workflow` (ADR-52) → §Q |
| 39.8 | **1** | Cerrar el índice de fuentes (37.15) | TODO | 0 % sin indexar o lista exacta de las imposibles |
| 39.9 | **2** | Explicaciones de < 2 frases en tracks 13, 15, 16, 17 | **PARCIAL** | track13 4/4; track15/16/17: 11 reescritas y `q160303005` corregida (`687426f`, #104); sin muestreo de los ~113 «falsos positivos» → §R |
| 39.10 | **3** | Mapa de tracks con rutas y recomendación | TODO | vitest + e2e, ES/EN, a11y |
| 39.11 | **2** | Límite de gasto de Groq por usuario y global | DONE | → §M |
| 39.12 | **3** | LLM de respaldo (ADR-50f) | DONE | → §M |
| 39.13 | **3** | Emails de re-enganche (ADR-50g) | TODO | Flag apagado, baja en un clic, tests |
| 39.14 | **3** | Plantilla de lección con formato (ADR-50d) | **DONE** | `4e8d941` (#98): `lessonScreen.icons.test.tsx` 3 passed (2026-10-03, en `c6d0545`) |
| 39.15 | **1** | Fichero `LICENSE` (ADR-50e) | DONE | → §M |
| 39.25 | **1** | **MLA-C01 retirado: ampliar track43 sin reestructurar** | **DONE** | `a6fe453` (#99): +7 skills `sk430121`–`127`, los 4 dominios intactos (2026-10-03, en `c6d0545`) → §R |
| 39.26 | **2** | **Security+ V8 hacia el 17-11-2026** (comptia.org, leído 2026-09-26) | TODO | track42 revisado contra el temario V8 al publicarse |
| 39.24 | **1** | **AI-900 retirado: track45 a AI-901** | **DONE** | `7522e23` (#96): track45 = AI-901 con 2 dominios; contenido 70341 passed (2026-10-03, en `c6d0545`) → §R |
| 39.18 | **1** | vitest: 4 fallos (`StatusPage` `/api/v1` relativo, `common.back`,… | DONE | → §M |
| 39.20 | **2** | PostHog en el frontend (ADR-50j) | **DECIDIDO: no** | La analítica ya es propia (`analytics_events` + embudo admin); PostHog en el navegador rompería la promesa de la landing y la CSP (ADR-50j revisada) |
| 39.21 | **2** | Sentry en el frontend (ADR-50k) | **DECIDIDO: no** | Solo backend; privacidad y DPA ES/EN actualizados: Sentry activo desde 2026-09-26, UE, sin PII |
| 39.22 | **2** | Backups: `backup_db.sh` + `restore_check.sh` + runbook | DONE | → §M |
| 39.23 | **1** | H.30 honesto: sin proveedor, 503 `email_not_configured` | DONE | → §M |

### 40. Superar a Brilliant y Kodree donde hoy ganan (abierta 2026-09-28, a petición del dueño; spec `PLAN_EXPERIENCIA.md`)

> **Estado:** `ABIERTA`. **PRI:** 2. Origen: `COMPETENCIA.md` §A.2b. Nada de esto se anuncia hasta 40.13.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 40.1 | **2** | **Tipo `interactive`**: `{widget, params, target, checker}`; checker en cliente y servidor; alimenta BKT/Elo/FSRS | TODO | esquema en `check_question_bank.py`; test de discrepancia cliente↔servidor en rojo al mutar |
| 40.2 | **2** | **Piloto 3 widgets** (búsqueda binaria, CIDR, JOIN) × 10 ítems ES/EN | TODO (tras 40.1) | e2e móvil+escritorio, axe 0, ≤ 30 KB gz/widget, LCP < 2,5 s 4G; sin piloto verde no hay 40.3 |
| 40.3 | **3** | **Biblioteca de 15 widgets** mapeados a dominios de cert (IAM, Git DAG, TCP, CPU…) | TODO (tras 40.2) | contrato `render/serialize/check` testeado por widget; cada uno suma al readiness |
| 40.4 | **3** | **Widget ↔ código** en los dos sentidos (Pyodide, sql.js, Worker JS) | TODO (tras 40.2) | e2e: editar el widget cambia el código y ejecutar el código anima el widget |
| 40.5 | **3** | **Tutor que señala**: acciones estructuradas (resaltar línea, marcar nodo) validadas por esquema, con texto accesible | TODO (tras 40.2) | acción fuera de esquema rechazada (test); sin grounding lo dice (línea roja 2) |
| 40.6 | **3** | **Tutor por voz ES/EN**: TTS `speechSynthesis`; STT por Groq `/audio/transcriptions` (H.49); pulsar para hablar, audio no guardado | TODO (tras 40.5) | WER en ES medido con muestras propias; retención de audio de Groq leída con URL; consentimiento ES/EN; cuenta contra 38.6 y 39.11 |
| 40.7 | **3** | **Comunidad con contexto**: hilos por pregunta/lección, soluciones tras resolver, salas ES/EN, denuncias + antifraude | TODO (construir; abrir con ≥ 100 activos) | e2e: la solución ajena no se ve antes de resolver; notificación y retirada ES/EN |
| 40.8 | **4** | **Grupos de estudio por cert + revisión por pares** de proyectos (revisor con Open Badge del track) | TODO (tras 40.7, 37.11) | readiness de grupo sin datos personales (test) |
| 40.9 | **2** | **Plan anual** junto al mensual; solo esos dos, sin vitalicio ni familiar (dueño, 2026-09-28). Precio anual y reembolso como la competencia directa (`COMPETENCIA.md` §A); responde H.35 (1) | TODO | precio anual con su referente citado; cancelar en 2 toques (línea roja 7) y aviso de renovación (21.4) |
| 40.10 | **4** | **Ruta Analista de datos ejecutable** (pandas en Pyodide + SQL, datasets abiertos) | TODO | cert confirmada con URL; fuentes ADR-11 |
| 40.11 | **4** | **TypeScript ejecutable** en el Worker, carga perezosa solo en su track | TODO | licencia del compilador verificada; peso fuera del bundle base |
| 40.12 | **4** | **Investigar Java en navegador y UX/UI** (runtime, peso, licencias) | TODO | informe con URL; nada entra sin fuentes H.LIC y línea roja 8 |
| 40.13 | **3** | **Medir la superación**: tabla criterio a criterio frente a Brilliant y Kodree, re-capturada con fecha | TODO (cierra la serie) | cada «mejor que» con evidencia ejecutable o URL; sin ella no sale a la landing (línea roja 9) |

## 3. Cola HUMAN-BLOCKED

> → `docs/archive/LEDGER_HISTORY.md` §J

| H.16 | **DECIDIDA** (ADR-50p) — dueño: proteger `master` (PR obligatorio) en GitHub → Branches; staging (31.1) aprobado, alta con coste por el dueño |
| H.15 | **RESUELTA** (ADR-50n) — proxy a `127.0.0.1:8000` + guarda `pretest:e2e` |
| H.12 | PRI 0 de seguridad — rotar la `GROQ_API_KEY`. Estuvo commite… |
| H.13 | PRI 0 — Actions: corrió verde el 2026-10-01 y desde ~12:52 UTC ningún job recibe runner (`runner_id: 0`). Dueño: GitHub → Billing → Actions (ADR-50o). Puerta real: la local |
| H.2 | Apple Developer Program — y desde 2026-09-18 también bloquea… |
| H.3 | Google Play Console |
| H.4 | OBSOLETA 2026-10-01: sin Stripe (H.29) |
| H.5 | Submisión a stores |
| H.14 | iOS no se puede generar ni compilar en este PC (Windows, sin… |
| H.6 | Cadena de sesiones |
| H.7 | Rutina remota — única forma de no depender de la app abierta |
| H.8 | **OBSOLETA 2026-10-02**: bloqueo falso (13.2); P.8 y 10.2, lo único que bloqueaba, están DONE (LEDGER_HISTORY). La rotación de la clave es H.12 |
| H.9 | Dispositivo físico o emulador con lector de pantalla real pa… |
| H.10 | Cohorte beta ≥ 30 usuarios reales (11.8) |
| H.17 | Ver H.13 |
| H.18 | La cadena solo corre con la app Claude abierta y el PC despi… |
| H.19 | RESUELTA por H.29 (2026-10-01) |
| H.20 | Revisión profesional de los textos legales antes de publicar… |
| H.22 | RESUELTA 2026-10-01 (dueño): OWASP CC BY-SA no se usa (ADR-47); seguridad con NIST + MITRE |
| H.23 | Abrir la Serie 26 (distribución ES) cuando 24.14 esté DONE |
| H.24 | **OBSOLETA 2026-10-02**: la serie 28 ya está abierta en §2 (9 filas) |
| H.25 | Activar payouts de instructores en producción (28.7) |
| H.26 | **OBSOLETA 2026-10-02**: la serie 29 ya está abierta en §2 (8 filas) |
| H.27 | cNFT de certificados en Solana (29.10, opcional; ADR-37): wa… |
| H.28 | Grant / bounty de la Solana Foundation o Superteam para trac… |
| H.29 | DECIDIDO 2026-10-01 (dueño): Grecia; web = Paddle, tiendas = IAP/Play Billing vía RevenueCat; sin Stripe. Web: `/checkout` hecho; falta alta Paddle y dominio |
| H.30 | RESUELTA 2026-10-01: Resend en producción (log «Email: proveedor resend») |
| H.31 | **RESUELTA** (ADR-50m) — landing servida 2026-09-26 sin testimonios ni «1.2M» |
| H.32 | **RESUELTA** `e40ba75` (2026-09-24): la API sale solo de `.env.production` y el prerender va en todo `vite build` → §J |
| H.33 | **RESUELTA 2026-09-26** — log Railway `b64e2a9a`/`f097361c`: `[owner] unchanged: admin@whetzy.com` (falta solo login `/admin` de 30.8) |
| H.34 | **RESUELTA 2026-09-26** — conector Railway activo; permisos en `CONECTORES.md` |
| H.35 | **PARCIAL** (2026-09-25): mensuales fijados (ADR-41, ADR-49); faltan anual, tarifa regional, base del 80 %, cupo de Pro y la cert 39,99 $ → §J |
| H.38 | Afiliación con Python Institute y CompTIA (38.3) |
| H.39 | 3 pilotos B2B gratuitos (38.2, ADR-22) |
| H.40 | Reclutar 5 instructores fundadores (28.9) |
| H.41 | **RESUELTA 2026-09-26** (aprobación en bloque, ADR-50k) — proyecto Sentry `whetzy-backend` + `SENTRY_DSN` en Railway; deploy `f097361c`: `Sentry initialised (env=production)` |
| H.42 | **DECIDIDA 2026-09-26** (ADR-50j): analítica = PostHog; Mixpanel no se instrumenta |
| H.43 | RESUELTA 2026-10-01: Hugging Face conectado |
| H.44 | Terminar o quitar Firecrawl, Amplitude, Mailchimp y Lusha (a medio conectar) |
| H.45 | Conectar redes (X, LinkedIn…) en Metricool/Typefully para que la distribución deje de ser solo borradores |
| H.46 | ¿Monitor de uptime de Sentry para `/health`? (puede consumir cuota de pago) |
| H.49 | **DECIDIDA 2026-09-28** — dueño: la voz a texto del tutor (40.6) usa el mismo proveedor que el tutor (Groq, `/audio/transcriptions`) |
| H.48 | Clave de API de Anthropic con gasto para un pipeline por **Batch API** de rellenos con Haiku 4.5 (ADR-52); hoy ningún código del repo llama a la API | Dueño |
| H.47 | ¿Mantener el correo personal del dueño como contacto en la página pública `/evidence` (`EvidenceScreen.tsx:340`)? Por defecto (ADR-47) se deja y se propone un alias tipo `support@whetzy.com` | Dueño |
| H.50 | Descarga del corpus (`scripts/corpus/`) en el setup script del entorno cloud, para que `corpus/` exista en cada sesión de autoría (ADR-59, `PLAN_CONTENIDO.md` §3) | Dueño |

## 5. Bitácora de decisiones

> Decisiones archivadas en `docs/archive/LEDGER_HISTORY.md` §J.
> ADRs formales: `docs/DECISIONS.md`.

---

## 6. Cadena de sesiones

> → `docs/archive/LEDGER_HISTORY.md` §G
