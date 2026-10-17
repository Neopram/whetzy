# Documentos legales

## Qué manda: lo publicado (ADR-55, 2026-10-01)

Los textos que un usuario ve y acepta son la **única fuente**:

| Página | Texto | Pinta |
|---|---|---|
| whetzy.com/privacy | claves i18n `legal.privacy*` (`frontend/src/i18n/{es,en}/common.json`) | `LegalScreen.tsx` → `PrivacyContent` |
| whetzy.com/terms | claves `legal.terms*` | `TermsContent` |
| whetzy.com/refund | claves `legal.refund*` (desistimiento: `legal.termsP5withdrawal`) | `RefundContent` |

Cambiar una política es cambiar esas claves en los dos idiomas. Las versiones largas
que vivían aquí y en `legal/` (raíz) eran borradores nunca publicados que ya se
contradecían con lo publicado (Stripe como procesador, «14 días de prueba gratis»,
`[ENTIDAD LEGAL PENDIENTE]`): están en `docs/archive/legal-borradores/` como material
para la revisión profesional (H.20), no como texto vigente. `scripts/check_legal_facts.py`
impide que vuelva una segunda copia aquí ([5b]) y exige que la política publicada nombre
a cada procesador que el código usa ([1b]: Paddle, Groq, Resend, Sentry).

Pendiente del dueño para que lo publicado esté completo: el **nombre legal del titular**
(responsable del tratamiento y parte de los Términos) y confirmar con cada proveedor
fuera del EEE la garantía de su transferencia (H.20).

## Qué hay en esta carpeta

**Borradores de cara al usuario que la app aún no publica** (llevan BORRADOR/DRAFT; la
guarda vigila su paridad ES/EN):

- `ai-notice.{es,en}.md` — aviso de uso de IA
- `dpa.{es,en}.md` — acuerdo de tratamiento de datos para clientes B2B
- `ip-disclaimers.{es,en}.md` — marcas y propiedad intelectual

**Textos comerciales sin publicar** (movidos desde `content/legal/` el 2026-10-01; ningún
código los carga):

- `affiliation_dossier_{es,en}.md` — dossier de afiliación (38.3)
- `b2b_pilot_offer_{es,en}.md` — oferta de piloto B2B (38.2)
- `credits_terms_{es,en}.md` — condiciones de los créditos (economía, serie 29)
- `instructor_recruitment_kit_{es,en}.md` — kit de reclutamiento de instructores (28.9)

**Instrumentos internos** (no los ve un usuario):

- `antifraud-legal-basis.md`, `dmca-policy.md`, `security-breach-procedure.md` — movidos
  desde `legal/` (raíz) el 2026-10-01
- `ai-act-dsa-eaa.md`, `privacy-matrix.md`, `trademark-search.md` — investigación
- `h29-grecia-paddle-revenuecat-obligaciones.md` — investigación vigente (2026-10-02) de lo
  que exige operar bajo H.29 (Grecia, Paddle MoR, RevenueCat); `H29-DECISION-LOG.md` queda
  como historia de la comparación anterior a la decisión, con Stripe (ya descartado)
- `H29-DECISION-LOG.md`, `h21-decision.md` — historia de decisiones de entidad y pagos

## Procesadores verificados (2026-10-01)

| Proveedor | Uso | Prueba |
|---|---|---|
| Railway | servidores y PostgreSQL | la API vive en `api.whetzy.com` (dominio propio servido por Railway) |
| Cloudflare | web (Pages) y correo entrante (Email Routing) | MX de whetzy.com → `route*.mx.cloudflare.net` |
| Groq | explicaciones del tutor con IA, sin nombre ni correo | `backend/app/services/ai/provider.py` |
| Resend | correos de la cuenta | log de producción «Email: proveedor resend» |
| Sentry | errores del servidor, `send_default_pii=False`, región UE | log de producción «Sentry initialised (env=production…)» |
| Paddle | pagos web (Merchant of Record) | `backend/app/services/paddle_billing.py`, webhook en 200 |

RevenueCat (compras en las apps) tiene código pero no está activo: no hay apps en las
tiendas (17.14). Se nombra en la política el día que se encienda.
