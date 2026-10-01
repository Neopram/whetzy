# Inventario de documentos — 2026-10-01

Paso 6 del prompt del dueño del 2026-10-01: todos los `.md` del repo fuera de `node_modules`, cada uno
con su clase y una línea de por qué. Lo generó la sesión leyendo la cabecera de cada fichero, la fecha
de su último commit y quién lo cita (`git ls-files '*.md'`, 127 ficheros más este). **[sin verificar]**
marca un documento cuyo contenido no se ha contrastado frase a frase con el código: no se da por bueno
ni se borra.

**Clases.** *normativo-vivo*: manda sobre el trabajo. *referencia-viva*: describe el sistema o el mercado
y se mantiene al día. *histórico*: registro fechado; no manda. *obsoleto*: describe un plan, una cifra o un
estado sustituido y no lo dice. *legal*: texto legal; ninguna sesión lo cambia, solo señala contradicciones.

**Guarda.** `scripts/check_docs.py` [12]: todo `.md` de `docs/` fuera de `archive/` aparece en
`docs/README.md` o en este inventario, y ningún enlace markdown relativo de los `.md` fuera de `archive/`
está roto.

## Resumen

| Clase | Ficheros |
|---|---|
| normativo-vivo | 17 |
| referencia-viva | 37 |
| histórico | 34 |
| legal | 34 |
| obsoleto | 6 |
| **Total** | **128** |

## Raíz del repo y otras carpetas

| Documento | Clase | Por qué | Acción | Último commit |
|---|---|---|---|---|
| `CLAUDE.md` | normativo-vivo | instrucciones del proyecto; check_docs vigila HEAD de Alembic y la pausa | se queda; ruta de AUDITORIA_EXTERNA actualizada | 2026-09-30 |
| `docs/archive/COMPETITIVE_RESEARCH.md` | obsoleto | investigación de 8 plataformas del 2026-09-23, sin referencias; la sustituye docs/COMPETENCIA.md (URL y fecha) | archivado el 2026-10-01 | 2026-09-23 |
| `EVALUACION_COMPLETA_WHETZY.md` | histórico | evaluación fechada con notas «Superado»; no manda | archivar tras fusionar #52 (que la toca) | 2026-09-30 |
| `README.md` | referencia-viva | presentación del repo (raíz) | se queda | 2026-09-26 |
| `docs/archive/SERIE_28_STATUS.md` | obsoleto | estado de la serie 28 del 2026-09-19; ADR-48 archiva los SERIE*_STATUS y el ledger es el único plan | archivado el 2026-10-01 | 2026-09-23 |
| `backend/IMPLEMENTATION_GUIDE_22_6.md` | referencia-viva | guía de integración de 22.6 (rate limit, paginación, caché, jobs) | se queda [sin verificar] contra el código | 2026-09-23 |
| `content/_quarantine/README.md` | normativo-vivo | regla de la carpeta en cuarentena (no se carga ni se mide) | se queda | 2026-09-23 |
| `content/legal/affiliation_dossier_en.md` | legal | textos comerciales/contractuales (afiliación, piloto B2B, créditos, instructores) | no se toca el texto | 2026-09-26 |
| `content/legal/affiliation_dossier_es.md` | legal | textos comerciales/contractuales (afiliación, piloto B2B, créditos, instructores) | no se toca el texto | 2026-09-26 |
| `content/legal/b2b_pilot_offer_en.md` | legal | textos comerciales/contractuales (afiliación, piloto B2B, créditos, instructores) | no se toca el texto | 2026-09-26 |
| `content/legal/b2b_pilot_offer_es.md` | legal | textos comerciales/contractuales (afiliación, piloto B2B, créditos, instructores) | no se toca el texto | 2026-09-26 |
| `content/legal/credits_terms_en.md` | legal | textos comerciales/contractuales (afiliación, piloto B2B, créditos, instructores) | no se toca el texto | 2026-09-26 |
| `content/legal/credits_terms_es.md` | legal | textos comerciales/contractuales (afiliación, piloto B2B, créditos, instructores) | no se toca el texto | 2026-09-26 |
| `content/legal/instructor_recruitment_kit_en.md` | legal | textos comerciales/contractuales (afiliación, piloto B2B, créditos, instructores) | no se toca el texto | 2026-09-26 |
| `content/legal/instructor_recruitment_kit_es.md` | legal | textos comerciales/contractuales (afiliación, piloto B2B, créditos, instructores) | no se toca el texto | 2026-09-26 |
| `docs/archive/detallessesionultima.md` | histórico | volcado de la sesión 2026-09-29/30 pedido por el dueño | archivado el 2026-10-01 | 2026-09-30 |
| `docs/archive/frontend-README-plantilla-vite.md` | obsoleto | plantilla de Vite («React + TypeScript + Vite»): no describe el frontend de Whetzy | archivado el 2026-10-01 | 2026-09-23 |
| `legal/antifraud-legal-basis.md` | legal | borradores legales de la raíz (el README de docs/ dice que no mandan) | no se toca el texto | 2026-09-26 |
| `legal/dmca-policy.md` | legal | borradores legales de la raíz (el README de docs/ dice que no mandan) | no se toca el texto | 2026-09-26 |
| `legal/dpa-template.md` | legal | borradores legales de la raíz (el README de docs/ dice que no mandan) | no se toca el texto | 2026-09-26 |
| `legal/privacy-policy.md` | legal | borradores legales de la raíz (el README de docs/ dice que no mandan) | no se toca el texto | 2026-09-26 |
| `legal/security-breach-procedure.md` | legal | borradores legales de la raíz (el README de docs/ dice que no mandan) | no se toca el texto | 2026-09-26 |
| `legal/terms-of-service.md` | legal | borradores legales de la raíz (el README de docs/ dice que no mandan) | no se toca el texto | 2026-09-26 |
| `scripts/content_qa/README.md` | referencia-viva | herramientas de QA de contenido | se queda | 2026-09-26 |

