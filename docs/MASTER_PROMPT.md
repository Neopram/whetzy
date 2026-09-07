# NEURIUM — Prompt Maestro de Ejecución: 8 Fases al 100%

> **Ejecutor:** Opus 4.8 · **Subagentes:** Haiku 4.5 (volumen mecánico) + Sonnet 4.6 (implementación)
> **Restricción #1:** gastar el mínimo de tokens posible.
> **Restricción #2 (la más importante):** el contenido debe ser de **calidad máxima**, redactado
> nativamente en ES y EN desde fuentes canónicas actualizadas — **nunca traducción automática**.

---

## 0. REGLAS DE EJECUCIÓN (token economy — obligatorias)

1. **No re-explores.** `docs/STATUS.md` es la verdad del estado actual. No vuelvas a leer archivos que ya
   están en contexto ni re-derives lo ya conocido.
2. **Routing de modelos** (obligatorio, no negociable):

   | Modelo | Úsalo para | NO lo uses para |
   |---|---|---|
   | **Haiku 4.5** | Generar JSON de preguntas desde un brief de fuente; extraer términos de glosario; boilerplate de tests; CSS repetitivo; claves i18n; scripts de iconos | Decisiones de arquitectura; revisión técnica de exactitud |
   | **Sonnet 4.6** | Implementar pantallas; servicios; wiring de integración; Terraform/K8s/Helm; pipelines CI; documentación | Diseño del motor adaptativo; revisión de seguridad |
   | **Opus (tú)** | Motor/arquitectura; revisión de exactitud técnica del contenido; seguridad; scorecard final | Todo lo que un subagente más barato pueda hacer |

3. **Briefs autocontenidos.** Cada subagente arranca en frío: dale rutas exactas, esquema JSON exacto,
   ejemplos, y criterio de aceptación. Nunca "mira el repo y averigua".
4. **Verificación más barata primero:** `tsc -b` → `pytest` → `curl` → y solo si es UI, navegador.
   Un screenshot cuesta ~10× un curl.
5. **Batch.** Agrupa escrituras independientes en un mismo turno. No hagas ida y vuelta por archivo.
6. **Gate por fase:** construir → verificar → actualizar `docs/STATUS.md` → commit. No avances sin verificar.
7. **Nunca declares "hecho" sin evidencia.** Si no lo verificaste, dilo.

---

## 1. ESTADO ACTUAL (no lo re-descubras)

**Ya funciona y está verificado:** rebrand Neurium (azul cielo `--le-brand:#1CB0F6`, light por defecto vía
`src/theme.ts`); registro obligatorio email/manual + JWT con refresh; quiz adaptativo real
(Elo+BKT+FSRS+Thompson persistiendo); 6 pantallas con datos 100% reales; 180 preguntas/7 tracks;
gamificación (5 ligas, 4 misiones, 8 badges con auto-award); tutor `/tutor/explain` (Groq swappable +
fallback grounded); ASVS-5.0-L2 headers + rate limit; Docker Compose + CI + README.

**Gotchas del entorno (no los redescubras, cuestan 30 min cada uno):**
- `python -m venv` **falla** en rutas con espacios → crea el venv en un path sin espacios.
- SQLite necesita `DATABASE_URL` con **ruta absoluta**.
- El navegador del preview **no alcanza** `localhost:8000` → usa el proxy Vite `/api` (ya configurado).
- El **service worker cachea bundles viejos** en dev → ya solo se registra en PROD; si ves UI vieja,
  desregistra SW + limpia caches.
- `fill_blank` está **excluido** de la selección de quiz (options null, se califica por índice).

---

## 2. LAS 8 FASES → 100%

### FASE 0 → 100% (falta 10%)
- Migraciones **Alembic** reales (sustituir `init_db`/`create_all` en producción).
- Verificar el stack **con PostgreSQL** end-to-end (hoy solo probado en SQLite).
- **Desplegar** a Railway o Fly.io con URL pública viva. *(Requiere credenciales del usuario — pídelas.)*
- **Aceptación:** URL pública responde `/health`; registro+quiz funcionan contra Postgres.

### FASE 1 → 100% — CONTENIDO (la fase de mayor valor)
- **1.500+ preguntas** en los 7 tracks, **redactadas nativamente en ES y EN por separado**.
- **Glosario por track**: todos los términos del dominio, definición + ejemplo, ES y EN. Modelo
  `GlossaryTerm` + `GlossaryScreen.tsx` + búsqueda.
