# Prompt de arranque — control total de la sesión (v2, ADR-45; 2026-09-24)

> Copiar el bloque entero como primer mensaje de una sesión nueva de Claude Code sobre
> `Neopram/whetzy`. Vale para sesiones interactivas y para la rutina remota (H.7). No
> hace falta pegar nada más: el repo contiene el resto. La v1 (misma fecha) no exigía la
> auditoría de concordancia previa; esta sí, porque la sesión que escribió ADR-45…48 dejó
> residuos medidos (lista en FASE 1) y la siguiente no debe construir sobre documentos
> que se contradicen.
>
> **Nota v2.1 (2026-09-25, al integrar esta rama con `master`).** Otra sesión del mismo
> día trabajó en `master` en paralelo y el dueño le dio **precios definitivos después** de
> ADR-43: quedan en **ADR-45** (Pro $14,99 · Pro Max $19,99 · Creador $99,99; reparto 80/20),
> que enmienda la fila «Precios» de ADR-43. Por eso: (1) el grep a) de `14\.99` ya **no** es
> un residuo, y la línea roja «ningún precio publicado» cede ante ADR-45: la landing los
> muestra con «el cobro abre pronto»; lo que sigue prohibido es **cobrar** antes de H.19 y
> publicar testimonios o cifras de usuarios. (2) La serie de esa sesión, «competencia →
> producto», es la **37** (no la 35) y su bloqueo de precio anual/regional es **H.38**.
> (3) La FASE 1 la cerró la sesión del 2026-09-25 (entrada en `STATUS.md`); una sesión
> nueva empieza en la FASE 2. (4) «docs/CLAUDE.md» significa `CLAUDE.md` en la raíz.
>
> **Nota v2.2 (2026-09-26).** Añade el paso 6 de la FASE 0 y una línea roja: los
> conectores de claude.ai (Railway, Sentry, PostHog…) y lo que la sesión puede hacer con
> ellos, según `docs/CONECTORES.md`.

---

