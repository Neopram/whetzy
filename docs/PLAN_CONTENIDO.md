# Plan de producción de contenido (ADR-59)

> Normativo vivo desde el 2026-10-03. Manda sobre cómo se escribe contenido nuevo para el
> alumno: preguntas, lecciones y términos. Las metas siguen siendo las de ADR-54. Las cifras
> pendientes no se copian aquí: salen de `python scripts/catalog_coverage.py`.

## 1. Qué falta y por qué hace falta un método

El 2026-10-03, tras fusionar el #99, `catalog_coverage.py` sobre `master` daba **4.522 preguntas pendientes**:

- 2.610 para llevar los 24 tracks construidos a la forma 32 × 10, con +261 skills, +261 lecciones
  y +266 términos;
- 872 de práctica de certificación;
- 1.040 reservadas.

`question_diversity_baseline.json` suma además 3.903 preguntas cuya fuente no está indexada
(fila 39.8).

Ese volumen no se escribe a mano en una sesión. Escribirlo «de memoria» con un modelo ya falló
dos veces, las dos con Haiku 4.5:

- **Piloto de track28 (2026-09-26):** 7 de 10 lecciones con relleno, errores técnicos o fuentes
  que no respaldaban el texto (ADR-52, «Riesgo»).
- **Piloto de 39.37 (track20):** en la ronda 1, `correct_index` era siempre 0; en la ronda 2,
  6 de 10 preguntas eran redundantes (`STATUS.md`). Con Sonnet como autor, la fila quedó DONE.

## 2. Decisiones (ADR-59, dueño, 2026-10-03)

1. La autoría masiva va por **`Workflow`**.
2. **Escribe Sonnet 5.** Revisa y corrige Sonnet 5. Haiku 4.5 solo hace lecturas, inventarios
   y diffs.
3. **Primero el piloto de 10 ítems** (fila 37.25). Si más de 3 de 10 salen con problema
   `blocker` o `major`, se para y decide el dueño.
4. El contenido corre **en paralelo** al piloto con alumnos (31.8).
5. **Un solo motor.** La producción nueva la lleva la sesión coordinadora. S2 cierra sus PRs en
   curso y no empieza autoría nueva.

## 3. Método: escribir desde la fuente

Ninguna pregunta se escribe de memoria. Cada pregunta sale de un **fragmento concreto** de una
fuente marcada `reusar` en `content/sources/index.json`. Las licencias permitidas son MIT,
Apache, BSD, CC BY, CC0 y PSF (ADR-11, 46 y 47). CC BY-SA, NC y propietarias **no** se
reutilizan: se citan y se enlazan.

1. **Corpus fuera del repo** (`corpus/` está en `.gitignore`, ADR-46). El pipeline de
   `scripts/corpus/` es este:
   ```bash
   python -m scripts.corpus.fetch --name <n> --kind git --url <url> [--sparse <carpetas>]
   python -m scripts.corpus.verify_license --name <n>
   python -m scripts.corpus.clean --name <n> --track <trackNN>
   python -m scripts.corpus.index --name <n> [--alias <url>]   # solo si la fuente es nueva
   ```
   El contenedor de una sesión en la nube es efímero: hay que descargar el corpus en cada
   sesión. Para no repetirlo, el dueño puede añadir el paso al setup script del entorno
   (cola humana).
   **Corte en fragmentos (local, sin agentes, desde el track44):** un script parte cada
   artículo por encabezados `##`/`###` en trozos de 40 a 600 palabras, con
   `{id, repo, file, title, url, heading, text}`. A cada escritor le llega en el prompt solo el
   paquete de fragmentos de su skill; ningún agente lee artículos enteros.
2. **Escritor (Sonnet 5):** recibe la skill, el fragmento (texto limpio de
   `corpus/<n>/clean/`) y su URL. Primero decide `correct_index` y solo después escribe las
   opciones. Así no se repite el bug de 39.37. La respuesta correcta tiene que poder deducirse
   del fragmento, sin saber nada más. El campo `source` lleva la URL indexada. No se añaden
   campos al esquema de `content/questions/`.
3. **Revisor (Sonnet 5), revisión adversaria completa, no por muestreo:** contrasta cada
   pregunta con su fragmento. Etiqueta cada defecto como `blocker`, `major` o `minor`: respuesta
   no respaldada, distractor correcto, redundancia con otra pregunta, relleno o error técnico.
4. **Corrector (Sonnet 5):** arregla lo marcado. Lo que no se pueda arreglar se descarta; no se
   rebaja la etiqueta.
   **Comprobación literal (local):** cada frase del `fragment` que cita la pregunta tiene que
   aparecer en el fragmento fuente. Un script lo comprueba antes de integrar; el campo
   `fragment` no entra en el banco.
   **Variante `cita` (AWS, ADR-59 «Fuentes `cita`»):** el escritor redacta con sus palabras a
   partir del fragmento, sin copiar frases; el revisor marca `major` cualquier copia de más de
   8 palabras seguidas; `source` enlaza `docs.aws.amazon.com`. La comprobación literal se
   invierte: falla si hay copia.