- **Pantalla de ruta** (`TracksScreen.tsx`): mapa de tracks→módulos con desbloqueo por BKT visible.
- **Calibración IRT** (1PL/2PL/3PL) sobre `elo_rating`.
- **Fuentes canónicas obligatorias** (cita la fuente en cada pregunta):
  - Python: CPython docs 3.13/3.14, PEPs, *Fluent Python 2e* (Ramalho), *Effective Python 3e* (Slatkin)
  - Ingeniería: *Designing Data-Intensive Applications* (Kleppmann), *Architecture Patterns with Python*
    (Percival & Gregory), 12-Factor App, OWASP ASVS/Top 10
  - AI/ML: *Attention Is All You Need*, PyTorch docs, scikit-learn user guide, Hugging Face docs,
    documentación de APIs de Anthropic/OpenAI, LangChain/LlamaIndex docs, *Designing ML Systems* (Huyen)
  - DevOps: Kubernetes docs, Terraform registry, Docker docs
- **Regla de calidad de distractores:** cada opción incorrecta debe codificar un **malentendido real**
  (argumentos mutables por defecto, late binding en closures, `is` vs `==`, coma flotante, mitos del GIL,
  confundir `yield` con `return`, creer que RAG "entrena" el modelo). Nada de rellenos absurdos.
- **Pipeline:** Haiku genera desde el brief de fuente → Sonnet valida esquema/unicidad → **Opus revisa
  exactitud técnica** por muestreo estratificado (≥10% y el 100% de las `expert`).
- **Aceptación:** ≥1.500 Q válidas cargadas; glosario navegable ES/EN; ruta gated visible; 0 colisiones de ID.

### FASE 2 → 100% — TUTOR + RAG
- **RAG vectorial real**: ChromaDB + `sentence-transformers` multilingüe; indexa preguntas, explicaciones
  y glosario; retrieval + reranking; **citas forzadas** y guardrail anti-alucinación.
- **Memoria del tutor**: corto plazo (conversación), largo plazo (perfil), episódica (fallos previos).
- **Aceptación:** fallar 3× la misma pregunta produce explicaciones distintas y progresivamente más simples,
  cada una con cita verificable al material.

### FASE 3 → 100% — GAMIFICACIÓN + SOCIAL + OFFLINE
- **Framer Motion** (ya es dependencia): transiciones, feedback de respuesta, confetti, llenado de XP, flip de card.
- **Duelos multiplayer** por WebSocket (mismas preguntas, timer compartido), **torneos** por brackets,
  **grupos de estudio** con chat.
- **Offline-first real**: sync engine sobre el IndexedDB existente, cola de acciones, resolución de
  conflictos (last-write-wins + vector clocks), indicadores online/offline.
- **Cofres, streak freeze, combos** completos.
- **Aceptación:** duelo entre dos navegadores; responder sin red → reconectar → sincroniza sin pérdida.

### FASE 4 → 100% — ML AVANZADO + MLOps
- **DKT** (LSTM en PyTorch) sobre secuencias de respuestas; servir <50 ms; A/B contra BKT.
- **Churn** (XGBoost) sobre features de engagement → push de re-enganche.
- **MLOps:** feature store (Feast), registry (MLflow) con shadow/canary, drift (Evidently), auto-retrain semanal.
- **Aceptación:** dashboard de ML health; forzar drift dispara retrain; A/B mide learning outcomes reales.

### FASE 5 → 100% — PIPELINE MULTI-AGENTE + ANALYTICS
- Cadena **generador → revisor → verificador** con quality gate (~35% rechazo esperado).
- Analytics: curvas de aprendizaje, matriz de confusiones, predicción, cohortes, funnel; ETL (Dagster/Prefect)
  + Great Expectations.
- **Aceptación:** de una URL/texto fuente salen N preguntas validadas, calibradas e ingestadas automáticamente.

### FASE 6 → 100% — MICROSERVICIOS + OBSERVABILIDAD
- Split por bounded context: Auth, Content, Quiz, Analytics, AI, Gamification, Notification + API Gateway.
- gRPC interno + RabbitMQ/Kafka (`answer_recorded` → Elo+FSRS+BKT+XP+badges). Saga, circuit breaker, retry.
- OpenTelemetry/Jaeger, Prometheus + Grafana, Sentry, logs con trace ID.
- **Aceptación:** traza de una request por 5 servicios; matar un servicio degrada sin caer (chaos test).

