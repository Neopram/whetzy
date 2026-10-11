"""LLM provider abstraction.

Whetzy starts on Groq's free tier (Llama 3.3) and can swap to Claude later
without touching any caller — everything goes through `get_provider()`.
When no API key is configured the NullProvider returns a graceful,
content-grounded fallback so the tutor endpoint always responds.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

from app.core.config import settings

logger = logging.getLogger("whetzy.llm")


class LLMProvider(Protocol):
    name: str

    async def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 600,
        history: list[dict[str, Any]] | None = None,
    ) -> str: ...


class NullProvider:
    """Fallback used when no LLM API key is configured. Returns the grounding
    context itself so the user still gets a useful, source-accurate answer."""

    name = "fallback"

    async def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 600,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        return (
            "💡 " + _extract_grounding(user)
        ).strip()

    async def complete_with_tokens(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 600,
        history: list[dict[str, Any]] | None = None,
    ) -> tuple[str, int]:
        """41.17: nunca llama a un LLM real, así que su coste es 0."""
        text = await self.complete(system, user, max_tokens=max_tokens, history=history)
        return text, 0


class GroqProvider:
    """Groq's OpenAI-compatible chat completions (Llama 3.x)."""

    name = "groq"

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    async def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 600,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        text, _ = await self.complete_with_tokens(
            system, user, max_tokens=max_tokens, history=history
        )
        return text

    async def complete_with_tokens(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 600,
        history: list[dict[str, Any]] | None = None,
    ) -> tuple[str, int]:
        """41.17: `usage.total_tokens` del propio Groq -- nada se estimaba
        antes, así que el cupo por tokens no tenía ninguna cifra real que
        comprobar."""
        import httpx

        messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user})

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.4,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"].strip()
            tokens = int(data.get("usage", {}).get("total_tokens", 0))
            return text, tokens


def _extract_grounding(user_prompt: str) -> str:
    """Pull the explanation/context block out of the built prompt for the
    fallback path so the answer stays grounded in real material."""
    marker = "CONTEXTO:"
    if marker in user_prompt:
        return user_prompt.split(marker, 1)[1].strip()
    return user_prompt.strip()


class GuardedProvider:
    """Primary LLM behind a daily call budget and an optional fallback (39.11, 39.12).

    A Groq outage or an exhausted budget used to surface as a 500 from the tutor;
    now the learner gets the next best answer: the fallback LLM if configured,
    else the grounded context (NullProvider). The budget is per process and per
    UTC day because Railway runs no Redis; with N workers the real ceiling is N×.
    """

    def __init__(
        self,
        primary: LLMProvider,
        fallback: LLMProvider | None,
        daily_limit: int,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._daily_limit = daily_limit
        self._day: str | None = None
        self._calls = 0
        self.name = primary.name

    def _take_budget(self) -> bool:
        from datetime import UTC, datetime

        today = datetime.now(UTC).date().isoformat()
        if today != self._day:
            self._day, self._calls = today, 0
        if self._daily_limit and self._calls >= self._daily_limit:
            return False
        self._calls += 1
        return True

    async def complete_named(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 600,
        history: list[dict[str, Any]] | None = None,
    ) -> tuple[str, str, int]:
        import httpx

        if not self._take_budget():
            logger.warning("llm_daily_budget_exhausted limit=%s", self._daily_limit)
            text, tokens = await NullProvider().complete_with_tokens(
                system, user, max_tokens=max_tokens, history=history
            )
            return text, NullProvider.name, tokens
        chain = [self._primary] + ([self._fallback] if self._fallback else [])
        for provider in chain:
            complete_with_tokens = getattr(provider, "complete_with_tokens", None)
            try:
                if complete_with_tokens is not None:
                    text, tokens = await complete_with_tokens(
                        system, user, max_tokens=max_tokens, history=history
                    )
                else:
                    text = await provider.complete(system, user, max_tokens=max_tokens, history=history)
                    tokens = 0
                return text, provider.name, tokens
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                logger.warning("llm_provider_unavailable provider=%s error=%s", provider.name, exc)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code < 500 and exc.response.status_code != 429:
                    raise
                logger.warning(
                    "llm_provider_error provider=%s status=%s", provider.name, exc.response.status_code
                )
        text, tokens = await NullProvider().complete_with_tokens(
            system, user, max_tokens=max_tokens, history=history
        )
        return text, NullProvider.name, tokens

    async def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 600,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        text, _, _ = await self.complete_named(system, user, max_tokens=max_tokens, history=history)
        return text


_provider: LLMProvider | None = None


def get_provider() -> LLMProvider:
    global _provider
    if _provider is not None:
        return _provider
    if settings.GROQ_API_KEY:
        fallback: LLMProvider | None = None
        if settings.LLM_FALLBACK_BASE_URL and settings.LLM_FALLBACK_API_KEY and settings.LLM_FALLBACK_MODEL:
            fallback = GroqProvider(
                settings.LLM_FALLBACK_API_KEY, settings.LLM_FALLBACK_MODEL, settings.LLM_FALLBACK_BASE_URL
            )
            fallback.name = "fallback-llm"
        _provider = GuardedProvider(
            GroqProvider(settings.GROQ_API_KEY, settings.GROQ_MODEL, settings.GROQ_BASE_URL),
            fallback,
            settings.LLM_DAILY_CALL_LIMIT,
        )
    else:
        _provider = NullProvider()
    return _provider
