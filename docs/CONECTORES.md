# Conectores de Claude — inventario, uso y permisos

Documento vivo. Dice **qué servicio externo puede tocar una sesión de Claude, a qué
cuenta apunta, para qué se usa en Whetzy y qué puede hacer sin preguntar**. Lo que no
esté aquí no se toca desde una sesión.

**Medido el 2026-09-26** desde una sesión cloud: `ListConnectors` para el estado y una
llamada de solo lectura por conector (columna «Cuenta») para saber a qué apunta. Un
conector se conecta en <https://claude.ai/customize/connectors> y **se carga al arrancar
la sesión**: una sesión abierta antes de conectarlo no lo ve. Las credenciales viven en
claude.ai, nunca en el repo.

## 1. Clases de acción

| Clase | Qué es | Quién |
|---|---|---|
| **L** — lectura | Consultar estado, logs, métricas, incidencias, analítica, documentación | Sin preguntar. Si sostiene una afirmación de un doc o de un `DONE`, se cita herramienta + fecha (Regla Cero) |
| **E** — escritura reversible y privada | Crear o editar algo que **ningún usuario ve**, que no afecta a producción y que se deshace borrándolo: borradores, dashboards, notebooks, diseños, triaje de incidencias | Sin preguntar; se anota en el PR de la oleada |
| **H** — lo demás | Producción (variables, redeploy, reinicio, dominios, volúmenes), **publicar** (posts, emails, landing, blog), datos de personas reales (CRM), secretos, **crear recursos o proyectos nuevos** aunque sean gratis, cualquier gasto | `HUMAN-BLOCKED` con su valor por defecto (ADR-47). En sesión interactiva, solo con el «sí» explícito del dueño para esa acción concreta |

La regla sale del contrato de autonomía de `ORCHESTRATOR.md` y de ADR-45: **producción
solo cambia cuando el dueño fusiona `master`**. Un conector no es una puerta trasera a
producción. Leer el **valor** de una variable (`list-variables` de Railway) cuenta como
exponer un secreto, así que es **H**. Leer sus nombres en el panel lo hace el dueño.

## 2. Conectores activos y su uso

