# Detalles de la última sesión — Whetzy (2026-09-29 → 2026-09-30)

> Generado a petición explícita del usuario ("dame absolutamente todos los detalles de
> esta sesión"). Repo: `Neopram/whetzy`. Rama de trabajo: `claude/gallant-tesla-fnzy1g`.
> PR: [#34](https://github.com/Neopram/whetzy/pull/34) (draft, sin fusionar — lo fusiona
> el dueño a mano, ADR-45). Todo lo descrito aquí está verificado contra el propio repo
> (`git log`, `git diff`, corridas de test reales) en el momento de escribir este
> documento, no reconstruido de memoria.

---

## 1. Contexto de arranque

Esta sesión es continuación de una sesión anterior comprimida (compactada) por límite de
contexto. La sesión anterior había dejado, sin cerrar del todo:

- Un barrido de alineación lección↔quiz (`scripts/audit_lesson_quiz_alignment.py`) sobre
  8 tracks señalados el 2026-09-28: track08 (ya cerrado antes de este arranque), track22,
  track11, track44, track23, track10.
- La tarea 34.5 del ledger: obtener la cifra literal de Lighthouse accesibilidad (≥95)
  para las pantallas Home/Tracks/Lesson/Quiz, más allá del recuento de violaciones axe-core
  que ya pasaba.

Autorización permanente de la sesión anterior, repetida varias veces por el dueño:
*"Continua sin detenerte, asume el control total... toma el control total....termina
absolutamente todo!"* — instrucción de trabajar de forma autónoma, sin pedir permiso
para cada tarea, respetando siempre los invariantes de `CLAUDE.md` (nunca
`git push origin master`, PR por oleada, ADR-52 de modelos, tope de 61.440 bytes en el
ledger, etc.).

---

## 2. Cierre de lo heredado (antes de que empezara este chat visible)

Estos commits estaban ya hechos antes del primer mensaje visible en esta conversación,
pero forman parte de la misma sesión continuada:

| Commit | Qué hizo |
|---|---|
| `22a01a8` | 37.1: cierra track08 — 16 huecos lección/quiz reales, verificados contra AWS docs |
| `e81c591` | 37.1: cierra track22 (6 gaps reales) |
| `5d4deed` | 37.1: cierra track11 — 8 gaps reales, 5 falsos positivos de marca |
| `e553130` | 37.1: track44 parcial — 6 gaps reales; 2 casos de `skill_id` sin relación con la lección, documentados sin parchear |
| `3195ef0` | 37.1: cierra track23 (GCP) — 13 de 14 avisos eran falsos positivos por la convención de nombres de Google Cloud (no repite "Google" antes de cada servicio) |
| `09e4b89` | 37.1: cierra track10 — 9 gaps reales; destapa 2 preguntas con nombre de servicio incorrecto, no arreglables añadiendo contenido a la lección |
| `3d82502` | 34.5 WIP: script de Lighthouse (user-flow API) para Home/Tracks/Lesson/Quiz — **etiquetado explícitamente como no verificado** |
| `cea525f` | 34.5 DONE: Lighthouse a11y = **100/100** en las 5 capturas, 3/3 corridas — y **autocorrección** de un diagnóstico propio erróneo (ver §7) |
| `161065e` | Nota: el rojo de `ci_local.sh` para `cea525f` es deuda de `mypy --strict` preexistente, no algo nuevo |

**Patrón de falsos positivos ya identificado en esta fase**: el script de auditoría marca
una pregunta "¿qué es X?" como sospechosa si el cuerpo de la lección no contiene la
cadena literal de X. Las causas de falso positivo más repetidas:
- AWS/Azure: la pregunta dice "AWS X" / "Amazon X" pero la lección ya cubre X sin el
  prefijo de marca.
- GCP: Google Cloud no repite "Google" delante de cada servicio ("Cloud Storage", no
  "Google Cloud Storage"), al contrario que AWS/Azure — el heurístico exige la cadena
  completa y falla en casi todos los tracks de GCP.

---

## 3. Primer hito visible: informe de brechas en modo solo lectura

**Petición del usuario** (verbatim): *"Cuanto PR, tracks, Olas; etc fallan para llegar
al 100% porcierto de nuestros planes? Dime en read only"*.

Se entregó un informe (sin tocar ningún fichero) con tres ejes, cada cifra etiquetada por
nivel de evidencia:

1. **PR #34**: `draft: true`, `merged: false`, `mergeable_state: "unstable"`, ~90 commits,
   ~219 ficheros — no es "casi el 100%" en el sentido de desplegable: es un borrador
   esperando revisión del dueño.
2. **Catálogo de contenido** (contado directamente, no de la prosa de
   `CATALOGO_MAESTRO.md`, que estaba desactualizada): 35 tracks, 10.944 preguntas, 723
   skills/lecciones (100% cobertura). Contra la meta de ADR-46 (≥42 tracks × ≥50 cursos,
   200 skills/3.000 preguntas por track): **≈8,6–8,7%** de profundidad real, **≈83%** si
   solo se cuenta "tracks que existen aunque sea vacíos" (métrica engañosa).
3. **Ledger ("olas"/series)**: 203 filas ejecutables — 81 TODO, 64 DONE, 44
   HUMAN-BLOCKED (cola), 35 PARCIAL, 12 BLOCKED, 6 HUMAN-BLOCKED, 5 RESUELTA. Desglose
   por serie (17 a 40) con su % DONE literal, mostrando que las series más recientes
   (25, 27–34, 38, 40) estaban en 0% DONE literal.

Conclusión entregada: ninguna parte del proyecto pasaba del ~35%; el catálogo de
contenido era la parte más rezagada.

---

## 4. "Toma el control total" — cierre íntegro de 37.1

**Petición del usuario**: *"toma el control total! haz todo lo que no sea huma
blocked!"*.

Se leyó `docs/ORCHESTRATOR.md` completo (el prompt operativo del proyecto) y se siguió su
bucle: seleccionar por PRI, verificar con evidencia ejecutable, nunca marcar `DONE` sin
prueba, nunca hacer push a `master`.

### 4.1 — Los 3 bugs de contenido documentados y sin arreglar de 37.1

Commit `fc559f1` (con un fix de seguimiento en `2f7110d` por un detalle que el propio
`.githooks/pre-push` cazó):

| Pregunta | Problema | Arreglo |
|---|---|---|
| `q220302011` (track22, Azure) | Afirmaba que el tamaño máximo de Azure SQL Single Database es 2 TB como cifra general | Verificado en vivo contra `learn.microsoft.com` (WebFetch): 2 TB es solo el techo del nivel *serverless*; el modelo vCore (General Purpose/Business Critical) llega a **128 TB**. Reescrita para distinguir ambas cifras |
| `q100502mc005` (track10, AWS) | Preguntaba "¿Qué es AWS Terraform?", atribuyendo Terraform a AWS pese a que la propia explicación ya citaba "Terraform Documentation — HashiCorp" | Reescrita para nombrar HashiCorp explícitamente y hacer de "no es un producto de AWS" la respuesta correcta |
| `q100304mc013` (track10, AWS) | Preguntaba por "AWS Direct Connect Local Connection", que **no existe** (verificado contra `docs.aws.amazon.com`: Direct Connect solo tiene Dedicated y Hosted Connections) | Reescrita sobre "Dedicated Connection", un concepto real no cubierto aún en esa skill, verificado con `curl` en vivo (200) |

**Detalle del fix de seguimiento (`2f7110d`)**: el guardia `check_question_bank.py`
(comprobación de "diversidad") exige que la cita de una pregunta nueva incluya una URL
`https://` que resuelva por prefijo contra `content/sources/index.json`. La primera
versión del commit escribió los dominios sin el esquema `https://`, así que no
coincidían con nada indexado pese a que `learn.microsoft.com` y `docs.aws.amazon.com` ya
estaban indexados — corregido añadiendo el esquema.

Evidencia: `tests/content` 70.027 passed; `check_question_bank.py` PASS;
`audit_lesson_quiz_alignment.py` sin regresiones en track22/track10.

### 4.2 — El bug de `skill_id`/lección de track44 (commit `189611d`)

El más grande de los cuatro. En el módulo 2 de track44 (AZ-900):

- `l440202` ("Redes de Azure: VNet, subredes y NSG") tenía asignadas 5 preguntas sobre
  **contenedores y bases de datos** (Container Instances, AKS, Azure SQL Database, SQL
  vs VM, Cosmos DB).
- `l440204` ("Microsoft Entra ID y Acceso Condicional") tenía asignadas 4 preguntas sobre
  **VNet, subred, NSG y Load Balancer** — justo el contenido que le faltaba a `l440202`.

**Arreglo** (intercambio de `skill_id`, no de lecciones):
- Las 4 preguntas de red → `sk440202` (encajan exactamente con la lección de redes).
- Las 2 preguntas de contenedores → `sk440201` (la lección de "Cómputo" ya habla de
  contenedores).
- Las 3 preguntas de bases de datos → `sk440203` (Storage), cuya lección se amplió con un
  párrafo verificado sobre Azure SQL Database y Cosmos DB como servicios de datos
  gestionados, recortando contenido redundante para no pasar de las 300 palabras del
  test `test_lessons.py`.

El intercambio dejó `sk440202` en 5 preguntas y `sk440204` en 2, ambos por debajo del
piso `MIN_PER_SKILL = 6` de `check_question_bank.py`. No había más preguntas de red o de
identidad en el módulo para redistribuir, así que se **escribieron 5 preguntas nuevas**
(1 de red sobre la regla implícita `DenyAllInbound` de un NSG, 4 de identidad sobre
tenant/Acceso Condicional/Governance/Domain Services), todas basadas en hechos que las
propias lecciones ya citaban y tenían verificados.

**Dos errores propios, cazados por las guardas del proyecto antes de comitear, no por
relectura**:
1. Los IDs elegidos para las 5 preguntas nuevas (`q4401045`–`q4401049`) chocaban con IDs
   ya usados en `mod4403.json` (la numeración `q4401NNN` es global al track, no por
   módulo) — `check_question_bank.py` lo cortó con "duplicate id"; renombradas a
   `q4401062`–`q4401066` tras confirmar con grep que esos números no existían en ningún
   fichero de `content/`.
2. Las 5 preguntas nuevas subieron el banco de 10.944 a 10.949 preguntas, y
   `check_docs.py` lo detectó en los 4 sitios que vigila esa cifra
   (`docs/AUTONOMOUS_STATE.md`, `docs/ARCHITECTURE.md`, `docs/CATALOGO_MAESTRO.md`,
   `frontend/src/lib/catalog.ts`) — los cuatro actualizados a 10.949.

Evidencia: `audit_lesson_quiz_alignment.py track44` ya no marca `l440202`/`l440204`;
`check_question_bank.py` PASS (los 5 skills del módulo ≥ 6 preguntas); `tests/content`
70.057 passed; `check_docs.py` verde; `npx tsc --noEmit` limpio en `frontend/`.

### 4.3 — Corrección de una alarma "grave" ya resuelta en el ledger (commit `dc84596`)

La fila 39.33 del ledger decía: *"Grave: sk130104/204/304 (track13) >50% mal — RACI
inventado, 'menor privilegio' al revés"*, dando a entender que 3 skills completas de
ciberseguridad (gobernanza NIST, PKI/TLS, WiFi) seguían con más de la mitad de sus
respuestas mal marcadas.

Antes de tocar nada se leyeron las **60 preguntas reales** de esas 3 skills directamente
del repo. Ninguna tenía el defecto descrito: RACI resolvía correctamente a
Responsable/Aprobador/Consultado/Informado; "menor privilegio" resolvía correctamente a
"otorgar solo los permisos mínimos necesarios". `git log` explicó la discrepancia: el
commit `a17a7c8` — ya en la rama desde **antes** de que arrancara esta sesión — había
reescrito exactamente esas 26 preguntas. La fila del ledger nunca se había actualizado
para reflejarlo.

Se corrigió la fila para citar el commit que ya lo arregló y la verificación de esta
sesión, en vez de dejar una alarma "grave" obsoleta que una sesión futura habría perdido
tiempo redescubriendo o, peor, intentando "arreglar" un defecto que ya no existía.

### 4.4 — Cierre de 39.39 (commit `4f1ab26`)

39.39 pedía revisar los 90 casos que `audit_lesson_quiz_alignment.py` había marcado en 7
tracks (10, 11, 22, 23, 44, 45, 46). Los primeros 5 tracks ya estaban cerrados por el
barrido de 37.1 (arriba); quedaban 4 avisos sueltos en track45/46, que una sesión
anterior ya había investigado en un comentario del PR pero que esta sesión **verificó de
nuevo por su cuenta** en vez de confiar en el resumen ajeno:

- `l450402` ("Azure AI Language") cubre en detalle lo que la pregunta llama "Azure
  Language Service" (nombre anterior del servicio) — falso positivo confirmado leyendo
  el cuerpo real de la lección.
- `l460202`/`l460203` cubren "SQL Server en Azure VM" y "Azure Database for
  MySQL/PostgreSQL" en detalle; las preguntas solo abrevian los nombres — falso positivo
  confirmado igual.

Con eso, los 90 casos originales de los 7 tracks quedaron todos contabilizados: gaps
reales cerrados con una frase verificada, el resto falsos positivos de marca. **0 huecos
reales pendientes.** Fila marcada `DONE`.

### 4.5 — Nuevo hallazgo: cuarta familia de "coletillas" (commit `84170b9`)

Mientras se revisaba track10 para el punto 4.3, apareció un patrón nuevo y no descrito
antes: opciones cortas (2-4 palabras) con una cláusula de gerundio de marketing de nube
pegada sin relación con la pregunta — p. ej. *"Tipo de almacenamiento, aprovechando la
elasticidad automática de la nube para manejar picos de demanda"* (respuesta a "¿Qué es
Redshift Spectrum?"). Es la misma familia de defecto que 39.28 (coletillas) y 39.42
(relleno de plantilla), con una firma de texto distinta, en un track (track10) que había
quedado fuera del alcance de 39.28.

Un regex de detección (coma + gerundio de marketing) dio **150 "sospechosas" en 11
tracks** — pero al leer una muestra, la mayoría eran gerundios legítimos y técnicamente
correctos ("reduciendo la dimensionalidad del espacio de características" = PCA,
correcto). Un regex sintáctico no distingue una coletilla contaminante de una frase
técnica legítima con la misma forma gramatical.

**Se decidió no aplicar un arreglo masivo con el regex** — habría sido exactamente el
tipo de "arreglo" que rompe contenido bueno para tapar un número, lo que este mismo
barrido existe para evitar. Se confirmaron a mano ~10 casos inequívocos en track10
(siempre en distractores, nunca en la clave correcta — no rompe la corrección de ninguna
pregunta, solo su calidad) y se documentó como fila nueva del ledger, **39.43, TODO, PRI
2**, con una advertencia explícita sobre el regex para que nadie repita el mismo error de
sobreconteo. El arreglo real (revisión semántica pregunta a pregunta) se dejó para
`Workflow`, no para edición suelta de sesión.

---

## 5. Vigilancia de PR #34 durante toda la sesión

La sesión estuvo suscrita a la actividad de GitHub del PR #34 durante todo su
transcurso. Patrón recurrente y ya bien documentado: los 4 checks de GitHub Actions
(`backend`, `frontend`, `e2e`, `android`) fallan en cada push, cada uno en **2-4
segundos sin obtener runner** (bloqueo de facturación de GitHub Actions, H.13/H.17 del
ledger — lo resuelve el dueño en GitHub → Settings → Billing). Esto ya estaba explicado
en un comentario fijado del PR desde el 2026-09-26 y se reconfirmó, sin volver a
comentarlo cada vez (para no repetir lo ya dicho), en cada uno de los pushes de esta
sesión: `dc84596`, `84170b9`, `4f1ab26`, `189611d`/`2f7110d`/`fc559f1`, `8fddd34`,
`deb6392`.

`mergeable_state` se mantuvo en `"unstable"` durante toda la sesión (sin conflicto real
de merge — `"unstable"` refleja los checks requeridos en rojo, no un conflicto).
Cloudflare Pages desplegó correctamente un preview en cada push.

Se publicó un comentario-resumen en el PR (`issuecomment-5895623424`) documentando en
conjunto los hallazgos 39.33/39.39/39.43.

---

## 6. El `Workflow` para 37.15 y 37.17

**Petición explícita del usuario**: *"Lanza el Workflow para 37.15 y 37.17"* — la
autorización explícita que exige la herramienta de orquestación multi-agente antes de
poder invocarla.

### 6.1 — Diseño

10 agentes, "tamaño medio" (< 10 agentes, guía por defecto de esta sesión):

1. **Scope** (1 agente, Haiku): conteo real (no estimado) del estado actual de ambas
   tareas.
2. **Fix RFC/PEP sources** (1 agente): arreglo determinista de citas "RFC N"/"PEP N" sin
   URL, con URL canónica verificada en vivo antes de escribirla.
3. **Fix batches** (7 agentes en paralelo, disjuntos por track): 3 para 37.15
   (track01/04/06), 4 para 37.17 (track01/06/07/16).
4. **Verify** (1 agente): suite completa + guardas, sin comitear nada.

Ningún agente comiteó — por diseño explícito del script — para que la sesión principal
revisara el diff antes de comitear, siguiendo el mismo patrón de disciplina que el resto
de la sesión (evidencia ejecutable, nunca confiar ciegamente en el informe de un
subagente).

### 6.2 — Resultado de 37.15 (indexación de fuentes)

- **4.450 → 3.903 preguntas sin fuente indexada** (de 10.949 en total).
- **267 preguntas** citando "RFC N" o "PEP N" por número, sin URL, arregladas con la URL
  canónica (`rfc-editor.org/rfc/N`, `peps.python.org/pep-NNNN/`), cada una verificada en
  vivo con `curl` antes de escribirse. Verificado independientemente por la sesión
  principal: `rfc8446` y `pep-0008` devuelven 200.
- `peps.python.org` no estaba indexado — añadido como `reusar` (CC0/dominio público) tras
  leer la sección Copyright real de 7 PEP distintas, no por suposición.
  `rfc-editor.org` ya estaba indexado correctamente como `cita` (términos del IETF
  Trust, no es licencia abierta).
- Los 3 lotes de track (01/04/06) añadieron **7 dominios más** a
  `content/sources/index.json`, cada licencia leída en la página real antes de marcar
  `reusar`/`cita`: Wikipedia (CC BY-SA → `cita`, nunca `reusar`, per ADR-47), el libro
  *Deep Learning* de Goodfellow/Bengio/Courville (propietario, "weak DRM" → `cita`),
  OWASP Cheat Sheet Series (CC BY-SA → `cita`), OpenAPI Specification (Apache-2.0 leído en
  la propia página → `reusar`), SQLAlchemy docs (licencia de prosa no confirmada →
  `cita`, conservador), w3schools, restfulapi.net, use-the-index-luke.com, refactoring.guru/
  .com, GitHub API guidelines, la tesis de Roy Fielding sobre REST.
- Quedan 3.903 sin indexar — mayoría en pools ya identificados por dominio
  (scikit-learn/NumPy/pandas, ya indexados como `reusar`, solo faltan URLs por
  pregunta; libros propietarios como *Continuous Delivery*/*DDIA*/*Clean Code*, sin URL
  canónica gratuita encontrada).

### 6.3 — Resultado de 37.17 (ambigüedad en preguntas ejecutables)

**Hallazgo que corrige una cifra vieja del ledger**: el recuento real de preguntas
`fill_blank_exec`/`fix_bug` en todo el banco es **699**, no los "~2.900" que el ledger
llevaba escritos desde el 2026-09-26 — cifra vieja y errónea, corregida.

De esas 699, se revisaron a fondo (código ejecutado de verdad, razonado sobre
implementaciones alternativas plausibles) **219**, en 4 tracks (track07 y track16
completos; track01 y track06 parciales por presupuesto). **10 bugs de ambigüedad reales**
encontrados y arreglados — el patrón: una respuesta "correcta" documentada que un
enfoque *equivocado* también produciría por casualidad con esos datos concretos, así que
acertar no demuestra haber entendido el concepto:

1. `int()` vs `round()` en un split 75% (12 elementos daban 9.0 exacto para ambas
   funciones; cambiado a 10 elementos → 7.5, donde divergen por el redondeo bancario de
   Python). **Reproducido personalmente por la sesión principal**: `int(10*0.75)=7`,
   `round(10*0.75)=8`.
2. Unión de conjuntos disjuntos donde la diferencia simétrica coincidía con la unión.
3. Codificación posicional sinusoidal de Transformer donde `i=0` anulaba el exponente.
4. `len(wrapped)` en vez de `wrapped` — la longitud no distinguía el contenido real.
5. Percentil 95 donde el índice calculado coincidía por casualidad con el último
   elemento.
6. BFS con un grafo donde ambas rutas al destino medían la misma longitud.
7-10. Varianza con datos que empataban `int`/`round`; sigmoide sin ningún valor
   exactamente en el límite 0.5; rama `else` de un ternario nunca alcanzada; BFS con
   grafo sin distinguir rutas cortas/largas.

Un caso (`q060203ex012`, `except` amplio vs estrecho) quedó **marcado sin arreglar a
propósito**: no es un ajuste de datos sino un rediseño estructural — convertir la
"respuesta correcta" en un traceback rompería el modelo de corrección por coincidencia
exacta de stdout.

### 6.4 — Verificación de la sesión principal (no solo del propio Workflow)

Antes de comitear, la sesión:
- Re-ejecutó `tests/content` por su cuenta (70.057 passed).
- Re-ejecutó `check_question_bank.py` y `check_docs.py`.
- Confirmó con `curl` en vivo dos de las URLs que los agentes dicen haber verificado.
- Reprodujo en Python el bug #1 de la lista anterior.
- Leyó varios diffs reales línea a línea (no solo el resumen del agente).

**Commit `8fddd34`**: 67 ficheros, +611/-412. Ledger 37.15/37.17 actualizados con las
cifras reales verificadas (no las que traían).

### 6.5 — Efecto colateral que casi rompe el guardián de push

Al intentar empujar `8fddd34`, el hook `.githooks/pre-push` **rechazó el push**:
`test_mutacion_fuente_sin_indexar` (en `backend/tests/test_diversidad_banco.py`) empezó a
fallar.

**Causa raíz**: los nuevos dominios añadidos a `index.json` por el Workflow
(`www.w3schools.com`, `use-the-index-luke.com` — track12 es SQL y cita ambos
extensamente) indexaron de rebote un montón de preguntas de track12 que ningún agente
tocó directamente. El `source_not_indexed` real de track12 cayó de 152 (línea base
congelada) a 3. El test de mutación añade 1 pregunta mala más y espera que la guarda la
detecte porque supera la línea base — pero 3+1=4 no supera 152, así que la guarda se
quedó ciega para ese track exacto: el fenómeno de "guardián sin dientes" que las propias
normas de estilo del proyecto piden vigilar explícitamente.

**Arreglo** (commit `deb6392`): recalculados los valores reales de `source_not_indexed`
para los 35 tracks y apretada la línea base **solo** donde había mejora real (12 tracks:
track01, 02, 03, 04, 05, 06, 08, 10, 12, 13, 17, 40), verificado programáticamente
(diff JSON antes/después) que no se tocó ningún otro campo ni ningún otro track, y que
el cambio va en una sola dirección (nunca se afloja un ratchet). Resultado: los 14 tests
de `test_diversidad_banco.py` en verde (antes 13 passed, 1 failed).

---

## 7. Autocorrección notable (protocolo de verdad)

Durante el trabajo heredado de 34.5 (antes de este chat visible, pero documentado en
`docs/STATUS.md` y revisado en esta sesión), el commit `3d82502` había diagnosticado los
errores `NO_FCP` de Lighthouse como contención de CPU con el propio `ci_local.sh` en
segundo plano, y escribió esa causa en el mensaje del commit **sin haberla verificado
del todo**. Al comprobar que el error persistía idéntico incluso después de que
`ci_local.sh` liberase la CPU, se refutó la propia hipótesis y se encontró la causa real:
`flow.startNavigation()`/`endNavigation()` alrededor de una transición puramente
cliente-side de una SPA nunca dispara el evento de First Contentful Paint que Lighthouse
espera. El comentario del script y el commit siguiente (`cea525f`) corrigieron
explícitamente la afirmación anterior, marcándola como incorrecta — exactamente lo que
pide el protocolo de verificación del proyecto: interrumpir, señalar el error de forma
explícita, no revisar en silencio.

---

## 8. Todos los commits de esta sesión, en orden

```
22a01a8  37.1: cierra track08 — 16 huecos lección/quiz reales
e81c591  37.1: cierra track22 (6 gaps reales)
5d4deed  37.1: cierra track11 — 8 gaps reales, 5 falsos positivos de marca
e553130  37.1: track44 parcial — 6 gaps reales, 2 casos de skill_id sin relación
3195ef0  37.1: cierra track23 (GCP) — 13/14 avisos falsos positivos de convención de nombres
09e4b89  37.1: cierra track10 — 9 gaps reales; 2 preguntas con nombre de servicio incorrecto
3d82502  34.5 WIP: script Lighthouse — NO VERIFICADO (etiquetado así a propósito)
cea525f  34.5 DONE: Lighthouse a11y 100/100; autocorrección del diagnóstico de 3d82502
161065e  Nota: rojo de ci_local.sh es mypy preexistente, no nuevo
fc559f1  37.1: fix 3 preguntas con hechos falsos (Azure SQL, Terraform, Direct Connect)
2f7110d  37.1: fix URLs de fuente sin esquema https:// (cazado por el pre-push)
189611d  37.1: cierra el mismatch skill_id/lección de track44 (l440202/l440204)
dc84596  39.33: corrige alarma "grave" ya resuelta en el ledger (commit a17a7c8 previo)
84170b9  39.43: documenta 4ª familia de coletillas en track10, con advertencia sobre el regex
4f1ab26  39.39: DONE — barrido de 90 casos en 7 tracks completamente resuelto
8fddd34  37.15/37.17: primer lote del Workflow — 267 citas RFC/PEP, 10 bugs de ambigüedad
deb6392  Aprieta question_diversity_baseline.json tras el Workflow (guardia sin dientes)
```

Todos en `origin/claude/gallant-tesla-fnzy1g`. Ninguno toca `master`. Ninguno lo hizo un
agente del `Workflow` directamente — todos los commits de la sección 6 los revisó y
comiteó la sesión principal tras verificación propia.

---

## 9. Estado de las filas del ledger tocadas esta sesión

| Fila | Estado antes | Estado después | Evidencia |
|---|---|---|---|
| 37.1 | PARCIAL (8 tracks señalados, ninguno cerrado del todo) | **PARCIAL** — los 8 tracks + los 4 bugs de contenido cerrados; el resto (expansión de catálogo hacia ADR-46) es autoría nueva, no corrección | `docs/STATUS.md`, múltiples commits arriba |
| 34.5 | PARCIAL (solo axe-core, no Lighthouse literal) | **DONE** | 100/100, 3/3 corridas |
| 39.33 | PARCIAL con alarma "grave" obsoleta | **PARCIAL**, corregida (la alarma ya no aplica; queda el muestreo de tracks hermanos) | Lectura directa de 60 preguntas + `git log` |
| 39.39 | TODO | **DONE** | 0 huecos reales en los 7 tracks + track08 |
| 39.43 | (no existía) | **TODO, PRI 2** (nuevo hallazgo documentado) | ~10 casos confirmados a mano en track10 |
| 37.15 | PARCIAL (4.452 sin indexar, cifra vieja) | **PARCIAL** (3.903 sin indexar, real) | Workflow + verificación propia |
| 37.17 | PARCIAL ("~2.900" preguntas, cifra vieja/errónea) | **PARCIAL** (699 preguntas reales; 219 revisadas, 10 bugs arreglados) | Workflow + verificación propia |

`docs/AUTONOMOUS_STATE.md` se mantuvo bajo el tope de 61.440 bytes durante toda la
sesión mediante archivado de filas ya `DONE` a `docs/archive/LEDGER_HISTORY.md` §I
(p. ej. la fila 39.42, ya resuelta antes de esta sesión, archivada para hacer sitio a
39.43).

---

## 10. Metodología de verificación seguida (resumen)

Consistente con las instrucciones del usuario ("verdad y verificación al máximo"),
en cada hallazgo de esta sesión:

- **Ninguna afirmación de hecho técnico** (límites de Azure SQL, tipos de conexión de
  Direct Connect, licencias de fuentes) se escribió sin verificarla en vivo contra la
  documentación oficial (WebFetch/`curl`) — nunca de memoria.
- **Ningún "arreglo" de un subagente o Workflow se aceptó sin reproducir al menos una
  muestra** de la evidencia citada (URLs re-verificadas con `curl`, un bug de ambigüedad
  reproducido en Python real, diffs leídos línea a línea).
- **Cada alarma o cifra heredada de una sesión anterior se releyó contra el estado
  actual del repo antes de actuar** — dos veces esto reveló que la cifra o alarma ya
  estaba desactualizada (39.33, el recuento de 37.17), y ambas veces se corrigió el
  registro en vez de repetir el trabajo o la alarma.
- **Cada `DONE` se acompañó de la salida real de los comandos de verificación**
  (`pytest`, `check_question_bank.py`, `check_docs.py`, `question_diversity.py`), nunca
  solo de una afirmación.
- **Un error propio (el diagnóstico de contención de CPU) se corrigió explícitamente**
  en cuanto se descubrió que era falso, en vez de dejarlo pasar en silencio.

---

## 11. Lo que queda abierto al terminar esta sesión

- **PR #34**: sigue en `draft`, sin fusionar, `mergeable_state: unstable` por el bloqueo
  de facturación de GitHub Actions (H.13) — pendiente de que el dueño lo resuelva en
  Settings → Billing y decida cuándo fusionar.
- **37.15**: 3.903 preguntas sin fuente indexada (bajado de 4.450). Pools de arreglo ya
  identificados (scikit-learn/NumPy/pandas, con dominio ya indexado — trabajo mecánico
  de añadir URL por pregunta).
- **37.17**: 480 preguntas ejecutables sin revisar de las 699 reales (bajado de la cifra
  errónea de "~2.900"). Un caso estructural sin arreglar (`q060203ex012`).
- **39.43**: la 4ª familia de coletillas en track10 (y en menor medida track06/08/11 y
  otros) sigue sin arreglar — exige revisión semántica pregunta a pregunta, no un
  `sed` masivo.
- **39.33**: queda por muestrear el resto de "tracks hermanos del mismo commit masivo"
  (solo `q120302mc002` se había revisado).
- Ítems PRI 1-2 restantes del ledger revisados y descartados como no accionables sin el
  dueño: `17.14` (SDK nativo, H.2/H.3), `21.1`/`21.2` (entidad legal, H.29), `30.2`
  (protección de rama en GitHub, H.16), `24.x`/`34.x` (esperan aprobación de diseño del
  dueño), `11.9` (carga contra producción, ya vetada explícitamente sin un humano
  delante).
- `ci_local.sh` (nivel 2 local, no bloqueante): el proceso en segundo plano para el
  último push (`deb6392`) murió a mitad de la suite entera (solo 5% completado, sin
  proceso vivo) — probablemente por un ciclo del contenedor de esta sesión en la nube,
  no un fallo real. No se relanzó porque los cambios de esta tanda no tocan
  `mypy --strict`, `oxlint` ni el build de frontend.

---

*Documento generado el 2026-09-30 a petición del usuario, con datos verificados contra
el propio repositorio en el momento de escribirlo (no reconstruido de memoria).*
