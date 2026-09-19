# Análisis estratégico

`00-auditoria-e2e.html` es la única página de esta carpeta que se ha **medido**: sale de
leer el árbol y de ejecutar los guardias y las suites el 2026-09-19, más peticiones reales
contra producción. Empieza por ahí.

Las otras cuatro son análisis de negocio escritos el 2026-09-18 con el modelo Fable 5.1 en
una sesión interactiva del dueño. **No son documentos normativos** y su estado del producto
venía de una memoria del 08-sep: cada una lleva arriba un aviso con lo que hoy sabemos que
es falso. Si algo ahí contradice a la auditoría, al ledger o a un documento vivo del índice
`../README.md`, gana el otro.

| Fichero | Qué contiene |
|---|---|
| `00-auditoria-e2e.html` | **Estado medido**: contenido, backend, frontend, producción, guardias y lo que no está demostrado |
| `01-como-funciona-y-competencia.html` | Arquitectura resumida, posición competitiva (44/100, techo ≈ 66), probabilidad por segmento |
| `02-proyeccion-ingresos-1k-20k.html` | Neto mensual/anual a 1 K · 5 K · 10 K · 15 K · 20 K usuarios con suscripciones + certs + bootcamps async |
| `03-hito-1M-usuarios.html` | Escenario hipotético a 1 M usuarios con live bootcamps e instructor marketplace |
| `04-coste-desbloqueo-total.html` | Tres caminos (solo · híbrido · equipo), coste por pieza en tres tiers, techo de calidad |

## Errata del 18-sep (se mantiene por trazabilidad)

Los HTML se escribieron desde una memoria del estado del proyecto **del 2026-09-08**.
Entre esa fecha y el 18-sep el proyecto avanzó ~10 series. Afirmaciones que hoy son
**falsas** y que cualquier lector debe ignorar:

| Afirmación en el HTML | Realidad (ledger, 2026-09-18) |
|---|---|
| «Stripe / RevenueCat NO construidos» | 7.2 Stripe checkout+webhook **DONE** (test-mode); 7.3 entitlements **DONE**; 7.6 IAP `HUMAN-BLOCKED` (cuentas) |
| «Solo 3 ficheros de tests; test infra es la mayor deuda» | Q.1–Q.10 **DONE**: 24 unit + 28 integration + 16 e2e; cobertura backend 83 % (11.5) |
| «`exec_correct` viene del cliente — hay que cerrarlo» | 2.3 **DONE**: validación server-side |
| «Login social pendiente» | 19.1 GitHub+Google **DONE** (`48bd81c`); 19.2 Apple `HUMAN-BLOCKED` (H.2) |
| «Onboarding, reset de contraseña, email transaccional no existen» | P.1–P.4 **DONE** |
| «Apps nativas Capacitor pendientes» | 7.5 **DONE** (Android; iOS bloqueado por H.14, sin Xcode) |
| «Observabilidad pendiente» | 6.1–6.7 **DONE** (JSON logs, OTEL, Prometheus, Sentry-compatible, rate limiting) |
| «Accesibilidad WCAG pendiente» | 9.2 **DONE** (axe); 9.7 audit con lector real `HUMAN-BLOCKED` |
| «Legal básico pendiente» | 9.4 **DONE** pero `legal/*.md` aún dice «Learning Engine» y lista planes que no existen → Serie 20/21 |
| «1.253 preguntas» | 5.024+ preguntas · 12+ tracks · 301 skills (fila `Contenido` del ledger) |
| «Marketplace de certificaciones = Fase 10 pendiente» | 10.1–10.3 **DONE** (schema, 300 Q AWS CP, simulacro); 10.4 espera Stripe live (H.4) y ≥ 100 usuarios (catálogo §9) |

Lo que **sigue siendo válido**: el marco competitivo (distribución 34 %, techo ≈ 66
sin usuarios), las proyecciones de ingresos por escala (dependen de conversión, no
del estado del código), la secuencia Tier 1 → distribución → Tier 2 → Tier 3, y la
conclusión de que la única variable que mueve el marcador es la distribución.
