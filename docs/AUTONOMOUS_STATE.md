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
| Alembic HEAD | `20260927_iap_provider` (45 migraciones) |
| Contenido | **10.989 preguntas** / 35 tracks / 723 skills / **723 lecciones (100 %)** / **1.044 términos glosario**. Tracks 09/10/11 =… |

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
| 19 | Catálogo 27 tracks (histórico; meta actual ADR-46) + cert marketplace | 2/10 | 20 % | 19.2–19.10 |
| 18 | Nuevos tracks (frontend, SQL, linux, algos, redes, certs) | 3/5 | 60 % | 18.5 |
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
| 11.9 | **2** | 11.9 | **PARCIAL** | **PARCIAL** → §I |

### 14 — La cuña (dirección aprobada 2026-09-14)
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
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
| 17.5 | **3** | **Tracks nuevos desde fuentes con licencia permisiva** | PARCIAL | → LEDGER_HISTORY.md §E |
| 17.6 | **2** | **UI de clase mundial, medida** | TODO | → LEDGER_HISTORY.md §E |
| 17.7 | **4** | **Vídeos explicativos generados desde código** | TODO | → LEDGER_HISTORY.md §E |
| 17.10 | **3** | **Re-puntuar frente a la competencia con lo anterior hecho** | TODO | → LEDGER_HISTORY.md §E |
| 17.14 | **1** | **Compras dentro de la app (la antigua 7.6, sin fila desde hace meses; `legal/h21-decision.md:58`)**: RevenueCat +… | **PARCIAL** | **PARCIAL** (2026-09-27): mitad backend — `POST /billing/revenuecat/webhook` (sandbox, auth por Authorization header verificado en vivo contra la doc de RevenueCat), mismos campos de entitlement que Stripe, `subscription_provider` nuevo. Falta: SDK/UI de compra nativa (Capacitor) — activación real HUMAN-BLOCKED (H.2, H.3) → §I |

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
| 19.2 | **1** | **Sign in with Apple** — obligatorio por App Store Review 4.8 en cuanto exista 19.1 | HUMAN-BLOCKED (H.2) | Necesita… |
| 19.3 | **2** | **Android: Google Sign-In nativo + Google Play Billing vía RevenueCat** (absorbe la mitad Android de 17.14, la antigua… | | → §I (criterio archivado por 20.10) |
| 19.7 | **2** | **Biblioteca de autoría con fuentes libres + RAG local** | TODO | → LEDGER_HISTORY.md §E |
| 19.8 | **3** | **Landing y SEO de whetzy.com al nivel de Educative** | TODO | → LEDGER_HISTORY.md §E |
| 19.9 | **3** | **Assets de tiendas e iconos de todos los tracks** (meta ADR-46) | TODO | → LEDGER_HISTORY.md §E |
| 19.10 | **4** | **Vídeo: Manim + Remotion (`editor-pro-max`)** — absorbe 18.9 | TODO | → LEDGER_HISTORY.md §E |

### 20. Verificación masiva código ↔ docs ↔ prod (abierta 2026-09-18, sesión bf — **ABIERTA 2026-09-18 (H.21 ejecutada)**)
| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 20.7 | **1** | CI ciego: `verify_ci_local.ps1` replica `ci.yml` paso a paso | **DONE** | **DONE** `d4de5d2` (2026-09-28), verificador CONFIRMADA: pin de ruff, ámbito de oxlint y paso `check:i18n` verificados por `grep` en los 3 ficheros; 6/6 pasos backend, 10/10 frontend; stubs SKIP e2e+android 2/2; sin fallo → §I |

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
| 23.1 | **1** | **Auditoría E2E por idioma**: cada pantalla, email, push, PDF/certificado,… | **DONE** | `c0a5af6` (2026-09-28). Pantallas: `ForgotPasswordPage`/`ResetPasswordPage` sin i18n, `/evidence` entero (34.12) — invisibles a la paridad de claves. Push: racha/duelo en inglés fijo — `push_service.localize()` nuevo. Tutor/PDF/certificado ya correctos → §I |
| 23.2 | **2** | **Landing y SEO por segmento**: `/es` y `/en` con copy nativo (no traducido), `hreflang` (existe), `sitemap` por idioma,… | | → §I (criterio archivado por 20.10) |
| 23.3 | **2** | **Tiendas, emails y soporte por idioma**: listings ES/EN en `store/`, plantillas de email por idioma (P.1) verificadas,… | | → §I (criterio archivado por 20.10) |
| 23.4 | **3** | **Segmento en el admin**: todas las métricas de 22.1 filtrables por idioma; cohortes ES vs. EN | **DONE** | **DONE**: `segment` param (all/es/en) added to `/metrics/reports` — all 12 admin endpoints now support language segmentation → `66925f8` |
| 23.5 | **1** | **Las dos guardias de i18n daban números falsos y la que cita el protocolo no existía**: `audit_i18n.py` buscaba… | **DONE** | **DONE** `d991fe4` (2026-09-19) → §I |

### 24. Interfaz que venda al verse — UI/UX + competencia en vivo + vídeo (sesión interactiva; **después** de 20-23; absorbe 17.6 y 19.8;…

> **Estado:** `ABIERTA 2026-09-24` (ADR-45/47). Las filas BLOCKED pasan a PARCIAL: hay commits `24.x` en `master` pero son maquetas con…
> **Modo:** rama + PR + preview de Cloudflare (`<rama>.whetzy.pages.dev`); el dueño revisa el preview antes de fusionar, no cada pantalla…
> **Modelo:** Sonnet para código (`frontend/src` es fichero de riesgo); Haiku para inventarios y verificación.
> **Evidencia común a toda fila:** captura fechada en `docs/screenshots/<fecha>/`, `npx tsc -b --force` + `npx vitest run` + `npm run…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 24.0 | **1** | **Investigación competitiva en vivo**: navegar el free tier de los 8… | **PARCIAL** | **PARCIAL** (2026-09-28): 21 capturas landing+precios de 7/8 en `COMPETENCIA.md` §A.2c (sin cuentas de terceros). Falta: onboarding/dashboard/gamificación (piden cuenta), Exercism (Turnstile), `decisiones-24.0.md` → §I |
| 24.1 | **1** | **Identidad visual**: tokens de diseño (color con hue propio, tipografía… | **PARCIAL** | **PARCIAL** (2026-09-28): 6/51 `.module.css` con hex literal (88,2 %, bajo 90 %) → 0/51 (100 %), token nuevo por caso (marca de lenguaje, editor, tarjeta Pro); `docs/design/identidad.md` escrito; guarda `tokens.noLiterals` mutada. Bug real de paso: enlace invisible sobre su propio fondo en `/evidence`, arreglado. Falta: aprobación del dueño (no la firmo yo) → §I |
| 24.2 | **1** | **Landing que vende** (`/es`, `/en`; absorbe 19.8 y 23.2): hero con el… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 24.3 | **1** | **Onboarding rediseñado**: 3 preguntas de segmento (`SEGMENTOS.md` §«Cómo… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 24.4 | **1** | **Dashboard con el motor visible**: mapa de dominio por skill (BKT como… | **PARCIAL** | **PARCIAL** (2026-09-28): Elo real visible — el nivel mostrado era XP; Territorio pinta la media de `elo_rating` de skills con intentos (dato del motor, ya llegaba sin usarse); sin intentos no se muestra nada (evita el 1500 de arranque inventado). 4 tests, mutado. Falta: fuente por número, vista por segmento → §I |
| 24.6 | **2** | **Gamificación original + wallet de créditos**: racha con identidad… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 24.7 | **2** | **Panel de certificación**: readiness por dominio (18.1), simulacros (comprables con créditos), certificado… | **DONE** | **DONE**: ReadinessScreen + MockExamScreen + CertificateScreen + CertificateCard + tests + API endpoints + i18n ES/EN → §I |
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

### 25. Expansión de contenido — subordinada a la serie 37 (ADR-46 sustituye a ADR-25; ADR-38)

> **Estado:** `ABIERTA 2026-09-24` — reabierta por ADR-46/47 (H.22 decidido por defecto: **no** CC BY-SA; OWASP se cita). **Ninguna fila…
> **Dependencias:** 37.0 DONE; corpus de la área descargado y verificado (37.1–37.3).
> **PRI:** 2 (detrás de 30 y de 37.0–37.3).
> **Modelo:** Haiku para generación de contenido (cada bloque = 1 worker, 1 commit verde). Sonnet solo si toca ficheros de riesgo.
> **Nota:** Esta serie no tiene fecha límite — es la expansión continua del catálogo. Se ejecuta en paralelo con la campaña de distribución…

| ID | PRI | Tarea | Estado | Criterio de aceptación | Deps |
|---|---|---|---|---|---|
| 25.0 | **3** | Infraestructura de generación: script `scripts/generate_track_content.py` que toma track_id + nivel + fuentes y produce… | | → §I (criterio archivado por 20.10) | |
| 25.1 | **3** | Completar tracks 1-3 (Python básico/intermedio/avanzado) a 100 cursos por nivel usando PSF docs + exercism/python +… | | → §I (criterio archivado por 20.10) | |
| 25.2 | **3** | Completar tracks 6-7 (IA/ML/LLMs) a 100 cursos usando ML-For-Beginners + HF course + fastai + openai/anthropic cookbooks… | | → §I (criterio archivado por 20.10) | |
| 25.3 | **3** | Completar tracks 4-5 (Ingeniería + Arquitectura) a 100 cursos usando system-design-primer + aosabook +… | | → §I (criterio archivado por 20.10) | |
| 25.4 | **3** | Completar tracks 12, 20, 21, 27 (SQL + Data Eng + DS + NoSQL) usando PostgreSQL docs + DuckDB + Kaggle Learn +… | | → §I (criterio archivado por 20.10) | |
| 25.5 | **3** | Completar tracks 13, 24, 25 (Ciberseguridad fundamentos + Pentest + Seguridad cloud) usando NIST + MITRE ATT&CK +… | | → §I (criterio archivado por 20.10) | |
| 25.6 | **3** | Completar tracks 8-11, 22-23 (AWS + Azure + GCP) usando AWS docs (cita) + Microsoft Learn CC BY + GCP docs CC BY | BLOCKED… | | |
| 25.7 | **3** | Completar tracks 14, 28 (Frontend JS + Backend FastAPI/Node) usando lydiahallie + Web-Dev-For-Beginners + freeCodeCamp ES… | | → §I (criterio archivado por 20.10) | |
| 25.8 | **3** | Completar tracks 15, 17, 26 (Linux + Redes + Git) usando exercism/bash + Peterson/Davie CC BY + github/docs | BLOCKED… | | |
| 25.9 | **3** | Completar tracks 16, 29, 30 (Algoritmos + QA + Agile) usando Erickson CC BY + pytest docs + Scrum Guide cita | BLOCKED… | | |
| 25.10 | **3** | Completar tracks 18, 19 (Docker/K8s + IaC/CI/CD) usando Kubernetes docs CC BY + Docker docs + actions/* | BLOCKED (37.0)… | | |
| 25.11 | **3** | Completar track 31 (Móvil) usando swift-book CC BY + android docs + flutter docs | BLOCKED (37.0) | track31 ≥ 900 Q,… | |
| 25.12 | **3** | Glosario máximo: ≥ 100 términos por track × 28 tracks = 2,800+ términos totales, ES y EN nativos | BLOCKED |… | |
| 25.14 | **3** | **track32 — Solana / Web3 developer** (ADR-38): 5 módulos × 4 skills, JS con `@solana/web3.js` en el Worker (18.3) +… | | → §I (criterio archivado por 20.10) | |
| 25.13 | **3** | Scorecard ADR-25: verificar que los 28 tracks pasan §7 quality gate (≥ 15 % exec donde aplica, ≥ 144 términos, BKT… | | → §I (criterio archivado por 20.10) | |

**H.22 — Decisión del dueño:** ¿Aceptar [H.LIC] para OWASP CheatSheets/WSTG/ASVS (CC BY-SA 4.0) en tracks de seguridad? Si sí: contenido…

### 26. Distribución masiva ES (ADR-23, ADR-27; spec `DISTRIBUCION.md`)

> **Estado:** `ABIERTA 2026-09-24` — 24.14 es DONE y H.23 queda decidido por defecto (ADR-47: sí). **La sesión redacta y construye todo;…
> **Dependencias:** 24.14 DONE. Ningún dato inventado en ningún activo (30.1/H.31).
> **PRI:** 3. **Modelo:** Haiku para contenido; Sonnet para copy de landing/emails.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 26.0 | **4** | Canal YouTube ES creado: banner, descripción, links, 3 videos demo subidos (grabados en 24.13); **cada vídeo con su código… | | → §I (criterio archivado por 20.10) |
| 26.1 | **4** | 5 artículos en Dev.to / Hashnode ES sobre el motor técnico (BKT, FSRS, gap de mercado) | TODO (redactar/construir;… | → §I (criterio archivado por 20.10) |
| 26.2 | **4** | PR en `EbookFoundation/free-programming-books` agregando Whetzy en sección Python ES | TODO (redactar/construir; publicar… | → §I (criterio archivado por 20.10) |
| 26.3 | **4** | Template de email para universidades LATAM + lista de 50 contactos | TODO (redactar/construir; publicar bajo cuenta nueva… | → §I (criterio archivado por 20.10) |
| 26.4 | **4** | Página de landing para segmento career-switcher ES (dentro de whetzy.com/es/carrera) | TODO (redactar/construir; publicar… | → §I (criterio archivado por 20.10) |
| 26.5 | **4** | Página de landing para segmento B2B ES (whetzy.com/es/empresas) | TODO (redactar/construir; publicar bajo cuenta nueva =… | → §I (criterio archivado por 20.10) |
| 26.6 | **4** | Show HN post en español (Hacker News): preparación + activos | TODO (redactar/construir; publicar bajo cuenta nueva =… | → §I (criterio archivado por 20.10) |
| 26.7 | **4** | Perfiles en comunidades ES: Python Argentina Discord, Dev En Español, LatamDevs | HUMAN-BLOCKED (H.23: perfiles… | |
| 26.8 | **4** | **Superteam LATAM (México, Argentina, Brasil) como canal** (ADR-38): presencia en sus Discord/eventos, 1 charla o taller… | | → §I (criterio archivado por 20.10) |
| 26.9 | **3** | **Blog `/blog` ES/EN** (SEO orgánico, `archive/SPEC_WEB.md:152`): Markdown en `content/blog/`, prerender en `vite build`… | | → §I (criterio archivado por 20.10) |
| 26.10 | **3** | **Newsletter** (`archive/EXECUTION_PLAN_25-29.md:87`): alta con doble opt-in vía Resend (H.30), ES o EN según usuario,… | | → §I (criterio archivado por 20.10) |

### 27. Distribución masiva EN (ADR-27; spec `DISTRIBUCION.md`)

> **Estado:** `ABIERTA 2026-09-24` (ADR-47). Misma regla que la 26: se redacta y construye todo; publicar bajo cuenta nueva = H.23.
> **Dependencias:** ninguna para redactar; 26.0 DONE antes de grabar vídeo EN.
> **PRI:** 3. **Modelo:** Haiku para contenido; Sonnet para copy.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 27.0 | **4** | Canal YouTube EN creado: banner, descripción, 3 videos EN (mismo contenido que 24.13 pero grabado en inglés nativo, no… | | → §I (criterio archivado por 20.10) |
| 27.1 | **4** | Show HN EN: "I built an adaptive Python→AI learning engine in Spanish because no one else did" | TODO (redactar/construir;… | → §I (criterio archivado por 20.10) |
| 27.2 | **4** | 5 artículos en Dev.to / freeCodeCamp News EN sobre motor técnico | TODO (redactar/construir; publicar = H.23) | 5… |
| 27.3 | **4** | PR en `jwasham/coding-interview-university` y `donnemartin/system-design-primer` READMEs | TODO (redactar/construir;… | → §I (criterio archivado por 20.10) |
| 27.4 | **4** | Product Hunt preparación: assets, lista de 100 upvoters confirmados, tagline | TODO (redactar/construir; publicar = H.23)… | → §I (criterio archivado por 20.10) |
| 27.5 | **4** | Product Hunt lanzamiento | HUMAN-BLOCKED (H.23) | Top 5 del día en categoría Education |
| 27.6 | **4** | Reddit strategy EN: 10 respuestas de valor en r/learnpython, r/cscareerquestions | HUMAN-BLOCKED (H.23: cuenta y karma… | |
| 27.7 | **4** | Landing page segmento career-switcher EN (whetzy.com/en/career) | TODO (redactar/construir; publicar = H.23) | Lighthouse… |
| 27.8 | **4** | Landing page segmento B2B EN (whetzy.com/en/enterprise) | TODO (redactar/construir; publicar = H.23) | Demo request form… |
| 27.9 | **4** | **Superteam global / Solana developer communities EN** (ADR-38): Solana Stack Exchange y Discord oficial con respuestas de… | | → §I (criterio archivado por 20.10) |
| 27.10 | **3** | **Comparativa honesta frente a Coursera/Udemy** (`DECISIONS.md` ADR-24, sin fila hasta hoy): página `/en/compare` y… | | → §I (criterio archivado por 20.10) |

### 28. Marketplace de instructores (ADR-29; spec `MARKETPLACE.md`)

> **Estado:** `ABIERTA 2026-09-24` (ADR-47). El código de 28.0–28.7 ya está en `master` (migración `u1v2w3x4y5z6_admin_tables`,…
> **Dependencias:** 22.1 PARCIAL (basta), 22.3 DONE. Ver spec completo en `docs/MARKETPLACE.md`.
> **PRI:** 3. **Modelo:** Sonnet (toca DB schema y auth — ficheros de riesgo).

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 28.0 | **4** | Schema DB: `instructor_profiles`, `marketplace_courses`,… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 28.1 | **4** | API: CRUD cursos instructor, upload contenido JSON, preview; **código de… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 28.2 | **4** | Quality gate pipeline para instructores: `scripts/instructor_quality_gate.py` corriendo en upload | **DONE** — `scripts/instructor_quality_gate.py` valida preguntas/skill≥15, ejecutables≥15%, glosario≥36/track, lecciones con contenido, licencias válidas | |
| 28.3 | **4** | Panel instructor — React: dashboard revenue, cursos, métricas por curso | **PARCIAL** — Verificado 2026-09-25 contra el… | → §I (criterio archivado por 20.10) |
| 28.4 | **4** | Marketplace público: catálogo con filtros, ratings, preview de primera lección | **PARCIAL** — Verificado 2026-09-25… | → §I (criterio archivado por 20.10) |
| 28.5 | **4** | Checkout cursos de instructor: Stripe/Paddle, split automático 70/30 | **PARCIAL** — Verificado 2026-09-25 contra el… | → §I (criterio archivado por 20.10) |
| 28.7 | **4** | Payouts mensuales: job día 15 de cada mes, mínimo $50; **rail elegido por… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 28.8 | **3** | **UI del marketplace conectada**: `MarketplaceScreen` e `InstructorScreen` (hoy maquetas, 24.10/24.11) contra… | | → §I (criterio archivado por 20.10) |
| 28.9 | **3** | **Kit de reclutamiento de instructores** (`MARKETPLACE.md:161-167`: 5 fundadores → 20 → 50+): oferta escrita ES/EN (70 %,… | **DONE** — `content/legal/instructor_recruitment_kit_{es,en}.md`: oferta 70/30, badge fundador, visibilidad prioritaria, requisitos de calidad (puerta automática), hoja de ruta 3 fases, proceso de aplicación | |

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
| 29.3 | **2** | **Referidos**: código permanente por usuario, enlace `/r/<código>` que fija… | **DONE** | **DONE** `89eb7a7`: modelo+endpoint+frontend /r/ ruta+servicio con ladder de créditos → §I |
| 29.6 | **2** | **Admin** (en 22.1): economía (emitidos/gastados/caducados, ratio sumidero/grifo, alerta de inflación), referidos… | **DONE** | **DONE**: 3 endpoints — `/economy/credits` con summary (emitted/spent/expired, sink_source_ratio, inflation_alert, by_reason) + rows; `/economy/referrals`; `/economy/k-factor` → §I |
| 29.7 | **3** | **Reactivación automática**: job (cola 22.6) que a los 14 días de inactividad emite código de 72 h y envía email **ES o EN… | **DONE** — `reactivation_check` job handler: consulta `User.last_active < 14d`, genera código 72h vía `PromoCodeService`, envía email ES/EN con plantilla `reactivation` | |
| 29.8 | **3** | **UI**: wallet (saldo, lotes que caducan, historial), escalera de referidos con código y enlace, canje de códigos **solo… | **DONE** | **DONE**: WalletScreen con balance card, earn/spend lists, referral code + clipboard, promo redeem form; economy API methods; 22 i18n keys ES/EN; lazy route + profile nav → `66925f8` |
| 29.9 | **3** | **USDC como rail** (ADR-36): si H.19 = Stripe → activar *Pay with Crypto* en **test mode** y documentar en 7.2; payouts de… | | → §I (criterio archivado por 20.10) |


### 30. Integridad del despliegue — incidente de login del 2026-09-24 (PRI 0)

> **Estado:** `ABIERTA`. 30.0/30.7/30.8 DONE en producción (archivo §N). **30.9 solo en rama (PR #34): hasta que se fusione, un login válido en producción vuelve a la landing.**
> **PRI:** 0. **Origen:** captura del dueño — `POST whetzy.com/auth/login` → **405**, pantalla «Incorrect email or password».
> **Invariante de la serie:** un deploy del frontend no está hecho hasta que `node scripts/check-deployed.mjs` sale PASS contra…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 30.2 | **1** | **Se puede publicar sin puerta.** `ba686fc`, `50e73ea`, `46789fa`, `f8719b1`, `2efdfb7` y `8a0dce0` entraron en `master`… | | → §I (criterio archivado por 20.10) |
| 30.4 | **1** | **`npm run build` estaba en rojo y nadie lo vio**: el prerender buscaba… | **DONE** | `be07294`, verificador CONFIRMADA: Node 22 tiene `navigator.language` real (Node 20 no); `detectLanguage()` fuerza `es` sin `window`. Mutación en rojo/verde. `check-prerender` solo en `ci.yml` (no corre) → `ci_local.sh` → §I |
| 30.5 | **2** | El script `build` ya no corre `tsc -b` (lo quitó `8a0dce0`,… | **PARCIAL** | **PARCIAL** `8a0dce0` (2026-09-24) → §I |
| 30.9 | **0** | Login válido devolvía a la landing (cookie cross-site + host-only; `logout()` no llamaba a `/auth/logout`) → STATUS.md | **DONE** | `395e8a1` (2026-09-27), verificador CONFIRMADA: 42 backend + 251 frontend limpios. Navegador real: `master` 0 cookies, esta rama `/auth/me` 200. Safari (ITP) sin probar → §I |

### 31. Fuente única de cifras, staging y migraciones con datos (del plan del 2026-09-24, cuyo fichero no está en el repo: estas filas son…

> **Estado:** `TODO`. **PRI:** 1. **Por qué:** los documentos vivos dan cifras distintas del mismo banco (6.233 frente a 6.305 preguntas)…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 31.1 | **1** | Staging: un preview de Cloudflare Pages y un servicio de Railway de staging; `master` solo por PR verde | HUMAN-BLOCKED… | |
| 31.2 | **2** | Migración con datos: fixture de base en la revisión anterior, `upgrade head`,… | **DONE** | **DONE** `d3290b8` → §I |
| 31.3 | **2** | Smoke post-deploy de backend: login con cuenta QA, `POST /quiz/start`, `GET`… | **DONE** | **DONE** `cf2fc58` → §I |

### 32. Motor demostrable — calibración y evidencia de aprendizaje (del plan del 2026-09-24; ídem)

> **Estado:** `TODO` (32.2 `BLOCKED` por H.10). **PRI:** 2. **Relación:** complementa 11.8 y 14.8; no las sustituye.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 32.2 | **3** | A/B BKT contra DKT con el framework 24.14 (asignación estable por usuario) | BLOCKED (H.10) | DKT se adopta solo si AUC ≥… |
| 32.3 | **2** | «¿Por qué esta pregunta?»: el scheduler devuelve sus razones (dominio, repaso… | **DONE** | **DONE** `d92e164` → §I |
| 32.4 | **2** | **La lección bloquea el quiz** (decisión del dueño 2026-09-27, tras el hallazgo de que `TracksScreen.tsx` no lo exigía) | **DONE** | **DONE** `b860e83`, verificador CONFIRMADA en 2ª ronda: `LessonCompletion` + `lesson_gate.py` + filtro en `quiz._candidate_skill_ids`. **Post-DONE `e2f0d45`:** 5 tests ajenos rotos por el gate, arreglados → STATUS.md |

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
| 34.11 | **1** | **Hallazgos de comportamiento vistos al rediseñar (no son estilo):** (a)… | **DONE** | `be2e83b` (2026-09-28), verificador CONFIRMADA: (a-d) siguen bien; texto de privacidad de segmento añadido (`d3453d1`); (b) sin test → añadido y mutado, primer verificador REFUTADA solo por eso, cerrado → §I |
| 34.12 | **2** | Plural e idioma en la UI: `HomeScreen.tsx` sin `count`, `/evidence` en inglés fijo | **DONE** | `772fe5d` (2026-09-28), verificador CONFIRMADA: plurales `_one`/`_other`, `/evidence` traducida (~60 cadenas), `docTitle.evidence` añadido. 8 tests, mutados; capturas entregadas al dueño → §I |
| 34.1 | **0** | **Devolver el estilo a las 13 pantallas rotas**: por fichero,… | **PARCIAL** | **PARCIAL** `d7f6711`: e2e real 44/45 verdes; 2 bugs hallados y arreglados → STATUS.md. Capturas antes (`03220e4`, Auth invisible)/después + 9 pantallas más entregadas al dueño y comentadas en el PR (sin subida de imagen vía API); falta insertarlas de verdad en el PR → §I |
| 34.2 | **1** | **Un solo juego de tokens**: una sola fuente (`src/theme/tokens.css` o… | **PARCIAL** | **PARCIAL** (2026-09-28): 0 `var(--x, #hex)` en `src/` (era 1, `--color-cyan` no existía en ningún fichero, caía al respaldo) → `var(--color-primary)` real. Guarda `tokens.noHexFallback` mutada. Falta: modo claro por el dueño → §I |
| 34.3 | **1** | **Componentes base** al estilo de la landing: `Button`, `Card`, `Badge`, `Modal`,… | **PARCIAL** | **PARCIAL** → §I |
| 34.4 | **1** | **Primer uso**: Auth (login, registro, OAuth, olvido/reset), Onboarding,… | **PARCIAL** | **PARCIAL** `d11db88` → §I |
| 34.5 | **1** | **Aprendizaje**: Home, Tracks, Lesson y Quiz (con Monaco, WhyButton, GlossaryText, TermCard) | **PARCIAL** — pantallas del… | → §I (criterio archivado por 20.10) |
| 34.6 | **2** | **Progreso y social**: Profile, Stats, League, Duel, Readiness, MockExam,… | **PARCIAL** | **PARCIAL** `d11db88` → §I |
| 34.7 | **2** | **Resto**: Admin, Instructor, Marketplace, Legal, Evidence, DeleteAccount | **PARCIAL** — pantallas del bloque revisadas… | → §I (criterio archivado por 20.10) |
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
| 35.8 | **2** | **Cada deploy de Railway deja ~1 min de 502/503.** Medido 2026-09-24: tras los pushes `a6a5a91` y `f2ea9cb`, `/health` dio… | **DONE** | **DONE**: railway.toml healthcheckPath=/health 120s + lifespan shutdown handler con close_db() → §I |
| 35.9 | **2** | **El nivel 2 de la puerta (`ci_local.sh`) corre sobre el árbol… | **PARCIAL** | **PARCIAL** `a021e92` (2026-09-24) → §I |


### 37. Catálogo total — todos los tracks de la industria, ≥ 50 cursos por track, sobre un corpus abierto (ADR-46; abierta 2026-09-24)

> **Estado:** `ABIERTA`. **PRI:** 1 (detrás de la serie 30). **Modelo:** Haiku para descarga, inventario, limpieza y autoría por fichero;…
> **Orden obligatorio:** 37.0 → 37.1 → 37.2 → 37.3 → bloques. **Nadie escribe una pregunta nueva hasta que 37.0 esté DONE**: el intento del…
> **Corpus (ADR-46 §4-5):** `corpus/` está en `.gitignore`. Se descarga con `git clone --depth 1`, dumps oficiales y **torrents solo cuando…
> **Unidad:** curso = módulo = 4 skills · 60 Q · 4 lecciones · ≥ 8 términos · ≥ 15 % ejecutable donde aplique. Un bloque = un PR verde con…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 37.1 | **1** | **Inventario de la industria vs catálogo**: contrastar… | **PARCIAL** | **PARCIAL** (2026-09-28): Microsoft Learn y Google Cloud, antes JS sin leer, ya capturados (Playwright, TLS del sandbox arreglado esta sesión): 74 certificaciones MS + catálogo GCP completo, `CATALOGO_MAESTRO.md` §2.0.1. Ninguna abre track nuevo. Falta: re-auditar las 19 lecciones cortas de track08 (no verificado esta sesión) → §I |
| 37.4 | **2** | **Descarga y verificación del corpus por área** (una subfila por área en… | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| 37.5 | **2** | **Generador desde corpus**: `scripts/generate_track_content.py` (absorbe 25.0) toma track + módulo + fragmentos del corpus… | | → §I (criterio archivado por 20.10) |
| 37.6 | **2** | **Bloques de tracks existentes a 50 cursos** — orden: track01-03 → 12 → 06-07 → 04-05 → 13/24/25 (reescribiendo las 800… | | → §I (criterio archivado por 20.10) |
| 37.7 | **2** | **Tracks del mapa sin construir** (18-23, 26-27, 29-32) al molde mínimo primero (20 skills · 300 Q) y luego a 50 cursos —… | | → §I (criterio archivado por 20.10) |
| 37.8 | **2** | **Tracks nuevos de §2.0** (Java/JVM, C#/.NET, Go, Rust, C/C++ y sistemas, TypeScript, SRE/observabilidad, MLOps,… | | → §I (criterio archivado por 20.10) |
| 37.9 | **2** | **Glosario ≥ 400 términos por track**, ES y EN nativos (absorbe 25.12) | BLOCKED (37.6) | `check_docs.py`: 0 términos sin… |
| 37.10 | **2** | **Certificaciones: blueprints de las 55 del catálogo §3** con simulacro por dominio, pesos verificados contra la guía… | | → §I (criterio archivado por 20.10) |
| 37.11 | **3** | **Proyectos multi-paso**: 10 por track ejecutable (hoy 0; catálogo §1) | BLOCKED (37.6) | Cada proyecto con tests de… |
| 37.12 | **3** | **Monitoreo trimestral de competencia** (`CATALOGO_MAESTRO.md` §11.4 apuntaba a una fila que no existía; complementa… | | → §I (criterio archivado por 20.10) |
| 37.13 | **3** | **Scorecard ADR-46** (absorbe 25.13): tracks × cursos × 37.0 verde; re-puntuación de Contenido en el teardown con… | | → §I (criterio archivado por 20.10) |
| 37.14 | **1** | **track13 (ciberseguridad) tiene enunciados repetidos: 87,9 %… | **DONE** | **DONE** `fbf9baf` (2026-09-25) → §I |
| 37.15 | **1** | **Fuentes sin indexar:** 3.906 de 6.305 preguntas (62 %) no llevan URL en… | **PARCIAL** | **PARCIAL** (2026-09-25); 2026-09-28: `check_content_sources.py` 58→0 URLs muertas (30 ficheros, MongoDB/K8s/AWS/Redis/MDN/SQLite/Docker/w3schools/sqlshack/tcpdump/cisco/wifi/NIST); `index.json` NIST 800-53 también corregido (guardia de diversidad). Indexado sigue en 62 %, sin tocar → §I |
| 37.16 | **1** | **La correcta es la opción más larga.** Medido 2026-09-25 sobre… | **DONE** | **DONE** `46764ff` (2026-09-26): 8 tracks restantes (02-04, 06, 08, 10, 12, 17) corregidos; todos ≤22 %. Banco PASS, diversidad PASS, content 38062 passed → §I |
| 37.17 | **1** | **Inglés dentro del español y ejecutables que aceptan atajos** (medido 2026-09-26 con grep y `scripts/video/solve_blank.py`, que prueba candidatos contra la salida esperada): 282 enunciados ES en 9 ficheros empiezan «Completa el blank»; `track11_aws_aif_c01/mod01.json:715` dice «directional»; la pregunta ES de EC2 con 100.000 conexiones TCP tiene las opciones en inglés. Respuestas equivocadas dan la salida esperada (Python local): en `q060104ex010` (varianza) `median_low` y `mode` imprimen `4` igual que `pvariance`; en `q010105ex001` `eval` imprime lo mismo que `int`. Si la corrección solo compara la salida, las acepta; sin probar en la app (el sandbox podría bloquear `eval`) | **TODO** | 0 «blank» en `question_es`; una guarda que falle con palabras EN frecuentes en campos `_es`; datos de los ejecutables que distingan la función pedida (varianza ≠ mediana ≠ moda); `eval`/`exec` rechazados en el sandbox o en la corrección, con test |

### 38. Negocio medible — KPIs, pilotos B2B, instructores, afiliados (ADR-47; abierta 2026-09-24)

> **Estado:** `ABIERTA`. **PRI:** 2. Todo lo que aquí exige hablar con personas o crear cuentas lo prepara la sesión y lo ejecuta el dueño…

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 38.1 | **2** | **Precios: una sola fuente = ADR-41 (dueño)**: Pro 14,99 $ · Pro Max 19,99 $ ·… | **DONE** | **DONE** `cf2fc58` → §I |
| 38.2 | **2** | **Oferta de 3 pilotos B2B gratuitos** (ADR-22): documento ES/EN (qué damos, qué pedimos: testimonio y datos de uso, 90… | **DONE** — `content/legal/b2b_pilot_offer_{es,en}.md`: 3 pilotos 90d, 25 asientos Pro Max, a cambio de datos agregados + testimonio + llamada cierre; post-piloto $99/asiento/año mín 10 | |
| 38.3 | **2** | **Dossier de afiliación** Python Institute y CompTIA (`archive/whetzy_estrategia_definitiva_v3.md:392`): condiciones,… | **DONE** — `content/legal/affiliation_dossier_{es,en}.md`: certs relevantes por proveedor, programa de afiliados, pasos para aplicar, modelo de ingresos estimado, integración técnica y acciones inmediatas | |
| 38.5 | **3** | **Página `/evidence` como única prueba social** (19.8, 30.1): cifras del banco y del motor calculadas en build, cero… | **DONE** | **DONE**: EvidenceScreen.tsx + CSS module + ruta registrada en App.tsx → §I |
| 38.6 | **2** | **Pro Max = tutor IA ilimitado; Pro con cupo diario** (ADR-49). `POST`… | **DONE** | **DONE** `843015e` (2026-09-25) → §I |
| 38.7 | **2** | **Certificación a 39,99 $ de pago único** (ADR-49). Hoy los tracks… | **DONE** | **DONE** `843015e` (2026-09-25) → §I |

### 39. Noche 2026-09-26 — incidente de arranque, deuda de calidad y aprobación en bloque (ADR-50)

> **Estado:** `ABIERTA`. Viene del prompt de control total v5 y de `EVALUACION_COMPLETA_WHETZY.md`. Lo que exige cuenta o dinero va a §3.

| ID | PRI | Tarea | Estado | Criterio de aceptación |
|---|---|---|---|---|
| 39.0 | **0** | **Producción caída 09:35–10:48 UTC tras `ec97405`**: `content_loader`… | DONE | → §M |
| 39.1 | **0** | Coletillas de relleno en opciones incorrectas de tracks 26/28/29/30 y `mod2903` rotado | DONE | 0 coletillas por grep en 26/28/29/30; correcta más larga 15 / 11,7 / 23,7 / 33 % (37.16 ≤ 40 %); `test_no_new_file_is_a_pure_rotation` verde. Revisión adversaria de las 1.200: 7 + 10 + 16 + 4 arreglos; el reescritor movió claves en 28, 29 y todo `mod3002` (52, reparado por similitud con la clave original y revisado). Trinquete `test_no_filler_options.py` con mutación en rojo (2026-09-26) |
| 39.2 | **1** | Fuentes inferidas en 146 lecciones normalizadas en #28 | **DONE** | De las 146, 13 duplicadas se borraron en #28; las 133 vivas (18, 19, 21, 23, 27, 44-46) reescritas con la fuente oficial concreta; `check_urls`: 126 URL distintas, todas 200. Verificador Sonnet de 39.3: una fuente parcial (`lesson230101`) → `machine-resource` |
| 39.3 | **1** | `tests/content` en verde (1.254 fallos en master, 792 tras #28) | **DONE** | 2026-09-26 noche: 440 (medido 18:00 UTC; 21 y 23 **no** pasaban, contra lo anotado) → **0**: `70270 passed, 1 skipped, 21 xfailed`. 185 lecciones de 14, 21, 22, 23 y 41-46, un commit por track, escritor/revisor/corrector Sonnet, `scripts/content_qa`, lectura propia (3 errores técnicos corregidos a mano: /24 GCP = 252, Hyperscale 128 TB, NSG). `test_lessons.py` sin cambios frente a `master`. Verificador adversario Sonnet sobre 20 lecciones elegidas por hash: CONFIRMADA |
| 39.4 | **2** | `content_quota` detrás de flag (ADR-50a) | **DONE** | `fecab20`: `FREE_DAILY_QUOTA_ENABLED=false`; 30 preguntas y 5 lecciones/día UTC; repaso/placement/examen exentos; Pro/Pro Max/Creador/dueño/admin sin cupo; 429 propio; migración `20260927_lesson_views`. 15 tests, 4 mutaciones en rojo. Verificador: DUDOSA por huecos, decisiones en ADR-51 b-d. Texto de UI: 39.34 |
| 39.5 | **2** | Gamification auditada de punta a punta | **DONE** | `9b016a9`: «Perfeccionista» no se concedía nunca (criterio sin estadística) y con `autoflush=False` llegaba una respuesta tarde; tests en rojo antes y verdes después. `e2e/gamification.spec.ts` en verde en local (1 passed) con 3 capturas (Inicio con racha 1 y 270 XP, Liga, Perfil con la insignia). El helper e2e no marcaba la casilla de 13+ años: todos los specs con registro estaban rotos. Verificador: «e2e no ejecutado» refutado (capturas en `E2E_SHOTS_DIR`); racha acumulada y ascensos de liga fuera del criterio |
| 39.6 | **2** | `audit_ai_traces.py` | DONE | → §M |
| 39.7 | **2** | Detector de originalidad / casi-duplicados | DONE | → §M |
| 39.27 | **2** | Reescribir las 12 parejas casi-duplicadas anotadas en `KNOWN` (track01 ×3, track09 ×5, track41 ×4) | TODO | Cada pareja arreglada se quita de `KNOWN`; el test sigue verde |
| 39.28 | **0** | Segunda familia de coletillas («como concepto principal» 982, «sin excepciones ni variantes» 296, «de manera exclusiva y permanente» 238 y sus versiones EN) en tracks 18-23, 27, 41-43 | **DONE** | **Los 10 tracks del alcance en 0** (`7912cff`/`68df5ab`, 2026-09-27, cierran 18-23/27; 41-43 ya lo estaban). 23 y 27 necesitaron un segundo pase por la guarda de «correcta más larga» al *aggregate* (23/27 techo 40 %), arreglado alargando la opción incorrecta más corta sin tocar la correcta. `question_diversity`/`check_question_bank`/`check_source_licenses` PASS; `tests/content` 70.277 passed → 39.37 |
| 39.29 | **0** | 1.404 explicaciones de plantilla en track41/42/44-46/23 | DONE | `audit_ai_traces.py`: 0 en el banco vivo. Autor+revisión Sonnet por fichero, solo explicaciones. De paso: V/F track42 al azar (153 corregidas), 13 GKE track23 reescritas. Fuentes verificadas: NIST CSF 2.0, Azure Analysis Services (learn.microsoft.com) |
| 39.30 | **1** | Datos personales en el contenido: `l260101` enseñaba el nombre y correo del dueño | DONE | → §M |
| 39.31 | **2** | `user_meets_tier` no mira `subscription_expires_at` | **DONE** | `749e07f`: peor de lo pensado — `customer.subscription.deleted` limpia `is_premium` pero nunca resetea `subscription_tier`, así que una cancelación explícita también mantenía el tier para siempre. Vencido → «free» (comparación aware/UTC, `None` = sin vencimiento). Verificador adversario **CONFIRMADA**: mutación (comentar el chequeo) puso 3 tests en rojo, restaurado verde; 14 tests propios + 72 de entitlements/tutor_quota/content_quota/quiz; suite entera 1303 passed |
| 39.32 | **3** | `test_rag_self_retrieval` tarda ~28 min (cuadrático en el banco) | TODO | Muestra fija o índice invertido en el test; la suite backend baja de ~37 min a < 10 sin perder el listón del 95 % |
| 39.33 | **1** | Claves sospechosas previas: la explicación se parece más a otra opción (`check_expl_key`: 22 en `mod2201`…, 24 en track41) | **PARCIAL** | 41 claves falsas corregidas (3 individuales + 38 de un patrón sistemático en `mod4301`: variantes parafraseadas con `correct_index` reasignado al azar, agrupando por `(options_en, explanation_en)` idéntico — 0 grupos inconsistentes tras el arreglo). Rebalanceo de posición + 4 casi-duplicadas reescritas. `check_expl_key` sigue con ~495 sospechosas de 521: muestreadas las 42 de señal más fuerte, el resto es mayormente falso positivo (opciones cortas/simbólicas sin solapamiento léxico). TODO: resto de tracks sin muestrear |
| 39.34 | **2** | Texto de UI del cupo Free (ES/EN) antes de encender `FREE_DAILY_QUOTA_ENABLED` | **DONE** | `e754b50`: `api.ts` descartaba el `detail` del 429 → «HTTP 429» genérico; `ApiError.detail`+`isQuotaError()` nuevos, Quiz/Lección muestran límite y hora de reinicio. Verificador CONFIRMADA: 16 tests mutados, tsc/oxlint limpios → STATUS.md |
| 39.35 | **0** | El limitador de peticiones de producción fallaba en abierto:… | DONE | → §M. **Post-DONE `95cdfbf`, verificador CONFIRMADA**: `except` solo cazaba `redis.RedisError`, dejaba pasar `RuntimeError`/`OSError` sin caer a memoria (mismo fallo de la fila) — visto como 204 tests rotos en la suite entera, resueltos a 0 tras el arreglo |
| 39.36 | **1** | `options_en` escritas en español en track21 (194 preguntas) y track44-46 (46, 33, 49) | **DONE** | 295 preguntas traducidas por Sonnet, solo `options_en`. Verificador **CONFIRMADA**: recuento en vivo = 0; `check_question_bank`/`question_diversity`/`test_en_options_language` PASS; `correct_index` intacto; `tests/content` 70.277 passed |
| 39.37 | **0** | **Relleno de generador en producción**: 180 preguntas de track20 `mod2003`-`mod2005` y 209 de track21 `mod2102`-`mod2105` con explicación «Explicación para ¿…?» y enunciados telegráficos; una clave falsa ya corregida (`q210502007`, PCA) | **DONE** | 389/389 (180+209; Sonnet, ADR-52 tras piloto Haiku fallido) → detalle en STATUS.md. Verificador 2ª ronda CONFIRMADA (1ª REFUTADA por un «409» mío sin sumar); `tests/content` 70.277 passed |
| 39.38 | **0** | Dos claves falsas de Bicep en track22 (`q220503008`: «using» no… | DONE | → §M |
| 39.8 | **1** | Cerrar el índice de fuentes (37.15) | TODO | 0 % sin indexar o lista exacta de las imposibles |
| 39.9 | **2** | Explicaciones de < 2 frases en tracks 13, 15, 16, 17 | TODO | 2–4 frases correctas, adversario |
| 39.10 | **3** | Mapa de tracks con rutas y recomendación | TODO | vitest + e2e, ES/EN, a11y |
| 39.11 | **2** | Límite de gasto de Groq por usuario y global | DONE | → §M |
| 39.12 | **3** | LLM de respaldo (ADR-50f) | DONE | → §M |
| 39.13 | **3** | Emails de re-enganche (ADR-50g) | TODO | Flag apagado, baja en un clic, tests |
| 39.14 | **3** | Plantilla de lección con formato (ADR-50d) | TODO | Sin tocar contenido; test y captura |
| 39.15 | **1** | Fichero `LICENSE` (ADR-50e) | DONE | → §M |
| 39.25 | **1** | **MLA-C01 deja de ofrecerse en inglés el 28-09-2026**; MLA-C02 en beta desde el 29-09-2026 (código beta ME1-C02) — aws.amazon.com, leído 2026-09-26 | TODO | track43 migrado al blueprint MLA-C02 cuando AWS publique la guía; mientras, el nombre lo avisa |
| 39.26 | **2** | **Security+ V8 hacia el 17-11-2026** (comptia.org, leído 2026-09-26) | TODO | track42 revisado contra el temario V8 al publicarse |
| 39.24 | **1** | **AI-900 retirado por Microsoft el 30-06-2026**; la certificación Azure AI Fundamentals exige ahora **AI-901** (Conceptos 40–45 %, Microsoft Foundry 55–60 %, requiere Python) | TODO | track45 migrado al blueprint AI-901 (dominios, preguntas, lecciones); hasta entonces el nombre del track lo avisa |
| 39.18 | **1** | vitest: 4 fallos (`StatusPage` `/api/v1` relativo, `common.back`,… | DONE | → §M |
| 39.20 | **2** | PostHog en el frontend (ADR-50j) | **DECIDIDO: no** | La analítica ya es propia (`analytics_events` + embudo admin); PostHog en el navegador rompería la promesa de la landing y la CSP (ADR-50j revisada) |
| 39.21 | **2** | Sentry en el frontend (ADR-50k) | **DECIDIDO: no** | Solo backend; privacidad y DPA ES/EN actualizados: Sentry activo desde 2026-09-26, UE, sin PII |
| 39.22 | **2** | Backups: `backup_db.sh` + `restore_check.sh` + runbook | DONE | → §M |
| 39.23 | **1** | H.30 honesto: sin proveedor, 503 `email_not_configured` | DONE | → §M |

## 3. Cola HUMAN-BLOCKED

> → `docs/archive/LEDGER_HISTORY.md` §J

| H.16 | **DECIDIDA** (ADR-50p) — dueño: proteger `master` (PR obligatorio) en GitHub → Branches; staging (31.1) aprobado, alta con coste por el dueño |
| H.15 | **RESUELTA** (ADR-50n) — proxy a `127.0.0.1:8000` + guarda `pretest:e2e` |
| H.12 | PRI 0 de seguridad — rotar la `GROQ_API_KEY`. Estuvo commite… |
| H.13 | PRI 0 — Actions sin runner (facturación). **Decidido** (ADR-50o): dueño pone spending limit $0 en GitHub → Billing |
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
| H.30 | PRI 0 — correo: **decidido Resend** (ADR-50l). Dueño: cuenta en resend.com + `RESEND_API_KEY` en Railway (RUNBOOK «Correo»). La pantalla ya no miente (`bb59562`) |
| H.31 | **RESUELTA** (ADR-50m) — landing servida 2026-09-26 sin testimonios ni «1.2M» |
| H.32 | **2** | H.32 | **RESUELTA** | **RESUELTA** `e40ba75` (2026-09-24) → §I |
| H.33 | **RESUELTA 2026-09-26** — log Railway `b64e2a9a`/`f097361c`: `[owner] unchanged: admin@whetzy.com` (falta solo login `/admin` de 30.8) |
| H.34 | **RESUELTA 2026-09-26** — conector Railway activo; permisos en `CONECTORES.md` |
| H.35 | **2** | H.35 | **PARCIAL** | **PARCIAL** (2026-09-25) → §I |
| H.38 | Afiliación con Python Institute y CompTIA (38.3) |
| H.39 | 3 pilotos B2B gratuitos (38.2, ADR-22) |
| H.40 | Reclutar 5 instructores fundadores (28.9) |
| H.41 | **RESUELTA 2026-09-26** (aprobación en bloque, ADR-50k) — proyecto Sentry `whetzy-backend` + `SENTRY_DSN` en Railway; deploy `f097361c`: `Sentry initialised (env=production)` |
| H.42 | **DECIDIDA 2026-09-26** (ADR-50j): analítica = PostHog; Mixpanel no se instrumenta |
| H.43 | Reconectar Hugging Face en claude.ai (token OAuth caducó 2026-09-26 19:09 UTC) |
| H.44 | Terminar o quitar Firecrawl, Amplitude, Mailchimp y Lusha (a medio conectar) |
| H.45 | Conectar redes (X, LinkedIn…) en Metricool/Typefully para que la distribución deje de ser solo borradores |
| H.46 | ¿Monitor de uptime de Sentry para `/health`? (puede consumir cuota de pago) |
| H.48 | Clave de API de Anthropic con gasto para un pipeline por **Batch API** de rellenos con Haiku 4.5 (ADR-52); hoy ningún código del repo llama a la API | Dueño |
| H.47 | ¿Mantener el correo personal del dueño como contacto en la página pública `/evidence` (`EvidenceScreen.tsx:340`)? Por defecto (ADR-47) se deja y se propone un alias tipo `support@whetzy.com` | Dueño |

## 5. Bitácora de decisiones

> Decisiones archivadas en `docs/archive/LEDGER_HISTORY.md` §J.
> ADRs formales: `docs/DECISIONS.md`.

---

## 6. Cadena de sesiones

> → `docs/archive/LEDGER_HISTORY.md` §G
