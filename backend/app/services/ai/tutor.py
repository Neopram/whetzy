"""AI tutor: personalized, content-grounded explanations.

Builds a prompt from the question, its canonical explanation (the grounding
context — the model is told to stay faithful to it), the skill it belongs to,
and three memory layers:

  Short-term  — conversation_history from the current session (injected as
                prior messages so the model can reference earlier exchanges).
  Long-term   — user's weak skills (p_known < threshold) injected into the
                system prompt so the tutor adapts its framing.
  Episodic    — times_missed for this specific question:
                  0–1: neutral explanation
                  2  : simpler, targets the misunderstanding
                  ≥3 : mandatory executable code example added
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.content import Question, Skill
from app.models.session import Response, StudySession
from app.models.user import User, UserSkillState
from app.services.ai import rag as rag_service
from app.services.ai.provider import NullProvider, get_provider

_SYSTEM = {
    "es": (
        "Eres el tutor de Whetzy, experto en Python e ingeniería de IA. "
        "Explicas con claridad, en español, adaptándote al nivel del estudiante. "
        "DEBES basarte en el CONTEXTO proporcionado y no inventar hechos. "
        "Si el estudiante ya falló varias veces, ataca el malentendido específico. "
        "Sé conciso (máx 5 frases), usa un ejemplo de código corto cuando ayude."
    ),
    "en": (
        "You are Whetzy's tutor, an expert in Python and AI engineering. "
        "You explain clearly, in English, adapting to the student's level. "
        "You MUST ground your answer in the provided CONTEXT and never invent facts. "
        "If the student has failed several times, target the specific misunderstanding. "
        "Be concise (max 5 sentences); use a short code example when it helps."
    ),
}


async def _times_missed(db: AsyncSession, user_id: uuid.UUID, question_id: str) -> int:
    result = await db.execute(
        select(func.count(Response.id))
        .join(StudySession, StudySession.id == Response.session_id)
        .where(
            StudySession.user_id == user_id,
            Response.question_id == question_id,
            Response.correct.is_(False),
        )
    )
    return int(result.scalar_one() or 0)


async def _get_weak_skills(
    db: AsyncSession,
    user_id: uuid.UUID,
    threshold: float = 0.4,
    limit: int = 3,
) -> list[Skill]:
    result = await db.execute(
        select(Skill)
        .join(UserSkillState, UserSkillState.skill_id == Skill.id)
        .where(
            UserSkillState.user_id == user_id,
            UserSkillState.p_known < threshold,
        )
        .order_by(UserSkillState.p_known)
        .limit(limit)
    )
    return list(result.scalars().all())


def _sanitize_history(
    history: list[dict[str, Any]] | None,
) -> list[dict[str, str]] | None:
    """`conversation_history` lo manda el cliente y se pega sin filtrar a los
    mensajes que ve el LLM (`provider.py` hace `messages.extend(history)`
    justo después del system prompt real). Sin esto, un turno con
    `role="system"` viajaba igual que cualquier otro y podía intentar
    sobreescribir las instrucciones reales (inyección de prompt), y sin
    tope de turnos ni de caracteres una sola petición podía costar mucho
    más de lo que el cupo por petición asume -- crítico en Pro Max, que no
    tiene cupo de peticiones (ADR-49).

    Se queda solo con los últimos `TUTOR_HISTORY_MAX_TURNS` turnos de role
    "user"/"assistant" con content de texto, recortados a
    `TUTOR_HISTORY_MAX_CHARS_PER_TURN`; cualquier otra cosa (role distinto,
    content que no es texto) se descarta en silencio, no se rechaza la
    petición entera por un turno suelto mal formado.
    """
    if not history:
        return None
    cleaned: list[dict[str, str]] = []
    for turn in history[-settings.TUTOR_HISTORY_MAX_TURNS :]:
        role = turn.get("role")
        content = turn.get("content")
        if role not in ("user", "assistant") or not isinstance(content, str):
            continue
        cleaned.append({"role": role, "content": content[: settings.TUTOR_HISTORY_MAX_CHARS_PER_TURN]})
    return cleaned or None


async def explain_question(
    db: AsyncSession,
    user: User,
    question_id: str,
    conversation_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    question = (
        await db.execute(select(Question).where(Question.id == question_id))
    ).scalar_one_or_none()
    if question is None:
        return {
            "degraded_fallback": False,
            "explanation": "",
            "provider": "none",
            "grounded": False,
            "times_missed": 0,
        }

    skill = (
        await db.execute(select(Skill).where(Skill.id == question.skill_id))
    ).scalar_one_or_none()

    lang = user.language if user.language in ("es", "en") else "es"
    q_text = question.question_es if lang == "es" else question.question_en
    canonical = question.explanation_es if lang == "es" else question.explanation_en
    skill_name = (skill.name_es if lang == "es" else skill.name_en) if skill else ""

    # --- Episodic memory: how many times has this user failed this question? ---
    missed = await _times_missed(db, user.id, question_id)
    miss_note = ""
    if missed >= 2:
        miss_note = (
            f"\nEl estudiante ya falló esta pregunta {missed} veces — explica de otra forma, más simple."
            if lang == "es"
            else f"\nThe student has missed this question {missed} times — explain differently, more simply."
        )
    if missed >= 3:
        # Episodic escalation: add mandatory code example
        miss_note += (
            "\n⚠️ OBLIGATORIO: incluye un ejemplo de código Python ejecutable (```python ... ```) que ilustre el concepto."
            if lang == "es"
            else "\n⚠️ MANDATORY: include an executable Python code example (```python ... ```) that illustrates the concept."
        )

    # --- Long-term memory: weak skills context ---
    weak_skills = await _get_weak_skills(db, user.id)
    system_prompt = _SYSTEM[lang]
    if weak_skills:
        names = [s.name_es if lang == "es" else s.name_en for s in weak_skills]
        weak_ctx = (
            f"\n[Áreas de dificultad del estudiante: {', '.join(names)}. Adapta la explicación.]"
            if lang == "es"
            else f"\n[Student struggles with: {', '.join(names)}. Adapt your explanation accordingly.]"
        )
        system_prompt = system_prompt + weak_ctx

    # --- RAG: related content chunks ---
    # n=3 (not 2): the question's own chunk is almost always the top hit
    # (self-retrieval ~99.8%, see tests/unit/test_rag.py), and it is excluded
    # from `related` below by doc_id — bumping n keeps up to 2 *other* chunks
    # available after that exclusion.
    rag_chunks = await rag_service.retrieve(f"{skill_name}: {q_text}", n=3)
    # `grounded` reflects a real retrieval hit carrying a citation — never a
    # fixed True. It is False whenever the index isn't built yet (startup,
    # or no lifespan in tests) or nothing in it shares a term with the query.
    grounded = any(chunk.source for chunk in rag_chunks)
    related = [chunk.text for chunk in rag_chunks if chunk.doc_id != f"q_{question_id}"][:2]
    related_block = ("\n\nCONTEXTO RELACIONADO:\n" + "\n---\n".join(related)) if related else ""

    user_prompt = (
        f"Tema/Skill: {skill_name}\n"
        f"Pregunta: {q_text}\n"
        f"{miss_note}\n\n"
        f"CONTEXTO: {canonical}"
        f"{related_block}"
    )

    # --- Short-term memory: prior conversation turns ---
    # history is a list of {"role": "user"|"assistant", "content": "..."}
    # passed directly to the provider as prior messages.
    history = _sanitize_history(conversation_history)

    provider = get_provider()
    complete_named = getattr(provider, "complete_named", None)
    if complete_named is not None:
        explanation, provider_name = await complete_named(
            system_prompt, user_prompt, max_tokens=500, history=history
        )
    else:
        explanation = await provider.complete(system_prompt, user_prompt, max_tokens=500, history=history)
        provider_name = provider.name

    # 41.5: un `GuardedProvider` configurado (hay API key) que agota el cupo
    # diario o falla la cadena entera cae en el `NullProvider` por dentro —
    # `complete_named` no es None aquí, así que se distingue de cuando
    # `get_provider()` ya devuelve un `NullProvider` a secas (sin API key:
    # degradado por diseño, no por un fallo puntual) y cobra igual. Solo el
    # primer caso es "no hubo explicación real" y no debe gastar cupo.
    degraded_fallback = complete_named is not None and provider_name == NullProvider.name

    return {
        "degraded_fallback": degraded_fallback,
        "explanation": explanation,
        "provider": provider_name,
        "grounded": grounded,
        "times_missed": missed,
    }
