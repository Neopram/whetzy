# Prompt de verificación exhaustiva — Track 07 + hito Fase 1

> Ejecutar en sesión NUEVA después de que la sesión de autoría de Track 07 declare "terminado".
> Objetivo: comprobar que lo declarado es cierto, no repetir el trabajo.
> **Postura: escéptica.** Auditorías previas de este repo encontraron drift real
> (track05 sin documentar, conteos 835→931→979). Asume que puede haberlo otra vez.

---

## CONTEXTO (lo que la sesión anterior dice haber hecho)

- Tracks 01–06 completos: **1.117 preguntas** verificadas, campo `source` cableado.
- Track 07 (Ingeniería de IA): 6 módulos `mod0701`–`mod0706` — LLMs y Prompt Engineering,
  RAG, Agentes de IA, MLOps, Ética y seguridad en IA, Evaluación y observabilidad.
  ~28 skills → ~168 preguntas nuevas.
- **Riesgo conocido:** track07 YA tenía 30 preguntas antiguas sin `source`. La sesión debía
  comprobar IDs existentes antes de autorar (evitar colisión) y decidir si backfillear.
- Patrón: 6 Q/skill, ES+EN nativo (no traducción), easy→expert, tipos mixtos,
  distractores de malentendidos reales, `source` canónico.
- Al cerrar: tracks 01–07 completos = **hito de contenido de Fase 1**.

**No confíes en `docs/STATUS.md` como evidencia.** STATUS.md es lo que hay que auditar,
no la fuente de verdad para esta auditoría. La fuente de verdad son los archivos JSON y la DB.

---

## GOTCHAS DEL ENTORNO (verificados 2026-09-07 — no los redescubras)

| Gotcha | Detalle |
|---|---|
| Python | `python` del sistema (3.12) **ya tiene** sqlalchemy, aiosqlite, pydantic, pydantic-settings. No crees venv. |
| venv | `python -m venv` **falla** en rutas con espacios ("Banco de preguntas"). No lo necesitas. |
| SQLite en Desktop | **Permission denied.** `sqlite3.connect('C:/Users/feder/Desktop/x.db')` → `unable to open database file`. |
| SQLite que SÍ funciona | `%TEMP%` → `C:\Users\feder\AppData\Local\Temp\`. Usa esa ruta para la DB de verificación. |
| DATABASE_URL | Ruta **absoluta**, barras normales: `sqlite+aiosqlite:///C:/Users/feder/AppData/Local/Temp/neurium_verify.db` |
| .env | `config.py` lo lee del **CWD**. Crea `backend/.env` antes de correr el loader; bórralo al terminar. |
| content_loader | `cd backend && python -m app.services.content_loader` |
| CONTENT_DIR | Env var opcional; por defecto infiere `repo/content` desde la ruta del módulo. |
| **Esquema DB real** | `tracks` **NO tiene** columna `track_id`. Columnas: `id, name_es, name_en, order, icon, color, total_questions`. Join por `modules.track_id → tracks.id`. Filtra track07 por `tracks.name_es LIKE '%Ingenieria de IA%'` (sin tilde en DB). |
| `questions` | `id, skill_id, type, difficulty_tier, question_es, question_en, options_es, options_en, correct_index, correct_answer_es, correct_answer_en, explanation_es, explanation_en, source, elo_rating, discrimination, guessing, expected_time_ms` |
| **`validate_content.py`** | ⚠️ **NO EXISTE en el repo** (búsqueda 2026-09-07: 0 resultados). STATUS.md sesiones (c)(d)(e)(f) afirman haberlo ejecutado. **Compruébalo**: si sigue sin existir, esas afirmaciones no son reproducibles → márcalo como hallazgo. Escribe tu propio validador. |
| Limpieza | Borra `backend/.env`, la DB de temp y cualquier script de verificación al terminar. No dejes basura en el repo. |

---

## NIVEL 1 — Integridad de los archivos de contenido (sin DB)

