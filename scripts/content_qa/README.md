# Herramientas de QA de contenido (26-09-2026)

Salieron de la noche del 26-09, cuando la reescritura de contenido con agentes produjo
fallos que ninguna guarda del repo veía: claves movidas de ranura, URLs inventadas,
correos reales en ejemplos y validadores sobrescritos por un agente. El proceso completo
está en `docs/RUNBOOK.md` («Contenido reescrito por agentes»).

| Script | Qué detecta |
| --- | --- |
| `validate_lessons.py DIR [ORIG]` | Lo mismo que `backend/tests/content/test_lessons.py` (importa sus funciones), más Python solo de la biblioteca estándar e `id`/`skill_id` sin cambios |
| `check_key_drift.py BASE NEW` | La opción marcada como correcta ya no es la que más se parece a la correcta original: el reescritor la movió de ranura |
| `check_expl_key.py DIR` | La explicación se parece más a una opción incorrecta que a la marcada |
| `check_only_fields.py ORIG NEW --fields a,b` | Cambió algún campo fuera de los permitidos, o quedaron explicaciones de plantilla o repetidas |
| `rebalance_positions.py REWRITE REPO OUT` | Devuelve la correcta a la posición que tenía en el repo (o por hash del id si el repo las rotaba 0,1,2,3…) |
| `check_urls.py DIR` | URLs de `source` que no responden 200; un 403 sale como «revisar a mano» (bloqueo de bots) y no falla |

`check_key_drift` y `check_expl_key` dan **sospechosas**, no veredictos: cada marca se lee
a mano. Una pregunta cuya clave original ya era falsa también se marca.

Los agentes no deben crear, editar ni reemplazar estos scripts: se llaman desde el
scratchpad por su ruta en el repo.
