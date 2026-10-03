---
title: "H.29 vigente: qué exige Grecia + Paddle (MoR web) + RevenueCat (IAP tiendas)"
last_updated: "2026-10-02"
status: "DRAFT — investigación para revisión de abogado/fiscalista (H.20); no es asesoría legal ni fiscal"
---

# H.29 vigente: qué exige Grecia + Paddle (MoR web) + RevenueCat (IAP tiendas)

**Esto no es asesoría legal ni fiscal.** Es investigación con fuentes para que un abogado y un
contable griego la revisen (H.20) antes de que el dueño actúe. Ninguna afirmación de este
documento es "cumple" ni "válido legalmente".

## 0. Qué decide este documento y qué no

`docs/AUTONOMOUS_STATE.md` §3 (en `origin/master`, commit `42ec740`, leído 2026-10-02):

> H.29 | DECIDIDO 2026-10-01 (dueño): Grecia; web = Paddle, tiendas = IAP/Play Billing vía
> RevenueCat; sin Stripe. Web: `/checkout` hecho; falta alta Paddle y dominio

Esto **sustituye** la premisa de `ADR-47` (`docs/DECISIONS.md:917-927`, 2026-09-24: "entidad y
jurisdicción sin decidir") y dentro de la fila 21.1/21.2 del ledger, cuyo texto todavía dice
"premisa griega suspendida" (`docs/AUTONOMOUS_STATE.md:184-185`) porque `DECISIONS.md` no se
actualizó tras la decisión del 01-10 — incoherencia documental señalada en
`https://github.com/Neopram/whetzy/issues/89#issuecomment-5961900574` (dueño, 2026-10-02),
pendiente de que S5 registre un ADR nuevo que la corrija (fuera de mi terreno: `DECISIONS.md`
es fichero compartido, solo lo edita S5).

`docs/legal/H29-DECISION-LOG.md` (2026-09-19) compara Italia vs. Grecia y Stripe vs. Paddle
bajo una decisión **todavía no tomada**; hoy esa comparación es historia (Stripe está
descartado — `H.4 | OBSOLETA 2026-10-01: sin Stripe (H.29)`, `docs/AUTONOMOUS_STATE.md:521`).
Este documento no la reemplaza como registro histórico; añade lo que falta: **qué exige
operar ya bajo la decisión tomada** (Grecia + Paddle + RevenueCat), con fuentes de 2026.

## 1. Alta en Grecia (persona física / ατομική επιχείρηση)

Fuente oficial: portal EUGO (Ventanilla Única, réplica del trámite de la AADE) —
`https://eugo.gov.gr/services/788475` (leído 2026-10-02; `aade.gr` devuelve 403 a una
petición automatizada, así que esta es la fuente primaria accesible, no una secundaria).

- **Autoridad competente:** AADE (Independent Authority for Public Revenue), vía el trámite
  "Τα Αιτήματά μου" en myAADE, con credenciales TaxisNet.
- **Formulario:** declaración D211 ("Δήλωση εγγραφής/έναρξης... επιχείρησης").
- **Coste:** gratuito. **Plazo:** ~30 minutos si la documentación está completa; antes de
  facturar la primera operación.
- **Documentos típicos:** identificación (pasaporte/DNI UE), prueba de domicilio del
  negocio (si aplica), y para extranjeros de fuera de la UE, permiso de residencia.
- **Confirmación:** la AADE envía el certificado a la bandeja myAADE
  (`myAADE / Μητρώο & Επικοινωνία / e-κοινοποιήσεις`) — fuente secundaria que coincide:
  `https://www.taxheaven.gr/news/62209/enarxh-atomikhs-epixeirhshs-mesw-govgr-apo-1301`
  (leída 2026-10-02).

**Seguridad social (e-ΕΦΚΑ), cuotas mensuales 2026** (fuente secundaria de prensa fiscal
griega, no oficial — pendiente de contrastar con `efka.gov.gr`):
`https://nerally.gr/arthra/eisfores-efka-eleftheri-epaggelmatias-2025-2026-pinakas.html`
y `https://clevertax.gr/posa-chrimata-tha-plirono-ston-efka-an-kano-enarxi-os-neos-eleytheros-epaggelmatias-i-aytoapascholoymenos-poia-asfalistiki-katigoria-na-epilexo/`
(ambas leídas 2026-10-02):

| Categoría | Cuota mensual total |
|---|---|
| Especial nuevos autónomos (primeros años) | 160,46 € |
| 1ª categoría (ατομική επιχείρηση: 244,65 € + 10 € ΔΥΠΑ) | 254,65 € |
| 2ª categoría | 310,93 € |
| 3ª categoría | 370,63 € |
| 4ª categoría | 443,47 € |
| 5ª categoría | 529,45 € |
| 6ª categoría | 685,87 € |

El `H29-DECISION-LOG.md` (2026-09-19) daba "~€300-400/trimestre"; las fuentes de 2026-10-02
hablan de cuotas **mensuales**, no trimestrales, y más altas que esa cifra — **discrepancia
sin resolver, a contrastar con un contable griego**, no con fuentes de prensa.

## 2. IVA frente al Merchant of Record (Paddle)

### 2.1 Quién es Paddle legalmente

Companies House (Reino Unido), leído 2026-10-02:
`https://find-and-update.company-information.service.gov.uk/company/08172165` —
**Paddle.com Market Limited**, registrada en Inglaterra y Gales (nº 08172165), domicilio
30 Old Bailey, Londres EC4M 7AU, nº de IVA británico GB150848114. Paddle también opera
entidades en EE. UU. (Paddle.com Inc., Nueva York) y Canadá, pero el checkout de Whetzy
(`backend/app/services/paddle_billing.py`) usa la cuenta de producción verificada en
`docs/legal/README.md` ("Paddle | pagos web (Merchant of Record)").

**Consecuencia:** a efectos de IVA, Paddle.com Market Limited es una entidad del Reino
Unido — desde el Brexit, un "tercer país" frente a la UE, no un Estado miembro. Esto importa
para la factura Whetzy→Paddle (§2.3): no es una operación intracomunitaria con inversión del
sujeto pasivo "clásica" (la de un cliente de otro Estado miembro UE), sino una prestación de
servicios a un cliente establecido fuera de la UE.

### 2.2 Qué hace Paddle por el vendedor

Fuentes primarias (Paddle Help Center, leídas 2026-10-02):
- `https://www.paddle.com/help/sell/tax/how-paddle-handles-vat-on-your-behalf`
- `https://www.paddle.com/help/start/intro-to-paddle/how-paddle-is-able-to-take-on-your-vat-and-tax-responsibilities`

Cita literal: *"Paddle acts as a reseller of your product, and is, therefore, the 'seller on
record'. This way, Paddle will be responsible for the collection and payment of VAT and tax
instead of you."* Paddle calcula, cobra y remite el IVA/sales tax al cliente final en cada
país donde sea exigible, y emite la factura al comprador. Ninguna de las dos páginas dice
expresamente qué queda a cargo del vendedor (Whetzy) — remiten a soporte para el detalle.
**No tomar como definitivo sin confirmarlo con Paddle o con el fiscalista.**

### 2.3 Lo que probablemente NO cubre Paddle: la factura Whetzy → Paddle

Paddle actúa de cara al **comprador final**. La relación entre Whetzy y Paddle es, en sí
misma, una prestación de servicios B2B (Whetzy "vende" el derecho de revender su producto
a Paddle, o recibe de Paddle el neto de cada venta, según la calificación contractual exacta
del Master Services Agreement de Paddle — `https://www.paddle.com/legal/terms`, no leído aún
en detalle). Bajo la regla general B2B del art. 44 de la Directiva 2006/112/CE (IVA), los
servicios entre empresas se gravan donde está establecido el **cliente**: si el cliente de
ese servicio es Paddle.com Market Limited (Reino Unido), la prestación cae fuera del ámbito
del IVA griego — sin IVA griego en esa factura, igual que ocurriría con cualquier cliente B2B
no establecido en Grecia.

**Esto es una inferencia mía a partir de la regla general de la Directiva del IVA, no una
fuente que lo confirme para el contrato real Whetzy-Paddle** [etiqueta: Likely, no Verified].
Depende de cómo califique exactamente el MSA de Paddle la relación (¿reventa, comisión,
licencia?) y de si Paddle factura algo de vuelta a Whetzy. Pregunta abierta para el
fiscalista en §5.

### 2.4 Alta de IVA en Grecia y myDATA, con independencia de lo anterior

Iniciar actividad económica en Grecia típicamente obliga a darse de alta en el régimen de
IVA griego (ΦΠΑ) salvo exención por pequeño volumen — el umbral exacto y si aplica a
servicios digitales transfronterizos es otra pregunta para el fiscalista (§5).

Aparte del IVA, Grecia exige la transmisión electrónica de facturas/resúmenes a la
plataforma **myDATA** de la AADE, con independencia de si la factura lleva IVA griego:
fuente secundaria (prensa fiscal, no oficial) leída 2026-10-02:
`https://www.capital.gr/tax/3591986/mydata-upoxreotika-apo-simera-gia-olous-epixeiriseis-kai-epaggelmaties-ta-ilektronika-biblia/`
y `https://www.newshub.gr/el/oikonomia/mydata-ti-allazei-poies-einai-oi-nees-ypochreoseis-pliris-odigos`.
Cronograma citado: facturación electrónica B2B obligatoria desde el 2 de marzo de 2026 para
empresas con ingresos >1.000.000 €, ampliada a todas las empresas griegas desde el 1 de
octubre de 2026. **No verificado contra el texto oficial de la AADE** (403 al intentar
leerlo directamente); a confirmar con el fiscalista antes de asumir la fecha.

## 3. RevenueCat / IAP en las tiendas

Fuente primaria: documentación propia de RevenueCat, leída 2026-10-02:
`https://www.revenuecat.com/docs/dashboard-and-metrics/taxes-and-commissions` — confirma
que son las tiendas (App Store, Google Play, Amazon Appstore) quienes cobran IVA/impuestos
sobre cada transacción, y que RevenueCat solo **estima** esas retenciones para informar al
desarrollador, sin tomar su ubicación como referencia fiscal.

Fuente secundaria que lo dice explícito (leída 2026-10-02):
`https://paywend.com/revenuecat.html` — *"RevenueCat is not a payment processor and not a
merchant of record... Apple and Google are the merchants of record for in-app purchases."*

**Conclusión de esta investigación (Likely, no Verified por una fuente única definitiva):**
Apple y Google son el Merchant of Record en sus tiendas; retienen y remiten el IVA/sales tax
ellos mismos; RevenueCat es solo infraestructura de suscripciones (webhooks, entitlements,
analítica), no cambia quién factura al usuario. Mientras Whetzy no tenga apps publicadas
(ledger 17.14, hoy sin apps en tiendas — RevenueCat con código pero inactivo, por
`docs/legal/README.md`), esta vía no genera obligación fiscal griega adicional.

## 4. Resumen de facturación esperada (a confirmar con el fiscalista)

| Flujo | Quién cobra IVA al usuario | Qué factura Whetzy y a quién |
|---|---|---|
| Web (Paddle) | Paddle, como MoR, en el país del comprador | Posible factura B2B a Paddle.com Market Ltd (UK), probablemente sin IVA griego por la regla general art. 44 — **sin confirmar** |
| App Store / Google Play (RevenueCat) | Apple / Google, como MoR de cada tienda | Ninguna — Whetzy no emite factura al comprador; cobra el neto que liquida cada tienda |

## 5. Preguntas abiertas para el abogado/fiscalista (H.20)

1. ¿Whetzy (persona física en Grecia) debe registrarse en el régimen de IVA griego desde el
   primer euro de actividad, o existe un umbral de exención aplicable a servicios digitales
   transfronterizos?
2. Calificación exacta de la relación contractual Whetzy–Paddle según el Master Services
   Agreement vigente (`https://www.paddle.com/legal/terms`): ¿reventa, comisión o licencia?
   De eso depende si la factura Whetzy→Paddle (si existe) lleva IVA griego, cae en inversión
   del sujeto pasivo, o queda fuera de ámbito.
3. ¿La obligación de transmisión a myDATA aplica igual si la factura está fuera del ámbito
   del IVA griego (venta B2B a un no establecido en Grecia)?
4. ¿Conviene la forma de "ατομική επιχείρηση" (persona física) o una sociedad (IKE) dado el
   volumen de ingresos esperado y el reparto de responsabilidad personal?
5. Confirmar con `efka.gov.gr` (no con prensa fiscal) la cuota EFKA real aplicable y su
   periodicidad (mensual, según las fuentes de 2026 citadas en §1, no trimestral como decía
   `H29-DECISION-LOG.md` de 2026-09-19).
6. ¿Cuándo entra RevenueCat a generar obligación fiscal griega real (al publicar la primera
   app) y cambia algo de lo anterior?

## 6. Fuentes citadas (todas leídas 2026-10-02)

- `docs/AUTONOMOUS_STATE.md:540` (H.29, `origin/master` `42ec740`)
- `docs/DECISIONS.md:917-927` (ADR-47)
- https://github.com/Neopram/whetzy/issues/89#issuecomment-5961900574
- https://eugo.gov.gr/services/788475
- https://www.taxheaven.gr/news/62209/enarxh-atomikhs-epixeirhshs-mesw-govgr-apo-1301
- https://nerally.gr/arthra/eisfores-efka-eleftheri-epaggelmatias-2025-2026-pinakas.html
- https://clevertax.gr/posa-chrimata-tha-plirono-ston-efka-an-kano-enarxi-os-neos-eleytheros-epaggelmatias-i-aytoapascholoymenos-poia-asfalistiki-katigoria-na-epilexo/
- https://find-and-update.company-information.service.gov.uk/company/08172165
- https://www.paddle.com/help/sell/tax/how-paddle-handles-vat-on-your-behalf
- https://www.paddle.com/help/start/intro-to-paddle/how-paddle-is-able-to-take-on-your-vat-and-tax-responsibilities
- https://www.paddle.com/legal/terms (citado, no leído en detalle — pendiente)
- https://www.capital.gr/tax/3591986/mydata-upoxreotika-apo-simera-gia-olous-epixeiriseis-kai-epaggelmaties-ta-ilektronika-biblia/
- https://www.newshub.gr/el/oikonomia/mydata-ti-allazei-poies-einai-oi-nees-ypochreoseis-pliris-odigos
- https://www.revenuecat.com/docs/dashboard-and-metrics/taxes-and-commissions
- https://paywend.com/revenuecat.html

**Estado:** DRAFT — investigación, no asesoría. Generado 2026-10-02.