## `docs/` — vivos

| Documento | Clase | Por qué | Acción | Último commit |
|---|---|---|---|---|
| `docs/archive/25.0-planning.md` | obsoleto | marcado SUPERADO (ADR-48); se conservaba solo por un test de tests/ (raíz) que pytest no recoge | archivado el 2026-10-01; ruta del test actualizada | 2026-09-30 |
| `docs/archive/32_0_response_inventory.md` | histórico | inventario de datos por respuesta de la tarea 32.0 (2026-09-26), sin referencias | archivado el 2026-10-01 | 2026-09-26 |
| `docs/API.md` | referencia-viva | referencia de la API | se queda [sin verificar] ruta a ruta contra openapi.json | 2026-09-27 |
| `docs/ARCHITECTURE.md` | referencia-viva | arquitectura del sistema | se queda [sin verificar] frase a frase | 2026-09-29 |
| `docs/archive/AUDITORIA_EXTERNA_2026-09-19.md` | histórico | foto del 2026-09-19; dice que el CI nunca ha corrido, falso desde el 2026-10-01 (H.13 resuelto) | archivado el 2026-10-01; CLAUDE.md y capacity.md apuntan a archive/ | 2026-09-25 |
| `docs/AUTONOMOUS_STATE.md` | normativo-vivo | ledger, fuente de verdad (ADR-40); ledger.py check | se queda | 2026-09-30 |
| `docs/archive/BALANCE-12-DIAS.md` | histórico | balance narrativo escrito el 2026-09-20 («no es un plan ni un informe de estado») | archivado el 2026-10-01 | 2026-09-23 |
| `docs/CATALOGO_MAESTRO.md` | normativo-vivo | alcance del producto; ADR-54 en #51/#52 | se queda | 2026-09-30 |
| `docs/CHANGELOG.md` | histórico | registro por versión; solo se añade | se queda (6.4: 0 enlaces rotos) | 2026-09-30 |
| `docs/CIERRE_2026-09-30.md` | normativo-vivo | estado PAUSA y guía de fusión del #34; check_docs [11] | se queda | 2026-09-30 |
| `docs/COMPETENCIA.md` | referencia-viva | mercado con URL y fecha | se queda | 2026-09-30 |
| `docs/CONECTORES.md` | normativo-vivo | qué servicios externos toca una sesión y con qué permiso | se queda | 2026-09-26 |
| `docs/DECISIONS.md` | normativo-vivo | ADR; solo se añade al final | se queda (6.4: 0 enlaces rotos) | 2026-09-30 |
| `docs/DISTRIBUCION.md` | normativo-vivo | plan de distribución («manda» sobre distribución) | se queda | 2026-09-30 |
| `docs/ECONOMIA.md` | normativo-vivo | economía de créditos («manda»); check_docs [9] la contrasta con credits.json | se queda | 2026-09-30 |
| `docs/INVENTARIO_DOCS.md` | normativo-vivo | este inventario; check_docs [12] | nuevo | 2026-10-01 |
| `docs/LANZAMIENTO_PILOTO.md` | normativo-vivo | kit del piloto de 20-50 personas (fila 31.8, #50); llegó a `master` después de la primera versión de este inventario | se queda | 2026-10-01 |
| `docs/MARKETPLACE.md` | referencia-viva | spec del marketplace (serie 28) | se queda | 2026-09-30 |
| `docs/ORCHESTRATOR.md` | normativo-vivo | prompt operativo; check_docs [11] | se queda | 2026-09-30 |
| `docs/PLAN_EXPERIENCIA.md` | referencia-viva | spec de la serie 40 | se queda | 2026-09-30 |
| `docs/archive/PROMPT_CIERRE_2026-09-30.md` | histórico | prompt de un solo uso para cerrar el #34, ya ejecutado (#34 fusionado el 2026-10-01) | archivado el 2026-10-01 | 2026-09-30 |
| `docs/PROMPT_CONTROL_TOTAL.md` | normativo-vivo | prompt de arranque con control total | se queda; ruta de i18n-audit actualizada | 2026-09-30 |
| `docs/PROTOCOLO_VERIFICACION.md` | normativo-vivo | protocolo de verificación | se queda | 2026-09-27 |
| `docs/README.md` | normativo-vivo | índice de documentos vivos | se queda; filas de los archivados actualizadas | 2026-09-30 |
| `docs/RELEASE.md` | normativo-vivo | guía de release | se queda [sin verificar] paso a paso | 2026-09-25 |
| `docs/RUNBOOK.md` | normativo-vivo | operación: despliegue, migraciones, backup | se queda [sin verificar] comando a comando | 2026-09-27 |
| `docs/SEGMENTOS.md` | referencia-viva | segmentos y personas | se queda | 2026-09-30 |
| `docs/STATUS.md` | histórico | registro por sesión; no se reescribe | se queda (6.4: 0 enlaces rotos) | 2026-09-30 |
| `docs/STORE_LISTING.md` | referencia-viva | ficha de tienda consolidada (iOS + Android), citada por el ledger | se queda | 2026-09-30 |
| `docs/ab-framework.md` | referencia-viva | framework A/B (24.14) | se queda [sin verificar] | 2026-09-25 |
| `docs/capacity.md` | referencia-viva | capacidad y escalado a coste cero (22.6) | se queda [sin verificar]; ruta de AUDITORIA_EXTERNA actualizada | 2026-09-25 |
| `docs/cloudflare-config.md` | referencia-viva | configuración de Cloudflare free tier (22.5) | se queda [sin verificar] contra el panel | 2026-09-23 |
| `docs/competitive-teardown.md` | referencia-viva | marcador competitivo con pesos fijos; §14 histórico desde #52 | se queda | 2026-09-30 |
| `docs/restore_log.md` | referencia-viva | registro del simulacro de restauración; lo escribe scripts/db_restore_test.sh | se queda | 2026-09-26 |
| `docs/supply-chain.md` | referencia-viva | seguridad de la cadena de suministro (22.4) | se queda [sin verificar] | 2026-09-26 |

## `docs/` — subcarpetas

| Documento | Clase | Por qué | Acción | Último commit |
|---|---|---|---|---|
| `docs/analisis-estrategico/README.md` | referencia-viva | análisis de la sesión bf, no normativo (lo dice su README) | se queda | 2026-09-30 |
| `docs/design/admin-spec.md` | referencia-viva | spec del panel de admin (22.1) | se queda [sin verificar] | 2026-09-23 |
| `docs/design/auth-hardening.md` | referencia-viva | spec de endurecimiento de auth (22.3, DONE) | se queda [sin verificar] | 2026-09-23 |
| `docs/design/decisiones-24.0.md` | referencia-viva | decisiones de identidad visual 24.0/24.1 | se queda | 2026-09-25 |
| `docs/archive/i18n-audit.md` | histórico | auditoría i18n del 2026-09-19, marcada «Histórico» por ella misma | archivado el 2026-10-01 | 2026-09-25 |
| `docs/design/identidad.md` | referencia-viva | guía de tokens de diseño (24.1) | se queda | 2026-09-28 |
| `docs/design/threat-model-stride.md` | referencia-viva | modelo de amenazas STRIDE (2026-09-23) | se queda [sin verificar] | 2026-09-23 |
| `docs/distribucion-assets/CANAL_ES_CHECKLIST.md` | referencia-viva | material de distribución (guiones, códigos de campaña, checklist del canal ES) | se queda | 2026-09-25 |
| `docs/archive/CRITERIOS_ACEPTACION_26.md` | obsoleto | una sola línea («scaffolding ready»): no describe nada | archivado el 2026-10-01 | 2026-09-23 |
| `docs/distribucion-assets/campaign-codes.md` | referencia-viva | material de distribución (guiones, códigos de campaña, checklist del canal ES) | se queda | 2026-09-23 |
| `docs/distribucion-assets/guiones/motor-en.md` | referencia-viva | material de distribución (guiones, códigos de campaña, checklist del canal ES) | se queda | 2026-09-23 |
| `docs/distribucion-assets/guiones/motor-es.md` | referencia-viva | material de distribución (guiones, códigos de campaña, checklist del canal ES) | se queda | 2026-09-23 |
| `docs/distribucion-assets/guiones/producto-en.md` | referencia-viva | material de distribución (guiones, códigos de campaña, checklist del canal ES) | se queda | 2026-09-23 |
| `docs/distribucion-assets/guiones/producto-es.md` | referencia-viva | material de distribución (guiones, códigos de campaña, checklist del canal ES) | se queda | 2026-09-23 |
| `docs/distribucion-assets/guiones/short-en.md` | referencia-viva | material de distribución (guiones, códigos de campaña, checklist del canal ES) | se queda | 2026-09-30 |
| `docs/distribucion-assets/guiones/short-es.md` | referencia-viva | material de distribución (guiones, códigos de campaña, checklist del canal ES) | se queda | 2026-09-30 |
| `docs/incidents/postmortem-template.md` | referencia-viva | respuesta a incidentes (22.7) y plantilla de post-mortem | se queda [sin verificar] | 2026-09-25 |
| `docs/incidents/runbook.md` | referencia-viva | respuesta a incidentes (22.7) y plantilla de post-mortem | se queda [sin verificar] | 2026-09-23 |
| `docs/archive/24-12-implementation.md` | obsoleto | dice «Commit: Pendiente»; 24.12 está DONE (c912713, LEDGER_HISTORY) | archivado el 2026-10-01 | 2026-09-23 |
| `docs/store/app-store-review-checklist.md` | referencia-viva | fichas y checklists de tiendas | se queda | 2026-09-30 |
| `docs/store/ios/listing.md` | referencia-viva | fichas y checklists de tiendas | se queda | 2026-09-30 |
| `docs/store/play-store-data-safety.md` | referencia-viva | fichas y checklists de tiendas | se queda | 2026-09-30 |
| `docs/support/response-templates-en.md` | referencia-viva | plantillas de respuesta de soporte ES/EN | se queda | 2026-09-23 |
| `docs/support/response-templates-es.md` | referencia-viva | plantillas de respuesta de soporte ES/EN | se queda | 2026-09-23 |
| `docs/ui-snapshots/34.1/README.md` | histórico | evidencia de capturas de 34.1 | se queda (junto a sus PNG) | 2026-09-28 |
| `docs/ui-snapshots/design-v2/README.md` | histórico | evidencia de capturas de los pasos 4 y 5 del port design/v2 (Rutas y Lección) | se queda (junto a sus PNG) | 2026-10-01 |
| `docs/MAPA_PRODUCTO.md` | referencia-viva | inventario de rutas, pantallas y subvistas con el documento que especifica cada una y sus huecos; `check_docs.py` exige que nombre todo lo que existe | se queda | 2026-10-01 |

## `docs/legal/`

| Documento | Clase | Por qué | Acción | Último commit |
|---|---|---|---|---|
| `docs/legal/H29-DECISION-LOG.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-23 |
| `docs/legal/README.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-26 |
| `docs/legal/ai-act-dsa-eaa.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-23 |
| `docs/legal/ai-notice.en.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-23 |
| `docs/legal/ai-notice.es.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-23 |
| `docs/legal/cookie-policy.en.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-23 |
| `docs/legal/cookie-policy.es.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-23 |
| `docs/legal/dpa.en.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-26 |
| `docs/legal/dpa.es.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-26 |
| `docs/legal/h21-decision.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-25 |
| `docs/legal/ip-disclaimers.en.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-23 |
| `docs/legal/ip-disclaimers.es.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-23 |
| `docs/legal/privacy-matrix.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-23 |
| `docs/legal/privacy-policy.en.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-28 |
| `docs/legal/privacy-policy.es.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-28 |
| `docs/legal/refund-policy.en.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-23 |
| `docs/legal/refund-policy.es.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-23 |
| `docs/legal/terms-of-service.en.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-23 |
| `docs/legal/terms-of-service.es.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-23 |
| `docs/legal/trademark-search.md` | legal | textos legales ES/EN | no se toca el texto; contradicciones abajo | 2026-09-23 |

## `docs/archive/`

| Documento | Clase | Por qué | Acción | Último commit |
|---|---|---|---|---|
| `docs/archive/26-PLANNING.md` | histórico | archivo: no manda (README) | se queda | 2026-09-24 |
| `docs/archive/28-INTEGRATION.md` | histórico | archivo: no manda (README) | se queda | 2026-09-24 |
| `docs/archive/28-PLANNING.md` | histórico | archivo: no manda (README) | se queda | 2026-09-24 |
| `docs/archive/29-PLANNING.md` | histórico | archivo: no manda (README) | se queda | 2026-09-24 |
| `docs/archive/EXECUTION_PLAN_25-29.md` | histórico | archivo: no manda (README) | se queda | 2026-09-24 |
| `docs/archive/LEDGER_HISTORY.md` | histórico | archivo: no manda (README) | se queda | 2026-09-30 |
| `docs/archive/MASTER_PROMPT.md` | histórico | archivo: no manda (README) | se queda | 2026-09-23 |
| `docs/archive/PROMPT_DEPLOY.md` | histórico | archivo: no manda (README) | se queda | 2026-09-23 |
| `docs/archive/PROMPT_FASE2_CIERRE.md` | histórico | archivo: no manda (README) | se queda | 2026-09-23 |
| `docs/archive/PROMPT_PROD_VERIFY.md` | histórico | archivo: no manda (README) | se queda | 2026-09-23 |
| `docs/archive/ROADMAP_25-29.md` | histórico | archivo: no manda (README) | se queda | 2026-09-24 |
| `docs/archive/SERIE29_STATUS.md` | histórico | archivo: no manda (README) | se queda | 2026-09-24 |
| `docs/archive/SERIES_22_4_7_SUMMARY.md` | histórico | archivo: no manda (README) | se queda | 2026-09-24 |
| `docs/archive/SPEC_PYODIDE.md` | histórico | archivo: no manda (README) | se queda | 2026-09-23 |
| `docs/archive/SPEC_WEB.md` | histórico | archivo: no manda (README) | se queda | 2026-09-23 |
| `docs/archive/STRATEGY_MARKETPLACE_CERTS.md` | histórico | archivo: no manda (README) | se queda | 2026-09-23 |
| `docs/archive/VERIFICATION_CHECKLIST_FINAL.md` | histórico | archivo: no manda (README) | se queda | 2026-09-24 |
| `docs/archive/VERIFY_MASTER_PROMPT.md` | histórico | archivo: no manda (README) | se queda | 2026-09-23 |
| `docs/archive/VERIFY_TRACK07.md` | histórico | archivo: no manda (README) | se queda | 2026-09-23 |
| `docs/archive/competencia-analysis-2026-09-19.md` | histórico | archivo: no manda (README) | se queda | 2026-09-25 |
| `docs/archive/competencia-screenshots-2026-09-19/README.md` | histórico | archivo: no manda (README) | se queda | 2026-09-25 |
| `docs/archive/runbook_db_backup_restore.md` | histórico | archivo: no manda (README) | se queda | 2026-09-23 |
| `docs/archive/verificacion/claims-2026-09-18.md` | histórico | archivo: no manda (README) | se queda | 2026-09-23 |
| `docs/archive/whetzy_estrategia_definitiva_v3.md` | histórico | archivo: no manda (README) | se queda | 2026-09-23 |

## Legal: contradicciones con el código (para que decida el dueño)

Ninguna sesión cambia estos textos. Lo comprobable, comprobado el 2026-10-01:

1. ~~Purga de cuenta a 30 días que no existe~~ — **resuelta en código por el #44 (fila 19.12)**. La primera
   versión de este inventario se escribió sobre una rama anterior a esa fusión y la daba por abierta; era
   falso sobre `master`. Hoy `backend/app/services/account_deletion.py` hace lo que prometen
   `docs/legal/privacy-policy.{es,en}.md` §4 y `terms-of-service.*.md` §8.3: la baja desactiva y abre una
   solicitud en `gdpr_requests` (`request_deletion`), volver a entrar en 30 días la recupera
   (`restore_if_pending`, llamada desde el login en `auth.py:181`) y `purge_due` anonimiza y borra al vencer
   (`GRACE_PERIOD = timedelta(days=30)`), en un bucle de fondo cada 6 h (`main.py:71`). [Verified: lectura del
   código y log de producción «Account purge: background loop started (19.12, every 6 h)» del 2026-10-01
   11:00 UTC.] Que una purga real haya corrido en producción: [sin verificar] (una sesión no consulta datos de
   producción).
2. **Proveedores que el código trae y la política de privacidad no nombra**: Paddle (pagos, H.29) y
   RevenueCat (compras dentro de la app, 17.14). Hoy sus claves están vacías por defecto
   (`backend/app/core/config.py:244-265`) y el webhook de RevenueCat responde 503 sin ellas; la política tiene
   que nombrarlos **antes** de encenderlos. Si ya están configurados en producción: [sin verificar] (no se
   leen variables de producción desde una sesión).
3. `legal/` (raíz) y `docs/legal/` tienen versiones distintas de la política de privacidad y de los términos;
   el índice de `docs/` dice que `legal/` (raíz) no manda. Cuál publica la app: [sin verificar].

## Hallazgos de la auditoría (no arreglados aquí)

- `tests/integration/test_security_tracks.py` vive en una carpeta `tests/` de la raíz que
  `backend/pytest.ini` (`testpaths = tests`, relativo a `backend/`) no recoge: probablemente no corre nunca
  [Likely]. Era la única razón para conservar `docs/25.0-planning.md` (archivado el 2026-10-01; el test apunta a `docs/archive/`).
- `docs/README.md` dice «veintiún documentos vivos»; la tabla tiene más filas y el número no lo vigila
  ninguna guarda. Se rehace con la agrupación por propósito (6.6) cuando estén fusionados #50 y #52, que
  tocan el mismo índice.
- Los documentos marcados [sin verificar] en la tabla (API, ARCHITECTURE, RUNBOOK, RELEASE, specs de las
  series 22 y 24) no se han contrastado frase a frase con el código en esta sesión.

