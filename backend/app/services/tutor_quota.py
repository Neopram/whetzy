"""Cupo diario del tutor (38.6, ADR-49).

Pro (`plus`) tiene `TUTOR_DAILY_LIMIT_PLUS` explicaciones por día UTC; Pro Max
(`pro`), Creador, el dueño y los admins no tienen cupo de explicaciones (ADR-49
es explícito: "ilimitado"), pero sí hay un cupo por tokens (41.17) -- no es un
límite de negocio, es un cinturón de seguridad de ingeniería contra un abuso
puntual (una conversación enorme), y se comprueba pero nunca bloquea a quien
ADR-49 dice que no debe tener tope. El uso (explicaciones y tokens) se cuenta
en todos los planes: sin esa cifra no hay forma de saber cuánto cuesta el
tutor ilimitado. El freno por minuto del middleware sigue aparte y vale para
todos.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.entitlements import user_meets_tier
from app.models.tutor_usage import TutorUsage
from app.models.user import User

LIMIT_REACHED = "tutor_daily_limit"

# 41.17: el total real de tokens de una llamada no se sabe hasta que el
# proveedor responde, pero la reserva que evita la carrera tiene que ser
# atómica con el chequeo del límite -- así que reserva este peor caso antes
# de llamar al LLM (cupo por tokens), y settle() lo corrige al valor real
# después. TUTOR_HISTORY_MAX_TURNS × TUTOR_HISTORY_MAX_CHARS_PER_TURN da un
# techo de ~10.000 tokens de historial en el peor caso; de sobra para el
# resto del prompt (pregunta, contexto, skill) y los 500 de completado.
TOKEN_RESERVE_ESTIMATE = 12_000


def today_utc(now: datetime | None = None) -> date:
    return (now or datetime.now(UTC)).astimezone(UTC).date()


def resets_at(day: date) -> datetime:
    return datetime.combine(day + timedelta(days=1), time.min, tzinfo=UTC)


def daily_limit(user: User) -> int | None:
    """Cupo de explicaciones del usuario, o None si no tiene (ADR-49)."""
    if user.is_admin or user.role == "owner" or user_meets_tier(user, "pro"):
        return None
    return settings.TUTOR_DAILY_LIMIT_PLUS


def daily_token_limit(user: User) -> int | None:
    """41.17: cinturón de seguridad por tokens, no una decisión de negocio.

    Se aplica a la misma población que ya tiene `daily_limit` (hoy, Plus) --
    quien ADR-49 ya declaró "ilimitado" (Pro Max, Creador, dueño, admin)
    sigue sin tope aquí tampoco: este cupo nunca puede bloquear a nadie que
    `daily_limit` ya deja pasar sin límite.
    """
    if daily_limit(user) is None:
        return None
    return settings.TUTOR_DAILY_TOKEN_LIMIT_PLUS


async def used_on(db: AsyncSession, user_id: uuid.UUID, day: date) -> int:
    row = await db.get(TutorUsage, (user_id, day))
    return row.explanations if row else 0


async def _increment_if_exists(
    db: AsyncSession, user_id: uuid.UUID, day: date, *, tokens: int = 0
) -> int | None:
    """`UPDATE ... SET explanations = explanations + 1`, atómico en la base:
    no hay lectura en Python que una segunda llamada pueda pisar. None si
    la fila de hoy todavía no existe (no afectó ninguna)."""
    result = await db.execute(
        update(TutorUsage)
        .where(TutorUsage.user_id == user_id, TutorUsage.day == day)
        .values(
            explanations=TutorUsage.explanations + 1,
            tokens_used=TutorUsage.tokens_used + tokens,
        )
        .returning(TutorUsage.explanations)
    )
    row = result.first()
    return int(row[0]) if row is not None else None


async def record(db: AsyncSession, user_id: uuid.UUID, day: date, *, tokens: int = 0) -> int:
    """Conteo incondicional -- para quien `daily_limit`/`daily_token_limit`
    ya dejan sin tope (ADR-49): no hay nada que reservar ni que bloquear,
    solo sumar lo que de verdad costó.

    Lee-suma-escribe en Python era una carrera real -- dos llamadas a
    /tutor/explain a la vez (dos pestañas, o un script) podían leer la
    misma fila antes de que ninguna hiciera commit, y la que comiteara
    segunda pisaba el incremento de la primera: dos explicaciones servidas
    (y dos llamadas reales al LLM cobradas) contaban como una sola. Fijado
    con `_increment_if_exists`, atómico; si la fila de hoy todavía no
    existe se crea con un `INSERT` protegido por savepoint, igual que
    `certification.grant`, para la misma carrera en la primera llamada del
    día entre dos usuarios -- un `UPDATE` que no afectó ninguna fila puede
    deberse a que otra petición ganó la carrera de crearla entre medias; se
    reintenta el incremento, que esta vez sí la encuentra.
    """
    updated = await _increment_if_exists(db, user_id, day, tokens=tokens)
    if updated is not None:
        return updated

    try:
        async with db.begin_nested():
            db.add(TutorUsage(user_id=user_id, day=day, explanations=1, tokens_used=tokens))
            await db.flush()
        return 1
    except IntegrityError:
        updated = await _increment_if_exists(db, user_id, day, tokens=tokens)
        if updated is None:
            raise
        return updated


async def reserve(
    db: AsyncSession,
    user_id: uuid.UUID,
    day: date,
    *,
    explanation_limit: int | None,
    token_limit: int | None,
    token_estimate: int,
) -> bool:
    """41.17: reserva atómica de un hueco (una explicación + el presupuesto
    de tokens peor-caso) ANTES de llamar al LLM.

    Antes, comprobar el cupo (`used_on`) y apuntarlo (`record`, después de
    la respuesta del LLM) eran dos pasos separados por la latencia del
    proveedor: la ventana en medio es justo donde dos peticiones a la vez
    veían las dos "cupo libre" y las dos seguían adelante -- con el límite
    en 20, Plus podía recibir 21 explicaciones (y pagar 21 llamadas reales
    al LLM). Aquí el chequeo del límite y la reserva son el mismo `UPDATE`
    condicional: la segunda petición encuentra la fila ya al borde y su
    `WHERE` no encaja, así que no actualiza nada y no debe llamar al
    proveedor.

    Devuelve False sin tocar la base si cualquiera de los dos cupos ya
    estaba al límite. `settle()`/`release()` ajustan la reserva después de
    la respuesta (o del fallo) del proveedor.
    """
    conditions = [TutorUsage.user_id == user_id, TutorUsage.day == day]
    if explanation_limit is not None:
        conditions.append(TutorUsage.explanations < explanation_limit)
    if token_limit is not None:
        conditions.append(TutorUsage.tokens_used < token_limit)

    result = await db.execute(
        update(TutorUsage)
        .where(*conditions)
        .values(
            explanations=TutorUsage.explanations + 1,
            tokens_used=TutorUsage.tokens_used + token_estimate,
        )
        .returning(TutorUsage.explanations)
    )
    if result.first() is not None:
        return True

    # El UPDATE no afectó ninguna fila: o no existe todavía (primera
    # llamada del día) o existe y el WHERE del límite la bloqueó. Hay que
    # distinguir los dos casos antes de decidir si crear la fila o negar.
    existing = await db.get(TutorUsage, (user_id, day))
    if existing is not None:
        return False  # la fila existe: el límite es lo que bloqueó el UPDATE

    try:
        async with db.begin_nested():
            db.add(
                TutorUsage(
                    user_id=user_id, day=day, explanations=1, tokens_used=token_estimate
                )
            )
            await db.flush()
        return True
    except IntegrityError:
        # Otra petición creó la fila entre nuestro SELECT y el INSERT:
        # reintentar entero, esta vez la encuentra el UPDATE de arriba.
        return await reserve(
            db,
            user_id,
            day,
            explanation_limit=explanation_limit,
            token_limit=token_limit,
            token_estimate=token_estimate,
        )


async def settle(
    db: AsyncSession, user_id: uuid.UUID, day: date, *, token_estimate: int, actual_tokens: int
) -> None:
    """Corrige la reserva peor-caso de tokens al valor real que devolvió el
    proveedor (41.17). El conteo de explicaciones ya quedó bien con la
    reserva: una explicación de verdad se sirvió."""
    delta = actual_tokens - token_estimate
    if delta:
        await db.execute(
            update(TutorUsage)
            .where(TutorUsage.user_id == user_id, TutorUsage.day == day)
            .values(tokens_used=TutorUsage.tokens_used + delta)
        )


async def release(db: AsyncSession, user_id: uuid.UUID, day: date, *, token_estimate: int) -> None:
    """Deshace una reserva cuando el proveedor falla antes de responder --
    "un fallo del proveedor no gasta cupo" ya era la regla; con la reserva
    atómica antes de la llamada, ahora hay que devolverla explícitamente en
    vez de simplemente no apuntarla."""
    await db.execute(
        update(TutorUsage)
        .where(TutorUsage.user_id == user_id, TutorUsage.day == day)
        .values(
            explanations=TutorUsage.explanations - 1,
            tokens_used=TutorUsage.tokens_used - token_estimate,
        )
    )