Escribe un validador autónomo (stdlib solamente) que compruebe, sobre
`content/questions/track07_ai_engineering/*.json`:

1. **Existencia**: los 6 módulos `mod0701`–`mod0706` están presentes.
2. **IDs únicos globales** — cruza contra **los 7 tracks**, no solo track07.
   *Este es el riesgo #1 declarado.* Cualquier colisión con las 30 preguntas antiguas es fallo.
3. **6 preguntas por skill** exactas. Lista cualquier skill con ≠6.
4. **Esquema por tipo**:
   - `mcq` / `true_false` / `code_output` → `options_es`, `options_en`, `correct_index` en rango
   - `fill_blank` → `correct_answer_es`, `correct_answer_en`, `options` null, `correct_index` null
5. **Bilingüe real**: `question_es` ≠ `question_en` y ambos no vacíos.
   Igual para `explanation_*` y `options_*`. **Si ES == EN, es traducción/copia → fallo.**
6. **`source` presente** en las ~168 nuevas. Reporta cuántas antiguas siguen sin él.
7. **Distribución de `difficulty_tier`**: debe haber progresión easy→expert, no todo un tier.
8. **Mezcla de tipos**: no todo `mcq`. Reporta el histograma.
9. **UTF-8 limpio**: sin mojibake (`Ã©`, `â€"`, `\ufffd`).
10. **Conteo real por módulo/skill/track** — no lo asumas, cuéntalo.

**Criterio de aceptación N1:** 0 colisiones de ID, 0 campos faltantes, 0 pares ES==EN,
0 mojibake, 6 Q/skill en todas.

---

## NIVEL 2 — Ingestión en base de datos

```
cd backend
# crea .env con DATABASE_URL a %TEMP% (ver gotchas)
python -m app.services.content_loader
```

**Criterio de aceptación N2:**
- Salida `{'tracks': 7, 'questions': <N>, 'skipped': 0, 'files': <F>}` con **`skipped: 0`**.
- Introspecciona la DB y reporta por track: preguntas, módulos, skills, cobertura de `source`,
  nº de `fill_blank`, histograma de tipos.
- **Calcula el total esperado y compáralo con el real.** No aceptes "≈". Si 1.117 + nuevas ≠ total,
  explica exactamente de dónde sale la diferencia.
- Confirma que **tracks 01–06 no han cambiado** (regresión): si track01 ya no es 306, algo se rompió.

---

## NIVEL 3 — Camino HTTP end-to-end (el que nadie re-verificó)

STATUS.md sesiones (c)(d)(e)(f) dicen *"no re-verificado por HTTP"*. **Ciérralo ahora para track07.**

1. Arranca el backend contra la DB de verificación.
2. `POST /api/v1/auth/register` → usuario nuevo → token.
3. `POST /api/v1/quiz/start` con un `skill_id` **de track07** (p. ej. el primero de mod0701).
4. Confirma que devuelve una pregunta de track07 renderizable
   (`options` no null salvo fill_blank, `correct_index` no null).
5. `POST /api/v1/quiz/answer` → confirma en la respuesta:
   - `source` poblado con la cita canónica
   - `explanation_es` / `explanation_en` presentes
   - Elo / BKT / FSRS / XP actualizados y **persistidos** (re-consulta y compruébalo)
6. Confirma que `fill_blank` **sigue excluido** de la selección (`correct_index IS NOT NULL` filter).

**Criterio de aceptación N3:** flujo completo sin error, `source` visible en la respuesta,
estado del motor persistido.

---

## NIVEL 4 — Exactitud técnica del contenido (aquí es donde hace falta juicio)

Track 07 es contenido de IA con **citas a papers**. El fallo más probable y más caro es una
**cita alucinada o mal atribuida**. Un producto que vende "fuentes canónicas citadas" no puede
tener papers inventados.

