# 14.9 — Informe de dominio verificable por URL: la aritmética, no la URL

**Estado: aritmética lista y probada; la URL pública NO está construida en
este PR.** Explicado abajo por qué, y qué hace falta para cerrarlo.

## Qué pide el ticket

> URL pública: «p_known ≥ 0,95 en N de M skills, X respuestas en Y semanas,
> Z % a la primera». Un reclutador puede confiar en esto más que en un
> «terminó el curso».

Tres números verificables, no una afirmación vaga:

1. **N de M skills con p_known ≥ 0,95** — `compute_mastery_summary`.
2. **X respuestas en Y semanas** — `compute_weeks_active` sobre las marcas
   de tiempo de `Response.created_at`.
3. **Z % a la primera** — `compute_first_try_accuracy`: de cada pregunta
   DISTINTA, ¿acertó en su primer intento? No es la precisión agregada de
   todos los intentos (eso dejaría que reintentar ilimitadamente infle el
   número) — mirar solo el primer intento por pregunta es precisamente lo
   que hace creíble la cifra para un reclutador.

`backend/app/services/domain_report.py` implementa las tres, más
`build_domain_report`/`DomainReport.headline()` que las junta en el formato
exacto del ejemplo del ticket. Todas son funciones puras — nada toca la base
de datos aquí — probadas con datos sintéticos en
`backend/tests/unit/test_domain_report.py` (15 tests, incluida una mutación
de Regla 11: invertir "primer intento" por "último intento" tumba 3 de 15
tests).

## Por qué esto NO es "validar con datos simulados con parámetros conocidos" — salvo en un punto

A diferencia de 14.8 (predictor estadístico, con una probabilidad que puede
estar mal calibrada) y 14.10 (parámetros de ítem que hay que recuperar), dos
de estos tres números son **hechos exactos**, no estimaciones: contar
respuestas, y mirar si una respuesta concreta fue correcta. Para esos dos no
hay "parámetro verdadero" que recuperar — la verificación correcta es la que
se hizo: que la aritmética no se equivoca en los casos límite (banco vacío,
sin respuestas, reintentos, orden de entrada), probado con unit tests
deterministas, no con una simulación de Monte Carlo que no aportaría nada
aquí.

**El tercer número, N de M skills con `p_known >= 0.95`, es la excepción —
corrección de la revisión adversaria del `[COORD]` (17:21 UTC): `p_known`
sale de `UserSkillState.p_known`, una ESTIMACIÓN de BKT, no un hecho medido
directamente.** Con los parámetros por defecto del motor (`SkillParams` en
`app/services/engine/bkt.py`), `p_known` cruza 0,95 tras solo **4 aciertos
seguidos** (verificado: `0.1 → 0.4286 → 0.7838 → 0.9431 → 0.9868`) — una
racha corta, no necesariamente dominio real de la skill. Por eso
`compute_mastery_summary`/`build_domain_report` ahora exigen también
`skill_attempts[skill_id] >= MIN_ATTEMPTS_PER_SKILL` (10, el tamaño de una
skill completa del catálogo — ADR-54) antes de contar una skill como
dominada: una skill con `p_known` alto pero menos de 10 respuestas sigue
contando en `M` (sigue siendo una skill del track) pero no en `N`, hasta que
tenga práctica suficiente para que el número sea defendible delante de un
reclutador. Regla 11:
`tests/unit/test_domain_report.py::test_mastery_summary_excludes_a_lucky_streak_with_too_few_attempts`
y `test_build_domain_report_does_not_credit_mastery_without_enough_attempts`,
confirmados rojo quitando el filtro de `skill_attempts` (ambos pasan a
contar la skill como dominada) y verde al restaurarlo.

## Qué falta, y por qué no lo hago yo

Publicar esto por una URL pública necesita:

1. **Un token compartible** — probablemente una columna nueva o una tabla
   (`public_report_token` en `User`, o una tabla de informes publicados con
   expiración/revocación) → **migración de Alembic**.
2. **Un endpoint público, sin autenticación**, que lea ese token y devuelva
   el informe — `backend/app/api/v1/endpoints/**`.
3. Decisiones de producto que no son mías: ¿el alumno elige qué dominios
   publicar? ¿puede revocar el enlace? ¿expira?

Esto es terreno de API/infraestructura, no del motor — el mapa de terrenos
de la fase 0 (`[COORD] → S5` en el issue #89) pone
`backend/app/api/v1/endpoints/**` en S1 salvo los endpoints del motor, y una
migración nueva necesita comprobar antes los PRs abiertos de las demás
sesiones (regla 5) para no chocar con otra migración en vuelo — ahora mismo
hay varios PRs abiertos de otras sesiones y no he visto ninguna migración de
`public_report_token`, pero abrirla aquí mismo, sin ser quien toca los
endpoints, duplicaría trabajo si S1 ya tiene planeado dónde vive el
token. **`[S3] NECESITO de S1`**: si nadie más lo ha tomado, el endpoint
público + la migración del token, usando `build_domain_report` de este
módulo para los números — ya no hay matemática pendiente, solo
infraestructura.

**Fuera de alcance de este PR, visto en la misma revisión del `[COORD]`:**
`DomainReport.headline()` arma su frase solo en español ("de", "respuestas
en", "a la primera"), mientras que `CLAUDE.md` pide contenido y UI en ES y
EN nativos. No lo toco aquí porque los 5 puntos pedidos para este PR eran
otros y esto es un cambio de forma del texto, no de la aritmética — queda
anotado para quien conecte el endpoint público (el `NECESITO` de arriba),
ya que ahí hace falta decidir también en qué idioma sirve el informe.
