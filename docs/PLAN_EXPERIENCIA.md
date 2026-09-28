# Plan maestro de experiencia: superar a Brilliant y Kodree donde hoy ganan

> **Documento vivo nº 21.** Abierto el 2026-09-28 a petición del dueño. Las filas
> ejecutables son la **serie 40** de `AUTONOMOUS_STATE.md`; este documento es su
> spec. Un plan que no sea una fila del ledger no es un plan (ADR-48).
>
> **Punto de partida.** `COMPETENCIA.md` §A.2b (captura del 2026-09-28): con todo el
> backlog cerrado, a Whetzy le seguían faltando cinco cosas que Brilliant o Kodree
> tienen, y ninguna fila las cubría. Son problemas visuales manipulables, tutor por
> voz que señala, comunidad dentro de la app, planes anual/vitalicio/familiar, y
> rutas de análisis de datos, TypeScript/Java y UX/UI.

## 0. Qué significa «superar» aquí

Igualar no basta. Cada pilar dice qué hace el rival, qué hará Whetzy **además**
y cómo se mide. Hasta que la fila 40.13 lo mida, **ninguna** afirmación de
superioridad sale a la landing ni a un listing (línea roja 9). Las ventajas
estructurales de Whetzy entran en cada pilar:

- **Motor adaptativo.** Todo lo nuevo alimenta BKT, FSRS y Elo; nada es un
  contenido aparte.
- **Certificaciones.** Todo se mapea a un dominio de un exam guide y suma al
  *readiness*.
- **Bilingüe.** ES y EN nativos (línea roja 3).
- **Líneas rojas del ORCHESTRATOR.** Offline (4), privacidad (5), accesible (6) y
  rápido en móvil (8) son la vara, no un extra.

## 1. Pilar A: problemas visuales manipulables (frente a Brilliant)

**Qué tiene Brilliant.** Lecciones de lienzo interactivo: el alumno mueve
piezas y ve la consecuencia. En programación se queda en lo conceptual y en
Python. No da certificados, no publica declaración de accesibilidad y su
secuencia es fija. Datos en `COMPETENCIA.md` §A.2b; parte son reportados y no
reproducidos.

**Qué hará Whetzy además:**

1. **Cada manipulación es un ítem del motor.** Nuevo tipo de pregunta
   `interactive`: estado inicial, objetivo y un *checker* determinista. El
   resultado actualiza BKT/Elo y entra en el repaso espaciado de FSRS.
   Brilliant no anuncia repaso espaciado.
2. **Widget y código en los dos sentidos.** Al mover el widget se reescribe el
   código de ejemplo. Al ejecutar código en Pyodide, sql.js o el Worker de JS,
   el widget se anima con el resultado real. Ningún rival une el lienzo con un
   runtime real.
3. **Widgets de certificación.** Subnetting CIDR (Network+/CCNA), evaluador de
   políticas IAM (AWS), grafo de commits de Git, handshake TCP, JOIN de SQL,
   planificador de CPU. Brilliant no toca ese terreno.
4. **Accesible de verdad.** Cada widget se puede operar solo con teclado y
   tiene alternativa textual equivalente. Axe da 0 violaciones.
5. **Offline y ligero.** Solo React + SVG, sin motor gráfico. Carga perezosa
   por widget, con presupuesto de **≤ 30 KB gz por widget**, medido en el build.

**Arquitectura.**

- **Esquema.** `interactive` = `{widget, params, target, checker}` en
  `content/` con esquema validado por `check_question_bank.py`.
- **Doble corrección.** El checker corre en cliente, para dar feedback
  inmediato, y en servidor, para puntuar. Si los dos discrepan, el test se pone
  en rojo.
- **Una sola fuente.** Una biblioteca `frontend/src/widgets/` con un contrato
  común: `render`, `serialize` y `check`. Un widget sin test de contrato no se
  registra.

**Piloto antes de escalar**, como el vídeo (18.9):

- **Qué entra.** Tres widgets: búsqueda binaria (track16), CIDR (track17) y
  JOIN (SQL), con 10 ítems cada uno en ES/EN.
- **Cuándo escala.** Solo si el e2e pasa en móvil y escritorio, axe da 0, el
  presupuesto de peso se cumple y el LCP de la lección sigue < 2,5 s en 4G.

## 2. Pilar B: tutor que habla y señala (frente a Koji de Brilliant)

**Qué tiene Koji.** Voz (ElevenLabs), dibuja en el lienzo y no da la
respuesta. No publica qué modelo de texto usa ni si cita fuentes. Datos
reportados en `COMPETENCIA.md` §A.2b.

**Qué hará Whetzy además:**

1. **Cita o calla** (línea roja 2). Cada respuesta hablada lleva sus fuentes
   en pantalla. Si no hay grounding, lo dice en voz alta.
2. **Señala, no garabatea.** El tutor devuelve **acciones estructuradas**
   validadas contra un esquema: resaltar la línea 7, marcar este nodo, animar
   este paso del widget. Sin trazos libres: es reproducible, testeable y
   accesible, porque cada acción tiene su descripción textual.
3. **Sabe en qué fallas.** El contexto incluye las skills débiles según BKT.
   Koji «tracks what you've mastered», pero no dice con qué modelo.
4. **ES y EN nativos en voz.** Koji solo existe en inglés.