5. **Puerta de `CATALOGO_MAESTRO.md` §7**, completa y ejecutada:
   - `scripts/content_qa/*` (`check_key_drift`, `check_expl_key`, `check_only_fields` y
     `check_urls`);
   - `pytest backend/tests/content` (los ejecutables con su fill en
     `exec_reference_solutions.json` o `sql_exec_reference_fills.json`);
   - `scripts/check_question_bank.py`;
   - `scripts/question_diversity.py` (en track nuevo, umbrales exactos; en track con baseline,
     no empeorar ninguna métrica);
   - `scripts/catalog_coverage.py --check`;
   - `scripts/check_docs.py`.

## 4. Piloto (fila 37.25)

- **10 ítems de una sola skill** de una certificación **sin PR abierto**: track44 (AZ-900), por
  ejemplo. Nunca en track43, track40 ni track01 mientras sigan abiertos #99, #102 o #106.
- **Se mide:** defectos por etiqueta antes y después del corrector, ítems aceptados, coste en
  tokens por ítem aceptado y tiempo de pared.
- **Resultado:** en la descripción del PR del piloto y en el #89. La cifra de coste se anota
  aquí, en §7.
- **Regla de parada:** si más de 3 de 10 salen `blocker`/`major` tras la revisión, se para, se
  anota en el ledger y decide el dueño. No se cambia de modelo ni de método por cuenta propia.

## 5. Orden de producción (si el piloto pasa)

1. **37.10, certificaciones:** primero MLA-C01 (track43, cuando se fusione el #99) y las tres
   de Microsoft (track44 AZ-900, track45 AI-901 y track46 DP-900). Después, el resto de la
   regla de ADR-54.
2. **37.6, tracks construidos a la forma 32 × 10:** primero los de nivel A, luego B y C. Cada
   skill nueva lleva su lección y su término.
3. **39.8:** indexar la fuente de las preguntas que no la tienen, o dejar la lista exacta de las
   que no se pueden indexar.

## 6. Organización

- **Rama y PR por track:** `claude/youthful-allen-i8k7zb-<trackNN>`, con unas 100 preguntas o
  más por PR. Un bloque que no pasa la puerta no existe.
- **Fusiones de una en una.** Cada PR actualiza las líneas de cifras que comprueba
  `check_docs.py`: la fila «Contenido» del ledger, `docs/ARCHITECTURE.md` (cifras del banco),
  `CATALOGO_MAESTRO.md` §1 y `frontend/src/lib/catalog.ts`. La cifra real la da
  `scripts/project_snapshot.py`.
- **Nivel 2** como tarea gestionada (`ci_local.sh --carril <track>`), y LISTO en el #89 solo
  con VERDE (regla 7d). Fusiona el dueño (ADR-45).
- **Paralelo por dentro, en serie por fuera:** el `Workflow` escribe varias skills o tracks a la
  vez sobre ficheros disjuntos, y se fusiona un PR detrás de otro.

## 7. Registro

| Fecha | Qué | Resultado |
|---|---|---|
| 2026-10-03 | Plan escrito y decisiones del dueño (ADR-59) | Piloto 37.25 pendiente |
| 2026-10-03 | **Piloto 37.25:** 10 Q de sk440203 (AZ-900, Azure Storage) desde 4 artículos de `azure-docs` (CC BY 4.0) | Revisión: **0 blocker, 1 major** (distractor defendible, corregido), 17 minor; 0 descartadas; 10/10 citas literales (comprobado con búsqueda en el texto). Puerta §7 PASS. Coste: 21 agentes Sonnet, 1.762.599 tokens de subagente según el Workflow (≈ 176 k por pregunta aceptada, casi todo relectura de artículos de ~3.400 palabras), 212 s de pared. Precio en dólares sin calcular |
| 2026-10-04 | **Producción 37.10, track44 (AZ-900):** 190 Q en 10 skills (sk440201–sk440305), desde fragmentos de 7 repos de Microsoft Learn (CC BY 4.0; `entra-docs`, MIT) | Integradas 190, 0 descartadas; posiciones 48/47/47/48. Revisión del pase que entra: **1 blocker y 17 major en 17 preguntas** (8,9 %, bajo el umbral del 30 %), 433 minor; todas corregidas; releídas a mano contra su fragmento las 7 marcadas como no literales o no respaldadas y 5 al azar. Comprobación literal: 190/190 (el script cazó una mutación a propósito). Puerta §7 PASS. **Coste: 58.358.792 tokens de subagente, ≈ 307 k por pregunta**, porque fueron **dos pases**: el primero (29,1 M) se quedó sin 18 correctores por el límite de sesión, y al reanudarlo la caché solo sirvió a los 19 escritores; revisores y correctores corrieron otra vez (29,2 M). Un pase completo habría costado ≈ 153 k por pregunta, frente a 176 k del piloto: los fragmentos casi no abaratan. Pendiente: averiguar por qué la reanudación no reutilizó a los revisores antes del próximo track |