| Conector | Cuenta (2026-09-26) | Estado real | Uso en Whetzy | L / E sin preguntar | Solo el dueño (H) |
|---|---|---|---|---|---|
| **Railway** | Proyecto `whetzy`, entorno `production`, servicios `api` y `Postgres` | Deploy `b64e2a9a` en `SUCCESS` (10:46 UTC); log `[owner] unchanged: admin@whetzy.com` | Verificar despliegues sin adivinar: logs de arranque (`alembic`, `content_loader`, `[owner]`), estado, errores HTTP, latencia, diagnóstico de deploys fallidos | `get-status`, `list-deployments`, `get-logs` (con `filter`: el stream trae mucho ruido de OpenTelemetry), `get-deployment-diagnosis`, `http-error-rate`, `http-response-time`, `get-service-metrics`, `search-docs` | `set-variables`, `list-variables`, `redeploy`, `restart-service`, `accept-deploy`, `create-*`, `delete-*`, dominios, volúmenes, `update-service`, `railway-agent` con cambios |
| **GitHub** (herramientas de la sesión, no conector de claude.ai) | `Neopram/whetzy` | — | PR por oleada, checks, revisiones | Leer; crear y actualizar el PR de la rama de la sesión | Fusionar, push a `master` (ADR-45) |
| **Sentry** | Organización `whetzy`, región `de.sentry.io` | **0 proyectos.** El backend ya trae `sentry-sdk[fastapi]` y `configure_sentry()` (`backend/app/core/error_tracking.py`), que no hace nada si `SENTRY_DSN` está vacío. Hoy no llega ningún error | Errores del backend en producción, y del frontend cuando se instale su SDK | `search_issues`, `search_events`, `get_sentry_resource`, `analyze_issue_with_seer`; E: `update_issue` (asignar, resolver) | Crear el proyecto y poner `SENTRY_DSN` en Railway (**H.41**) |
| **PostHog** | Proyecto «Default project» (id 285042), creado el 2026-09-26 | `ingested_event: false`. El frontend no tiene SDK | Analítica de producto (funnel de onboarding, retención, activación), web analytics, feature flags, experimentos A/B, encuestas | Consultas (`read-data-schema` antes de cada una), `query-*`; E: insights, dashboards, notebooks, cohortes, flags **al 0 % o apagados** | Flags o experimentos que cambien lo que ve un usuario real, lanzar encuestas, borrar datos; elegir herramienta (**H.42**) |
| **Mixpanel** | Proyecto «Whetzy IKE» (id 4067601) | Sin SDK en el frontend | Duplica a PostHog. No se instrumentan las dos (**H.42**) | Lectura | Todo lo demás |
| **Cloudflare Developer Platform** | Cuenta con 0 Workers | Sus herramientas cubren Workers, KV, R2, D1, Hyperdrive y documentación, **no Pages**. Pages sigue desplegando por Git (`README.md`) | Buscar en la documentación de Cloudflare; KV, R2 o D1 si una fila lo pide | `workers_list`, `search_cloudflare_documentation` | Crear o borrar Workers, KV, R2 o D1 |
| **Hugging Face** | Usuario `fgalindezta`, sin PRO | El token OAuth leído a las ~11 UTC caducaba ese mismo día a las 19:09 UTC. Si el conector falla, se reconecta | Buscar modelos, datasets y papers para `docs/ml/` y para el inventario de corpus (serie 37). Un dataset entra solo con licencia de ADR-11 | `hf_fs`, `hub_repo_search`, `hub_repo_details` | Subir repos, lanzar jobs (gasto) |
| **HubSpot** | Cuenta 149416550, sin onboarding. Campañas requieren plan de pago | Vacío | CRM de los pilotos B2B (H.39) y de los instructores fundadores (H.40) | Lectura | **Toda escritura**: contactos y empresas son datos de personas; emails, landing, blog y páginas son publicación |
| **Metricool** | Marca `blogId 7101824` | **Sin ninguna red social conectada**: el conector no puede hacer nada útil | Programar y medir redes (`DISTRIBUCION.md`) cuando haya cuentas | E: `createScheduledPostForReview` (queda pendiente de aprobación) | Conectar redes; `createScheduledPost`; aprobar |
| **Typefully** | 0 cuentas sociales | Vacío | Hilos de X, LinkedIn, Threads y Bluesky (`DISTRIBUCION.md`) | E: `create_draft` y `edit_draft` **sin fecha de publicación** | Programar, publicar |
| **Canva** · **Figma** · **Adobe** | Cuentas del dueño | — | Assets de marca, capturas para tiendas (`store/`), OG images, piezas de distribución. Todo asset que entra al repo es original o de licencia libre, con fuente | E: crear y editar diseños, exportar | Publicar plantillas de marca, compartir fuera |
| **OpusClip** | Cuenta del dueño | — | Clips cortos a partir de vídeos propios (fase de vídeo, posterior a ingresos) | E: proyectos y clips | `opusclip_schedule_publish` y cualquier publicación |
| **Neon** | 0 proyectos | Modo escritura: expone herramientas destructivas | Nada. La base de datos está en Railway | — | Crear cualquier proyecto |
| **Sanity** | 0 proyectos | — | Nada. El contenido vive en JSON en el repo (ADR-40, ADR-46) | — | Crear cualquier proyecto |
| **Intuit QuickBooks** | Sin autenticación propia | — | Contabilidad cuando exista entidad (H.29) | Lectura | Todo lo demás |
| **Adobe Marketing Agent** | — | Requiere Adobe Experience Platform | Ninguno previsto | — | — |
| **FMP** | — | Datos de mercados financieros | Ninguno en Whetzy. Se puede desactivar en el chat | — | — |
| **Lovable** | — | Constructor de apps con su propia base de código | **No se usa sobre este repo**: crea otro proyecto y consume créditos | — | — |

**A medio conectar** (`connect_incomplete`): **Firecrawl** (útil para 37.1, inventario
de la industria con URL fechada: 1.000 páginas al mes gratis), **Amplitude** (sería una
tercera analítica: no hace falta), **Intuit Mailchimp** y **Lusha** (prospección B2B, sin
uso hoy). Terminarlos o quitarlos es cosa del dueño en claude.ai.

**El correo de la app no depende de un conector.** H.30 (el correo no sale) se arregla
con un proveedor SMTP o API en las variables de Railway. El conector de Resend, si se
conecta, sirve para ver entregas y rebotes, no para enviar desde el backend.

## 3. Rutinas remotas

Una rutina programada (`create_trigger`) lleva **solo los conectores que se le pasen en
`connectors`**, y cada disparo los usa con los mismos permisos de §1. La rutina
nocturna necesita `["Railway", "Sentry", "PostHog"]` para verificar despliegues y
errores. Nada de redes, CRM ni diseño: una sesión sin nadie mirando no publica.

## 4. Cómo se mantiene este documento

- Al conectar o quitar un conector, se añade o se borra su fila con la cuenta medida y
  la fecha.
- Si una fila dice «0 proyectos» o «sin SDK» y eso cambia, se actualiza con la
  evidencia (herramienta + fecha).
- Lo que un conector revela y exige al dueño va a `AUTONOMOUS_STATE.md` §3 como fila H,
  no solo aquí (ADR-48).
