# Prompt de arranque — control total de la sesión (ADR-41, 2026-09-24)

> Copiar el bloque entero como primer mensaje de una sesión nueva de Claude Code sobre
> `Neopram/whetzy`. Vale para sesiones interactivas y para la rutina remota (H.7).
> No hace falta pegar nada más: el repo contiene el resto.

---

```
Tienes control total de esta sesión sobre Neopram/whetzy hasta que el límite te detenga.
No preguntes qué hacer; no pidas permiso para lo que ADR-41 ya te permite; no te cierres
solo mientras quede una fila ejecutable.

CONTRATO (docs/DECISIONS.md ADR-41…44; docs/ORCHESTRATOR.md «Contrato de autonomía»):
1. Trabaja en la rama que te asignen (o crea `claude/<nombre>` desde origin/master).
   Abre un PR desde el primer commit y mantenlo al día. NUNCA `git push origin master`,
   NUNCA fusiones: master lo fusiona el dueño a mano tras ver el preview de Cloudflare.
2. Sin preguntar: código, tests, contenido, docs, migraciones aditivas en local,
   scripts, dependencias del proyecto, reorganizar, descargar/verificar/limpiar corpus
   abierto en corpus/ (ADR-42). Detente y escribe en HUMAN-BLOCKED (ledger §3) solo
   para: gasto, claves live, DNS, datos de usuarios reales, DB de producción, tiendas,
   secretos, crear cuentas en servicios, reabrir una decisión cerrada.
3. Valores por defecto de la cola humana: ADR-43. Asúmelos; no esperes al dueño.

ARRANQUE (docs/ORCHESTRATOR.md «PRE-FLIGHT»):
- git config core.hooksPath .githooks   (config local; en un clon nuevo hay que repetirlo)
- python scripts/ledger.py next          (NO leas AUTONOMOUS_STATE.md entero)
- python scripts/ledger.py show <ID> de las 3 primeras; `blocked` y `stats` una vez.
- Lee docs/PROTOCOLO_VERIFICACION.md §7 (verificador adversario) antes del primer DONE.

ORDEN DE TRABAJO (por PRI del ledger; no lo reordenes salvo bloqueo real):
1. Serie 30 (PRI 0): login, landing honesta, correo, cuenta de dueño — producción rota.
2. Serie 34 PRI 0: guarda .tsx↔.module.css y e2e verde en CI.
3. Serie 35 en su orden estricto: 35.0 guarda de diversidad (mutación en rojo antes de
   fiarte) → 35.1 inventario de la industria con URL fechada → 35.2 recuento por módulos
   → 35.3 pipeline de corpus (fetch/verify_license/clean/index; torrents solo como canal
   oficial de un corpus legal) → 35.4 descarga por área → 35.5 generador → bloques.
   Ninguna pregunta nueva antes de que 35.0 esté DONE. Un bloque = un PR verde.
4. Después, `ledger.py next` manda: 17.14 IAP, 22.14-22.16, 26/27 (redactar todo;
   publicar bajo cuenta nueva = H.23), 28.8, 29.x, 31-33, 36.

CADA COMMIT: ruff + guardas del pre-push; si tocas contenido o docs, además
`python scripts/check_question_bank.py`, `python scripts/check_docs.py`,
`python scripts/ledger.py check`, `cd backend && pytest tests/content`. Frontend:
`npx tsc -b --force && npx vitest run && npm run build`. Correr subconjuntos no es correr
la suite: antes de cerrar una fila como DONE, la suite entera del área.

CADA DONE: evidencia ejecutable pegada en la fila (comando + salida), verificador
adversario (protocolo §7) con VEREDICTO, y la fila del ledger actualizada en el mismo
commit. «Aplicado pero no verificado» se escribe tal cual. Nunca un número a mano en un
doc: sale de check_docs.py o no sale.

LÍNEAS ROJAS (no negociables): fuentes solo gratuitas y legales (ADR-11; CC BY-SA no,
ADR-43); ningún precio, testimonio, cifra de usuarios o «calibrado con datos reales»
publicado (30.1/H.31); ES y EN nativos, nunca traducción; el motor, los datos y la API
no se tocan desde una serie de UI; nunca `create_all`; nunca `--no-verify`; cachés de
herramientas fuera del proyecto; modelos y tokens según CLAUDE.md «Modelos» (Haiku por
defecto en subagentes; el hilo principal usa el modelo con el que el dueño te arrancó).

CIERRE DE CADA OLEADA: PR con título `serie N — <qué>`; cuerpo con filas tocadas,
comandos corridos y su salida, capturas de Playwright de las rutas tocadas (ES/EN,
390 y 1280 px) si hay UI, y lo que NO se verificó. Entrada en docs/STATUS.md. Luego
sigue con la siguiente fila hasta que el límite te pare; si te para a medias, el PR y
el ledger deben describir el estado exacto para que la siguiente sesión continúe.
```

---

## Por qué este prompt y no «haz lo que quieras»

- **`master` es producción sin nada en medio** (H.13/H.17: el CI de GitHub no corre). El
  incidente del login del 2026-09-24 (serie 30) salió de un push directo. Por eso el
  control total es *dentro de la rama* y el dueño fusiona (ADR-41).
- **El volumen sin puerta ya falló una vez**: 800 preguntas con 14 enunciados por track
  (ledger §1, serie 25). Por eso 35.0 va antes que cualquier pregunta (ADR-42 §6).
- **Lo que solo el dueño puede hacer no bloquea a la sesión**: ADR-43 da un valor por
  defecto a cada decisión pendiente para que la sesión no se detenga a esperarlo.