### FASE 7 → 100% — CLOUD, SEGURIDAD, PAGOS, NATIVO
- **IaC:** Terraform (dev/staging/prod), Kubernetes + Helm + HPA (1→5 pods), CI/CD blue-green.
- **Seguridad ASVS 5.0 L2 completa** (ver §3.B).
- **Pagos:** Stripe (web) + **RevenueCat** (Apple IAP + Google Play Billing).
- **i18next completo** ES/EN en toda la UI y contenido.
- **Nativo Capacitor:** builds iOS/Android, **iconos en todos los tamaños**, splash, push (VAPID/FCM/APNs).
- **Testing:** Playwright E2E de todos los flujos, visual regression, Locust 5.000 concurrentes, Lighthouse ≥90.
- **Aceptación:** load test 5k sin degradación; securityheaders.com A+; app instalable iOS/Android; CI verde.

### FASE 8 → 100% — GARANTÍA E2E + SCORECARD
- Recorrer **cada** flujo en la app desplegada hasta que no exista camino roto.
- Scorecard competitivo final actualizado (artifact).

---

## 3. REQUISITOS DE INVESTIGACIÓN → CONVERTIDOS EN TAREAS

### 3.A — Aprobación en App Store / Play Store (objetivo: 90% de aceptación)

Esto es lo que tienen las apps de la competencia y que **hoy Neurium no tiene**. Cada punto es bloqueante:

**Apple (causas reales de rechazo):**
- **Guideline 4.2 — Minimum Functionality:** una PWA envuelta se rechaza. Necesitas funcionalidad nativa
  demostrable: **push notifications, modo offline, haptics, biometría, widgets**.
- **Guideline 4.8 — Sign in with Apple:** si ofreces login con Google/Facebook, **estás obligado** a ofrecer
  también Sign in with Apple. Es una causa de rechazo automático.
- **Guideline 3.1.1 — In-App Purchase:** el contenido digital por suscripción **debe** usar StoreKit/IAP.
  Enlazar a Stripe requiere el *External Purchase Link Entitlement* y es terreno delicado.
- **Guideline 5.1.1(v) — Borrado de cuenta:** si permites crear cuenta, **debes permitir borrarla desde
  dentro de la app**. Obligatorio.
- **Guideline 5.1.2(i):** consentimiento explícito para compartir datos con IA.
- **Privacy Manifest** (`PrivacyInfo.xcprivacy`) + *App Privacy nutrition labels* + motivo de APIs de razón requerida.
- Cuenta demo funcional para el revisor, metadata completa, capturas de todos los tamaños.

**Google Play:**
- **Target API level** al día (Android 15+ / 36 según ventana vigente al publicar).
- **Data Safety form** coherente con lo que realmente recoges.
- **12 testers durante 14 días** antes de producción (cuentas de desarrollador personales nuevas).
- **Borrado de cuenta y datos** accesible **también desde web**, no solo in-app.
- Play Integrity API; política de suscripciones; clasificación de contenido.

**Ambas:** política de privacidad y términos con URL pública, edad mínima **13+** (evita COPPA).

**→ TAREA:** implementar Sign in with Apple + Google, borrado de cuenta in-app y web, Privacy Manifest,
Data Safety, IAP vía RevenueCat, push nativo, biometría, y preparar el paquete de review.

### 3.B — Seguridad y autenticación (lo que hacen ellos)

- **OAuth 2.0 / OIDC con PKCE** para móvil (nunca implicit flow).
- **Sign in with Apple + Google Sign-In** (y opcionalmente magic link / OTP por email).
- **"Olvidé mi contraseña" correcto:**
  - Token de un solo uso, expiración 15–60 min, hasheado en BD.
  - **Sin enumeración de cuentas:** responde siempre *"si existe una cuenta, enviamos un correo"*.
  - Rate limit por IP y por email; invalidar token al usarlo; **revocar todas las sesiones** tras el cambio.
- **Argon2id** para hashing (migrar desde bcrypt).
- **Rotación de refresh tokens con detección de reuso** (si se reusa uno viejo → revocar la familia).
- **Almacenamiento seguro en nativo:** iOS Keychain / Android Keystore — **nunca `localStorage`** en la app nativa.
- MFA/TOTP opcional, pantalla de gestión de sesiones/dispositivos, biometría para reabrir.

