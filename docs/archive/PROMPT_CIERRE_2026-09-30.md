> **Archivado el 2026-10-01:** prompt de un solo uso, ejecutado (el PR #34 se fusionó el 2026-10-01); el cierre vigente es `docs/CIERRE_2026-09-30.md`.

# Prompt de cierre para la sesión del PR #34 (2026-09-30)

Uso: el dueño pega el bloque de abajo, tal cual, en la sesión que trabaja en
`claude/gallant-tesla-fnzy1g`. Es la última tarea de esa sesión: al acabar, informa y para.
Contexto completo: `docs/CIERRE_2026-09-30.md`.

```
PROMPT FINAL — cerrar el PR #34 y dejar el proyecto en pausa (decisión del dueño 2026-09-30)

El dueño va a cerrar esta sesión y la otra. Esta es tu ÚLTIMA tarea. No hay nadie a quien
preguntar: si algo no se puede hacer, lo documentas en el PR #34 y sigues con lo siguiente
que no dependa de ello. Al final, informe y PARAS.

## Reglas absolutas (ninguna tiene excepción)
- Nunca `git push origin master`, nunca fusionar, nunca `--no-verify`, nunca `create_all`,
  nunca reescribir historia (sin rebase/amend/force-push).
- Nada de trabajo nuevo: ni features, ni contenido, ni métricas. Solo lo de este prompt.
- Nada contra producción: ni Railway (variables, deploys, backups), ni base de datos,
  ni cuentas. La copia de seguridad y la fusión son del dueño.
- Cada afirmación del informe final, etiquetada [Verified] (comando + salida en esta sesión),
  [Likely] o [Guessing]. "Aplicado pero no verificado" cuando lo sea.
- Trampas conocidas: ruff 0.16.8; vitest con Node 22 (no antepongas /usr/local/bin al PATH
  para vitest); nunca `pkill -f`/`pgrep -f` con un patrón que esté en tu propio comando
  (mata por PID); `PYTHONUNBUFFERED=1` para logs de pytest; ledger ≤ 61.440 bytes.

## Paso 1 — Traer los documentos de cierre
1. `git fetch origin` y confirma que tu árbol está limpio y en la cabeza de tu rama.
2. `git merge --no-ff origin/claude/eloquent-davinci-47pbpf`. Trae SOLO:
   `docs/CIERRE_2026-09-30.md`, `docs/PROMPT_CIERRE_2026-09-30.md` y una fila en `docs/README.md`.
   Comprueba con `git diff --stat HEAD^1 HEAD` que no trae nada más. Si hay conflicto o trae
   otros ficheros, aborta el merge (`git merge --abort`), anótalo en el PR y sigue sin él.
3. Lee `docs/CIERRE_2026-09-30.md` entero. No lo reescribas; si encuentras un dato falso,
   corrígelo con evidencia y dilo en el informe.

## Paso 2 — La pausa, escrita donde la lee cualquier sesión nueva
1. `CLAUDE.md`: sustituye la frase que manda ejecutar `docs/ORCHESTRATOR.md` sin
   instrucciones por: «**PAUSA desde el 2026-09-30 (decisión del dueño).** Si arrancas sin
   instrucciones explícitas del dueño, NO ejecutes `docs/ORCHESTRATOR.md`: lee
   `docs/CIERRE_2026-09-30.md`, informa del estado y para.»
2. `docs/ORCHESTRATOR.md`: el mismo aviso como primer bloque del fichero.
3. Guarda en `scripts/check_docs.py` (sección nueva): si `docs/CIERRE_2026-09-30.md`
   contiene «Estado: PAUSA», entonces `CLAUDE.md` y `docs/ORCHESTRATOR.md` deben contener
   «PAUSA» y citar `docs/CIERRE_2026-09-30.md`. Mutación obligatoria: quita el aviso de
   cada uno → rojo; restaura → verde.
4. Ledger: una fila corta (serie 31) «Pausa de sesiones autónomas y cierre, 2026-09-30 →
   docs/CIERRE_2026-09-30.md», DONE con el commit. Archiva lo necesario para seguir
   ≤ 61.440 bytes. Entrada breve en `docs/STATUS.md`.
5. `check_docs.py`, `ledger.py check` y `ruff` en verde. Commit.

## Paso 3 — Corregir el cuerpo del PR #34 (sección «Antes de fusionar»)
- Producción corre **`e83bf63`**, despliegue Railway **`68d3289f`**, no `ec9e702`
  (corrígelo en e) y en «Producción»).
- a) Copia de seguridad: primero la vía del panel (servicio **`Postgres`** → pestaña
  **Backups** → copia manual; fuente `docs.railway.com/volumes/backups`); después la CLI con
  el servicio real: `railway postgres pitr backup create --service Postgres --name pre-merge-pr34`.
- Añade: «El PR está en borrador: márcalo "Ready for review" antes de fusionar.»
- Añade al principio del cuerpo: «Guía completa del dueño: `docs/CIERRE_2026-09-30.md` §4.»

## Paso 4 — Un push y UN veredicto completo sobre esa cabeza
1. Push una sola vez con todo lo anterior (`git push -u origin claude/gallant-tesla-fnzy1g`;
   si falla por red, reintenta con 2 s, 4 s, 8 s, 16 s). Anota el SHA: es la cabeza a verificar.
2. El push lanza el nivel 2 (`ci_local.sh`). Vigílalo: cada ≤ 15 min,
   `bash scripts/ci_local.sh --estado`. Si el proceso murió, relánzalo UNA vez con
   `bash scripts/ci_local.sh --sha <SHA>` y mantén la sesión activa. Si muere otra vez, corre
   cada paso a mano desde `backend/` y `frontend/`, con salida a fichero:
   - `python -m pytest tests/ --ignore=tests/content -q -p no:randomly`
   - `python -m pytest tests/content -q -p no:randomly`
   - `python -m pytest tests/ -m slow -q -p no:randomly` (límite ≥ 60 min)
   - `python -m mypy app --strict --ignore-missing-imports`
   - `npx tsc -b` y `npx vitest run` (Node 22)
3. VERDE solo si TODOS los pasos terminan sin fallos. Algo que muere por tiempo no es verde.
4. Si sale ROJO:
   - Si la causa está en código del PR y el arreglo es pequeño: arregla con test en rojo antes,
     commit, push y vuelve al punto 2. Como mucho 2 ciclos.
   - Si no: NO arregles. Documenta en el PR el paso, el test y la salida literal, y deja el PR
     en borrador.

## Paso 5 — Comentario final en el PR #34
- Una tabla: paso · comando · resultado literal (línea de resumen) · etiqueta.
- La frase exacta «VEREDICTO: VERDE sobre <SHA>» o «VEREDICTO: ROJO sobre <SHA> — <motivo>».
- Si VERDE y tienes herramienta para ello: quita el borrador (Ready for review). Eso NO es
  fusionar. Si ROJO: déjalo en borrador.
- Termina con: «El dueño sigue `docs/CIERRE_2026-09-30.md` §4. Esta sesión se cierra.»

## Paso 6 — Limpieza antes de parar
- Borra los recordatorios o rutinas que ESTA sesión programó (send_later / triggers). Lista
  con `list_triggers`, borra solo los tuyos, confirma que la lista ya no los tiene.
- Cancela la suscripción a la actividad del PR #34.
- Para las tareas de fondo que queden; `git status` limpio y rama empujada.

## Paso 7 — Informe final (en el chat) y PARA
1. SHA final y VEREDICTO.
2. Qué hiciste en cada paso, etiquetado.
3. Qué quedó sin hacer y por qué.
4. La lista del dueño, en orden: copia de seguridad → Ready for review → fusionar →
   comprobar → H.13 → lanzamiento a 20–50 personas.
Después de este informe no hagas nada más, aunque lleguen eventos del PR.
```
