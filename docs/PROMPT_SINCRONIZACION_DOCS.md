# Prompt de sincronización de la documentación (Oleada 0 del plan ultracode)

> **Normativo-vivo, de un solo uso.** Texto del dueño del 2026-10-16, escrito sobre `master` `e85900b`.
> Al ejecutarse se archiva en `docs/archive/` (precedente: `INVENTARIO_DOCS.md`). Los `fichero:línea` y
> los números provisionales se vuelven a comprobar con `grep` antes de editar (riesgo R3 de
> `PLAN_ULTRACODE.md` §10); lo que ya cambió desde `e85900b` está en `PLAN_ULTRACODE.md` §0.

> **Aviso al ejecutar.** Desde `e85900b`, #217-#221 cerraron gran parte de las Oleadas 1, 2a, 2b y 6
> (`PLAN_ULTRACODE.md` §0). Varias citas del bloque que sigue apuntan a una línea o a un fichero que no
> es: `bkt.py` está en `services/engine/`, `quiz.py` está en `services/` y `declaredUnknown` está en
> `useOfflineSync.ts:44`. Usa la tabla de §0, no las líneas de abajo.

````
PROMPT_SINCRONIZACION_DOCS — Oleada 0 del plan ultracode (serie 41 del ledger; spec docs/PLAN_ULTRACODE.md)
Pégalo entero como primer mensaje de la sesión. Es de un solo uso: al terminar se archiva.

Tienes control total de esta sesión sobre Neopram/whetzy dentro de ADR-45 (rama + PR; master lo
fusiona solo el dueño). Tu única misión: antes de cualquier código, dejar TODA la documentación
del repositorio diciendo lo que el código y las sesiones hacen HOY. No escribes código de producto
ni contenido (preguntas, lecciones, términos): el dueño lo detuvo por consumo de tokens (ADR-62,
que propones en este mismo PR). Eres el advisor del dueño, no su asistente: evidencia ejecutable o
no pasó; «aplicado pero no verificado» se escribe tal cual; ninguna cifra a mano en un doc.

══ 0. REGLAS DURAS ══
1. Rama `claude/ultracode-0-docs-sync` desde origin/master; PR en borrador desde el primer commit;
   nunca fusiones en master. `git config core.hooksPath .githooks`; nunca `--no-verify`. Cachés
   fuera del proyecto (CLAUDE.md «Invariantes»).
2. Cerrojo `.session.lock` (PROTOCOLO_VERIFICACION §3). Si hay otro vivo (< 6 h), para.
3. Dieta de contexto: docs/AUTONOMOUS_STATE.md NUNCA entero (solo `python scripts/ledger.py
   next|show|series N|stats|blocked|check` y `sed -n` de ≤ 80 líneas). docs/STATUS.md solo head,
   tail y grep. docs/archive/ no se lee, salvo LEDGER_HISTORY.md por secciones (§J decisiones y el
   final, para añadir la §T: la última hoy es §S). Ningún worker pega ficheros enteros.
4. Modelos (CLAUDE.md «Modelos», ADR-52): hilo principal el que fije el dueño; workers de
   escritura y de revisión Sonnet; lecturas, inventarios y verificadores §7 Haiku; NUNCA Fable ni
   Opus 4.x como worker. Si el entorno ofrece un Haiku distinto del que nombra CLAUDE.md:75, no
   cambies la tabla: anótalo en el PR y en la fila H.57.
