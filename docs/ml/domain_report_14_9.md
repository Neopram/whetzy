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
`backend/tests/unit/test_domain_report.py` (13 tests, incluida una mutación
de Regla 11: invertir "primer intento" por "último intento" tumba 3 de 13
tests).

## Por qué esto NO es "validar con datos simulados con parámetros conocidos"

A diferencia de 14.8 (predictor estadístico, con una probabilidad que puede
estar mal calibrada) y 14.10 (parámetros de ítem que hay que recuperar),
estos tres números son **hechos exactos**, no estimaciones: contar cuántas
skills pasan un umbral, contar respuestas, mirar si una respuesta concreta
fue correcta. No hay "parámetro verdadero" que recuperar — la verificación
correcta es la que se hizo: que la aritmética no se equivoca en los casos
límite (banco vacío, sin respuestas, reintentos, orden de entrada), probado
con unit tests deterministas, no con una simulación de Monte Carlo que no
aportaría nada aquí.

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