1. **100% de las preguntas `expert`** — revisión técnica completa.
2. **≥10% estratificado** del resto (muestra por módulo y por tier).
3. **Verificación de TODAS las citas únicas de `source`**:
   - ¿El paper existe? ¿El título es exacto? ¿Los autores son correctos?
   - Comprobaciones de referencia: *Attention Is All You Need* = Vaswani et al. 2017;
     RAG = Lewis et al. 2020; ReAct = Yao et al. 2022 (no 2023);
     OWASP **LLM** Top 10 ≠ OWASP Top 10 web; NIST AI RMF 1.0 = 2023.
   - Docs de Anthropic/OpenAI: ¿la sección citada existe realmente?
   - **Cualquier fuente que no puedas confirmar → márcala. No la des por buena.**
4. **Distractores**: ¿codifican malentendidos reales o son relleno?
   Para track07, los malentendidos reales son: creer que RAG "entrena" el modelo, confundir
   fine-tuning con RAG, creer que temperature=0 es determinista garantizado, confundir
   context window con memoria persistente, creer que un agente ReAct "razona" sin prompting,
   confundir embeddings con tokens, creer que más parámetros = mejor siempre.
   Distractores absurdos o descartables de un vistazo → fallo de calidad.
5. **Explicaciones**: ¿enseñan el *porqué* o repiten la respuesta?

**Criterio de aceptación N4:** 0 citas inverificables, 0 distractores de relleno,
0 errores técnicos en las `expert`.

---

## NIVEL 5 — Auditoría de veracidad de `docs/STATUS.md`

Compara **línea por línea** lo que STATUS.md afirma contra lo que acabas de medir.

- ¿El total declarado coincide con el conteo real de la DB?
- ¿Cada track declarado "completo" tiene realmente todos sus módulos?
- ¿La afirmación `validate_content.py → 0 errores` es reproducible? (ver gotcha: el script no existe)
- ¿Hay módulos en `content/` que STATUS.md no menciona? *(así se encontró track05)*
- ¿El backfill de `source` declarado coincide con la cobertura real?
- ¿El % de Fase 1 declarado es defendible con la evidencia?

**Cualquier discrepancia → corrige STATUS.md con el número real y deja constancia del hallazgo.**

---

## NIVEL 6 — El hito de Fase 1 (la afirmación grande)

La sesión anterior afirma que con track07 los **tracks 01–07 quedan completos**.
Esa es una afirmación fuerte. Compruébala:

- ¿Los 7 tracks tienen todos sus módulos según `content/curriculum/tracks.json`?
- ¿Cuántas preguntas hay realmente vs la meta de **1.500** del MASTER_PROMPT?
- Fase 1 también exige, además de las preguntas:
  - **Glosario por track** (`GlossaryTerm` + `GlossaryScreen.tsx`) → ¿existe?
  - **`TracksScreen.tsx`** con desbloqueo BKT visible → ¿existe?
  - **Calibración IRT** sobre `elo_rating` → ¿existe?
- **Si falta cualquiera de esos tres, Fase 1 NO está al 100%** — dilo claramente y da el % real.

---

## ENTREGABLE

Un informe honesto con:

1. **Veredicto por nivel** (N1–N6): PASA / FALLA, con la evidencia (números, no adjetivos).
2. **Tabla de hallazgos**: severidad, archivo, qué está mal, qué debería decir.
3. **Números reales**: total de preguntas, por track, cobertura de `source`, fill_blank, tipos.
4. **Citas marcadas**: lista de cualquier `source` que no pudiste verificar.
5. **`docs/STATUS.md` corregido** con los números medidos (no los declarados).
6. **% real de Fase 1** con justificación de por qué no es 100% si no lo es.
7. **Limpieza confirmada**: `backend/.env`, DB temporal y scripts de verificación borrados.

**Reglas de la auditoría:**
- Verificación más barata primero: archivos → DB → HTTP → juicio técnico.
- Nunca declares "verificado" sin haber ejecutado el comando y visto la salida.
- Si algo no lo comprobaste, escribe explícitamente "no verificado".
- Un número aproximado ("≈168") en el informe final es un fallo del informe.