5. Actúas como S5 (SESIONES.md §4.5). Antes de tocar ficheros con otro dueño (CATALOGO_MAESTRO,
   docs/ml/**, docs/store/**, docs/distribucion-assets/**, content/blog/**, scripts/content_qa/
   README.md) publica en el issue #89 «[S5] NECESITO: barrido documental <fecha>, ficheros: …» y
   limita ahí los cambios a errores de hecho con evidencia. docs/legal/** NO se edita
   (INVENTARIO_DOCS.md «legal: no se toca el texto»; manda lo publicado, ADR-55): sus
   contradicciones se anotan en INVENTARIO_DOCS.md y se escalan.
6. Reglas por clase (INVENTARIO_DOCS.md:9-11): normativo-vivo y referencia-viva se corrigen en
   sitio; lo no verificado lleva `[sin verificar]` y solo se quita con evidencia; histórico
   (STATUS.md, CHANGELOG.md, cuerpos de ADR en DECISIONS.md, docs/ui-snapshots) NO se reescribe,
   solo se añade; obsoleto se archiva; legal no se toca; ningún fichero existente de docs/archive/
   se edita (solo se crean: la evidencia en archive/verificacion/ según PROTOCOLO §4 y la §T de
   LEDGER_HISTORY según PROTOCOLO §5).
7. Las cifras salen de los checks (`python scripts/check_docs.py`, `project_snapshot`,
   `ledger.py stats`, `scripts/catalog_coverage.py`), nunca se teclean (docs/README.md:86-88).
8. Un bug de producto hallado al verificar NO se arregla de paso: fila PRI 0/1 en la serie 42 con
   la reproducción exacta (PROTOCOLO §6).
9. Cada tarea cierra con su commit; un corte por límite de uso no debe perder nada. Al cerrar cada
   fase informa tokens aproximados (bytes leídos / 4) y modelos usados.

══ FASE A — SITUARTE (hilo principal, sin agentes) ══
A1. `git fetch origin && git log --oneline -15 origin/master`; crea la rama. Instala
    `backend/requirements.txt` (sin alembic, check_docs [1] y [5] no vigilan nada).
A2. Lee solo: CLAUDE.md; docs/DECISIONS.md desde «## ADR-45» (incluye ADR-52 de modelos);
    PROTOCOLO_VERIFICACION §3-§7; docs/INVENTARIO_DOCS.md; docs/SESIONES.md §3-§4;
    docs/PLAN_ULTRACODE.md.
A3. Línea base: `python scripts/check_docs.py` (esperado: All checks PASSED),
    `python scripts/ledger.py stats`, `python scripts/ledger.py check`, `wc -c` de todos los .md
    vivos fuera de archive/, node_modules y test-results (fija el presupuesto de la fase B).
A4. Sesiones recientes: `git log --first-parent origin/master --since=2026-09-30
    --format='%h %cs %s'`; lista de PR con el conector de GitHub (o `gh pr list --state all
    --limit 100` si existe). De cada PR desde #34 hasta el último (incluidos #214, #215, #216 y
    posteriores) lee SOLO título, cuerpo y ficheros tocados; construye la tabla PR → áreas y docs
    que invalida. Va al claims file de la fase B.
A5. Define «DONE sin actualizar» antes de tocar el ledger: `ledger.py stats` da DONE 79 de 203;
    toma 5 filas DONE y 5 no-DONE con ID citado en `git log --grep`, y escribe la definición
    operativa (¿falta hash de evidencia?, ¿el estado va por detrás del código?).

══ FASE B — INVENTARIO (Workflow; lectores Haiku, solo lectura) ══
Carga antes la skill `workflow-authoring`. Un agente por lote (≤ 60 KB; lotes por clase y
directorio de INVENTARIO_DOCS.md). Cobertura = TODO lo vivo: CLAUDE.md, README.md, docs/*.md,
docs/ml/*, docs/design/*, docs/store/**, docs/support/*, docs/distribucion-assets/**,
docs/analisis-estrategico/ (README y los 5 HTML), docs/ui-snapshots/*/README.md, docs/legal/*,
design/**/*.md, content/blog/**/*.md, content/_quarantine/README.md,
scripts/content_qa/**/README.md, STATUS.md y CHANGELOG.md (solo cola y cabecera), docs/archive/
(solo comprobar que sigue clasificado). Salida estructurada, no prosa: {ruta, clase según
INVENTARIO_DOCS.md (o «SIN FILA»), bytes, último commit, afirmaciones[≤ 40]: {línea, texto,
tipo: cifra|ruta|ADR|comando|estado|precio|flujo|modelo|promesa, comando o grep que la prueba}}.
Profundidad por nivel: (1) normativo-vivo (18 docs): todas las afirmaciones; (2) referencia-viva:
cifras, rutas, ADR, precios, estados y comandos; (3) legal, store, design, ml,
distribucion-assets, HTML: solo hechos contrastables con grep más una línea de cabecera. Entrega
además la lista de .md sin fila en el inventario.

══ FASE C — CONTRASTE (Workflow; Haiku por documento, máx. 6 en paralelo) ══
Cada agente ejecuta el comando o el grep de cada afirmación y devuelve
{OK | CONTRADICE | OBSOLETA | NO_VERIFICABLE} con `file:line` IMPRESO o la salida del comando.
Sin evidencia impresa no hay OK. Lo que toca producción o exige humano se etiqueta «requiere
cuenta/humano (H.x)», no se ejecuta. Resultado en `docs/archive/verificacion/claims-<fecha>.md`
(tabla `doc | línea | afirmación | comando | resultado | acción`, PROTOCOLO §4; fichero NUEVO, el
precedente es claims-2026-09-18.md).

══ FASE D — CORRECCIÓN (Workflow; Sonnet, un agente por documento, isolation worktree) ══
Un documento = un agente; nadie edita el mismo fichero. Solo corriges CONTRADICE y OBSOLETA. Por
cada cambio entregas la tripleta «qué decía (file:line) → qué dice → file:line del código, ADR o
comando que lo sostiene». No añadas prosa nueva, no cambies tono, no toques lo que está bien.
Español. Las rutas Windows y PowerShell de PROTOCOLO_VERIFICACION y ORCHESTRATOR no se borran: se
añade el equivalente bash para sesiones Linux y cloud.

══ FASE E — REFUTACIÓN (Workflow; Sonnet, un agente por documento corregido, que NO vio la fase D) ══
Misión: demostrar que el doc corregido sigue diciendo algo falso o que se cambió una frase sin
motivo (diff frente a origin/master). Dos refutaciones seguidas del mismo corrector: escala al
hilo principal. Esto se SUMA al verificador §7 de cada fila 41.x (Haiku Explore, solo lectura).

══ FASE F — REGISTROS (hilo principal) ══
F1. Ledger, por secciones y con ledger.py: primero 41.1 (liberar ≥ 6 KB moviendo a
    LEDGER_HISTORY.md §T las evidencias largas de filas DONE y dejando puntero con el ID,
    PROTOCOLO §5); luego inserta lo que falte de la serie 41 y la serie 42 (PLAN_ULTRACODE.md §6)
    entre la fila 40.13 y «## 3. Cola HUMAN-BLOCKED», y las filas H.51… en §3 (formato de H.50,
    AUTONOMOUS_STATE.md:563); `python scripts/ledger.py fases --write` y `ledger.py check`. Pon
    al día los estados según A5, cada DONE con `DONE — <hash> — <comando> → <salida> (<fecha>)`
    tras el verificador §7. Corrige las anomalías del ledger: 21.1 y 21.2 (`:187-188`) sin celda
    de estado y con «jurisdicción sin decidir» cuando H.29 (`:544`) está DECIDIDO; 14.10 colgada
    bajo «### 16»; las filas 22x/25x/28x no las parsea ledger.py (el ID exige punto): decide tras
    leer `ledger.py:65-79` si se renombran o se documentan como fuera de banda; la §6 «Cadena de
    sesiones» vacía mientras ORCHESTRATOR exige anotar ahí.
