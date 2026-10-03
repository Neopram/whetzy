---
title: "Paquete para la revisión profesional (H.20)"
last_updated: "2026-10-02"
status: "DRAFT — índice y preguntas para el abogado; no es asesoría legal"
---

# Paquete para la revisión profesional (H.20)

H.20 (`docs/AUTONOMOUS_STATE.md`, serie 21: "Revisión profesional de los textos legales antes
de publicar") sigue abierta. Esto no la cierra — es el índice, las preguntas concretas y los
riesgos ordenados por gravedad que un abogado necesita para empezar, reunidos en un solo
sitio en vez de repartidos en 20 ficheros.

**Nada en este documento ni en los que indexa es "cumple", "aprobado" ni "válido
legalmente".** Son investigación y borradores para que un abogado y, donde haga falta, un
fiscalista griego, los revisen.

## 1. Qué manda hoy (para que el abogado no revise lo que no importa)

Por **ADR-55** (2026-10-01), lo único que un usuario ve y acepta — y por tanto lo único con
efecto legal real hoy — son las claves i18n `legal.privacy*`, `legal.terms*` y
`legal.refund*` en `frontend/src/i18n/{es,en}/common.json`, renderizadas por
`LegalScreen.tsx`. **Todo lo demás en `docs/legal/` son borradores sin publicar o
investigación interna** — el código no los carga, ningún usuario los ve. Empezar la revisión
por los textos publicados, no por los borradores.

## 2. Índice de documentos

### 2.1 Publicado (fuente real, revisar primero)

| Qué | Dónde |
|---|---|
| Política de privacidad, términos, reembolsos (claves `legal.*`) | `frontend/src/i18n/{es,en}/common.json` |
| Guarda que exige que la política nombre cada procesador que el código usa | `scripts/check_legal_facts.py` [1b] |

### 2.2 Borradores de cara al usuario, sin publicar (BORRADOR/DRAFT, paridad ES/EN vigilada)

| Documento | Para qué | Fiabilidad |
|---|---|---|
| `ai-notice.{es,en}.md` | Aviso de uso de IA | Sin fuentes citadas — verificar antes de publicar |
| `dpa.{es,en}.md` | DPA para clientes B2B | Lista de subprocesadores (Railway, Cloudflare, Groq, Paddle, Resend/SMTP, Sentry) coherente con `README.md` §"Procesadores verificados"; el resto (plazos, derechos) sin fuente citada por artículo del RGPD |
| `ip-disclaimers.{es,en}.md` | Marcas y PI de terceros | No leído en profundidad en esta pasada — revisar junto a `trademark-search.md` |

### 2.3 Investigación interna (no la ve un usuario; con mi sello de fiabilidad 2026-10-02)

| Documento | Fiabilidad |
|---|---|
| `h29-grecia-paddle-revenuecat-obligaciones.md` | **Nuevo, 2026-10-02.** Fuentes oficiales/semi-oficiales con URL y fecha de lectura. 6 preguntas abiertas concretas (§5 del propio documento) |
| `ai-act-dsa-eaa.md` | **Corregido 2026-10-02** con fuentes; el cuerpo de 2026-09-19 (debajo de la corrección) no citaba ninguna. 3 preguntas abiertas marcadas en la corrección |
| `trademark-search.md` | **Actualizado 2026-10-02**: intento automatizado real documentado (EUIPO/WIPO/USPTO bloquean la consulta sin navegador); falta la búsqueda manual humana |
| `privacy-matrix.md` | **NO FIABLE, con su propio aviso desde 2026-09-19**: sin una sola fuente citada, con un error verificado (plazo de brecha de Brasil: dice 70 días, son 3 días hábiles) y varias cifras sin verificar (CPRA, Ley 21.719 chilena, retenciones de México/Argentina/Chile, autoridad de Perú mal nombrada, "COPPA (13+)" mal descrito). **No reutilizar ninguna fila sin rehacerla con fuente.** |
| `h21-decision.md` | **Histórico, ANULADO.** Un agente autónomo se autoautorizó una decisión de entidad (Estonia OÜ) y rail de pago (Lemon Squeezy) el 2026-09-19 — anulado el mismo día porque un agente no puede cerrar un `HUMAN-BLOCKED` ni decidir un gasto. Queda como registro del error, no como decisión. |
| `H29-DECISION-LOG.md` | **Histórico.** Comparativa Italia vs. Grecia y Stripe vs. Paddle de 2026-09-19, hecha ANTES de que el dueño decidiera (H.29, 2026-10-01). Las cifras de Stripe ya no aplican (H.4, obsoleta: sin Stripe). |
| `antifraud-legal-basis.md`, `dmca-policy.md`, `security-breach-procedure.md` | No revisados en esta pasada |

## 3. Preguntas abiertas concretas (para que el abogado/fiscalista responda, no para que las deduzca)

1. ¿Whetzy (hoy, un solo desarrollador) se registra como persona física
   (ατομική επιχείρηση) en Grecia, o conviene una sociedad (IKE)? — `h29-...md` §5.1
2. ¿Debe darse de alta en el IVA griego desde el primer euro, o hay umbral de exención para
   servicios digitales transfronterizos? — `h29-...md` §5.1
3. Calificación exacta del contrato Whetzy–Paddle (reventa, comisión, licencia) y su efecto
   sobre si la factura Whetzy→Paddle lleva IVA griego, inversión del sujeto pasivo, o queda
   fuera de ámbito. — `h29-...md` §5.2
4. ¿La transmisión a myDATA aplica igual si la factura queda fuera del ámbito del IVA griego?
   — `h29-...md` §5.3
5. Confirmar con `efka.gov.gr` (no con prensa fiscal) la cuota EFKA real y su periodicidad.
   — `h29-...md` §5.5
6. ¿Es Whetzy "microempresa" a efectos de la EAA (Directiva 2019/882, exención de
   obligaciones de servicio por <10 empleados y ≤ 2M€)? — `ai-act-dsa-eaa.md`, corrección 1
7. ¿Es Whetzy "provider" de su propia función de tutor-chat a efectos del art. 50(1) de la AI
   Act (Reglamento 2024/1689), aunque Groq dé el modelo subyacente? — `ai-act-dsa-eaa.md`,
   corrección 2
8. El art. 16 de la DSA (aviso y acción) parece aplicar ya por el `username`/`display_name`
   visible en duelos y ligas (sin filtro ni reportar/bloquear, ledger 19.11) — ¿lo confirma el
   abogado, y qué política mínima exige el texto? — `ai-act-dsa-eaa.md`, corrección 3
9. Nombre legal del titular (responsable del tratamiento, parte de los Términos) — pendiente
   del dueño en todos los borradores (`[ENTIDAD LEGAL PENDIENTE — H.29]`).
10. Garantía de transferencia internacional de cada proveedor fuera del EEE (Groq, Sentry si
    aplica, Resend) — pendiente de confirmar con cada proveedor (`docs/legal/README.md`).

## 4. Riesgos, ordenados por gravedad

**CRÍTICO**

- **Ningún texto legal publicado nombra todavía al responsable del tratamiento real** (placeholder `[ENTIDAD LEGAL PENDIENTE]` en los borradores; lo publicado en `common.json` depende de que el dueño dé el nombre legal — `docs/legal/README.md` §1, pendiente). Sin eso, cualquier reclamación de un usuario no tiene a quién dirigirse formalmente.
- **`privacy-matrix.md` tiene un error de plazo de notificación de brecha verificado (Brasil: dice 70 días, son 3 días hábiles)** y no está en uso en ningún texto publicado — pero si alguien lo reutilizara sin revisarlo, el error pasaría a producción. Marcado NO FIABLE desde 2026-09-19; confirmar que sigue sin usarse antes de cada publicación.

**ALTO**

- **DSA art. 16** probablemente exige ya un mecanismo de aviso y acción por el `username` visible en duelos/ligas (ledger 19.11), sin excepción por tamaño — hoy no existe filtro ni reportar/bloquear (`admin.py` no tiene nada, confirmado 2026-09-30).
- **Calificación fiscal Whetzy–Paddle sin confirmar**: si la factura Whetzy→Paddle requiriera IVA griego y no se está emitiendo así (o viceversa), hay riesgo de sanción tributaria una vez haya ingresos reales.

**MEDIO**

- **AI Act art. 50**: fecha de aplicación 2026-08-02 ya alcanzada; si Whetzy cuenta como *provider* de su función de tutor-chat, la obligación de etiquetar "esto es IA" es directa, no heredada de Groq. Acción de código pendiente, fuera de mi terreno (frontend).
- **EAA**: plazo general ya pasado (2025-06-28); si Whetzy no califica como microempresa exenta, hace falta una auditoría de accesibilidad que hoy no existe (`ai-act-dsa-eaa.md` checklist original, aún sin fuente contrastada para el calendario).
- **Búsqueda de marca incompleta**: el intento automatizado (2026-10-02) no sustituye una búsqueda humana real en EUIPO/WIPO/USPTO; existe al menos una marca fonéticamente próxima en EE. UU. ("WERKZY", clase distinta) sin confirmar en fuente primaria.

**BAJO**

- `privacy-matrix.md` tiene más cifras sin verificar (CPRA, Ley 21.719 chilena, retenciones de México/Argentina/Chile, autoridad de Perú) que no se usan en ningún texto publicado hoy — bajo mientras siga sin publicarse, alto el día que alguien lo use como fuente sin rehacerlo.
- `h21-decision.md` y partes de `H29-DECISION-LOG.md` están obsoletos (Stripe, Estonia OÜ) — riesgo solo si alguien los lee sin ver el aviso de "ANULADO"/histórico que ya llevan.

## 5. Qué no cubre este paquete

- `antifraud-legal-basis.md`, `dmca-policy.md`, `security-breach-procedure.md`,
  `ip-disclaimers.{es,en}.md`: no revisados a fondo en esta pasada (2026-10-02); indexados en
  §2 pero sin fiabilidad evaluada.
- Las 12 filas de `privacy-matrix.md` más allá de Brasil (ya marcado erróneo) no se han
  verificado una por una contra fuente primaria — rehacerlas es trabajo aparte, no este
  paquete.

---

**Generado**: 2026-10-02. No es asesoría legal ni fiscal.