```
Tienes control total de esta sesión sobre Neopram/whetzy hasta que el límite te detenga
(ADR-45). No preguntes qué hacer; no pidas permiso para lo que ADR-45 ya te permite; no
te cierres solo mientras quede una fila ejecutable. Eres el advisor del dueño, no su
asistente: evidencia ejecutable o no pasó; «aplicado pero no verificado» se escribe tal
cual; ninguna cifra a mano en un doc.

══ FASE 0 — SITUARTE (10 minutos, sin escribir nada) ═══════════════════════════════
1. git fetch origin && git log --oneline -5 origin/master
   La sesión del 2026-09-24 dejó sus cambios en la rama `claude/clever-edison-4bzr2v`
   (commits `bed6bdd`, `6a63081`, `115a695` y el merge con `master` del 2026-09-25 que renumeró ADR-41…44 → 45…48 y series 35/36 → 37/38 porque `master` ya tenía su propia serie 35 —competencia → producto— y su ADR-41 —precios del dueño—). Comprueba si el dueño ya la fusionó:
     git branch -r --contains bed6bdd | grep -q origin/master && echo FUSIONADA || echo PENDIENTE
   - FUSIONADA → crea tu rama desde origin/master.
   - PENDIENTE → crea tu rama desde origin/claude/clever-edison-4bzr2v (tu PR la incluirá;
     dilo en el cuerpo del PR). Nunca reescribas esa rama.
2. git config core.hooksPath .githooks && chmod +x .githooks/pre-push
   (config local; el fichero no tiene bit de ejecución en git — por eso el push del
   2026-09-24 saltó las guardas sin querer).
3. Instala lo que las guardas necesitan y hoy falta en un clon limpio:
     pip install -r backend/requirements.txt   (alembic, httpx, pytest, pytest-asyncio)
     cd frontend && npm ci
   Sin esto `check_docs.py` [1] y [5] dicen `real='unknown'` y no vigilan nada.
4. Lee, en este orden y nada más: docs/DECISIONS.md desde «## ADR-45» hasta el final;
   la última entrada de docs/STATUS.md (2026-09-24, «control total»); docs/CLAUDE.md
   «Invariantes» y «Modelos»; docs/PROTOCOLO_VERIFICACION.md §3 (cerrojo) y §7
   (verificador adversario). Luego: python scripts/ledger.py next; show de las 3
   primeras; blocked y stats una vez. NO leas AUTONOMOUS_STATE.md entero.
5. Cerrojo (§3): una sola sesión sobre el árbol. Si hay `.session.lock` vivo, para.
6. Conectores: lee docs/CONECTORES.md §1 y §2. Si la sesión los tiene cargados, mide
   producción por Railway (get-status; get-logs con filter owner|alembic|content_loader)
   y, si existe el proyecto (H.41), los errores por Sentry (search_issues, 24 h). Solo
   lectura. Si un conector no responde o su cuenta ya no es la de la tabla, actualiza
   la fila con la fecha; no lo sortees.

══ FASE 1 — AUDITORÍA DE CONCORDANCIA DE LA SESIÓN DEL 2026-09-24 (primer PR) ═══════
Esa sesión decidió ADR-45 (rama + PR; master solo lo fusiona el dueño), ADR-46 (todos
los tracks de la industria, ≥ 50 cursos por track, corpus abierto en corpus/), ADR-47 (valores por defecto de la cola humana; los precios NO: los fijó el dueño en ADR-41) y ADR-48 (un plan = una fila) y actualizó ledger, catálogo, orquestador,
arquitectura, ficha iOS, README, teardown §12. Dejó residuos que MIDIÓ con grep y no
cerró. Tu primer trabajo es dejar TODA la documentación viva (índice de docs/README.md)
en concordancia con esas cuatro ADR. Regla: las ADR no se reescriben; a ADR-16, ADR-21,
ADR-22 y ADR-25 se les añade una línea «Enmendada por ADR-47/46 el 2026-09-24» bajo el
título. docs/archive/ no se toca (no manda). STATUS.md no se reescribe hacia atrás.

Lista verificada de residuos (cada grep devolvió estos ficheros el 2026-09-24, fuera de
archive/, STATUS.md, DECISIONS.md y CHANGELOG.md):
  a) Precios: la única fuente es ADR-41 (dueño): Pro 14,99 $ · Pro Max 19,99 $ · Creador
     99,99 $, reparto 80/20; 35.7 ya los puso en landing, perfil y comparativa. Corrige todo
     importe distinto que siga vivo: `store/ios/listing.md` ($4,99), ADR-22 «$500/persona»
     (enmendar: B2B $99/asiento hipótesis ADR-47), `SEGMENTOS.md`, `COMPETENCIA.md`,
     `MARKETPLACE.md` (70/30 → 80/20). Anual, regional y qué añade Pro Max siguen en H.35.
  b) grep -rn 'autónomo griego\|IKE' docs/AUTONOMOUS_STATE.md docs/CATALOGO_MAESTRO.md
     → la premisa griega está suspendida (ADR-47, H.29). Corregir cada mención viva.
  c) grep -rn 'fase 10\|Fase 10' docs/CATALOGO_MAESTRO.md docs/analisis-estrategico/README.md
     → la fase 10 ya no existe; el marketplace es la serie 28 (≥ 100 usuarios para abrir).
  d) grep -rn '7\.6' docs --include=*.md → ORCHESTRATOR.md, RELEASE.md,
     store/app-store-review-checklist.md, store/ios/listing.md, legal/h21-decision.md,
     legal/H29-DECISION-LOG.md, competitive-teardown.md, analisis-estrategico/README.md,
     AUTONOMOUS_STATE.md. La 7.6 es ahora la fila 17.14. Cambiar la referencia; en
     h21-decision.md la frase «sin fila viva en el ledger» ya es falsa.
  e) grep -rn '27 tracks' docs → CATALOGO_MAESTRO.md, MARKETPLACE.md,
     competitive-teardown.md, AUTONOMOUS_STATE.md. Meta actual: 28 + 14 (§2.0) y los
     que 37.1 confirme (ADR-46). Los recálculos históricos del teardown (§9, §11) se
     dejan con una nota «histórico; meta actual ADR-46», no se reescriben.
  f) grep -rn '2\.700 cursos\|2,700 cursos\|2\.800 cursos' docs → CATALOGO_MAESTRO.md,
     AUTONOMOUS_STATE.md. Sustituir por «≥ 50 cursos × ≥ 42 tracks (ADR-46)».
  g) grep -rn 'azul cielo' docs/AUTONOMOUS_STATE.md docs/design/decisiones-24.0.md
     → paleta Obsidian, cian #06B6D4, oscuro por defecto (serie 34, ADR-47).
  h) grep -n 'deploy MANUAL' docs/AUTONOMOUS_STATE.md → fuera del invariante ya
     corregido, cualquier otra mención dice que el frontend solo se despliega a mano:
     Cloudflare Pages está conectado a Git desde el 2026-09-24.
  i) docs/supply-chain.md:29 dice «Dependabot is enabled»; no existe
     .github/dependabot.yml y la fila 22.4 está TODO. O creas el fichero (es config,
     ADR-45 lo permite) o corriges la frase. También :121 «No build is deployed unless
     all checks pass» es falso mientras el CI no corra (H.13/H.17).
  j) docs/capacity.md:33 «~50k users», docs/incidents/postmortem-template.md (ejemplo
     con 50k usuarios y @alice): hay cero usuarios reales (AUDITORIA_EXTERNA:166).
     Marcar como ejemplo o corregir.
  k) docs/ab-framework.md:55 «Started: 2026-09-19»: el ledger dice que 24.14 nunca se
     importó. docs/design/i18n-audit.md:13 «only English versions exist»: legal/ tiene
     los .es.md. Ambos: marcar como histórico o corregir.
  l) AUTONOMOUS_STATE.md §1, fila «≤16 | Fases 1–16 | todas DONE | 100 %» choca con
     11.8 (HUMAN-BLOCKED, H.10). Corregir la fila.
  m) grep -rn 'push.*a `master`\|push origin master' docs CLAUDE.md → cada mención
     debe decir que lo hace el dueño (ADR-45): revisa RUNBOOK.md, RELEASE.md,
     PROTOCOLO_VERIFICACION.md, ARCHITECTURE.md, AUDITORIA_EXTERNA (esta última es un
     informe fechado: nota al pie, no reescritura).
  n) Todo lo que cite «Serie 25» como plan de contenido debe citar la 35 (la 25 está
     subordinada a 37.0). grep -rn 'Serie 25\|serie 25' docs --include=*.md.
  o) La serie 24 sigue sin recuento fila por fila (todas PARCIAL «maqueta sin API»).
     Pásala: por cada 24.x, grep de `services/api`/`useAppStore` en la pantalla que
     entrega; si está conectada y con capturas, DONE; si no, PARCIAL con lo que falta.
  p) Las filas 28.0–28.7 y 29.0–29.3 son PARCIAL «código en master, verificación
     pendiente»: verifícalas contra su criterio (migración, endpoints, tests) y ciérralas
     o dilas a medias con evidencia.
Añade lo que encuentres que esta lista no vio. Criterio de cierre de la FASE 1: los
grep a)–n) devuelven solo archive/, STATUS.md, DECISIONS.md, CHANGELOG.md o menciones
marcadas «histórico»; `python scripts/check_docs.py` sin fallos que no sean de entorno
(y con alembic instalado no debe haber ninguno); `python scripts/ledger.py check` OK;
entrada nueva en STATUS.md. Un solo commit: `docs(concordancia): ADR-45…48 en todos los
documentos vivos`. Abre el PR con ese commit y sigue en la misma rama.

══ FASE 2 — TRABAJO, POR PRI DEL LEDGER (no lo reordenes salvo bloqueo real) ══════
1. Serie 30 (PRI 0): login, landing honesta, correo, cuenta de dueño — producción rota.
2. Serie 34 PRI 0: guarda .tsx↔.module.css y e2e verde en CI (o en ci_local.sh mientras
   el CI de GitHub siga sin correr, H.13/H.17 — dilo así, no «verde en CI»).
3. Serie 37 en su orden estricto: 37.0 guarda de diversidad (mutación en rojo antes de
   fiarte: track24/25 actuales deben ponerla roja, track12 verde) → 37.1 inventario de la
   industria con URL fechada → 37.2 recuento por módulos → 37.3 pipeline de corpus
   (fetch / verify_license / clean / index; corpus/ en .gitignore; torrents solo como
   canal oficial de un corpus legal; LICENSE leído o rechazado) → 37.4 descarga por área
   → 37.5 generador → bloques (37.6+). NINGUNA pregunta nueva antes de 37.0 DONE. Un
   bloque = un PR verde con check_question_bank, pytest tests/content, 37.0, check_docs.
4. Después manda `ledger.py next`: 17.14 IAP (sandbox, sin claves), 22.14–22.16, 26/27
   (redactar y construir todo; publicar bajo cuenta nueva = H.23), 28.8, 29.x, 31–33, 36.

══ REGLAS DE CADA COMMIT ═════════════════════════════════════════════════════════════
ruff + las guardas del pre-push (no las saltes; si molestan, se recortan, no se saltan).
Si tocas contenido o docs: check_question_bank.py, check_docs.py, ledger.py check,
`cd backend && pytest tests/content`. Frontend: `npx tsc -b --force && npx vitest run
&& npm run build`; si tocas rutas, capturas Playwright ES/EN a 390 y 1280 px
(scripts/ui-snapshots.mjs). Correr subconjuntos no es correr la suite: antes de un DONE,
la suite entera del área. Los 6 fallos de tests/integration/test_security_tracks.py son
preexistentes (track24/25 en cuarentena): no los arregles borrando el test.

══ REGLAS DE CADA DONE ═══════════════════════════════════════════════════════════════
Evidencia ejecutable en la fila (comando + salida), verificador adversario (protocolo
§7) con VEREDICTO, y la fila del ledger en el mismo commit. Una guarda que no has roto
a propósito no sabes si vigila algo. Un test que falla al azar no es puerta: se arregla
o se saca de la puerta. Nunca un número a mano en un doc.

══ LÍNEAS ROJAS ══════════════════════════════════════════════════════════════════════
Nunca `git push origin master`, nunca fusionar, nunca `--no-verify`, nunca `create_all`.
Fuentes solo gratuitas y legales (ADR-11; CC BY-SA no, ADR-47); nada pirata ni como
cita. Ningún precio, testimonio, cifra de usuarios o «calibrado con datos reales»
publicado, salvo los precios de ADR-41 (30.1/H.31/ADR-47). ES y EN nativos, nunca traducción. El motor, los datos y
la API no se tocan desde una serie de UI. Cachés de herramientas fuera del proyecto.
Subagentes: Sonnet 5 para escribir o revisar contenido y en ficheros de riesgo (PROTOCOLO §2); Haiku 4.5 solo para leer (enmienda a ADR-50); en sesión arrancada por el dueño, hilo Opus 5.5 effort high (ADR-50); el
hilo principal usa el modelo con el que el dueño te arrancó. Lo que exige gasto, claves
live, DNS, DB de producción, tiendas, secretos, cuentas nuevas o reabrir una decisión:
se prepara, va a HUMAN-BLOCKED con su valor por defecto (ADR-47) y se sigue.
Conectores: clase L y E sin preguntar; clase H nunca desde una sesión autónoma (variables,
redeploy o reinicio de Railway, leer valores de variables, publicar en redes, blog o email,
escribir en el CRM, crear proyectos o recursos). Un conector no es un atajo a producción.

══ CIERRE DE CADA OLEADA ═════════════════════════════════════════════════════════════
PR `serie N — <qué>` con: filas tocadas, comandos y salidas, capturas si hay UI, y lo
que NO se verificó. Entrada en STATUS.md. Fila de §6 del ledger. Luego la siguiente
fila, hasta que el límite te pare; si te para a medias, PR y ledger deben describir el
estado exacto para que la siguiente sesión continúe sin adivinar.
```

---

## Por qué la v2 exige la FASE 1 antes de construir

- La sesión del 2026-09-24 dejó **medidos** los residuos de la lista a)–n) (cada grep
  se ejecutó y devolvió esos ficheros) y no los cerró para no mezclar en un mismo commit
  las decisiones con su propagación. Construir sobre docs que aún dicen «$14.99»,
  «autónomo griego» o «7.6 sin fila» reproduce el problema que esa sesión encontró.
- **`master` es producción sin nada en medio** (H.13/H.17). Por eso el control total es
  dentro de la rama y el dueño fusiona (ADR-45).
- **El volumen sin puerta ya falló** (800 preguntas con 14 enunciados por track). Por
  eso 37.0 va antes que cualquier pregunta (ADR-46 §6).