### 3.C — Cómo lucen sus pantallas de registro/login (y qué copiar)

- **Social primero:** los botones *Continuar con Apple / Google* van **arriba**, el email debajo. Reduce
  fricción drásticamente.
- **Registro diferido (lo más importante):** Duolingo te deja **hacer una lección antes de registrarte**.
  Es la mayor palanca de conversión que existe. → **Neurium debe permitir hacer el test de nivelación
  antes de pedir cuenta**, y registrar al final para "guardar tu progreso".
- **Divulgación progresiva:** un campo (o un paso) a la vez en móvil, no un formulario de 5 campos.
- **Sí hay desplegables que cambian el flujo:** selector de idioma, de objetivo de aprendizaje
  ("¿por qué aprendes Python?"), de nivel declarado, y de meta diaria (5/10/20/30 min). Cada selección
  **personaliza el onboarding siguiente** — no son decorativos.
- Validación inline, medidor de fuerza de contraseña, toggle ver/ocultar, botón que dice **"Continuar"**.

### 3.D — Contenido: cómo ser superior (no solo distinto)

Ellos son lineales e idénticos para todos. La ventaja de Neurium es el motor; el contenido debe estar a la altura:
- Redacción **nativa** por idioma, no traducción. Cada pregunta **cita su fuente**.
- Código **ejecutable y verificado**, no pseudocódigo.
- La explicación enseña el **porqué**, no repite la respuesta.
- Distractores construidos desde errores reales documentados.
- **Diferenciador crítico: Pyodide (WebAssembly)** — el alumno **escribe y ejecuta código Python real**
  dentro del quiz, en el navegador, sin servidor. Ver spec completo en `docs/SPEC_PYODIDE.md`.
  Tres tipos: *code_output* (predice el resultado), *fill_blank_exec* (completa el código), *fix_bug*
  (corrige el error). Motor evalúa el output, tutor AI analiza el error específico. **Nadie combina
  código ejecutable + motor adaptativo. Implementar en Fase 2.**

### 3.E — Gamificación: igualar y superar a Duolingo

*Ellos tienen:* XP, rachas + freeze, ligas, misiones diarias, corazones/energía, gemas, cofres, logros,
quests con amigos, leaderboards, notificaciones, bonus de lección perfecta.

*Cómo superarlos (esto es lo que ellos no pueden hacer sin un motor como el nuestro):*
- **Medidor ZPD visible:** mostrar que el sistema te está sirviendo dificultad óptima.
- **Curva de olvido por concepto:** barra de "fuerza de memoria" que decae visiblemente y se recarga al repasar.
- **Mapa de conocimiento** tipo árbol que se desbloquea con prerequisitos verificados por BKT.
- **"Boss battles"** = exámenes de maestría de módulo.
- **Prueba social:** *"el 73% falla esta"*.
- **Duelos en vivo, torneos, clanes de estudio.**
- **Código ejecutable** dentro del reto (Pyodide) + haptics + diseño de sonido.

### 3.G — Entidad legal y estructura de negocio

**Decisión tomada: autónomo griego para lanzar → IKE al superar €2.000/mes.**

| Etapa | Entidad | Cuándo | Por qué |
|---|---|---|---|
| Lanzamiento | Autónomo griego (ατομική επιχείρηση) | Hoy | Sin coste, no bloquea stores ni Stripe |
| Crecimiento | IKE griega | Al superar €2.000/mes | Responsabilidad limitada, credibilidad B2B |
| Escala internacional | Valorar Estonia OÜ | Opcional, si el mercado es global | Jurisdicción EU reconocida, SaaS-friendly |

**Cuentas de desarrollador:**
- Apple Developer (individual): $99/año — lanzar con cuenta individual
- Google Play (individual): $25 único pago

**Fiscalidad:** Ley 5246/2025 — tasa del 9% para nuevos autónomos griegos (primeros años).
AFM (NIF griego) ya disponible — suficiente para registrarse como autónomo.

**→ TAREA:** Registrarse como autónomo + abrir cuenta Stripe + Apple/Google Developer accounts.
No crear IKE hasta validar ingresos recurrentes. Ver `docs/SPEC_WEB.md` §4 para el modelo
de pagos (Stripe web + RevenueCat nativo).

### 3.H — Web completa: neurium.app

**No una landing page — la plataforma central.** Ver spec completo en `docs/SPEC_WEB.md`.