F2. STATUS.md: UNA entrada nueva al final, «## <fecha> — Puesta al día del registro 2026-10-01 →
    <fecha>», con los PR fusionados (número, título, fecha, hash) y una «fe de erratas» (p. ej.
    STATUS.md:658-662 describe duelos pending/active/completed; el código usa
    pending/in_progress/completed). No reescribas entradas viejas. Solo puedes corregir la
    cabecera «Última actualización del cuerpo» (STATUS.md:3) y lo dices en el PR.
F3. CHANGELOG.md: `## [Unreleased] — <fecha> (Sincronización total de la documentación)`, bloque
    ES, separador `---`, bloque EN espejo.
F4. DECISIONS.md: solo AÑADIR al final, formato `## ADR-NN — título (PROPUESTA de la sesión,
    <fecha>; pendiente de firma del DUEÑO)`. Antes de numerar: `grep -n '^## ADR-'
    docs/DECISIONS.md | tail -1`. Redacta: ADR-61 (transcribe CATALOGO_MAESTRO §22/§23/§25, hoy
    citados como «ADR-61 … prop.» en :58, :97, :461; no inventes contenido), ADR-62 (pausa de
    contenido nuevo y deuda de contenido de estudio; texto en PLAN_ULTRACODE.md §7), ADR-63
    (política de evidencia por fuente y prior; texto en §7) y, si LEDGER_HISTORY §J contiene las
    decisiones D-10, D-17, D-18, D-20 y D-23 que cita el código con fecha 2026-10-12
    (placement.py:203,226; auth.py:74; webhooks.py:74,208; schemas/exam.py:112;
    onboarding.alta.test.tsx), un ADR-64 que las TRANSCRIBA con cita a su origen.
F5. INVENTARIO_DOCS.md: filas para todo lo «SIN FILA»; arregla el resumen de :19-26 (declara 128,
    las tablas tienen 150 filas) con conteos de un comando, no a mano; anota las contradicciones
    de legal. docs/README.md: indexa PLAN_MAESTRO.md, ESTADO_AUTOMATICO.md, MAPA_PRODUCTO.md,
    docs/ml/, docs/support/, restore_log.md.

