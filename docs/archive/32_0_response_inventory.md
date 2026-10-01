> **Archivado el 2026-10-01:** entregable de la tarea 32.0 (2026-09-26); el modelo vigente es `backend/app/models/session.py`.

# 32.0 — Inventario de datos por respuesta

## Tabla: `responses` (modelo `Response`, `backend/app/models/session.py`)

| Dato | Columna | Tipo | Línea | Estado |
|------|---------|------|-------|--------|
| Sesión | `session_id` | FK → `study_sessions.id` | :54 | ✓ existe |
| Pregunta | `question_id` | FK → `questions.id` | :56 | ✓ existe |
| Correcta | `correct` | Boolean | :59 | ✓ existe |
| Grado FSRS | `grade` | Integer (1-4) | :60 | ✓ existe |
| Tiempo de respuesta | `response_time_ms` | Integer | :61 | ✓ existe |
| Timestamp | `created_at` | DateTime(tz) | :62 | ✓ existe |
| Versión de pregunta | `question_version` | Integer | :68 | ✓ existe |
| "No lo sé" | `declared_unknown` | Boolean | :73 | ✓ existe |
| Idempotencia | `event_id` | String(64), unique | :77 | ✓ existe |
| **p_known antes** | `p_known_before` | Float, nullable | :82 | ✓ existe (mig. `20260925_response_snap`) |
| **p_known después** | `p_known_after` | Float, nullable | :83 | ✓ existe |
| **Elo antes** | `elo_before` | Float, nullable | :84 | ✓ existe |
| **Elo después** | `elo_after` | Float, nullable | :85 | ✓ existe |
| **P(acierto) esperada** | `expected_p` | Float, nullable | :86 | ✓ existe |

### Escritura verificada (`backend/app/services/quiz.py`)

```
:518  p_known_before = state.p_known
:519  elo_before = state.elo_rating
:524  user_entity, item_entity, expected_p = elo.update(...)
:573  p_known_before=p_known_before,
:574  p_known_after=state.p_known,
:575  elo_before=elo_before,
:576  elo_after=state.elo_rating,
:577  expected_p=expected_p,
```

## Tabla: `user_skill_states` (modelo `UserSkillState`, `backend/app/models/user.py`)

Estado acumulado por skill (no por respuesta individual):

| Dato | Columna | Línea | Estado |
|------|---------|-------|--------|
| BKT p_known | `p_known` | :109 | ✓ |
| Elo rating | `elo_rating` | :110 | ✓ |
| FSRS stability | `fsrs_stability` | :111 | ✓ |
| FSRS difficulty | `fsrs_difficulty` | :112 | ✓ |
| FSRS next due | `fsrs_due` | :113 | ✓ |
| Intentos | `attempts` | :115 | ✓ |
| Aciertos | `correct_count` | :116 | ✓ |
| "No lo sé" | `unknown_count` | :119 | ✓ |

## Lo que falta — propuesta de migración aditiva

| Dato faltante | Columna propuesta | Tipo | Justificación |
|---------------|-------------------|------|---------------|
| FSRS S antes | `fsrs_stability_before` | Float, nullable | Para auditar cambio de intervalo por respuesta |
| FSRS D antes | `fsrs_difficulty_before` | Float, nullable | Ídem |
| Skill ID directo | `skill_id` | String(64), nullable, FK | Hoy la skill se reconstruye via `question → skill`; columna directa simplifica queries de calibración |

Estas tres son **aditivas** (nuevas columnas nullable, sin tocar las existentes) y se
pueden añadir en una migración `20260926_response_fsrs_snap`. No bloquean la
calibración actual (32.1), que ya funciona con `p_known_before` + `expected_p`.

**No se añade PII**: la respuesta enlaza al usuario por `session → user_id`, no guarda
nombre, email ni IP en la tabla de respuestas.
