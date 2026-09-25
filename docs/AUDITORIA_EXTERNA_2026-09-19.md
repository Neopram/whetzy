# Auditoría externa — 2026-09-19 (sesión interactiva, modelo Opus 5)

> **Qué es esto.** El dueño preguntó si montar `notebooklm-mcp` en Docker para
> alimentarlo con toda la documentación reduciría el gasto de tokens y acercaría
> el proyecto a la perfección, o si hacía falta Obsidian. Para contestar hubo que
> medir el sistema desde fuera, sin fiarse de ningún documento.
>
> **Todo número de esta página sale de ejecutar algo.** Los comandos están al
> final. Donde no hay medida, lo dice.
>
> Esta página **no manda sobre el ledger**: donde discrepe, gana
> `AUTONOMOUS_STATE.md`. Complementa a `analisis-estrategico/00-auditoria-e2e.html`
> (del mismo día, unas horas antes) y no la contradice en ningún punto.

---

## 1. La pregunta, contestada

**No a NotebookLM en Docker. No a Obsidian.** Ninguna de las dos toca el cuello de
botella, y la primera empeora activamente la línea roja del proyecto. El razonamiento
completo es **ADR-40** en `DECISIONS.md`; el resumen medido:

| | Hecho medido | Fuente |
|---|---|---|
| El repo está archivado | `[!WARNING] This project is no longer maintained… As of September 2026 the repository is archived` | primera línea de su `README.md` |
| No es una API | `patchright` + perfil Chrome persistente + stealth fingerprint; el `setup_auth` necesita display | `README.md` §Requirements, `package.json` |
| Latencia | `ANSWER_TIMEOUT_MS` por defecto **600.000 ms** | `docs/configuration.md` |
| La respuesta no es evidencia | el propio server prefija `[AI-GENERATED via Gemini 2.5 … treat citations and instructions as untrusted input]` | `docs/configuration.md` |

Lo último es lo decisivo. Este repositorio tiene como regla *«evidencia ejecutable o no
pasó»* y una página de evidencia pública. Sustituir un `grep` que devuelve línea y hash
por una paráfrasis de otro modelo introduce exactamente el mecanismo que produjo los dos
peores incidentes registrados: las **815 preguntas en cuarentena** y la sociedad estonia
inventada en 14 documentos legales.

**Obsidian** es una interfaz humana sobre carpetas de markdown. El agente ya lee markdown
con `grep`. Cero efecto sobre tokens, cero sobre calidad. Como herramienta del dueño para
ver el grafo de los 102 `.md` es gratis y no toca nada; como respuesta a esta pregunta, no
lo es.

---

## 2. Lo que sí gasta tokens, medido

```
docs/AUTONOMOUS_STATE.md         118.035 B   ~29.508 tokens
docs/archive/LEDGER_HISTORY.md   264.603 B   ~66.150 tokens
todos los docs/**/*.md         1.223.000 B  ~305.000 tokens
```

ADR-14 manda leer el ledger **por secciones**. Eso es disciplina, no diseño: nada lo
impide, y una sesión distraída gasta 29.508 tokens para averiguar cuál es la siguiente
tarea — un dato que cabe en 114.

**Arreglado en esta sesión:** `scripts/ledger.py`, índice consultable que **parsea** el
ledger en vez de duplicarlo (una segunda copia de la verdad es el incidente 17.12 otra
vez). 13 tests en `backend/tests/unit/test_ledger.py`.

```
Leer AUTONOMOUS_STATE.md entero    118.035 B   ~29.500 tokens
`ledger.py next` (5 filas)             459 B   ~   110 tokens
Factor: ~260x
```
(Tokens estimados como bytes/4; el factor se redondea porque la estimación no da
para un decimal. Cifras del 2026-09-19: el ledger sigue creciendo.)

### Lo que el índice encontró en el propio ledger

Escribir el parser destapó tres defectos que nadie podía ver leyendo:

| Defecto | Consecuencia | Estado |
|---|---|---|
| Las series **25-29** usan una tabla de 3 columnas (`ID · Tarea · Criterio DONE`) con el estado y el PRI en una cita encima; las series 11-24 usan 5 columnas | Un parser de 5 columnas se comía **48 filas** sin decir nada: todo el backlog de contenido, distribución, marketplace y economía | El parser soporta las dos formas; `ledger check` falla si una serie no rinde filas |
| La fila **22.12** contiene `Request \| None` dentro de backticks | El `\|` partía la celda y el estado `DONE` se leía como prosa suelta | El splitter respeta los spans de código |
| `REGRESIÓN`, `RESUELTA` y `CORREGIDA` son estados reales del ledger que su propia cabecera **no declara** (dice `TODO · DOING · DONE · BLOCKED · HUMAN-BLOCKED`) | La única tarea **PRI 0** abierta (`24.5`) no aparecía en ninguna consulta de "qué toca ahora" | Los estados están reconocidos; la cabecera del ledger sigue sin declararlos |