══ FASE G — GUARDAS (scripts/check_docs.py, tras [14] y antes del cierre de :565) ══
Una guarda por contradicción cerrada. Cada una se prueba: mutar el doc → rojo (pega la salida) →
revertir → verde.
[15] Toda cita «ADR-NN» en un .md vivo (fuera de archive/, STATUS, CHANGELOG, DECISIONS) tiene
     cabecera `## ADR-NN` en DECISIONS.md. Mutación: «ADR-99» en un doc vivo.
[16] Ningún doc vivo dice «20 skills · 300 Q» sin «sustituid|históric» a ±2 líneas (extiende
     [10], :371-406). Mutación: restaurar la frase en ORCHESTRATOR.md:71-73.
[17] Ningún doc vivo dice «$49/año» para certificaciones; la cifra de ECONOMIA.md coincide con
     `CERT_EXAM_USD` (backend/app/core/prices.py:20). Mutación: SEGMENTOS.md.
[18] README.md y ORCHESTRATOR.md no afirman que un bandit decide la pregunta; si un doc cita
     Thompson, `gammavariate`/Thompson existe en backend/app/services/engine/placement.py.
[19] MARKETPLACE.md y DISTRIBUCION.md no dicen que los créditos pagan cursos, simulacros o
     bootcamps (ADR-58).
[20] Los estados de duelo citados en docs vivos ⊆ {pending, in_progress, completed}; ningún doc
     vivo dice «duelos en vivo».
[21] La fecha de la última entrada de STATUS.md y de CHANGELOG.md ≥ la fecha de la última
     cabecera ADR de DECISIONS.md.
[22] El resumen de INVENTARIO_DOCS.md coincide con sus filas y todo .md del repo (fuera de
     archive/, node_modules, test-results, corpus) tiene fila; hoy [12] solo mira docs/.
[23] `ledger.py check` exige evidencia no vacía en filas DONE (mide cuántas fallan hoy y dilo).
[24] Jurisdicción única en docs vivos y en payment_service.py:22 (solo tras la decisión H.54).

══ CONTRADICCIONES CONOCIDAS (cierra todas; el barrido encontrará más) ══
Corregir en sitio (hecho objetivo frente a decisión ya firmada):
- ORCHESTRATOR.md:71-73 molde «20 skills · 300 Q» → ADR-54 (32 × 10, ≥ 3 ejecutables, 1 lección
  y 1 término por skill; CATALOGO_MAESTRO.md:90; CLAUDE.md:12-14).
- SEGMENTOS.md:81 y :288 «certificaciones $49/año» → 39,99 $ pago único (ADR-49; prices.py:20).
- MARKETPLACE.md:98-100 «los cursos se pagan con créditos» → ADR-58 y ECONOMIA.md:44,113.
- DISTRIBUCION.md:310 «créditos para simulacros y bootcamps» → ADR-58.
- README.md:7 y ORCHESTRATOR.md:26 «un bandit decide la pregunta» → real: skill por peso
  1,1−mastery (quiz.py:420), pregunta por |p−objetivo| con Elo (quiz.py:472-476); Thompson solo en
  la prueba de nivel (engine/placement.py:91). ARCHITECTURE.md:91-93 ya lo dice bien.
- Duelos: STATUS.md:658-662 → fe de erratas en la entrada nueva; docs vivos con los estados
  reales; copy «duelos en vivo» en distribucion-assets/guiones/producto-es.md:24 y producto-en.md
  → asíncrono (el copy de código, currency.ts:80,88 e i18n `onboarding.f2d`, lo cierra la
  Oleada 3).
- PROTOCOLO_VERIFICACION.md:65 «STATUS.md (62 KB)» (hoy 201.540 B) y :121 («se corrige como error
  de hecho») frente a INVENTARIO «legal: no se toca el texto».
- PROMPT_CONTROL_TOTAL.md:59 «docs/CLAUDE.md» (es el de la raíz) y «última entrada de STATUS
  (2026-09-24)»; RELEASE.md:3 «Actualizado: 2026-09-18».
- ORCHESTRATOR.md:92-93 «sin perder ni una respuesta» es falso hoy (offlineQueue.ts:65-69):
  «[sin verificar] hasta la Oleada 7» o ajustar a lo que ocurre.
