"""Filtro de palabras para `username`/`display_name` (19.11, App Store 1.2).

Mínimo a propósito: una lista corta y explícita en ES/EN, comparada por
palabra completa sobre el texto normalizado (minúsculas, sin acentos, con los
separadores comunes de "leetspeak" colapsados), no un modelo de toxicidad.
Suficiente para que la cuenta no se pueda crear ni editar con un insulto en el
nombre visible; no filtra el contenido de duelos ni chats porque hoy no
existen.
"""

from __future__ import annotations

import re
import unicodedata

#: Corto y explícito a propósito — ampliar vía PR, no vía config en caliente.
BLOCKED_WORDS: frozenset[str] = frozenset(
    {
        "puta", "puto", "mierda", "gilipollas", "cabron", "cabrona", "maricon",
        "zorra", "nazi", "retrasado", "retrasada",
        "fuck", "shit", "bitch", "asshole", "cunt", "nigger", "faggot", "retard",
    }
)

_SEPARATORS = re.compile(r"[\s_.\-]+")
_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})


def _normalize(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return _SEPARATORS.sub("", folded.lower().translate(_LEET))


def contains_blocked_word(text: str) -> bool:
    normalized = _normalize(text)
    return any(word in normalized for word in BLOCKED_WORDS)