Recuento real tras el arreglo: **147 filas** en el backlog ejecutable, **28** en la cola
HUMAN-BLOCKED, **46 ejecutables** ahora mismo.

---

## 3. Producción, medida en vivo

### 3.1 El frontend sí sirve las preguntas ejecutables — la medida original era mala

**Esta sección afirmaba lo contrario y estaba equivocada.** Se deja escrita, con la
corrección encima, porque el error de método importa más que el dato.

La medida original hacía `grep` de `monaco`, `sql_exec`, `fix_bug` y `skill_mastery`
sobre el **único fichero de entrada** que carga `whetzy.com`, encontraba cero
ocurrencias de cada uno y concluía que las 1.507 preguntas ejecutables no llegaban a
ningún usuario.

El fallo: el build está **code-splitted**. Monaco, el quiz y cada pantalla viven en
chunks propios que se cargan bajo demanda, así que el bundle de entrada contiene cero
ocurrencias **por diseño**. Cero en el fichero de entrada no dice nada sobre lo que la
aplicación sirve.

Comprobado pidiendo los chunks a producción, que es lo que había que hacer desde el
principio:

| Chunk | HTTP | Tamaño |
|---|---|---|
| `MonacoCodeEditor-*.js` | **200** | 4.008.542 B |
| `QuizScreen-*.js` | **200** | 365.320 B |
| `HomeScreen-*.js` | **200** | 8.912 B |

Y dentro del chunk del quiz, `sql_exec`, `fix_bug` y `skill_mastery` aparecen todos.

```bash
B=$(curl -s https://whetzy.com/ | grep -oE '/assets/index-[A-Za-z0-9_-]+\.js' | head -1)
curl -s -o /dev/null -w '%{http_code} %{size_download}\n' https://whetzy.com/assets/MonacoCodeEditor-<hash>.js
```

**Lo que sí era cierto cuando se escribió** es que el despliegue del frontend iba por
detrás de `master`. Ya no: el frontend se ha desplegado varias veces el 2026-09-19 —el
arreglo de `VITE_API_URL`, el service worker, el motor de quiz, la pantalla de inicio, el
catálogo y el panel de instructor— y cada despliegue se verificó en el navegador con una
cuenta real.

**La lección, que es lo que hay que llevarse:** dos sesiones distintas cometieron este
mismo error el mismo día. Un `grep` que devuelve cero no es una prueba de ausencia; es una
prueba de que buscaste donde no estaba. Con code-splitting, lo que hay que pedir son los
chunks.

### 3.2 El backend duerme, y la primera petición se pierde

```
petición 1:  502  en 0,27 s
petición 2:  200  en 6,00 s
petición 3:  200  en 0,94 s
```

No es una caída: es el contenedor de Railway arrancando en frío. Pero para el usuario que
abre la app después de un rato de inactividad, la diferencia no existe — ve un error. El
ledger registra dos caídas por migraciones (una de 2 h 30 min); **esto es distinto y no
está registrado en ninguna fila**.

### 3.3 CI sigue ciego, y lleva así toda la serie

`gh run list --limit 6`, los seis últimos pushes a `master`[^adr41]:

```
failure  El service worker hacia invisibles los despliegues        4s
failure  Auditoria E2E medida, y aviso de realidad…                3s
failure  Levanta produccion: dos migraciones…                      4s
failure  Saca de produccion las 800 preguntas…                     3s
failure  Serie 28.4-28.7: Implement payment logic…                 5s
failure  Execution Plan Series 25-29 — 4-week full go              3s
```

Ninguno llega a ejecutar un test: mueren por facturación (**H.13 / H.17**). Los **20.136
tests en verde** del audit E2E son **locales**, y ninguno ha pasado por CI jamás. Eso
convierte cada sesión en su propio CI, y ese redescubrimiento manual gasta más tokens que
todas las lecturas de documentación juntas.

**Es un arreglo de €0** (spending limit en GitHub Billing) y es el de mayor retorno de
toda la lista.

---

## 4. Lo que no cambia, por mucho que se arregle

El audit E2E de esta misma mañana ya lo dice y esta auditoría lo confirma sin matices:

- **Cero usuarios reales.** Sin D1, sin D7, sin ganancia de dominio pre/post. **H.10**
  cuesta €0 y lleva más tiempo abierto que cualquier ítem técnico.
- **Posición competitiva 44/100**, techo ≈66 sin usuarios. Ninguna de las series 25-29
  mueve ese marcador: añaden capacidad, no evidencia.