- Banderas comerciales en False (config.py:266,294,299,310,367): ningún doc vivo describe como
  activos el paywall de certificación, el cupo diario, la reserva de simulacro, el marketplace de
  instructores ni el plan Creador.
- docs/analisis-estrategico/*.html (5, sin fila): clasifícalos; si sus precios chocan con
  ECONOMIA.md, aviso de cabecera «histórico fechado; vigente en ECONOMIA.md», sin reescribir.
- Tracks: la landing vende 35 rutas (frontend/src/lib/catalog.ts:12-13) y `catalog_coverage.py`
  da 24 construidos (1 en la forma ADR-54): aclara en CATALOGO_MAESTRO «existentes» frente a
  «construidos»; no toques la landing.
- La Oleada 0 NO arregla: currency.ts:47 `plus: 9.99` (código muerto, Oleada 9);
  payment_service.py:22 (Oleada 9 tras H.54); «Panel de equipo» (legal, H.56).
Escalar al dueño (filas H en §3 del ledger, con la opción recomendada en la fila):
- ADR-61 fantasma (H.54): redactarlo como PROPUESTA con CATALOGO_MAESTRO §22/§23/§25.
- Jurisdicción: Grecia (payment_service.py:22; H.29 DECIDIDO 2026-10-01) frente a Chipre
  (DECISIONS.md:543; CATALOGO_MAESTRO.md:461). Lee el contexto de DECISIONS.md:543 antes de
  proponer. Recomendado: Grecia.
- «Duelos en vivo» (H.52): el duelo es asíncrono; recomendado cambiar el copy, no construir
  tiempo real.
- «Panel de equipo» prometido en docs/legal/b2b_pilot_offer_es.md:23 sin producto
  (EnterprisePage.tsx:3) (H.56): texto legal, no lo edites; recomendado retirar la promesa (S4).
- Modelos (H.57) y cualquier cosa que no sea un hecho comprobable.

══ NO TOCAR ══
Código de producto (backend/app, frontend/src, migraciones), content/** (salvo hechos en
content/blog con aviso en #89), docs/legal/** (texto), entradas existentes de STATUS/CHANGELOG,
cuerpos de ADR existentes (solo añadir ADR nuevos y citas de enmienda en blockquote), ficheros
existentes de docs/archive/, esquema de preguntas (PLAN_CONTENIDO.md:76), docs/ml/kt-benchmark.json
y los iconos de docs/store.

══ FASE H — CIERRE ══
`python scripts/check_docs.py` (con las guardas nuevas), `python scripts/ledger.py check`,
`bash scripts/ci_local.sh`, verificador §7 por cada fila 41.x,
`git mv docs/PROMPT_SINCRONIZACION_DOCS.md docs/archive/` con su fila de INVENTARIO («archivado»)
y la de README. PR con: tabla de documentos tocados (qué decía → qué dice → file:line), guardas con
su salida roja y verde, lista de escalados H.51…, tokens aproximados y modelos usados.

══ CRITERIO DE TERMINADO ══
1. El claims file cubre el 100 % de los documentos del alcance con veredicto y `file:line`.
2. Cero CONTRADICE/OBSOLETA sin resolver: cada una CORREGIDA (tripleta) o ESCALADA (fila H).
3. `check_docs.py` verde con [15]-[23] (y [24] si el dueño decidió); `ledger.py check` OK;
   AUTONOMOUS_STATE.md ≤ 61.440 B con margen ≥ 4 KB.
4. Entradas nuevas en STATUS y CHANGELOG; ADR-61/62/63 con cabecera; filas 41.x DONE tras
   verificador y refutador.
5. `git diff --name-only origin/master` solo contiene docs/, CLAUDE.md, README.md,
   scripts/check_docs.py, scripts/ledger.py y, con aviso en #89, design/**/*.md, content/blog/**
   y los README de scripts/content_qa y content/_quarantine.

══ FORMA DEL WORKFLOW Y PRESUPUESTO ══
Fases B-E en un script Workflow (pipeline por documento: inventario → contraste → corrección en
worktree → refutación); A, F, G y H en el hilo principal. Lectura única estimada (bytes/4): ~1,17 MB
de .md vivos sin STATUS ≈ 290.000 tokens, más ~128 KB de HTML ≈ 32.000 y ~44 KB de docs/ml ≈
11.000; STATUS.md (201.540 B) no se lee; legal (173 KB) solo con grep. Si el consumo preocupa:
cierra por niveles (1 → 2 → 3), cada nivel con su commit; lo no alcanzado queda como filas TODO
con el motivo.
````