```
neurium.app
├── /              (Home + conversión)
├── /features      (motor adaptativo explicado visualmente)
├── /pricing       (Free / Pro $9.99 / Pro+ $19.99)
├── /certifications (marketplace de bootcamps — Fase 4+)
├── /creators      (para creadores — Fase 4+)
├── /blog          (SEO — artículos técnicos)
├── /app           (PWA — acceso web a Neurium)
└── /legal         (privacy, terms, /delete-account — requerido por Google)
```

**Arquitectura de 3 superficies — un solo backend:**
- Web (`/app`) → PWA → mismo backend FastAPI → misma DB PostgreSQL
- iOS → Capacitor nativo → mismo backend
- Android → Capacitor nativo → mismo backend

**Modelo de pagos Stripe vs IAP (el modelo Netflix/Spotify):**
- Suscripciones iniciadas **en web** → Stripe → sin comisión del 15-30% de las tiendas
- Suscripciones iniciadas **en la app nativa** → RevenueCat (StoreKit + Play Billing)
- La app **no muestra botón de pago** en iOS → Apple no puede exigir IAP
- La app **solo verifica estado de suscripción** vía el backend

**Stack web:** Next.js (App Router) o React + Vite. Hosting: Cloudflare Pages (gratis).
Dominio: ~$10-15/año. Construir con Claude Code: 1-2 semanas.

**→ TAREA (Fase 0/7):** Registrar dominio neurium.app + configurar Cloudflare + construir
web en Next.js con las páginas esenciales. La ruta `/app` sirve la PWA existente.

### 3.F — Vender a 1.000 usuarios (objetivo: 90%)

- Tiers ya decididos: Free (límite diario) · **Pro $9.99** · **Pro+ $19.99**; anual con ~40% de descuento;
  **precios localizados** para LATAM por tier regional de la store.
- **Paywall después del valor**, no antes: tras el test de nivelación y la primera racha.
- Trial de 7 días; primer "win" del usuario en **menos de 3 minutos**.
- Onboarding: nivelación → ruta personalizada → primera victoria.
- Retención: objetivos D1/D7/D30, push de racha y de repaso vencido, misiones diarias.
- **ASO:** keywords, capturas que muestren el motor adaptativo, video preview.
- Bucle de referidos + **B2B a bootcamps hispanohablantes** (2–3 clientes ≈ el mismo ingreso que 333 usuarios).
- Instrumentar el funnel completo desde el día 1.

---

## 4. ORDEN DE EJECUCIÓN RECOMENDADO

1. **Fase 1 (contenido)** — mayor valor por token; bloquea la propuesta de venta.
2. **Fase 0 (deploy real)** + **3.C** (registro diferido + social login) + **3.G** (autónomo + cuentas developer).
3. **3.H (web neurium.app)** — registrar dominio + Cloudflare + páginas esenciales + `/delete-account`.
4. **Fase 7 (seguridad/pagos/nativo)** — RevenueCat + Stripe + Sign in with Apple → stores.
5. **Fase 2 (RAG + Pyodide)** — tutor vectorial + código ejecutable en navegador (ver `docs/SPEC_PYODIDE.md`).
6. **Fase 3 (social/offline/animación)**.
7. **Fases 4, 5, 6** — escala; solo cuando haya usuarios que lo justifiquen.
8. **Fase 8** — garantía E2E + scorecard.

---

## 5. NO NEGOCIABLES

- ❌ Nunca traducción automática. Contenido nativo por idioma, con fuente citada.
- ❌ Nunca declarar una fase completa sin verificación ejecutada.
- ✅ Actualizar `docs/STATUS.md` al cerrar cada fase (es la fuente de verdad).
- ✅ Respetar el routing de modelos: si Haiku puede hacerlo, no lo hace Opus.
- ✅ Sin funciones de voz ni OCR (decisión cerrada del usuario).
- ✅ Marca: Neurium, azul cielo, modo light por defecto.
- ✅ Pyodide: código ejecutable en browser (Fase 2) — spec en `docs/SPEC_PYODIDE.md`.
- ✅ Web completa neurium.app — no landing page — spec en `docs/SPEC_WEB.md`.
- ✅ Entidad legal: autónomo griego para lanzar; IKE al superar €2.000/mes (§3.G).
- ✅ Pagos: Stripe en web + RevenueCat en nativo (modelo Netflix). No IAP en web.