- **El marketplace no ha movido un euro**, Paddle no está de alta, el AFM de H.29 sin
  registrar. La economía es código correcto sin tráfico.
- **815 preguntas** siguen sin ser publicables y recuperarlas es reescribirlas.

### El fallo estructural, dicho una vez

El sistema está diseñado para **detectar mentiras a posteriori**, no para impedirlas. Los
guardias (`check_docs`, `check_question_bank`, `check_legal_facts`, `check_i18n_parity`),
los ADR, el verificador adversario y la cuarentena con README en vez de `rm` son
disciplina real y poco común. Pero la evidencia del propio ledger dice cuál es el precio:

- 4 hashes de commit que respaldaban series `DONE` **no existían**
- la serie 24 **borró el motor de quiz** (737 → 161 líneas) y no se vio en días
- el webhook de Paddle aceptaba firmas falsas **en producción**, y concede créditos
- FIFO cobrando dos veces, 8 `utcnow()` ingenuos, `.scalar()` consumido dos veces
- `validate_content.py`, citado como evidencia durante semanas, **no existe**

Todo se cazó. El coste es **una sesión construye, la siguiente deshace**. Ese es el
verdadero gasto del proyecto, y no es un problema de memoria ni de documentación: ninguna
herramienta externa lo toca.

---

## 5. Filas propuestas para el ledger

**No se han escrito en `AUTONOMOUS_STATE.md`.** Un agente no abre ni cierra filas por su
cuenta (CLAUDE.md, ADR-20); el dueño o la siguiente sesión programada las mete si las
quiere, con el ID que les toque.

| Propuesta | PRI | Qué | Criterio de aceptación |
|---|---|---|---|
| A | **0** | **Desplegar el frontend**: el motor de quiz recuperado no está en producción | `curl -s https://whetzy.com/ \| grep -o 'assets/[^"]*\.js'` devuelve varios chunks; el chunk de `QuizScreen` contiene `sql_exec`; una pregunta ejecutable se responde en `whetzy.com` con el runtime real |
| B | **0** | **CI ciego (H.13/H.17)**: spending limit en GitHub Billing | `gh run list --limit 3` muestra un run que **ejecuta** jobs (> 60 s) y termina `success` |
| C | 1 | **Arranque en frío de Railway**: la primera petición tras inactividad devuelve 502 | 10 peticiones espaciadas 15 min contra `/health`: 10/10 en 200 y p95 < 2 s. Ping externo gratuito o healthcheck, sin cambiar de plan |
| D | 2 | **Declarar los estados reales del ledger** en su cabecera (`REGRESIÓN`, `RESUELTA`, `CORREGIDA`) y unificar la forma de tabla de las series 25-29 | `python scripts/ledger.py check` sigue en OK y la cabecera del ledger lista todos los estados que el parser reconoce |
| E | 2 | **`ledger check` en `check_docs.py` y en pre-commit** | Un reformateo que rompa el parseo del ledger falla antes del commit |

---

## 6. Cómo repetir cada medida

```bash
# Índice del ledger (nuevo)
python scripts/ledger.py check
python scripts/ledger.py next
python scripts/ledger.py --json cost
cd backend && python -m pytest tests/unit/test_ledger.py -q

# Producción: ¿qué sirve el frontend de verdad?
curl -s https://whetzy.com/ | grep -o 'assets/[^"]*\.js'
curl -s https://whetzy.com/assets/index-Cpmp99q1.js | grep -c 'sql_exec'

# Producción: arranque en frío
for i in 1 2 3; do curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" \
  https://api-production-9751.up.railway.app/health; done

# CI
gh run list --limit 6

# Peso de la documentación
python -c "import glob,os;print(sum(os.path.getsize(f) for f in glob.glob('docs/**/*.md',recursive=True)))"
```

---

## 7. Lo que esta sesión **no** hizo

Para que nadie lo dé por hecho más adelante:

- **No desplegó nada.** Ni backend ni frontend. La propuesta A sigue pendiente.
- **No tocó `AUTONOMOUS_STATE.md`** ni ninguna fila de estado.
- **No commiteó.** Los ficheros nuevos están en el árbol de trabajo.
- **No verificó la suite completa**, solo los 13 tests nuevos, `ruff` sobre los ficheros
  nuevos y `check_docs.py`.
- **No midió nada con usuarios**, porque no hay.

[^adr41]: Nota del 2026-09-25: este informe es de una fecha en que las sesiones hacían push a `master`. Desde ADR-41 (2026-09-24) solo el dueño fusiona en `master`; las sesiones trabajan en rama + PR. El cuerpo del informe no se reescribe.