**Decisiones que no toma la sesión (H.49):**

- **Texto a voz.** Por defecto (ADR-47), `speechSynthesis` del navegador: voces
  locales del sistema, sin coste y sin tercero. Piper (MIT) en servidor queda
  como alternativa si la calidad ES no basta.
- **Voz a texto.** La API de voz de Chrome envía el audio a Google, lo que
  choca con la línea roja 5. Las alternativas son un STT del proveedor LLM
  actual o Whisper local en WASM, que pesa y choca con la línea roja 8. Decide
  el dueño.
- **Condiciones fijas, decida lo que decida:** pulsar para hablar,
  consentimiento explícito, audio no almacenado (solo la transcripción) y todo
  documentado en la política de privacidad.
- **Coste.** La voz cuenta contra el cupo de 38.6 y contra el techo de gasto
  diario de 39.11. El tutor ilimitado de Pro Max (ADR-49) incluye voz solo si
  el techo de gasto lo sostiene. Eso se mide antes de anunciarlo.

## 3. Pilar C: comunidad con contexto (frente a Kodree)

**Qué tiene Kodree.** Chat de comunidad genérico dentro de la app. Dato
reportado en `COMPETENCIA.md` §A.2b.

**Qué hará Whetzy además:**

1. **Hilos pegados al contenido.** Un hilo por pregunta y por lección. Las
   soluciones de otros se ven **solo después** de haberla resuelto o agotado,
   para no regalar la respuesta.
2. **Grupos de estudio por certificación**, con fecha de examen y readiness
   medio del grupo, sin datos personales de nadie.
3. **Revisión por pares de los proyectos** de 37.11. Los revisores son
   usuarios con la credencial Open Badges del track (29.10).
4. **Salas separadas ES y EN.** No se mezclan idiomas en un mismo hilo.

**Moderación desde el día uno.**

- Se reutiliza `question_report` para denunciar, más límite de frecuencia y
  antifraude (29.5).
- Procedimiento de notificación y retirada redactado ES/EN (serie 21). La
  política la aprueba el dueño.
- **Se construye entera y se abre al público solo con ≥ 100 usuarios
  activos.** Es la misma regla que el marketplace (`CATALOGO_MAESTRO.md` §9):
  una comunidad vacía resta.

## 4. Pilar D: planes anual, vitalicio y familiar, con mejor trato (frente a los dos)

**Qué tienen.**

- **Brilliant:** $161.88/año y plan familiar de $45/mes para 6 plazas.
  Reembolso «solely as a courtesy».
- **Kodree:** $98.99/año y $199.99 de por vida. Reembolso solo si
  completaste un módulo y renovaciones no reembolsables.

**Qué hará Whetzy además.** Los precios los fija el dueño (ADR-41), así que
aquí solo se construye el andamiaje y se propone el trato:

1. **Modelo de asientos.** Una suscripción con N plazas (familiar o equipo
   pequeño), con entitlements por plaza. Reutiliza lo del piloto B2B (38.2).
2. **Cancelar en dos toques** (línea roja 7), con aviso de renovación antes de
   cobrar un anual (ya exigido en la UE, 21.4).
3. **Propuesta de reembolso (H.50).** 14 días sin condiciones en el primer
   pago y prorrata del anual si se cancela en el primer mes. Es mejor que las
   dos políticas medidas y es un argumento de venta. Decide el dueño.

## 5. Pilar E: rutas que hoy no están en el catálogo

1. **Analista de datos ejecutable.** pandas en Pyodide + SQL en el navegador,
   con datasets de licencia abierta (ADR-11). Kodree enseña Excel/Power BI sin
   ejecutar nada en la lección, según lo publicado. La certificación a mapear
   (p. ej. PL-300) se confirma con URL antes de construir.
2. **TypeScript ejecutable.** Transpilar en el Worker de JS con carga perezosa
   solo en el track de TS (línea roja 8). Las fuentes y la licencia del
   compilador se verifican antes de construir.
3. **Java y UX/UI: primero investigación.** Java en el navegador exige un
   runtime pesado o de licencia incierta. UX/UI hoy tiene una sola fuente
   (`CATALOGO_MAESTRO.md` §2.0.1). Cada uno entra en el catálogo solo con
   fuentes libres verificadas (H.LIC) y un runtime que cumpla la línea roja 8.

## 6. Orden y dependencias

1. **Motor y piloto:** 40.1 y 40.2. La puerta es el piloto verde.
2. **Tutor y planes:** 40.5–40.6 (el tutor que señala necesita widgets) y, en
   paralelo, 40.9 (planes).
3. **Escala:** 40.3–40.4 (biblioteca de widgets) y 40.7–40.8 (comunidad,
   cerrada al público).
4. **Rutas:** 40.10–40.12.
5. **Medición:** 40.13 cierra la serie. Sin ella, nada de esto se anuncia.

## 7. Lo que este plan no promete

- **Adelantar a Brilliant en todo.** Brilliant tiene un equipo de contenido
  dedicado a matemáticas escolares; Whetzy no entra en ese terreno.
- **Ganar a Kodree en rutas no técnicas** (gestión de proyectos genérica,
  diseño gráfico).
- **Una fecha.** Cada fila se cierra con evidencia, no con calendario.
