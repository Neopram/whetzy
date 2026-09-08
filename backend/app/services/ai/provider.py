"""LLM provider abstraction.

Whetzy starts on Groq's free tier (Llama 3.3) and can swap to Claude later
without touching any caller — everything goes through `get_provider()`.
When no API key is configured the NullProvider returns a graceful,
content-grounded fallback so the tutor endpoint always responds.
"""

from __future__ import annotations

from typing import Any, Protocol

from app.core.config import settings


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
            return data["choices"][0]["message"]["content"].strip()  # type: ignore[no-any-return]


def _extract_grounding(user_prompt: str) -> str:
    """Pull the explanation/context block out of the built prompt for the
    fallback path so the answer stays grounded in real material."""
    marker = "CONTEXTO:"
    if marker in user_prompt:
        return user_prompt.split(marker, 1)[1].strip()
    return user_prompt.strip()


_provider: LLMProvider | None = None


def get_provider() -> LLMProvider:
    global _provider
    if _provider is not None:
        return _provider
    if settings.GROQ_API_KEY:
        _provider = GroqProvider(
            settings.GROQ_API_KEY, settings.GROQ_MODEL, settings.GROQ_BASE_URL
        )
    else:
        _provider = NullProvider()
    return _provider
